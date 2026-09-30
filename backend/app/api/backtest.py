from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import uuid
import pandas as pd
import numpy as np
from datetime import datetime
import asyncio
import json

from app.schemas.common import APIResponse
from app.schemas.backtest import BacktestRunRequest
from app.db.models import Job, PortfolioRun as DBPortfolioRun, PortfolioWeight as DBPortfolioWeight, BacktestSeries, BacktestMetric, PriceDaily, IndexDaily
from app.core.database import get_db, AsyncSessionLocal
from app.backtest.engine import run_backtest as engine_run_backtest
from app.backtest.benchmarks import compute_benchmark_nav
from app.backtest.metrics import compute_metrics

router = APIRouter()

async def backtest_task(job_id: str, request: BacktestRunRequest):
    async with AsyncSessionLocal() as session:
        try:
            job = await session.get(Job, job_id)
            if not job:
                return
            job.status = 'running'
            job.progress = 5.0
            await session.commit()

            portfolio_run = await session.get(DBPortfolioRun, request.run_id)
            if portfolio_run is None or not portfolio_run.config_json:
                raise ValueError("This portfolio has no saved training-period metadata. Re-optimize it before backtesting.")
            try:
                saved_config = json.loads(portfolio_run.config_json)
                train_end = datetime.fromisoformat(saved_config['train_end']).date()
                portfolio_rf_annual = float(saved_config['rf'])
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError("The portfolio's saved training-period metadata is invalid. Re-optimize it before backtesting.") from exc
            if request.test_start <= train_end:
                raise ValueError(
                    f"Backtest must start after the portfolio training period ends ({train_end.isoformat()})."
                )
            
            # Fetch weights
            stmt_w = select(DBPortfolioWeight).where(DBPortfolioWeight.run_id == request.run_id)
            res_w = await session.execute(stmt_w)
            weight_rows = res_w.scalars().all()
            weight_dict = {w.ticker: w.weight for w in weight_rows}
            if not weight_dict:
                raise ValueError("No portfolio weights found for the given run_id")
            if not np.isclose(sum(weight_dict.values()), 1.0, atol=1e-6):
                raise ValueError("Saved portfolio weights do not sum to 1. Re-optimize the portfolio before backtesting.")
                
            tickers = list(weight_dict.keys())
            
            # Fetch prices
            stmt = select(PriceDaily.date, PriceDaily.ticker, PriceDaily.ret).where(
                PriceDaily.date >= request.test_start,
                PriceDaily.date <= request.test_end,
                PriceDaily.ticker.in_(tickers)
            )
            res = await session.execute(stmt)
            prices = res.all()
            df_prices = pd.DataFrame(prices, columns=['date', 'ticker', 'ret'])
            if df_prices.empty:
                raise ValueError("No price data found for the test period.")
            df_prices['ret'] = pd.to_numeric(df_prices['ret'], errors='coerce')
            if np.isinf(df_prices['ret'].to_numpy(dtype=float)).any():
                raise ValueError("Price returns contain infinite values; rebuild the price return data before backtesting.")
                
            df_prices['date'] = pd.to_datetime(df_prices['date'])
            
            # Figure out the exact tickers that run_backtest will use
            ret_wide = df_prices.pivot_table(index='date', columns='ticker', values='ret').fillna(0)
            if len(ret_wide) < 2:
                raise ValueError("At least two trading observations are required for backtesting.")
            sorted_tickers = ret_wide.columns.tolist()
            
            weights_array = np.array([weight_dict.get(t, 0.0) for t in sorted_tickers])
            # Use the same annual risk-free assumption that produced the saved
            # portfolio so optimization and backtest Sharpe ratios agree.
            rf_daily = (1 + portfolio_rf_annual) ** (1 / 252) - 1
            
            # Run backtest
            bt_result = await asyncio.to_thread(engine_run_backtest,
                weights=weights_array,
                prices=df_prices,
                start_date=request.test_start.isoformat(),
                end_date=request.test_end.isoformat(),
                rebalance_freq=request.rebalance,
                fee_buy=request.fee_buy,
                fee_sell=request.fee_sell,
                rf_daily=rf_daily,
            )
            job.progress = 65.0
            await session.commit()

            # Fetch index prices for benchmark
            stmt_idx = select(IndexDaily.date, IndexDaily.index_code, IndexDaily.close).where(
                IndexDaily.date >= request.test_start,
                IndexDaily.date <= request.test_end,
                IndexDaily.index_code == 'VN30'
            )
            res_idx = await session.execute(stmt_idx)
            df_index = pd.DataFrame(res_idx.all(), columns=['date', 'index_code', 'close'])
            df_index['close'] = pd.to_numeric(df_index['close'], errors='coerce')
            df_index = df_index.dropna(subset=['close'])
            if len(df_index) < 2 or (df_index['close'] <= 0).any():
                raise ValueError("At least two positive VN30 index observations are required for benchmark comparison.")

            # Compute benchmarks
            benchmarks = compute_benchmark_nav(
                index_prices=df_index,
                stock_prices=df_prices,
                tickers=sorted_tickers,
                start_date=request.test_start.isoformat(),
                end_date=request.test_end.isoformat(),
                fee_buy=request.fee_buy,
                fee_sell=request.fee_sell,
                rebalance_freq=request.rebalance
            )
            vn30_nav = benchmarks['vn30']
            equal_nav = benchmarks['equal']
            
            # Save results
            run_id = job_id
            
            # Compute VN30 returns/drawdown series
            # Convert index to date objects for consistent comparison with d
            vn30_nav.index = pd.to_datetime(vn30_nav.index).date
            equal_nav.index = pd.to_datetime(equal_nav.index).date
            
            vn30_ret = vn30_nav.pct_change().fillna(0)
            vn30_cummax = vn30_nav.cummax()
            vn30_dd = (vn30_nav / vn30_cummax - 1)
            vn30_excess = vn30_ret - rf_daily
            vn30_rolling_sharpe = (vn30_excess.rolling(60).mean() / vn30_excess.rolling(60).std() * np.sqrt(252)) if len(vn30_ret) > 60 else pd.Series(dtype=float)
            
            # Compute Equal Weight returns/drawdown series
            equal_ret = equal_nav.pct_change().fillna(0)
            equal_cummax = equal_nav.cummax()
            equal_dd = (equal_nav / equal_cummax - 1)
            equal_excess = equal_ret - rf_daily
            equal_rolling_sharpe = (equal_excess.rolling(60).mean() / equal_excess.rolling(60).std() * np.sqrt(252)) if len(equal_ret) > 60 else pd.Series(dtype=float)
            
            # Save series
            for _, row in bt_result.iterrows():
                d = row['date'].date()
                db_s = BacktestSeries(
                    run_id=run_id,
                    date=d,
                    portfolio="proposed",
                    nav=float(row['nav']),
                    ret=float(row['ret']),
                    drawdown=float(row['drawdown']),
                    rolling_sharpe=float(row['rolling_sharpe']) if pd.notna(row['rolling_sharpe']) else None,
                    turnover=float(row['turnover']),
                    cost=float(row['cost'])
                )
                session.add(db_s)
                
                # Add vn30 series with actual metrics
                if d in vn30_nav.index:
                    rs_vn = float(vn30_rolling_sharpe.get(d, 0)) if d in vn30_rolling_sharpe.index and pd.notna(vn30_rolling_sharpe.get(d)) else None
                    db_vn30 = BacktestSeries(
                        run_id=run_id, date=d, portfolio="vn30",
                        nav=float(vn30_nav.loc[d]),
                        ret=float(vn30_ret.get(d, 0)),
                        drawdown=float(vn30_dd.get(d, 0)),
                        rolling_sharpe=rs_vn,
                        turnover=0, cost=0
                    )
                    session.add(db_vn30)
                
                # Add equal series with actual metrics
                if d in equal_nav.index:
                    rs_eq = float(equal_rolling_sharpe.get(d, 0)) if d in equal_rolling_sharpe.index and pd.notna(equal_rolling_sharpe.get(d)) else None
                    db_equal = BacktestSeries(
                        run_id=run_id, date=d, portfolio="equal",
                        nav=float(equal_nav.loc[d]),
                        ret=float(equal_ret.get(d, 0)),
                        drawdown=float(equal_dd.get(d, 0)),
                        rolling_sharpe=rs_eq,
                        turnover=0, cost=0
                    )
                    session.add(db_equal)
                    

            # Use one metric implementation for the proposed and comparison portfolios.
            metric_rows = [
                ("proposed", bt_result.set_index(pd.to_datetime(bt_result['date']))['nav'], float(bt_result['turnover'].sum())),
                ("vn30", pd.Series(vn30_nav.values, index=pd.to_datetime(vn30_nav.index)), 0.0),
                ("equal", pd.Series(equal_nav.values, index=pd.to_datetime(equal_nav.index)), 0.0),
            ]
            for portfolio, nav_series, turnover in metric_rows:
                rf_series = pd.Series(rf_daily, index=nav_series.index)
                values = compute_metrics(nav_series, rf_daily=rf_series)
                session.add(BacktestMetric(
                    run_id=run_id,
                    portfolio=portfolio,
                    cagr=values['cagr'],
                    vol=values['volatility'],
                    sharpe=values['sharpe'],
                    sortino=values['sortino'],
                    max_dd=values['max_dd'],
                    calmar=values['calmar'],
                    turnover=turnover,
                ))
            
            job.status = 'done'
            job.progress = 100.0
            job.run_id = run_id
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            job = await session.get(Job, job_id)
            if job:
                job.status = 'error'
                job.error = str(e)
                await session.commit()

