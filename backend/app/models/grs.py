import numpy as np
import scipy.stats

def grs_test(
    alphas: np.ndarray,        # (N,) vector of alphas
    residuals: np.ndarray,     # (T, N) matrix of residuals
    factors: np.ndarray,       # (T, K) matrix of factor values
) -> dict:
    """Gibbons-Ross-Shanken (1989) test."""
    T, N = residuals.shape
    K = factors.shape[1]
    
    # Covariance matrix of residuals
    resid_cov = np.cov(residuals, rowvar=False)
    
    # Covariance matrix of factors and mean of factors
    factor_cov = np.cov(factors, rowvar=False)
    factor_mean = np.mean(factors, axis=0)
    
    try:
        resid_cov_inv = np.linalg.inv(resid_cov)
        factor_cov_inv = np.linalg.inv(factor_cov) if K > 1 else 1/np.var(factors)
    except np.linalg.LinAlgError:
        # Fallback to pseudo-inverse if singular
        resid_cov_inv = np.linalg.pinv(resid_cov)
        factor_cov_inv = np.linalg.pinv(factor_cov) if K > 1 else 1/np.var(factors)
    
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
