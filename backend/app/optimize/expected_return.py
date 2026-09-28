import numpy as np
import pandas as pd


def estimate_expected_returns(
    betas: pd.DataFrame,
    factor_means: pd.Series,
    rf_annual: float,
    include_alpha: bool = False,
    alphas: pd.Series = None,
    shrink_to_mean: bool = False,
    shrink_factor: float = 0.5,
    trading_days: int = 252
) -> pd.Series:
    """Estimate annualized expected returns from the factor model.
    
    mu_i = Rf + sum_k(beta_ik * lambda_k)
    where lambda_k = mean(factor_k) * 252 (annualized factor premium)
    
    If include_alpha: mu_i += alpha_i * 252
    If shrink_to_mean: mu_i = shrink_factor * mu_i + (1-shrink_factor) * mean(mu)
    
    CRITICAL: Only use TRAIN data (2021-2024) for estimation.
    Do NOT use any 2025 data.
    
    Args:
        betas: DataFrame (N x K) of factor loadings from regression
        factor_means: Series (K,) of mean daily factor returns from TRAIN period
        rf_annual: Annual risk-free rate
        include_alpha: Whether to add alpha to expected return
        alphas: Series (N,) of alphas from regression
        shrink_to_mean: Whether to shrink estimates toward cross-sectional mean
        shrink_factor: Shrinkage weight (0=full shrink, 1=no shrink)
        trading_days: Number of trading days per year
    
    Returns:
        Series (N,) of annualized expected returns
    """
    # Annualize factor premiums
    lambda_k = factor_means * trading_days  # (K,)
    
    # Ensure betas columns match factor_means index
    common_factors = betas.columns.intersection(factor_means.index)
    if len(common_factors) == 0:
        raise ValueError("No common factors between betas and factor_means")
    
    # mu_i = Rf + sum_k(beta_ik * lambda_k)
    factor_contribution = (betas[common_factors] * lambda_k[common_factors]).sum(axis=1)
    mu = rf_annual + factor_contribution
    
    if include_alpha and alphas is not None:
        mu = mu + alphas * trading_days  # Annualize alpha
    
    if shrink_to_mean:
        mu_mean = mu.mean()
        mu = shrink_factor * mu + (1 - shrink_factor) * mu_mean
    
    # Sanity check: warn if unreasonable
    if (mu.abs() > 0.5).any():  # > 50% annual return
        import warnings
        extreme = mu[mu.abs() > 0.5]
        warnings.warn(
            f"Extreme expected returns detected for: {extreme.index.tolist()}. "
            f"Consider using shrinkage."
        )
    
    mu.name = 'expected_return'
    return mu
