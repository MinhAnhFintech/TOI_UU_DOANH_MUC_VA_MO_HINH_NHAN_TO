from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class StockInfo(BaseModel):
    ticker: str
    company_name: str
    sector: str

class PriceRecord(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: float
    value: float

class IndexRecord(BaseModel):
    date: date
    close: float

class QualityReport(BaseModel):
    coverage_by_ticker: List[dict]
    missing_pct: List[dict]
    outliers: List[dict]
