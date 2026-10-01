import pandas as pd
import numpy as np


def build_for(
    prices: pd.DataFrame,
    foreign_data: pd.DataFrame,
    measure: str = 'ownership_pct',
    window: int = 20,
    pct_threshold: float = 0.3
) -> pd.Series:
    """Build FOR factor (High Foreign minus Low Foreign).
    
    FOR = R(High FOR top 30%) - R(Low FOR bottom 30%)
    
    If FOR is positive: stocks favored by foreign investors outperform.
    This captures the "foreign investor premium" specific to Vietnamese market
    where foreign ownership limits (room) create pricing effects.
    
    Args:
        prices: DataFrame with [date, ticker, ret, market_cap]
        foreign_data: DataFrame with [date, ticker, foreign_owned_pct, net_foreign_buy_value]
        measure: 'ownership_pct' or 'net_buy_20d'
        window: Rolling window for net_buy measure
        pct_threshold: Top/bottom percentile (default 0.3 = 30%)
    
    Returns:
        Series indexed by date with FOR factor values
    """
    if window < 1 or not 0 < pct_threshold < 0.5:
        raise ValueError("window must be positive and pct_threshold must be between 0 and 0.5")
    prices = prices.copy()
    foreign_data = foreign_data.copy()
    prices['date'] = pd.to_datetime(prices['date'])
    foreign_data['date'] = pd.to_datetime(foreign_data['date'])
    
    # Merge foreign data with prices
    merged = prices.merge(foreign_data[['date', 'ticker', 'foreign_owned_pct', 'net_foreign_buy_value']],
                          on=['date', 'ticker'], how='left')
    
    if measure == 'ownership_pct':
        merged['for_score'] = merged['foreign_owned_pct']
    elif measure == 'net_buy_20d':
        merged = merged.sort_values(['ticker', 'date'])
        merged['for_score'] = merged.groupby('ticker')['net_foreign_buy_value'].transform(
            lambda x: x.rolling(window, min_periods=1).mean()
        )
    else:
        raise ValueError(f"Unknown measure: {measure}")
    
    ret_wide = merged.pivot_table(index='date', columns='ticker', values='ret')
    for_wide = merged.pivot_table(index='date', columns='ticker', values='for_score').reindex(ret_wide.index)
    cap_wide = merged.pivot_table(index='date', columns='ticker', values='market_cap').reindex(ret_wide.index)
    
    for_wide = for_wide.shift(1)
    cap_wide_lagged = cap_wide.shift(1)
    # Chưa có vốn hoá (thiếu số cổ phiếu lưu hành): dùng trọng số bằng nhau thay vì để trống.
    equal_weight = not cap_wide.notna().to_numpy().any()
    
    results = []
    for date in ret_wide.index:
        for_day = for_wide.loc[date].dropna() if date in for_wide.index else pd.Series(dtype=float)
        if len(for_day) < 6:
            continue
        
        top_pct = for_day.quantile(1 - pct_threshold)
        bot_pct = for_day.quantile(pct_threshold)
        if not np.isfinite(top_pct) or not np.isfinite(bot_pct) or top_pct <= bot_pct:
            continue
        
        high_for = for_day[for_day >= top_pct].index.tolist()
        low_for = for_day[for_day <= bot_pct].index.tolist()
        
        if not high_for or not low_for:
            continue
        
        r_high = _vw_return(ret_wide, cap_wide_lagged, high_for, date, equal_weight)
        r_low = _vw_return(ret_wide, cap_wide_lagged, low_for, date, equal_weight)
        
        results.append({'date': date, 'for_': r_high - r_low})
    
    if not results:
        return pd.Series(dtype=float, name='for_')
    return pd.DataFrame(results).set_index('date')['for_']


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
