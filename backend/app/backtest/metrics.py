import pandas as pd
import numpy as np

def compute_metrics(
    nav: pd.Series,
    rf_daily: pd.Series = None,
    trading_days: int = 252
) -> dict:
    """Performance and risk metrics."""
    if nav is None or len(nav) < 2 or not np.isfinite(nav.to_numpy(dtype=float)).all():
        raise ValueError("At least two finite NAV observations are required")
    if (nav <= 0).any():
        raise ValueError("NAV values must remain positive")
    returns = nav.pct_change().dropna()
    
    n_years = len(returns) / trading_days
    
    cagr = (nav.iloc[-1] / nav.iloc[0]) ** (1 / n_years) - 1 if n_years > 0 else 0
    
    vol = returns.std() * np.sqrt(trading_days)
    
    if rf_daily is not None:
        rf_aligned = rf_daily.reindex(returns.index).fillna(0)
        excess_returns = returns - rf_aligned
    else:
        excess_returns = returns
        
    excess_std = excess_returns.std()
    sharpe = (excess_returns.mean() / excess_std) * np.sqrt(trading_days) if excess_std > 0 else 0
    
    downside_squared = np.minimum(excess_returns, 0) ** 2
    downside_std = np.sqrt(downside_squared.mean()) * np.sqrt(trading_days)
    sortino = (excess_returns.mean() * np.sqrt(trading_days)) / downside_std if downside_std != 0 else 0
    
    cum_max = nav.cummax()
    drawdown = nav / cum_max - 1
    max_dd = drawdown.min()
    
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0
    
    return {
        'cagr': float(cagr),
        'volatility': float(vol),
        'sharpe': float(sharpe),
        'sortino': float(sortino),
        'max_dd': float(max_dd),
        'calmar': float(calmar)
    }

def compute_drawdown_series(nav: pd.Series) -> pd.Series:
    """Drawdown = NAV / cummax(NAV) - 1"""
    return nav / nav.cummax() - 1

def compute_rolling_sharpe(
    returns: pd.Series,
    rf_daily: pd.Series,
    window: int = 60
) -> pd.Series:
    """Rolling Sharpe ratio with specified window."""
    excess = returns - rf_daily
    mean = excess.rolling(window).mean()
    std = excess.rolling(window).std()
    return (mean / std) * np.sqrt(252)
