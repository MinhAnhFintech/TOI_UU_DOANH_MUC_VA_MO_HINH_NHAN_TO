from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
import pandas as pd
import numpy as np
from datetime import datetime
import asyncio
import json

from app.schemas.common import APIResponse
from app.schemas.portfolio import OptimizeRequest, FrontierResponse
from app.db.models import Job, PortfolioRun as DBPortfolioRun, PortfolioWeight as DBPortfolioWeight, FrontierPoint as DBFrontierPoint, PriceDaily, Stock
from app.core.database import get_db, AsyncSessionLocal
from app.optimize.markowitz import optimize_max_sharpe, optimize_min_variance

router = APIRouter()

async def portfolio_task(job_id: str, request: OptimizeRequest):
    async with AsyncSessionLocal() as session:
        try:
            job = await session.get(Job, job_id)
            if not job:
                return
            job.status = 'running'
            job.progress = 5.0
            await session.commit()
            
            # Fetch daily returns for training period
            stmt = select(PriceDaily.date, PriceDaily.ticker, PriceDaily.ret).where(
                PriceDaily.date >= request.train_start,
                PriceDaily.date <= request.train_end
            )
            res = await session.execute(stmt)
            prices = res.all()
            df = pd.DataFrame(prices, columns=['date', 'ticker', 'ret'])
            if df.empty:
                raise ValueError("No data found for training period.")
            job.progress = 15.0
            await session.commit()
            
            df_wide = df.pivot(index='date', columns='ticker', values='ret').sort_index()
            df_wide = df_wide.replace([np.inf, -np.inf], np.nan)
            if len(df_wide) < 30:
                raise ValueError("Training period has fewer than 30 market observations")
            coverage = df_wide.notna().mean()
            df_wide = df_wide.loc[:, coverage >= 0.95].dropna(axis=0, how='any')
            if df_wide.shape[1] == 0 or len(df_wide) < 30:
                raise ValueError("Insufficient complete return data for portfolio optimization")
            rf_daily = (1 + request.rf)**(1/252) - 1

            # --- EXPECTED RETURNS ---
            from app.db.models import FactorsDaily
            from app.models.regression import run_regression
            from app.optimize.expected_return import estimate_expected_returns
            
            stmt_f = select(FactorsDaily).where(
                FactorsDaily.date >= request.train_start,
                FactorsDaily.date <= request.train_end
            )
            res_f = await session.execute(stmt_f)
            factors = res_f.scalars().all()
            if not factors:
                raise ValueError("No factor observations are available for the training period")
            else:
                df_factors = pd.DataFrame([f.__dict__ for f in factors]).drop(columns=['_sa_instance_state'])
                df_factors.rename(columns={'for_factor': 'for_'}, inplace=True)
                df_factors['date'] = pd.to_datetime(df_factors['date'])
                df_factors.set_index('date', inplace=True)
                df_factors = df_factors.replace([np.inf, -np.inf], np.nan)
                
                stmt_excess = select(PriceDaily.date, PriceDaily.ticker, PriceDaily.excess_ret).where(
                    PriceDaily.date >= request.train_start,
                    PriceDaily.date <= request.train_end
                )
                res_excess = await session.execute(stmt_excess)
                df_excess = pd.DataFrame(res_excess.all(), columns=['date', 'ticker', 'excess_ret'])
                df_excess_wide = df_excess.pivot(index='date', columns='ticker', values='excess_ret')
                df_excess_wide = df_excess_wide.replace([np.inf, -np.inf], np.nan)
                
                model = request.model
                from app.models.registry import get_model_factors
                factor_cols = get_model_factors(model)
                missing_factors = [name for name in factor_cols if name not in df_factors.columns]
                if missing_factors:
                    raise ValueError(f"Selected model is missing factor data: {', '.join(missing_factors)}")
                X = df_factors[factor_cols].dropna()
                if len(X) < 30:
                    raise ValueError("Fewer than 30 complete factor observations are available")
                
                reg_results = await asyncio.to_thread(run_regression, df_excess_wide, X, model)
                if not reg_results:
                    raise ValueError("The selected factor model could not estimate any stock betas")
                
                betas_dict = {}
                alphas_dict = {}
                for r in reg_results:
                    t = r['ticker']
                    alphas_dict[t] = r['alpha']
                    bd = {}
                    for f in X.columns:
                        result_name = 'for' if f == 'for_' else f
                        bd[f] = r[f'beta_{result_name}']
                    betas_dict[t] = bd
                
                df_betas = pd.DataFrame.from_dict(betas_dict, orient='index')
                df_alphas = pd.Series(alphas_dict)
                factor_means = X.mean()
                
                mu_annual = estimate_expected_returns(
                    betas=df_betas,
                    factor_means=factor_means,
                    rf_annual=request.rf,
                    include_alpha=False,
                    alphas=df_alphas
                )
                eligible = df_wide.columns.intersection(mu_annual.index)
                if len(eligible) == 0:
                    raise ValueError("No stocks have both valid returns and factor betas")
                df_wide = df_wide[eligible]
                mu_annual = mu_annual.reindex(eligible)
                if not np.isfinite(mu_annual.values).all():
                    raise ValueError("Expected returns contain missing or invalid values")
                mu_daily = mu_annual.values / 252.0

            from app.optimize.covariance import estimate_covariance
            method_map = {
                'sample': 'sample', 'Sample Covariance': 'sample',
                'ledoit_wolf': 'ledoit_wolf', 'Ledoit-Wolf Shrinkage': 'ledoit_wolf',
                'semi': 'semi', 'Semi-Covariance': 'semi',
            }
            method = method_map.get(request.cov_estimator)
            if method is None:
                raise ValueError(f"Unknown covariance estimator: {request.cov_estimator}")
            sigma_annual = estimate_covariance(df_wide, method=method, annualize=True, rf_daily=rf_daily)
            sigma_daily = sigma_annual / 252.0
            
            if request.objective == 'max_sharpe':
                res_opt = await asyncio.to_thread(optimize_max_sharpe, mu_daily, sigma_daily, request.rf, request.w_max)
            else:
                res_opt = await asyncio.to_thread(optimize_min_variance, sigma_daily, request.w_max)
            job.progress = 65.0
            await session.commit()
            
            run_id = job_id
            tickers = df_wide.columns
            weights = res_opt['weights']
            
            from sqlalchemy import delete
            await session.execute(delete(DBPortfolioWeight).where(DBPortfolioWeight.run_id == run_id))
            await session.execute(delete(DBFrontierPoint).where(DBFrontierPoint.run_id == run_id))
            
            for i, t in enumerate(tickers):
                if weights[i] > 0.0:
                    db_w = DBPortfolioWeight(
                        run_id=run_id,
                        ticker=t,
                        weight=float(weights[i]),
                        mu=float(mu_daily[i] * 252),  # save annualized maybe? keep daily to be safe
                        sigma=float(np.sqrt(sigma_daily[i, i]) * np.sqrt(252)),
                    )
                    session.add(db_w)
            
            from app.optimize.frontier import compute_frontier
            
            frontier_data = await asyncio.to_thread(compute_frontier,
                mu_daily, sigma_daily, request.rf, request.w_max, 
                n_points=30, n_random=0, tickers=list(tickers)
            )
            
            # Save frontier points
            for idx, pt in enumerate(frontier_data['frontier']):
                db_f = DBFrontierPoint(
                    run_id=run_id,
                    idx=idx,
                    ret=float(pt['ret']),
                    vol=float(pt['vol']),
                    sharpe=float(pt['sharpe']),
                    is_tangency=False
                )
                session.add(db_f)
                
            # Save tangency
            tang = frontier_data['tangency']
            db_t = DBFrontierPoint(
                run_id=run_id,
                idx=999,
                ret=float(tang['ret']),
                vol=float(tang['vol']),
                sharpe=float(tang['sharpe']),
                is_tangency=True
            )
            session.add(db_t)
            
            job.status = 'done'
            job.progress = 100.0
            job.run_id = run_id
            run_config = {
                'model': request.model,
                'cov_estimator': request.cov_estimator,
                'w_max': request.w_max,
                'rf': request.rf,
                'objective': request.objective,
                'train_start': request.train_start.isoformat(),
                'train_end': request.train_end.isoformat(),
            }
            session.add(DBPortfolioRun(
                run_id=run_id,
                config_json=json.dumps(run_config, sort_keys=True),
                config_hash=None,
                best_model=request.model,
                created_at=datetime.utcnow(),
            ))
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            job = await session.get(Job, job_id)
            if job:
                job.status = 'error'
                job.error = str(e)
                await session.commit()

