import pandas as pd
import numpy as np
from itertools import product
import warnings


def run_sensitivity_grid(
    run_backtest_fn,
    optimize_fn,
    estimate_mu_fn,
    estimate_cov_fn,
    returns_train: pd.DataFrame,
    returns_test: pd.DataFrame,
    betas: pd.DataFrame,
    factor_means: pd.Series,
    rf_annual: float,
    rf_daily: pd.Series,
    prices_test: pd.DataFrame,
    tickers: list[str],
    config_grid: dict = None,
    seed: int = 42
) -> list[dict]:
    """Run sensitivity analysis over a parameter grid.

    Tests how portfolio performance varies across different configurations:
    - w_max: Maximum weight constraint per stock
    - estimator: Covariance estimation method
    - fee: Transaction fee level
    - rebalance: Rebalancing frequency

    Default grid:
    - w_max: [0.10, 0.15, 0.20]
    - estimator: ['sample', 'ledoit_wolf', 'semi']
    - fee_buy: [0.0, 0.0015, 0.003]
    - rebalance: ['monthly', 'quarterly']

    For each combination, runs the full pipeline:
    estimate_mu → estimate_cov → optimize → backtest → compute_metrics

    Args:
        run_backtest_fn: Callable that runs backtest and returns NAV series
        optimize_fn: Callable for portfolio optimization (e.g., optimize_max_sharpe)
        estimate_mu_fn: Callable for expected return estimation
        estimate_cov_fn: Callable for covariance estimation
        returns_train: Training period returns DataFrame (T x N)
        returns_test: Test period returns DataFrame
        betas: Factor loadings DataFrame (N x K)
        factor_means: Mean daily factor returns (K,) from train period
        rf_annual: Annual risk-free rate
        rf_daily: Daily risk-free rate Series
        prices_test: Test period prices DataFrame
        tickers: List of stock tickers
        config_grid: Custom parameter grid dict
        seed: Random seed

    Returns:
        List of dicts with grid parameters and performance metrics
        [{w_max, estimator, fee_buy, rebalance, sharpe, max_dd, cagr, volatility}]
    """
    if config_grid is None:
        config_grid = {
            'w_max': [0.10, 0.15, 0.20],
            'estimator': ['sample', 'ledoit_wolf', 'semi'],
            'fee_buy': [0.0, 0.0015, 0.003],
            'rebalance': ['monthly', 'quarterly']
        }

    # Generate all parameter combinations
    keys = list(config_grid.keys())
    values = list(config_grid.values())
    combinations = list(product(*values))

    results = []

    for combo in combinations:
        params = dict(zip(keys, combo))

        try:
            # Step 1: Estimate covariance matrix
            cov = estimate_cov_fn(
                returns_train,
                method=params.get('estimator', 'ledoit_wolf')
            )

            # Step 2: Estimate expected returns
            mu = estimate_mu_fn(betas, factor_means, rf_annual)

            # Step 3: Optimize portfolio
            opt_result = optimize_fn(
                mu.values if hasattr(mu, 'values') else mu,
                cov,
                rf_annual,
                w_max=params.get('w_max', 0.15)
            )

            # Step 4: Run backtest
            fee_buy = params.get('fee_buy', 0.0015)
            fee_sell = fee_buy + 0.001  # Add 0.1% selling tax

            backtest_result = run_backtest_fn(
                weights=opt_result['weights'],
                prices=prices_test,
                start_date=str(returns_test.index[0].date()),
                end_date=str(returns_test.index[-1].date()),
                rebalance_freq=params.get('rebalance', 'quarterly'),
                fee_buy=fee_buy,
                fee_sell=fee_sell
            )

            # Step 5: Compute performance metrics
            from .metrics import compute_metrics
            nav_series = backtest_result if isinstance(backtest_result, pd.Series) else backtest_result.get('nav', pd.Series(dtype=float))
            metrics = compute_metrics(nav_series, rf_daily)

            result = {
                'w_max': params.get('w_max'),
                'estimator': params.get('estimator'),
                'fee_buy': fee_buy,
                'fee_sell': fee_sell,
                'rebalance': params.get('rebalance'),
                'sharpe': metrics.get('sharpe', float('nan')),
                'max_dd': metrics.get('max_dd', float('nan')),
                'cagr': metrics.get('cagr', float('nan')),
                'volatility': metrics.get('volatility', float('nan')),
                'sortino': metrics.get('sortino', float('nan')),
                'calmar': metrics.get('calmar', float('nan')),
            }
            results.append(result)

        except Exception as e:
            warnings.warn(f"Sensitivity run failed for {params}: {e}")
            result = {k: v for k, v in params.items()}
            result.update({
                'sharpe': float('nan'),
                'max_dd': float('nan'),
                'cagr': float('nan'),
                'volatility': float('nan'),
                'sortino': float('nan'),
                'calmar': float('nan'),
            })
            results.append(result)

    return results

