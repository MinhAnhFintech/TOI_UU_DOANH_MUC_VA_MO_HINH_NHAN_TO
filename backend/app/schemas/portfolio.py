from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date

class OptimizeRequest(BaseModel):
    model: str
    cov_estimator: str
    w_max: float
    rf: float
    train_start: date
    train_end: date
    objective: str

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
