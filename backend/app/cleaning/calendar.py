import pandas as pd

def align_trading_calendar(dfs: dict[str, pd.DataFrame]) -> dict:
    """Align all dataframes to common trading dates.
    Handle halted stocks (ffill max 5 days).
    Mark non-trading days.
    """
    # Find common dates
    all_dates = set()
    for name, df in dfs.items():
        if 'date' in df.columns:
            all_dates.update(df['date'].tolist())
            
    sorted_dates = sorted(list(all_dates))
    calendar = pd.DataFrame({'date': sorted_dates})
    
    aligned_dfs = {}
    for name, df in dfs.items():
        if 'date' not in df.columns:
            aligned_dfs[name] = df
            continue
            
        if 'ticker' in df.columns:
            # Panel data
            aligned = []
            for ticker, grp in df.groupby('ticker'):
                merged = pd.merge(calendar, grp, on='date', how='left')
                merged['ticker'] = ticker
                # ffill up to 5 days for halted stocks
                merged = merged.ffill(limit=5)
                aligned.append(merged)
            aligned_dfs[name] = pd.concat(aligned, ignore_index=True)
        else:
            # Time series data
            merged = pd.merge(calendar, df, on='date', how='left')
            merged = merged.ffill(limit=5)
            aligned_dfs[name] = merged
            
    return aligned_dfs
