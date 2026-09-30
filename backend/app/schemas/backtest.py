from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any, Optional
from datetime import date
from typing import Literal

class BacktestRunRequest(BaseModel):
    run_id: str = Field(min_length=1)
    mode: Literal['fixed']
    rebalance: Literal['monthly', 'quarterly']
    fee_buy: float = Field(ge=0, le=0.1)
    fee_sell: float = Field(ge=0, le=0.1)
    test_start: date
    test_end: date

    @model_validator(mode='after')
    def validate_period(self):
        if self.test_start > self.test_end:
            raise ValueError('test_start must be on or before test_end')
        return self

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