@router.post("/run", response_model=APIResponse)
async def run_backtest(
    request: BacktestRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    new_job = Job(job_id=job_id, type="backtest", status="pending", progress=0.0, created_at=datetime.utcnow())
    db.add(new_job)
    await db.commit()
    
    background_tasks.add_task(backtest_task, job_id, request)
    return APIResponse(data={"job_id": job_id})

@router.get("/equity", response_model=APIResponse)
async def get_equity(
    run_id: str,
    scale: str = 'linear',
    db: AsyncSession = Depends(get_db)
):
    stmt = select(BacktestSeries).where(BacktestSeries.run_id == run_id).order_by(BacktestSeries.date)
    res = await db.execute(stmt)
    
    df = pd.DataFrame([{'date': r.date, 'nav': float(r.nav) if r.nav else 0, 'portfolio': r.portfolio} for r in res.scalars().all()])
    if df.empty:
        return APIResponse(data={"dates": [], "vn30": [], "equal": [], "proposed": []})
    
    # Use pivot_table with aggfunc='first' to handle potential duplicates
    wide = df.pivot_table(index='date', columns='portfolio', values='nav', aggfunc='first')
    
    return APIResponse(data={
        "dates": [d.isoformat() for d in wide.index],
        "vn30": wide['vn30'].tolist() if 'vn30' in wide.columns else [],
        "equal": wide['equal'].tolist() if 'equal' in wide.columns else [],
        "proposed": wide['proposed'].tolist() if 'proposed' in wide.columns else []
    })

@router.get("/drawdown", response_model=APIResponse)
async def get_drawdown(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(BacktestSeries).where(BacktestSeries.run_id == run_id).order_by(BacktestSeries.date)
    res = await db.execute(stmt)

    df = pd.DataFrame([{'date': r.date, 'drawdown': float(r.drawdown) if r.drawdown else 0, 'portfolio': r.portfolio} for r in res.scalars().all()])
    if df.empty:
        return APIResponse(data={"dates": [], "vn30": [], "equal": [], "proposed": [], "max_dd": {}})
    
    # Use pivot_table with aggfunc='first' to handle potential duplicates
    wide = df.pivot_table(index='date', columns='portfolio', values='drawdown', aggfunc='first')
    
    vn30_dd = wide['vn30'] if 'vn30' in wide.columns else pd.Series(dtype=float)
    equal_dd = wide['equal'] if 'equal' in wide.columns else pd.Series(dtype=float)
    proposed_dd = wide['proposed'] if 'proposed' in wide.columns else pd.Series(dtype=float)
    
    return APIResponse(data={
        "dates": [d.isoformat() for d in wide.index],
        "vn30": vn30_dd.tolist() if len(vn30_dd) > 0 else [],
        "equal": equal_dd.tolist() if len(equal_dd) > 0 else [],
        "proposed": proposed_dd.tolist() if len(proposed_dd) > 0 else [],
        "max_dd": {
            "vn30": float(vn30_dd.min()) if len(vn30_dd) > 0 else 0,
            "equal": float(equal_dd.min()) if len(equal_dd) > 0 else 0,
            "proposed": float(proposed_dd.min()) if len(proposed_dd) > 0 else 0,
        }
    })

@router.get("/rolling-sharpe", response_model=APIResponse)
async def get_rolling_sharpe(run_id: str, window: int = 60, db: AsyncSession = Depends(get_db)):
    stmt = select(BacktestSeries).where(BacktestSeries.run_id == run_id).order_by(BacktestSeries.date)
    res = await db.execute(stmt)
    df = pd.DataFrame([{'date': r.date, 'rolling_sharpe': r.rolling_sharpe, 'portfolio': r.portfolio} for r in res.scalars().all()])
    if df.empty:
        return APIResponse(data={"dates": [], "vn30": [], "equal": [], "proposed": []})
    wide = df.pivot(index='date', columns='portfolio', values='rolling_sharpe')
    return APIResponse(data={
        "dates": [d.isoformat() for d in wide.index],
        "vn30": wide.get('vn30', pd.Series(dtype=float)).tolist(),
        "equal": wide.get('equal', pd.Series(dtype=float)).tolist(),
        "proposed": wide.get('proposed', pd.Series(dtype=float)).tolist()
    })

@router.get("/metrics", response_model=APIResponse)
async def get_metrics(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(BacktestMetric).where(BacktestMetric.run_id == run_id)
    res = await db.execute(stmt)
    cost_stmt = select(BacktestSeries.portfolio, func.coalesce(func.sum(BacktestSeries.cost), 0.0)).where(
        BacktestSeries.run_id == run_id
    ).group_by(BacktestSeries.portfolio)
    costs = dict((await db.execute(cost_stmt)).all())
    data = []
    for row in res.scalars().all():
        data.append({
            "portfolio": row.portfolio,
            "cagr": row.cagr,
            "vol": row.vol,
            "sharpe": row.sharpe,
            "sortino": row.sortino,
            "max_dd": row.max_dd,
            "calmar": row.calmar,
            "turnover": row.turnover,
            "cost": float(costs.get(row.portfolio, 0.0))
        })
    return APIResponse(data=data)

@router.get("/sensitivity", response_model=APIResponse)
async def get_sensitivity(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    return APIResponse(data=[])
