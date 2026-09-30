import pandas as pd
import numpy as np
from .costs import compute_transaction_costs


def compute_benchmark_nav(
    index_prices: pd.DataFrame,
    stock_prices: pd.DataFrame,
    tickers: list[str],
    start_date: str,
    end_date: str,
    fee_buy: float = 0.0015,
    fee_sell: float = 0.0025,
    rebalance_freq: str = 'quarterly',
    initial_capital: float = 100.0
) -> dict:
    """Compute benchmark NAV series for VN30 Index and Equal Weight portfolio.

    Benchmarks:
    1. VN30 Index: directly from index closing prices (price-return index).
       Note: if only price-return available, document that dividends are excluded.
    2. Equal Weight (1/N): rebalanced at specified frequency with transaction fees.
       Same rebalance dates and fee structure as the proposed portfolio.

    Both series start at initial_capital = 100.

    Args:
        index_prices: DataFrame with columns [date, index_code, close]
        stock_prices: DataFrame with columns [date, ticker, ret]
        tickers: List of 30 VN30 stock tickers
        start_date: Backtest start date (ISO format)
        end_date: Backtest end date (ISO format)
        fee_buy: Buying commission (default 0.15%)
        fee_sell: Selling commission + tax (default 0.25%)
        rebalance_freq: 'monthly' or 'quarterly'
        initial_capital: Starting NAV value

    Returns:
        Dict with:
        - vn30: pd.Series of VN30 Index NAV (indexed by date)
        - equal: pd.Series of Equal Weight NAV (indexed by date)
    """
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)

    # --- VN30 Index benchmark ---
    idx = index_prices[index_prices['index_code'] == 'VN30'].copy()
    idx['date'] = pd.to_datetime(idx['date'])
    idx = idx[(idx['date'] >= start_dt) & (idx['date'] <= end_dt)].sort_values(by='date')

    if len(idx) > 0:
        vn30_nav = (idx['close'] / idx['close'].iloc[0]) * initial_capital
        vn30_nav.index = idx['date'].values
        vn30_nav.name = 'vn30'
    else:
        vn30_nav = pd.Series(dtype=float, name='vn30')

    # --- Equal Weight benchmark ---
    sp = stock_prices.copy()
    sp['date'] = pd.to_datetime(sp['date'])
    sp = sp[(sp['date'] >= start_dt) & (sp['date'] <= end_dt)]

    ret_wide = sp.pivot_table(index='date', columns='ticker', values='ret')
    ret_wide = ret_wide.reindex(columns=tickers).sort_index()
    dates = ret_wide.index

    N = len(tickers)

    # Determine rebalance dates
    if rebalance_freq == 'monthly':
        freq_rule = 'ME'
    else:
        freq_rule = 'QE'

    rebalance_schedule = pd.date_range(start=start_dt, end=end_dt, freq=freq_rule)
    rebalance_set = set()
    for rd in rebalance_schedule:
        candidates = dates[dates <= rd]
        if len(candidates) > 0:
            rebalance_set.add(candidates[-1])

    nav = initial_capital
    w = np.ones(N) / N  # Start with equal weights
    nav_records = []

    for i, date in enumerate(dates):
        daily_ret = ret_wide.loc[date].fillna(0).values
        if i == 0:
            daily_ret = np.zeros(N, dtype=float)
        
        # Portfolio return using current weights
        port_ret = float(np.sum(w * daily_ret))
        gross_factor = 1 + port_ret
        post_return_weights = w * (1 + daily_ret)
        if gross_factor > 0 and np.isfinite(gross_factor):
            post_return_weights /= gross_factor
        else:
            post_return_weights = w.copy()

        # Transaction cost at rebalance
        cost = 0.0
        if date in rebalance_set and i > 0:
            w_target = np.ones(N) / N
            cost = compute_transaction_costs(post_return_weights, w_target, fee_buy, fee_sell)
            w = w_target.copy()
        else:
            w = post_return_weights

        nav = nav * gross_factor * (1 - cost)
        nav_records.append({'date': date, 'nav': nav})

    if nav_records:
        equal_df = pd.DataFrame(nav_records).set_index('date')
        equal_nav = equal_df['nav']
        equal_nav.name = 'equal'
    else:
        equal_nav = pd.Series(dtype=float, name='equal')

    return {
        'vn30': vn30_nav,
        'equal': equal_nav
    }
