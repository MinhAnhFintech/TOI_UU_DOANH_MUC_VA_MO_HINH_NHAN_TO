from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
import pandas as pd
import numpy as np
from datetime import datetime

from app.schemas.common import APIResponse
from app.schemas.backtest import BacktestRunRequest
from app.db.models import Job, PortfolioWeight as DBPortfolioWeight, BacktestSeries, BacktestMetric, PriceDaily
from app.core.database import get_db, AsyncSessionLocal
from app.backtest.engine import run_backtest as engine_run_backtest

router = APIRouter()

async def backtest_task(job_id: str, request: BacktestRunRequest):
    async with AsyncSessionLocal() as session:
        try:
            job = await session.get(Job, job_id)
            if not job:
                return
            job.status = 'running'
            await session.commit()
            
            # Fetch weights
            stmt_w = select(DBPortfolioWeight).where(DBPortfolioWeight.run_id == request.run_id)
            print("stmt_w", stmt_w)
            res_w = await session.execute(stmt_w)
            print("res_w", res_w)
            weight_rows = res_w.scalars().all()
            print("weight_rows", weight_rows)
            weight_dict = {w.ticker: w.weight for w in weight_rows}
            print("weight_dict", weight_dict)
            if not weight_dict:
                raise ValueError("No portfolio weights found for the given run_id")
                
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
                
            df_prices['date'] = pd.to_datetime(df_prices['date'])
            
            # Figure out the exact tickers that run_backtest will use
            ret_wide = df_prices.pivot_table(index='date', columns='ticker', values='ret').fillna(0)
            sorted_tickers = ret_wide.columns.tolist()
            
            weights_array = np.array([weight_dict.get(t, 0.0) for t in sorted_tickers])
            
            # Run backtest
            bt_result = engine_run_backtest(
                weights=weights_array,
                prices=df_prices,
                start_date=request.test_start.isoformat(),
                end_date=request.test_end.isoformat(),
                rebalance_freq=request.rebalance,
                fee_buy=request.fee_buy,
                fee_sell=request.fee_sell
            )
            
            # Save results
            run_id = job_id
            
            # Save series
            for _, row in bt_result.iterrows():
                db_s = BacktestSeries(
                    run_id=run_id,
                    date=row['date'].date(),
                    portfolio="proposed",
                    nav=float(row['nav']),
                    ret=float(row['ret']),
                    drawdown=float(row['drawdown']),
                    rolling_sharpe=float(row['rolling_sharpe']) if pd.notna(row['rolling_sharpe']) else None,
                    turnover=float(row['turnover']),
                    cost=float(row['cost'])
                )
                session.add(db_s)
                
            # Compute metrics
            cagr = float((bt_result['nav'].iloc[-1] / bt_result['nav'].iloc[0]) ** (252 / len(bt_result)) - 1) if len(bt_result) > 0 else 0
            vol = float(bt_result['ret'].std() * np.sqrt(252))
            sharpe = float(cagr / vol) if vol > 0 else 0
            max_dd = float(bt_result['drawdown'].min())
            
            db_m = BacktestMetric(
                run_id=run_id,
                portfolio="proposed",
                cagr=cagr,
                vol=vol,
                sharpe=sharpe,
                sortino=sharpe, # Simplified
                max_dd=max_dd,
                calmar=float(-cagr / max_dd) if max_dd < 0 else 0,
                turnover=float(bt_result['turnover'].sum())
            )
            session.add(db_m)
            
            job.status = 'done'
            job.progress = 100.0
            job.run_id = run_id
            await session.commit()
            
        except Exception as e:
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
    dates = []
    proposed = []
    for row in res.scalars().all():
        dates.append(row.date)
        proposed.append(row.nav)
        
    return APIResponse(data={
        "dates": dates,
        "vn30": proposed, # dummy
        "equal": proposed, # dummy
        "proposed": proposed
    })

@router.get("/drawdown", response_model=APIResponse)
async def get_drawdown(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(BacktestSeries).where(BacktestSeries.run_id == run_id).order_by(BacktestSeries.date)
    res = await db.execute(stmt)
    dates = []
    proposed = []
    for row in res.scalars().all():
        dates.append(row.date)
        proposed.append(row.drawdown)
        
    return APIResponse(data={
        "dates": dates,
        "vn30": proposed,
        "equal": proposed,
        "proposed": proposed,
        "max_dd": {"proposed": min(proposed) if proposed else 0}
    })

@router.get("/rolling-sharpe", response_model=APIResponse)
async def get_rolling_sharpe(
    run_id: str,
    window: int = 60,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(BacktestSeries).where(BacktestSeries.run_id == run_id).order_by(BacktestSeries.date)
    res = await db.execute(stmt)
    dates = []
    proposed = []
    for row in res.scalars().all():
        dates.append(row.date)
        proposed.append(row.rolling_sharpe if row.rolling_sharpe else 0)
        
    return APIResponse(data={
        "dates": dates,
        "vn30": proposed,
        "equal": proposed,
        "proposed": proposed
    })

@router.get("/metrics", response_model=APIResponse)
async def get_metrics(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(BacktestMetric).where(BacktestMetric.run_id == run_id)
    res = await db.execute(stmt)
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
            "cost": getattr(row, "cost", 0.0)
        })
    return APIResponse(data=data)

@router.get("/sensitivity", response_model=APIResponse)
async def get_sensitivity(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    return APIResponse(data=[])
