from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import date

class RegressionRunRequest(BaseModel):
    models: List[str]
    tickers: Optional[List[str]] = None
    freq: str
    cov_type: str = 'HAC'
    start: date
    end: date

class RegressionResult(BaseModel):
    ticker: str
    model: str
    alpha: float
    alpha_t: float
    alpha_p: float
    betas: Dict[str, float]
    t_stats: Dict[str, float]
    p_values: Dict[str, float]
    adj_r2: float
    aic: float
    bic: float
    n_obs: int

class DiagnosticsResult(BaseModel):
    vif: Dict[str, float]
    durbin_watson: float
    bp_p: float
    jb_p: float
    adf: Dict[str, float]

class ModelComparison(BaseModel):
    model: str
    avg_adj_r2: float
    delta_adj_r2: Optional[float] = None
    grs: float
    grs_p: float
    mean_abs_alpha: float

class GRSResult(BaseModel):
    model: str
    grs_stat: float
    p_value: float
    mean_abs_alpha: float

class HypothesisResult(BaseModel):
    id: str
    statement: str
    statistic: float
    p_value: float
    verdict: str
    note: str

class QuantileResult(BaseModel):
    tau: float
    factor: str
    coef: float
    ci_low: float
    ci_high: float

class BestModel(BaseModel):
    model: str
    criteria: Dict[str, float]
    ranking: List[str]
