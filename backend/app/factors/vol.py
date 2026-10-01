import pandas as pd
import numpy as np


def build_vol(
    prices: pd.DataFrame,
    measure: str = 'realized',
    window: int = 20,
    pct_threshold: float = 0.3
) -> pd.Series:
    """Build VOL factor (High Volatility minus Low Volatility).
    
    Measures:
    - realized: Realized volatility = std(return) rolling window
    - daily_std: Standard deviation of returns over full sample up to date
    - high_low_range: (High - Low) / Close
    
    VOL = R(High vol top 30%) - R(Low vol bottom 30%)
    
    Args:
        prices: DataFrame with [date, ticker, ret, high, low, close, market_cap]
        measure: Volatility measure
        window: Rolling window (default 20 trading days)
        pct_threshold: Top/bottom percentile
    
    Returns:
        Series indexed by date with VOL factor values
    """
    if window < 1 or not 0 < pct_threshold < 0.5:
        raise ValueError("window must be positive and pct_threshold must be between 0 and 0.5")
    prices = prices.copy()
    prices['date'] = pd.to_datetime(prices['date'])
    prices = prices.sort_values(['ticker', 'date'])
    
    if measure == 'realized':
        prices['vol_score'] = prices.groupby('ticker')['ret'].transform(
            lambda x: x.rolling(window, min_periods=max(1, window // 2)).std()
        )
    elif measure == 'daily_std':
        prices['vol_score'] = prices.groupby('ticker')['ret'].transform(
            lambda x: x.expanding(min_periods=20).std()
        )
    elif measure == 'high_low_range':
        prices['vol_score'] = (prices['high'] - prices['low']) / prices['close'].replace(0, np.nan)
        prices['vol_score'] = prices.groupby('ticker')['vol_score'].transform(
            lambda x: x.rolling(window, min_periods=max(1, window // 2)).mean()
        )
    else:
        raise ValueError(f"Unknown measure: {measure}")
    
    ret_wide = prices.pivot_table(index='date', columns='ticker', values='ret')
    vol_wide = prices.pivot_table(index='date', columns='ticker', values='vol_score')
    cap_wide = prices.pivot_table(index='date', columns='ticker', values='market_cap')
    
    vol_wide = vol_wide.shift(1)
    cap_wide_lagged = cap_wide.shift(1)
    # Chưa có vốn hoá (thiếu số cổ phiếu lưu hành): dùng trọng số bằng nhau thay vì để trống.
    equal_weight = not cap_wide.notna().to_numpy().any()
    
    results = []
    for date in ret_wide.index:
        vol_day = vol_wide.loc[date].dropna() if date in vol_wide.index else pd.Series(dtype=float)
        if len(vol_day) < 6:
            continue
        
        top_pct = vol_day.quantile(1 - pct_threshold)
        bot_pct = vol_day.quantile(pct_threshold)
        if not np.isfinite(top_pct) or not np.isfinite(bot_pct) or top_pct <= bot_pct:
            continue
        
        high_vol = vol_day[vol_day >= top_pct].index.tolist()
        low_vol = vol_day[vol_day <= bot_pct].index.tolist()
        
        if not high_vol or not low_vol:
            continue
        
        r_high = _vw_return(ret_wide, cap_wide_lagged, high_vol, date, equal_weight)
        r_low = _vw_return(ret_wide, cap_wide_lagged, low_vol, date, equal_weight)
        
        results.append({'date': date, 'vol': r_high - r_low})
    
    if not results:
        return pd.Series(dtype=float, name='vol')
    return pd.DataFrame(results).set_index('date')['vol']


def _vw_return(ret_wide, cap_wide, tickers, date, equal_weight=False):
    available = [t for t in tickers if t in ret_wide.columns]
    if not available:
        return np.nan
    rets = ret_wide.loc[date, available].dropna()
    if rets.empty:
        return np.nan
    if equal_weight:
        return float(rets.mean())
    if date in cap_wide.index:
        caps = cap_wide.reindex(columns=rets.index).loc[date]
        if caps.notna().all() and (caps > 0).all() and caps.sum() > 0:
            w = caps / caps.sum()
            return float((w * rets[w.index]).sum())
    return np.nan
