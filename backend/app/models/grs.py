import numpy as np
import scipy.stats

def grs_test(
    alphas: np.ndarray,        # (N,) vector of alphas
    residuals: np.ndarray,     # (T, N) matrix of residuals
    factors: np.ndarray,       # (T, K) matrix of factor values
) -> dict:
    """Gibbons-Ross-Shanken (1989) test."""
    alphas = np.asarray(alphas, dtype=float).reshape(-1)
    residuals = np.asarray(residuals, dtype=float)
    factors = np.asarray(factors, dtype=float)
    if factors.ndim == 1:
        factors = factors.reshape(-1, 1)
    if residuals.ndim != 2 or factors.ndim != 2:
        raise ValueError('Residuals and factors must be two-dimensional arrays.')
    T, N = residuals.shape
    K = factors.shape[1]
    if T != factors.shape[0] or len(alphas) != N:
        raise ValueError('GRS inputs must have matching observations and assets.')
    if N < 2 or K == 0 or T <= N + K:
        raise ValueError('GRS requires T > N + K and at least one asset and factor.')
    if not (np.isfinite(alphas).all() and np.isfinite(residuals).all() and np.isfinite(factors).all()):
        raise ValueError('GRS inputs must contain only finite values.')
    if np.any(np.var(factors, axis=0, ddof=1) <= np.finfo(float).eps):
        raise ValueError('GRS factors must have non-zero variance.')
    
    # The OLS residual covariance uses T-K-1 degrees of freedom.
    resid_cov = residuals.T @ residuals / (T - K - 1)
    
    # Covariance matrix of factors and mean of factors
    factor_cov = np.cov(factors, rowvar=False, ddof=1)
    factor_mean = np.mean(factors, axis=0)
    
    resid_cov_inv = np.linalg.inv(resid_cov)
    factor_cov_inv = np.linalg.inv(factor_cov) if K > 1 else 1 / np.var(factors, ddof=1)
    
    # Quadratic forms
    alpha_quad = alphas.T @ resid_cov_inv @ alphas
    factor_quad = factor_mean.T @ factor_cov_inv @ factor_mean if K > 1 else (factor_mean**2) * factor_cov_inv
    
    # GRS Statistic
    c = (T / N) * ((T - N - K) / (T - K - 1))
    grs_stat = c * (alpha_quad / (1 + factor_quad))
    
    # P-value from F-distribution
    p_value = scipy.stats.f.sf(grs_stat, N, T - N - K)
    
    return {
        'grs_stat': float(grs_stat),
        'p_value': float(p_value),
        'mean_abs_alpha': float(np.mean(np.abs(alphas))),
        'mean_alpha_sq': float(np.mean(alphas**2))
    }
