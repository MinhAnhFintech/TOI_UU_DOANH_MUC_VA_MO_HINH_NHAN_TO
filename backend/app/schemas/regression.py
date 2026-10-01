from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import List, Dict, Optional, Any, Literal
from datetime import date
from app.models.registry import get_model_factors

class RegressionRunRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    models: List[str]
    tickers: Optional[List[str]] = None
    freq: Literal['daily', 'weekly', 'monthly'] = 'daily'
    cov_type: Literal['HAC', 'HC0', 'HC1', 'HC2', 'HC3', 'nonrobust'] = 'HAC'
    start: date
    end: date

    @field_validator('models')
    @classmethod
    def validate_models(cls, models: List[str]) -> List[str]:
        if not models:
            raise ValueError('Select at least one regression model.')
        normalized = list(dict.fromkeys(model.upper() for model in models))
        for model in normalized:
            get_model_factors(model)
        return normalized

    @model_validator(mode='after')
    def validate_date_range(self):
        if self.start > self.end:
            raise ValueError('Regression start date must not be after end date.')
        return self

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