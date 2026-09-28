from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date

class BacktestRunRequest(BaseModel):
    run_id: str
    mode: str
    rebalance: str
    fee_buy: float
    fee_sell: float
    test_start: date
    test_end: date

class EquityResponse(BaseModel):
    dates: List[date]
    vn30: List[float]
    equal: List[float]
    proposed: List[float]
    split_date: Optional[date] = None

class DrawdownResponse(BaseModel):
    dates: List[date]
    vn30: List[float]
    equal: List[float]
    proposed: List[float]
    max_dd: Dict[str, float]

class RollingSharpeResponse(BaseModel):
    dates: List[date]
    vn30: List[float]
    equal: List[float]
    proposed: List[float]

class MetricsRecord(BaseModel):
    portfolio: str
    cagr: float
    vol: float
    sharpe: float
    sortino: float
    max_dd: float
    calmar: float
    turnover: float
    cost: float

class SensitivityRecord(BaseModel):
    w_max: float
    estimator: str
    fee: float
    rebalance: str
    sharpe: float
    max_dd: float
    cagr: float
