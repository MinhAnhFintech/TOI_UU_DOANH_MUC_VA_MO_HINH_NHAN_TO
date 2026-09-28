import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import date

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.factors import FactorRecord, FactorStat, CorrelationMatrix, CumulativeReturn, FactorComparison
from app.db.models import FactorsDaily
from app.factors.stats import (
    compute_factor_stats,
    compute_correlation_matrix,
    compute_cumulative_returns,
    compare_with_ken_french
)

router = APIRouter()

async def get_factors_df(db: AsyncSession, from_date: Optional[date], to_date: Optional[date]) -> tuple[pd.DataFrame, list]:
    query = select(FactorsDaily)
    if from_date:
        query = query.where(FactorsDaily.date >= from_date)
    if to_date:
        query = query.where(FactorsDaily.date <= to_date)
    query = query.order_by(FactorsDaily.date)
    result = await db.execute(query)
    records = result.scalars().all()
    
    data = []
    for r in records:
        data.append({
            'date': r.date,
            'mkt': r.mkt,
            'smb': r.smb,
            'hml': r.hml,
            'rmw': r.rmw,
            'cma': r.cma,
            'liq': r.liq,
            'for_': r.for_factor,
            'vol': r.vol
        })
    df = pd.DataFrame(data)
    if not df.empty:
        df.set_index('date', inplace=True)
    return df, records

@router.get("", response_model=APIResponse)
async def get_factors(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    factors: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    df, records = await get_factors_df(db, from_date, to_date)
    
    data = []
    for r in records:
        item = {
            'date': r.date,
            'mkt': r.mkt,
            'smb': r.smb,
            'hml': r.hml,
            'rmw': r.rmw,
            'cma': r.cma,
            'liq': r.liq,
            'for_': r.for_factor,
            'vol': r.vol
        }
        if factors:
            factor_list = factors.split(',')
            item = {k: v for k, v in item.items() if k in factor_list or k == 'date'}
        data.append(item)
        
    return APIResponse(data=data)

@router.get("/stats", response_model=APIResponse)
async def get_factor_stats(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db)
):
    df, _ = await get_factors_df(db, from_date, to_date)
    if df.empty:
        return APIResponse(data=[])
    
    stats = compute_factor_stats(df)
    return APIResponse(data=stats)

@router.get("/correlation", response_model=APIResponse)
async def get_factor_correlation(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db)
):
    df, _ = await get_factors_df(db, from_date, to_date)
    if df.empty:
        return APIResponse(data={"factors": [], "matrix": []})
        
    corr = compute_correlation_matrix(df)
    return APIResponse(data=corr)

@router.get("/cumulative", response_model=APIResponse)
async def get_cumulative_returns(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db)
):
    df, _ = await get_factors_df(db, from_date, to_date)
    if df.empty:
        return APIResponse(data=[])
        
    cum_ret = compute_cumulative_returns(df)
    
    data = []
    for date_idx, row in cum_ret.iterrows():
        item = row.to_dict()
        item['date'] = date_idx
        data.append(item)
        
    return APIResponse(data=data)

@router.get("/compare-kf", response_model=APIResponse)
async def compare_with_kf(
    factor: str,
    db: AsyncSession = Depends(get_db)
):
    return APIResponse(data={"dates": [], "vn": [], "kf": [], "corr": 0.0})
