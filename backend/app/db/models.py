from sqlalchemy import Column, String, Date, Numeric, BIGINT, Float, Integer, Text, Boolean, DateTime, Index
from sqlalchemy.orm import declarative_base

from app.db.base import Base

class Stock(Base):
    __tablename__ = 'stock'
    ticker = Column(String(10), primary_key=True)
    company_name = Column(Text)
    sector = Column(String(50))
    listing_date = Column(Date)

class VN30Constituent(Base):
    __tablename__ = 'vn30_constituent'
    ticker = Column(String, primary_key=True)
    start_date = Column(Date, primary_key=True)
    end_date = Column(Date)

class PriceDaily(Base):
    __tablename__ = 'price_daily'
    date = Column(Date, primary_key=True)
    ticker = Column(String, primary_key=True)
    open = Column(Numeric)
    high = Column(Numeric)
    low = Column(Numeric)
    close = Column(Numeric)
    adj_close = Column(Numeric)
    volume = Column(BIGINT)
    value = Column(Numeric)
    shares_outstanding = Column(BIGINT)
    market_cap = Column(Numeric)
    ret = Column(Float)
    excess_ret = Column(Float)
    
    __table_args__ = (
        Index('idx_price_daily_date_ticker', 'date', 'ticker'),
    )

class IndexDaily(Base):
    __tablename__ = 'index_daily'
    date = Column(Date, primary_key=True)
    index_code = Column(String, primary_key=True)
    close = Column(Numeric)

class RiskFree(Base):
    __tablename__ = 'risk_free'
    date = Column(Date, primary_key=True)
    rf_annual = Column(Float)
    rf_daily = Column(Float)
    source = Column(Text)

class FundamentalsQuarterly(Base):
    __tablename__ = 'fundamentals_quarterly'
    ticker = Column(String, primary_key=True)
    fiscal_year = Column(Integer, primary_key=True)
    quarter = Column(Integer, primary_key=True)
    report_date = Column(Date)
    book_equity = Column(Numeric)
    total_assets = Column(Numeric)
    net_income = Column(Numeric)
    roe = Column(Float)

class ForeignDaily(Base):
    __tablename__ = 'foreign_daily'
    date = Column(Date, primary_key=True)
    ticker = Column(String, primary_key=True)
    foreign_owned_pct = Column(Float)
    room_total_pct = Column(Float)
    room_remaining_pct = Column(Float)
    net_foreign_buy_value = Column(Numeric)

class KFFfactorsDaily(Base):
    __tablename__ = 'kff_factors_daily'
    date = Column(Date, primary_key=True)
    mkt_rf = Column(Float)
    smb = Column(Float)
    hml = Column(Float)
    rmw = Column(Float)
    cma = Column(Float)
    rf = Column(Float)
    
    __table_args__ = (
        Index('idx_kff_factors_daily_date', 'date'),
    )

class FactorsDaily(Base):
    __tablename__ = 'factors_daily'
    date = Column(Date, primary_key=True)
    mkt = Column(Float)
    smb = Column(Float)
    hml = Column(Float)
    rmw = Column(Float)
    cma = Column(Float)
    liq = Column(Float)
    for_factor = Column('for_', Float)
    vol = Column(Float)
    
    __table_args__ = (
        Index('idx_factors_daily_date', 'date'),
    )

class RegressionResult(Base):
    __tablename__ = 'regression_result'
    run_id = Column(String, primary_key=True)
    model = Column(String, primary_key=True)
    ticker = Column(String, primary_key=True)
    alpha = Column(Float)
    alpha_t = Column(Float)
    alpha_p = Column(Float)
    beta_mkt = Column(Float, nullable=True)
    beta_mkt_t = Column(Float, nullable=True)
    beta_mkt_p = Column(Float, nullable=True)
    beta_smb = Column(Float, nullable=True)
    beta_smb_t = Column(Float, nullable=True)
    beta_smb_p = Column(Float, nullable=True)
    beta_hml = Column(Float, nullable=True)
    beta_hml_t = Column(Float, nullable=True)
    beta_hml_p = Column(Float, nullable=True)
    beta_rmw = Column(Float, nullable=True)
    beta_rmw_t = Column(Float, nullable=True)
    beta_rmw_p = Column(Float, nullable=True)
    beta_cma = Column(Float, nullable=True)
    beta_cma_t = Column(Float, nullable=True)
    beta_cma_p = Column(Float, nullable=True)
    beta_liq = Column(Float, nullable=True)
    beta_liq_t = Column(Float, nullable=True)
    beta_liq_p = Column(Float, nullable=True)
    beta_for = Column(Float, nullable=True)
    beta_for_t = Column(Float, nullable=True)
    beta_for_p = Column(Float, nullable=True)
    beta_vol = Column(Float, nullable=True)
    beta_vol_t = Column(Float, nullable=True)
    beta_vol_p = Column(Float, nullable=True)
    r2 = Column(Float)
    adj_r2 = Column(Float)
    aic = Column(Float)
    bic = Column(Float)
    n_obs = Column(Integer)

class GRSResult(Base):
    __tablename__ = 'grs_result'
    run_id = Column(String, primary_key=True)
    model = Column(String, primary_key=True)
    universe = Column(String, primary_key=True)
    grs_stat = Column(Float)
    p_value = Column(Float)
    mean_abs_alpha = Column(Float)

class HypothesisResult(Base):
    __tablename__ = 'hypothesis_result'
    run_id = Column(String, primary_key=True)
    hypothesis = Column(String, primary_key=True)
    statistic = Column(Float)
    p_value = Column(Float)
    verdict = Column(String)
    note = Column(Text)

class PortfolioRun(Base):
    __tablename__ = 'portfolio_run'
    run_id = Column(String, primary_key=True)
    config_json = Column(Text)
    config_hash = Column(String)
    best_model = Column(String)
    created_at = Column(DateTime)

class PortfolioWeight(Base):
    __tablename__ = 'portfolio_weight'
    run_id = Column(String, primary_key=True)
    ticker = Column(String, primary_key=True)
    weight = Column(Float)
    mu = Column(Float)
    sigma = Column(Float)

class FrontierPoint(Base):
    __tablename__ = 'frontier_point'
    run_id = Column(String, primary_key=True)
    idx = Column(Integer, primary_key=True)
    ret = Column(Float)
    vol = Column(Float)
    sharpe = Column(Float)
    is_tangency = Column(Boolean)

class BacktestSeries(Base):
    __tablename__ = 'backtest_series'
    run_id = Column(String, primary_key=True)
    date = Column(Date, primary_key=True)
    portfolio = Column(String, primary_key=True)
    nav = Column(Float)
    ret = Column(Float)
    drawdown = Column(Float)
    rolling_sharpe = Column(Float, nullable=True)
    turnover = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)

class BacktestMetric(Base):
    __tablename__ = 'backtest_metric'
    run_id = Column(String, primary_key=True)
    portfolio = Column(String, primary_key=True)
    cagr = Column(Float)
    vol = Column(Float)
    sharpe = Column(Float)
    sortino = Column(Float)
    max_dd = Column(Float)
    calmar = Column(Float)
    turnover = Column(Float)

class Job(Base):
    __tablename__ = 'job'
    job_id = Column(String, primary_key=True)
    type = Column(String)
    status = Column(String, default='pending')
    progress = Column(Float, default=0)
    run_id = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime)
