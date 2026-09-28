from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str
    DATA_START: str
    DATA_END: str
    TRAIN_END: str
    RF_SOURCE: str
    SEED: int = 42
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    TRADING_DAYS_PER_YEAR: int = 252
    W_MAX: float = 0.15
    FEE_BUY: float = 0.0015
    FEE_SELL: float = 0.0025
    HAC_LAG: int = 5
    FACTOR_REBALANCE_MONTHS: int = 6

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
