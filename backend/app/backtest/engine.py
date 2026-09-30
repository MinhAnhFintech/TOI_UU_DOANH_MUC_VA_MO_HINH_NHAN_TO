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
    initial_capital: float = 100.0,
    rf_daily: float = 0.0
) -> pd.DataFrame:
    """Backtest a portfolio with weight drift and transaction costs.

    NAV_t = NAV_{t-1} × (1 + Σ w_i × R_i,t − cost_t)

    Between rebalance dates, weights drift with daily returns:
        w_i,t = w_i,t-1 × (1 + R_i,t) / Σ_j w_j,t-1 × (1 + R_j,t)

    At rebalance dates, weights are reset to target and transaction costs applied:
        cost_t = Σ max(Δw_i, 0) × fee_buy + Σ max(−Δw_i, 0) × fee_sell

    The target weights are estimated on the training period, then restored at
    the selected monthly or quarterly rebalance dates during the test period.

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
    if df.empty or not {'date', 'ticker'}.issubset(df.columns):
        raise ValueError("prices must contain at least one row and date/ticker columns")
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
    if N == 0 or not np.isfinite(weights).all():
        raise ValueError("weights and prices must contain at least one valid asset")
    if not np.isclose(np.sum(weights), 1.0, atol=1e-6) or np.any(weights < -1e-8):
        raise ValueError("weights must be non-negative and sum to 1")
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

        # Invest at the first observed close so all benchmarks share the same base date.
        if i == 0:
            daily_ret = np.zeros(N, dtype=float)

        # Returns accrue against holdings entering the day.
        port_ret = float(np.sum(w * daily_ret))
        post_return_weights = w * (1 + daily_ret)
        gross_factor = 1 + port_ret
        if gross_factor > 0 and np.isfinite(gross_factor):
            post_return_weights = post_return_weights / gross_factor
        else:
            post_return_weights = w.copy()

        # Check if this is a rebalance date
        turnover = 0.0
        cost = 0.0
        if date in rebalance_set and i > 0:
            # Rebalance from actual post-return weights at the close.
            turnover = float(np.sum(np.abs(target_weights - post_return_weights)))
            # Compute transaction costs
            cost = compute_transaction_costs(post_return_weights, target_weights, fee_buy, fee_sell)
            # Reset to target weights
            w = target_weights.copy()
        else:
            w = post_return_weights

        # Update NAV
        net_factor = gross_factor * (1 - cost)
        nav = nav * net_factor

        # Drawdown
        cum_max_nav = max(cum_max_nav, nav)
        drawdown = (nav / cum_max_nav) - 1 if cum_max_nav > 0 else 0

        results.append({
            'date': date,
            'nav': nav,
            'ret': net_factor - 1,
            'drawdown': drawdown,
            'turnover': turnover,
            'cost': cost
        })

    result_df = pd.DataFrame(results)

    # Add rolling Sharpe (60-day window)
    if len(result_df) > 60:
        excess_series = result_df['ret'] - rf_daily
        rolling_mean = excess_series.rolling(60).mean()
        rolling_std = excess_series.rolling(60).std()
        result_df['rolling_sharpe'] = (rolling_mean / rolling_std) * np.sqrt(252)
    else:
        result_df['rolling_sharpe'] = np.nan

    return result_df
