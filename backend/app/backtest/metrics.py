import pandas as pd
import numpy as np

def compute_metrics(
    nav: pd.Series,
    rf_daily: pd.Series = None,
    trading_days: int = 252
) -> dict:
    """Performance and risk metrics."""
    # Assuming nav is a pandas Series of values
    returns = nav.pct_change().dropna()
    
    n_years = len(returns) / trading_days
    
    cagr = (nav.iloc[-1] / nav.iloc[0]) ** (1 / n_years) - 1 if n_years > 0 else 0
    
    vol = returns.std() * np.sqrt(trading_days)
    
    if rf_daily is not None:
        rf_aligned = rf_daily.reindex(returns.index).fillna(0)
        excess_returns = returns - rf_aligned
    else:
        excess_returns = returns
        
    sharpe = (excess_returns.mean() / returns.std()) * np.sqrt(trading_days) if returns.std() != 0 else 0
    
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = downside_returns.std() * np.sqrt(trading_days)
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
    std = returns.rolling(window).std()
    return (mean / std) * np.sqrt(252)