@router.post("/optimize", response_model=APIResponse)
async def optimize_portfolio(
    request: OptimizeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    new_job = Job(job_id=job_id, type="portfolio", status="pending", progress=0.0, created_at=datetime.utcnow())
    db.add(new_job)
    await db.commit()
    
    background_tasks.add_task(portfolio_task, job_id, request)
    return APIResponse(data={"job_id": job_id})

# Ngành mặc định (phân loại tham khảo) dùng khi bảng stocks chưa có dữ liệu ngành
SECTOR_FALLBACK = {
    "ACB": "Ngân hàng", "BID": "Ngân hàng", "CTG": "Ngân hàng", "HDB": "Ngân hàng",
    "MBB": "Ngân hàng", "SHB": "Ngân hàng", "SSB": "Ngân hàng", "STB": "Ngân hàng",
    "TCB": "Ngân hàng", "TPB": "Ngân hàng", "VCB": "Ngân hàng", "VIB": "Ngân hàng",
    "VPB": "Ngân hàng",
    "SSI": "Chứng khoán",
    "BVH": "Bảo hiểm",
    "BCM": "Bất động sản", "VHM": "Bất động sản", "VIC": "Bất động sản", "VRE": "Bất động sản",
    "FPT": "Công nghệ",
    "GAS": "Dầu khí & Năng lượng", "PLX": "Dầu khí & Năng lượng", "POW": "Dầu khí & Năng lượng",
    "GVR": "Cao su & Vật liệu", "HPG": "Thép & Vật liệu",
    "MSN": "Tiêu dùng", "SAB": "Tiêu dùng", "VNM": "Tiêu dùng",
    "MWG": "Bán lẻ",
    "VJC": "Hàng không",
}

@router.get("/weights", response_model=APIResponse)
async def get_weights(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DBPortfolioWeight, Stock.sector).outerjoin(
        Stock, Stock.ticker == DBPortfolioWeight.ticker
    ).where(DBPortfolioWeight.run_id == run_id)
    res = await db.execute(stmt)
    data = []
    for row, sector in res.all():
        data.append({
            "ticker": row.ticker,
            "weight": row.weight,
            "mu": row.mu,
            "sigma": row.sigma,
            "sector": sector or SECTOR_FALLBACK.get(row.ticker, "Khác")
        })
    return APIResponse(data=data)

@router.get("/config", response_model=APIResponse)
async def get_portfolio_config(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Cấu hình đã lưu của một lần tối ưu (mô hình, estimator, w_max, rf, giai đoạn Train)."""
    run = await db.get(DBPortfolioRun, run_id)
    if run is None or not run.config_json:
        return APIResponse(data={})
    try:
        config = json.loads(run.config_json)
    except ValueError:
        config = {}
    return APIResponse(data=config)

@router.get("/frontier", response_model=APIResponse)
async def get_frontier(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DBFrontierPoint).where(DBFrontierPoint.run_id == run_id).order_by(DBFrontierPoint.idx)
    res = await db.execute(stmt)
    frontier = []
    tangency = {}
    for row in res.scalars().all():
        pt = {"ret": row.ret, "vol": row.vol, "sharpe": row.sharpe}
        if row.is_tangency or row.idx == 999:
            tangency = pt
        else:
            frontier.append(pt)
            
    cml = []
    if tangency:
        rf = tangency['ret'] - tangency['sharpe'] * tangency['vol']
        cml = [
            {"vol": 0.0, "ret": rf},
            {"vol": tangency['vol'] * 1.5, "ret": rf + tangency['sharpe'] * (tangency['vol'] * 1.5)}
        ]
        
    return APIResponse(data={
        "frontier": frontier,
        "tangency": tangency,
        "cml": cml,
        "random": [],
        "assets": []
    })