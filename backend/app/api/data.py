from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
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
    data = []
    for price in prices:
        use_adjusted = adjusted and price.adj_close is not None and price.close not in (None, 0)
        scale = price.adj_close / price.close if use_adjusted else 1
        data.append({
            "date": price.date,
            "ticker": price.ticker,
            "open": price.open * scale if price.open is not None else None,
            "high": price.high * scale if price.high is not None else None,
            "low": price.low * scale if price.low is not None else None,
            "close": price.adj_close if use_adjusted else price.close,
            "adj_close": price.adj_close,
            "volume": price.volume,
            "value": price.value,
        })
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
    # Get all tickers
    stock_res = await db.execute(select(Stock.ticker))
    tickers = [r[0] for r in stock_res.all()]
    
    if not tickers:
        return APIResponse(data=[])
    
    # Count actual market dates, then compare each ticker only from its listing date.
    market_dates_res = await db.execute(
        select(IndexDaily.date).where(IndexDaily.index_code == 'VN30').distinct()
    )
    market_dates = [row[0] for row in market_dates_res.all()]
    if not market_dates:
        market_dates_res = await db.execute(select(PriceDaily.date).distinct())
        market_dates = [row[0] for row in market_dates_res.all()]
    if not market_dates:
        return APIResponse(data=[])
    first_date, last_date = min(market_dates), max(market_dates)

    # Fetch listing dates without changing the previous ticker response contract.
    stock_rows = (await db.execute(select(Stock.ticker, Stock.listing_date))).all()
    listing_dates = {ticker: listing for ticker, listing in stock_rows}
    ticker_counts = await db.execute(
        select(PriceDaily.ticker, func.count(func.distinct(PriceDaily.date)))
        .join(Stock, Stock.ticker == PriceDaily.ticker)
        .where(or_(Stock.listing_date.is_(None), PriceDaily.date >= Stock.listing_date))
        .group_by(PriceDaily.ticker)
    )
    count_map = {row[0]: row[1] for row in ticker_counts.all()}

    data = []
    for ticker in tickers:
        listing = listing_dates.get(ticker) or first_date
        expected_days = sum(listing <= day <= last_date for day in market_dates)
        observed_days = count_map.get(ticker, 0)
        missing_pct = max(0, expected_days - observed_days) / expected_days if expected_days else 0
        data.append({"ticker": ticker, "missing_pct": round(missing_pct, 4)})
    
    data.sort(key=lambda x: x['missing_pct'], reverse=True)
    return APIResponse(data=data)
