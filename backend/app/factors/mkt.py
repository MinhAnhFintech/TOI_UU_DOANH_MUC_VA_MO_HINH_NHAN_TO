import pandas as pd

def build_mkt(index_daily: pd.DataFrame, risk_free: pd.DataFrame, index_code: str = 'VN30') -> pd.Series:
    """MKT_t = R_market,t - Rf_t
    
    Reference: Fama & French (1993), Journal of Financial Economics
    """
    df = index_daily[index_daily['ticker'] == index_code].copy()
    df = df.sort_values('date')
    
    # Calculate market return from index close price
    df['market_ret'] = df['close'].pct_change()
    
    # Merge risk-free rate
    df = pd.merge(df, risk_free[['date', 'rf_daily']], on='date', how='left')
    
    # Subtract risk-free rate
    df['mkt'] = df['market_ret'] - df['rf_daily']
    
    # Set index to date and return the Series
    df = df.set_index('date')
    return df['mkt'].dropna()
