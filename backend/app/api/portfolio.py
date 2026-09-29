from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
import pandas as pd
import numpy as np
from datetime import datetime

from app.schemas.common import APIResponse
from app.schemas.portfolio import OptimizeRequest, FrontierResponse
from app.db.models import Job, PortfolioWeight as DBPortfolioWeight, FrontierPoint as DBFrontierPoint, PriceDaily, Stock
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
            
            df_wide = df.pivot(index='date', columns='ticker', values='ret').fillna(0)
            rf_daily = (1 + request.rf)**(1/252) - 1

            # --- COVARIANCE ---
            from app.optimize.covariance import estimate_covariance
            method_map = {
                'Sample Covariance': 'sample',
                'Ledoit-Wolf Shrinkage': 'ledoit_wolf',
                'Semi-Covariance': 'semi'
            }
            method = method_map.get(request.cov_estimator, 'sample')
            sigma_annual = estimate_covariance(df_wide, method=method, annualize=True, rf_daily=rf_daily)
            sigma_daily = sigma_annual / 252.0

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
                mu_daily = df_wide.mean().values
            else:
                df_factors = pd.DataFrame([f.__dict__ for f in factors]).drop(columns=['_sa_instance_state'])
                df_factors['date'] = pd.to_datetime(df_factors['date'])
                df_factors.set_index('date', inplace=True)
                
                stmt_excess = select(PriceDaily.date, PriceDaily.ticker, PriceDaily.excess_ret).where(
                    PriceDaily.date >= request.train_start,
                    PriceDaily.date <= request.train_end
                )
                res_excess = await session.execute(stmt_excess)
                df_excess = pd.DataFrame(res_excess.all(), columns=['date', 'ticker', 'excess_ret'])
                df_excess_wide = df_excess.pivot(index='date', columns='ticker', values='excess_ret').fillna(0)
                
                model = request.model
                if model == 'CAPM':
                    X = df_factors[['mkt']]
                elif model == 'FF3':
                    X = df_factors[['mkt', 'smb', 'hml']]
                elif model == 'FF5':
                    X = df_factors[['mkt', 'smb', 'hml', 'rmw', 'cma']]
                else:
                    X = df_factors[['mkt']]
                
                reg_results = run_regression(df_excess_wide, X, model)
                
                betas_dict = {}
                alphas_dict = {}
                for r in reg_results:
                    t = r['ticker']
                    alphas_dict[t] = r['alpha']
                    bd = {}
                    for f in X.columns:
                        bd[f] = r[f'beta_{f}']
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
                mu_annual = mu_annual.reindex(df_wide.columns).fillna(0)
                mu_daily = mu_annual.values / 252.0
            
            if request.objective == 'max_sharpe':
                res_opt = optimize_max_sharpe(mu_daily, sigma_daily, rf_daily, request.w_max)
            else:
                res_opt = optimize_min_variance(sigma_daily, request.w_max)
            
            run_id = job_id
            tickers = df_wide.columns
            weights = res_opt['weights']
            
            from sqlalchemy import delete
            await session.execute(delete(DBPortfolioWeight).where(DBPortfolioWeight.run_id == run_id))
            await session.execute(delete(DBFrontierPoint).where(DBFrontierPoint.run_id == run_id))
            
            for i, t in enumerate(tickers):
                if weights[i] > 1e-4:
                    db_w = DBPortfolioWeight(
                        run_id=run_id,
                        ticker=t,
                        weight=float(weights[i]),
                        mu=float(mu_daily[i] * 252),  # save annualized maybe? keep daily to be safe
                        sigma=float(np.sqrt(sigma_daily[i, i]) * np.sqrt(252)),
                    )
                    session.add(db_w)
            
            from app.optimize.frontier import compute_frontier
            
            frontier_data = compute_frontier(
                mu_daily, sigma_daily, request.rf, request.w_max, 
                n_points=20, n_random=0, tickers=list(tickers)
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
            await session.commit()
            
        except Exception as e:
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

@router.get("/weights", response_model=APIResponse)
async def get_weights(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DBPortfolioWeight).where(DBPortfolioWeight.run_id == run_id)
    res = await db.execute(stmt)
    data = []
    for row in res.scalars().all():
        data.append({
            "ticker": row.ticker,
            "weight": row.weight,
            "mu": row.mu,
            "sigma": row.sigma,
            "sector": "N/A"
        })
    return APIResponse(data=data)

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
            
    return APIResponse(data={
        "frontier": frontier,
        "tangency": tangency,
        "cml": [],
        "random": [],
        "assets": []
    })
