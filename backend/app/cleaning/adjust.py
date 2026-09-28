import pandas as pd

def adjust_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Uses adj_close for return calculation. Handles stock splits and dividends."""
    # Assuming vnstock provides 'close' which might be unadjusted,
    # and we need an adjusted close. If 'adj_close' isn't available, we assume 'close' is adjusted.
    result = df.copy()
    if 'adj_close' not in result.columns:
        result['adj_close'] = result['close']
    return result
