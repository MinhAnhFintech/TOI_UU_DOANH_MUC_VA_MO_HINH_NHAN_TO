import numpy as np
import pandas as pd
from .costs import compute_transaction_costs


def run_backtest(
    weights: np.ndarray,
    prices: pd.DataFrame,
    start_date: str,
    end_date: str,
    rebalance_freq: str = 'quarterly',
    fee_buy: float = 0.0015,
    fee_sell: float = 0.0025,
    initial_capital: float = 100.0
) -> pd.DataFrame:
    """Backtest a portfolio with weight drift and transaction costs.

    NAV_t = NAV_{t-1} × (1 + Σ w_i × R_i,t − cost_t)

    Between rebalance dates, weights drift with daily returns:
        w_i,t = w_i,t-1 × (1 + R_i,t) / Σ_j w_j,t-1 × (1 + R_j,t)

    At rebalance dates, weights are reset to target and transaction costs applied:
        cost_t = Σ max(Δw_i, 0) × fee_buy + Σ max(−Δw_i, 0) × fee_sell

    Mode 1 (split): Fixed weights from Train → hold through Test period.
    Mode 2 (rolling): Re-optimize every rebalance period (caller handles this).

    NO look-ahead bias: weights are determined BEFORE the test period begins.

    Args:
        weights: (N,) target portfolio weights
        prices: DataFrame with columns [date, ticker, ret] (daily simple returns)
                OR [date, ticker, adj_close] (will compute returns internally)
        start_date: Backtest start date (ISO format YYYY-MM-DD)
        end_date: Backtest end date (ISO format YYYY-MM-DD)
        rebalance_freq: 'monthly' or 'quarterly'
        fee_buy: Buying commission (default 0.15%)
        fee_sell: Selling commission + tax (default 0.25%, includes 0.1% tax)
        initial_capital: Starting NAV (default 100)

    Returns:
        DataFrame with columns: [date, nav, ret, drawdown, turnover, cost]
    """
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)

    df = prices.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]

    # Build returns matrix (date × ticker)
    if 'ret' in df.columns:
        ret_wide = df.pivot_table(index='date', columns='ticker', values='ret')
    else:
        price_wide = df.pivot_table(index='date', columns='ticker', values='adj_close')
        ret_wide = price_wide.pct_change()
        ret_wide = ret_wide.iloc[1:]  # Drop first NaN row

    ret_wide = ret_wide.sort_index().fillna(0)
    tickers = ret_wide.columns.tolist()
    dates = ret_wide.index

    # Ensure weights match tickers
    N = len(tickers)
    if len(weights) != N:
        raise ValueError(f"weights length ({len(weights)}) != number of tickers ({N})")

    # Determine rebalance dates
    if rebalance_freq == 'monthly':
        freq_rule = 'ME'
    else:  # quarterly
        freq_rule = 'QE'

    rebalance_schedule = pd.date_range(start=start_dt, end=end_dt, freq=freq_rule)
    rebalance_set = set()
    for rd in rebalance_schedule:
        candidates = dates[dates <= rd]
        if len(candidates) > 0:
            rebalance_set.add(candidates[-1])

    # Initialize
    target_weights = weights.copy()
    w = target_weights.copy()  # Current weights
    nav = initial_capital
    cum_max_nav = initial_capital

    results = []

    for i, date in enumerate(dates):
        daily_ret = ret_wide.loc[date].values  # (N,) returns for each stock

        # Portfolio return with current (possibly drifted) weights
        port_ret = float(np.sum(w * daily_ret))

        # Check if this is a rebalance date
        turnover = 0.0
        cost = 0.0
        if date in rebalance_set and i > 0:
            # Compute turnover = total absolute weight changes
            turnover = float(np.sum(np.abs(target_weights - w)))
            # Compute transaction costs
            cost = compute_transaction_costs(w, target_weights, fee_buy, fee_sell)
            # Reset to target weights
            w = target_weights.copy()
        else:
            # Let weights drift with returns
            w_new = w * (1 + daily_ret)
            w_sum = w_new.sum()
            if w_sum > 0 and not np.isnan(w_sum):
                w = w_new / w_sum
            # If sum is 0 or NaN (all stocks -100%), keep previous weights

        # Update NAV
        nav = nav * (1 + port_ret - cost)

        # Drawdown
        cum_max_nav = max(cum_max_nav, nav)
        drawdown = (nav / cum_max_nav) - 1 if cum_max_nav > 0 else 0

        results.append({
            'date': date,
            'nav': nav,
            'ret': port_ret - cost,
            'drawdown': drawdown,
            'turnover': turnover,
            'cost': cost
        })

    result_df = pd.DataFrame(results)

    # Add rolling Sharpe (60-day window)
    if len(result_df) > 60:
        ret_series = result_df['ret']
        rolling_mean = ret_series.rolling(60).mean()
        rolling_std = ret_series.rolling(60).std()
        result_df['rolling_sharpe'] = (rolling_mean / rolling_std) * np.sqrt(252)
    else:
        result_df['rolling_sharpe'] = np.nan

    return result_df
