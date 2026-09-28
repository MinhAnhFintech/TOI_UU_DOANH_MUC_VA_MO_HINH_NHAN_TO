from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class FactorRecord(BaseModel):
    date: date
    mkt: float
    smb: float
    hml: float
    rmw: float
    cma: float
    liq: float
    for_: float
    vol: float

class FactorStat(BaseModel):
    factor: str
    mean: float
    std: float
    ann_mean: float
    t_stat: float
    p_value: float
    skew: float
    kurt: float

class CorrelationMatrix(BaseModel):
    factors: List[str]
    matrix: List[List[float]]

class CumulativeReturn(BaseModel):
    date: date
    mkt: float
    smb: float
    hml: float
    rmw: float
    cma: float
    liq: float
    for_: float
    vol: float

class FactorComparison(BaseModel):
    dates: List[date]
    vn: List[float]
    kf: List[float]
    corr: float
