import pandas as pd

def compute_returns(prices_df: pd.DataFrame, risk_free_df: pd.DataFrame = None) -> pd.DataFrame:
    """Compute simple returns and excess returns."""
    df = prices_df.copy()
    df = df.sort_values(['ticker', 'date'])
    
    # Simple return: R_t = P_t / P_{t-1} - 1
    df['ret'] = df.groupby('ticker')['adj_close'].pct_change()
    
    # Compute market cap if shares_outstanding is available
    if 'shares_outstanding' in df.columns and ('market_cap' not in df.columns or df['market_cap'].isna().all()):
        df['market_cap'] = df['close'] * df['shares_outstanding']
        
    if risk_free_df is not None:
        rf = risk_free_df[['date', 'rf_daily']].drop_duplicates('date')
        df = pd.merge(df, rf, on='date', how='left', validate='many_to_one')
        df['excess_ret'] = df['ret'] - df['rf_daily']
        
    return df

def generate_quality_report(df: pd.DataFrame) -> dict:
    """Coverage by ticker, missing %, outlier list."""
    report = {}
    
    # Coverage
    report['tickers'] = df['ticker'].nunique()
    report['dates'] = df['date'].nunique()
    
    # Missing %
    report['missing_pct'] = df.isnull().mean().to_dict()
    
    # Outliers: |return| > 7.5% (HOSE limit is 7%)
    if 'ret' in df.columns:
        outliers = df[df['ret'].abs() > 0.075]
        report['outliers_count'] = len(outliers)
        
    return report
