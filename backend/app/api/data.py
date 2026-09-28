from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.data import StockInfo, PriceRecord, IndexRecord, QualityReport
from app.db.models import Stock, PriceDaily, IndexDaily

router = APIRouter()

@router.get("/stocks", response_model=APIResponse)
async def get_stocks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Stock))
    stocks = result.scalars().all()
    data = [{"ticker": s.ticker, "company_name": s.company_name, "sector": s.sector, "listing_date": s.listing_date} for s in stocks]
    return APIResponse(data=data)

@router.get("/prices", response_model=APIResponse)
async def get_prices(
    ticker: str,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    adjusted: bool = True,
    db: AsyncSession = Depends(get_db)
):
    query = select(PriceDaily).where(PriceDaily.ticker == ticker)
    if from_date:
        query = query.where(PriceDaily.date >= from_date)
    if to_date:
        query = query.where(PriceDaily.date <= to_date)
    query = query.order_by(PriceDaily.date)
    
    result = await db.execute(query)
    prices = result.scalars().all()
    data = [{"date": p.date, "ticker": p.ticker, "open": p.open, "high": p.high, "low": p.low, "close": p.close, "adj_close": p.adj_close, "volume": p.volume, "value": p.value} for p in prices]
    return APIResponse(data=data)

@router.get("/index", response_model=APIResponse)
async def get_index(
    code: str,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db)
):
    query = select(IndexDaily).where(IndexDaily.index_code == code)
    if from_date:
        query = query.where(IndexDaily.date >= from_date)
    if to_date:
        query = query.where(IndexDaily.date <= to_date)
    query = query.order_by(IndexDaily.date)
    
    result = await db.execute(query)
    index_data = result.scalars().all()
    data = [{"date": i.date, "index_code": i.index_code, "close": i.close} for i in index_data]
    return APIResponse(data=data)

@router.get("/quality", response_model=APIResponse)
async def get_quality(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    
    # Get all tickers
    stock_res = await db.execute(select(Stock.ticker))
    tickers = [r[0] for r in stock_res.all()]
    
    if not tickers:
        return APIResponse(data=[])
    
    # Get global date range
    date_range = await db.execute(
        select(func.min(PriceDaily.date), func.max(PriceDaily.date))
    )
    min_date, max_date = date_range.one()
    if not min_date or not max_date:
        return APIResponse(data=[])
    
    # Count total trading days (from any ticker)
    total_days_res = await db.execute(
        select(func.count(func.distinct(PriceDaily.date)))
    )
    total_days = total_days_res.scalar() or 1
    
    # Count days per ticker
    ticker_counts = await db.execute(
        select(PriceDaily.ticker, func.count(PriceDaily.date)).group_by(PriceDaily.ticker)
    )
    count_map = {r[0]: r[1] for r in ticker_counts.all()}
    
    data = []
    for t in tickers:
        count = count_map.get(t, 0)
        missing = max(0, total_days - count)
        missing_pct = missing / total_days if total_days > 0 else 0
        data.append({"ticker": t, "missing_pct": round(missing_pct, 4)})
    
    data.sort(key=lambda x: x['missing_pct'], reverse=True)
    return APIResponse(data=data)
