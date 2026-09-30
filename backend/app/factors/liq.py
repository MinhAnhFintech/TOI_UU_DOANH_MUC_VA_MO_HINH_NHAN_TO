import pandas as pd
import numpy as np


def build_liq(
    prices: pd.DataFrame,
    measure: str = 'amihud',
    window: int = 60,
    pct_threshold: float = 0.3
) -> pd.Series:
    """Build LIQ factor (Illiquid minus Liquid).
    
    Measures:
    - amihud: Amihud (2002) illiquidity = mean(|R_i| / Volume_i) over rolling window
    - turnover: Turnover = Volume_i / SharesOutstanding_i (lower = less liquid)
    - trading_value: Trading Value = Price * Volume (lower = less liquid)
    
    LIQ = R(Illiquid top 30%) - R(Liquid bottom 30%)
    
    Higher LIQ means illiquid stocks outperform liquid stocks.
    
    References:
        Amihud, Y. (2002). Illiquidity and stock returns: cross-section and
        time-series effects. Journal of Financial Markets, 5(1), 31-56.
    
    Args:
        prices: DataFrame with columns [date, ticker, ret, volume, value, close, shares_outstanding, market_cap]
        measure: Liquidity measure to use
        window: Rolling window for Amihud measure
        pct_threshold: Percentile threshold for top/bottom groups (default 0.3 = 30%)
    
    Returns:
        Series indexed by date with LIQ factor values
    """
    if window < 1 or not 0 < pct_threshold < 0.5:
        raise ValueError("window must be positive and pct_threshold must be between 0 and 0.5")
    prices = prices.copy()
    prices['date'] = pd.to_datetime(prices['date'])
    prices = prices.sort_values(['ticker', 'date'])
    
    if measure == 'amihud':
        # Amihud illiquidity: |return| / trading value
        prices['illiq_raw'] = prices['ret'].abs() / prices['value'].replace(0, np.nan)
        prices['illiq'] = prices.groupby('ticker')['illiq_raw'].transform(
            lambda x: x.rolling(window, min_periods=max(1, window // 2)).mean()
        )
        higher_is_illiquid = True
    elif measure == 'turnover':
        # Turnover: volume / shares outstanding (lower = less liquid)
        prices['illiq'] = -(prices['volume'] / prices['shares_outstanding'].replace(0, np.nan))
        prices['illiq'] = prices.groupby('ticker')['illiq'].transform(
            lambda x: x.rolling(window, min_periods=max(1, window // 2)).mean()
        )
        higher_is_illiquid = True  # Negated above, so higher = more illiquid
    elif measure == 'trading_value':
        # Trading value: price * volume (lower = less liquid)
        prices['illiq'] = -(prices['close'] * prices['volume'])
        prices['illiq'] = prices.groupby('ticker')['illiq'].transform(
            lambda x: x.rolling(window, min_periods=max(1, window // 2)).mean()
        )
        higher_is_illiquid = True  # Negated
    else:
        raise ValueError(f"Unknown measure: {measure}. Use 'amihud', 'turnover', or 'trading_value'.")
    
    # For each date, sort stocks into illiquid (top 30%) and liquid (bottom 30%)
    results = []
    ret_wide = prices.pivot_table(index='date', columns='ticker', values='ret')
    illiq_wide = prices.pivot_table(index='date', columns='ticker', values='illiq')
    cap_wide = prices.pivot_table(index='date', columns='ticker', values='market_cap')
    
    illiq_wide = illiq_wide.shift(1)  # Lag signal by 1 day to prevent look-ahead bias
    cap_wide_lagged = cap_wide.shift(1)
    
    for date in ret_wide.index:
        illiq_day = illiq_wide.loc[date].dropna()
        if len(illiq_day) < 6:
            continue
        
        # Top 30% = most illiquid, Bottom 30% = most liquid
        top_pct = illiq_day.quantile(1 - pct_threshold)
        bot_pct = illiq_day.quantile(pct_threshold)
        if not np.isfinite(top_pct) or not np.isfinite(bot_pct) or top_pct <= bot_pct:
            continue
        
        illiquid_tickers = illiq_day[illiq_day >= top_pct].index.tolist()
        liquid_tickers = illiq_day[illiq_day <= bot_pct].index.tolist()
        
        if not illiquid_tickers or not liquid_tickers:
            continue
        
        # Value-weighted returns
        r_illiq = _vw_return(ret_wide, cap_wide_lagged, illiquid_tickers, date)
        r_liquid = _vw_return(ret_wide, cap_wide_lagged, liquid_tickers, date)
        
        results.append({'date': date, 'liq': r_illiq - r_liquid})
    
    if not results:
        return pd.Series(dtype=float, name='liq')
    
    return pd.DataFrame(results).set_index('date')['liq']


def _vw_return(ret_wide, cap_wide, tickers, date):
    """Value-weighted return for a group of tickers."""
    available = [t for t in tickers if t in ret_wide.columns]
    if not available:
        return np.nan
    rets = ret_wide.loc[date, available].dropna()
    if rets.empty:
        return np.nan
    if date in cap_wide.index:
        caps = cap_wide.loc[date, rets.index]
        if caps.notna().all() and (caps > 0).all() and caps.sum() > 0:
            w = caps / caps.sum()
            return float((w * rets[w.index]).sum())
    return np.nan
