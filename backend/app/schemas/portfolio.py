from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any, Optional
from datetime import date

class OptimizeRequest(BaseModel):
    model: str
    cov_estimator: str
    w_max: float = Field(gt=0, le=1)
    rf: float = Field(ge=-0.05, le=1)
    train_start: date
    train_end: date
    objective: str

    @model_validator(mode="after")
    def validate_period(self):
        if self.train_start > self.train_end:
            raise ValueError("train_start must be on or before train_end")
        if self.objective not in {"max_sharpe", "min_variance"}:
            raise ValueError("objective must be max_sharpe or min_variance")
        return self

class PortfolioWeight(BaseModel):
    ticker: str
    weight: float
    mu: float
    sigma: float
    sector: str

class FrontierPoint(BaseModel):
    ret: float
    vol: float
    sharpe: float

class FrontierResponse(BaseModel):
    frontier: List[FrontierPoint]
    tangency: Dict[str, Any]
    cml: List[FrontierPoint]
    random: List[FrontierPoint]
    assets: List[Dict[str, Any]]
