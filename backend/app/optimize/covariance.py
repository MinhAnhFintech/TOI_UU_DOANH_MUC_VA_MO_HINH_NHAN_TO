import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
import warnings


def estimate_covariance(
    returns: pd.DataFrame,
    method: str = 'ledoit_wolf',
    annualize: bool = True,
    trading_days: int = 252,
    rf_daily: float = 0.0
) -> np.ndarray:
    """Estimate the covariance matrix of returns.
    
    Methods:
    - sample: Standard sample covariance (np.cov)
    - ledoit_wolf: Ledoit-Wolf shrinkage estimator (more stable for N=30, T~1000)
    - semi: Semi-covariance using only downside returns (below Rf)
    
    Annualizes by multiplying by trading_days.
    Checks positive definiteness; applies eigenvalue clipping if needed.
    
    Args:
        returns: DataFrame (T x N) of daily returns
        method: Estimation method
        annualize: Whether to annualize
        trading_days: Trading days per year
        rf_daily: Daily risk-free rate (used for semi-covariance)
    
    Returns:
        ndarray (N x N) covariance matrix
    """
    returns_clean = returns.dropna()
    
    if method == 'sample':
        cov = np.cov(returns_clean.values, rowvar=False)
    
    elif method == 'ledoit_wolf':
        lw = LedoitWolf().fit(returns_clean.values)
        cov = lw.covariance_
    
    elif method == 'semi':
        # Semi-covariance: only use returns below rf_daily
        excess = returns_clean - rf_daily
        downside = excess.copy()
        downside[downside > 0] = 0  # Zero out upside returns
        cov = np.cov(downside.values, rowvar=False)
    
    else:
        raise ValueError(f"Unknown method: {method}. Use 'sample', 'ledoit_wolf', or 'semi'.")
    
    if annualize:
        cov = cov * trading_days
    
    # Check positive definiteness
    eigenvalues = np.linalg.eigvalsh(cov)
    if np.any(eigenvalues <= 0):
        warnings.warn(
            f"Covariance matrix is not positive definite. "
            f"Min eigenvalue: {eigenvalues.min():.6e}. Applying eigenvalue clipping."
        )
        # Eigenvalue clipping: set negative eigenvalues to small positive value
        eigvals, eigvecs = np.linalg.eigh(cov)
        eigvals = np.maximum(eigvals, 1e-8)
        cov = eigvecs @ np.diag(eigvals) @ eigvecs.T
        # Ensure symmetry
        cov = (cov + cov.T) / 2
    
    # Log condition number
    cond_number = np.linalg.cond(cov)
    if cond_number > 1e10:
        warnings.warn(f"High condition number: {cond_number:.2e}. Matrix may be ill-conditioned.")
    
    return cov
