import numpy as np
from scipy.optimize import minimize


def _validate_inputs(mu, sigma, w_max):
    mu = np.asarray(mu, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    if mu.ndim != 1 or not len(mu):
        raise ValueError("mu must be a non-empty one-dimensional array")
    if sigma.shape != (len(mu), len(mu)):
        raise ValueError("sigma dimensions must match mu")
    if not np.isfinite(mu).all() or not np.isfinite(sigma).all():
        raise ValueError("mu and sigma must contain only finite values")
    if not 0 < w_max <= 1:
        raise ValueError("w_max must be in (0, 1]")
    if len(mu) * w_max < 1 - 1e-10:
        raise ValueError(f"Infeasible weight cap: {len(mu)} assets × {w_max:.4f} < 1")
    return mu, sigma


def _check_solution(res, n, w_max):
    if not res.success or res.x is None or not np.isfinite(res.x).all():
        raise RuntimeError(f"Portfolio optimizer failed: {res.message}")
    weights = np.asarray(res.x, dtype=float)
    if np.any(weights < -1e-7) or np.any(weights > w_max + 1e-7) or not np.isclose(weights.sum(), 1, atol=1e-6):
        raise RuntimeError("Optimizer returned weights outside portfolio constraints")
    return np.clip(weights, 0, w_max)

def optimize_max_sharpe(
    mu: np.ndarray,
    sigma: np.ndarray,
    rf: float,
    w_max: float = 0.15,
    n_restarts: int = 10
) -> dict:
    """Find Maximum Sharpe Ratio portfolio."""
    mu, sigma = _validate_inputs(mu, sigma, w_max)
    N = len(mu)
    
    # Scale up for numerical stability (annualize internally)
    mu_ann = mu * 252
    sigma_ann = sigma * 252 + np.eye(N) * 1e-6 # Ridge penalty to ensure positive definite
    rf_ann = rf
    
    def negative_sharpe(w):
        ret = np.sum(w * mu_ann)
        vol = np.sqrt(w.T @ sigma_ann @ w)
        if vol < 1e-8: return 1e5
        return -(ret - rf_ann) / vol

    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # Sum of weights = 1
    ]
    bounds = tuple((0.0, w_max) for _ in range(N))
    
    best_result = None
    # Equal weights are feasible whenever the cap validation above passes.
    starts = [np.full(N, 1.0 / N)]
    rng = np.random.default_rng(42)
    for _ in range(max(0, n_restarts - 1)):
        starts.append(rng.dirichlet(np.ones(N)))
    for w0 in starts:
        
        res = minimize(
            negative_sharpe, 
            w0, 
            method='SLSQP', 
            bounds=bounds, 
            constraints=constraints,
            options={'ftol': 1e-9, 'maxiter': 1000}
        )
        
        if res.success and np.isfinite(res.fun) and (best_result is None or res.fun < best_result.fun):
            best_result = res
    if best_result is None:
        raise RuntimeError("Maximum-Sharpe optimizer did not converge to a feasible solution")
    best_w = _check_solution(best_result, N, w_max)
        
    ret = np.sum(best_w * mu)
    vol = np.sqrt(best_w.T @ sigma @ best_w)
    
    return {
        'weights': best_w,
        'expected_return': float(ret),
        'volatility': float(vol),
        'sharpe': float((ret - rf) / vol) if vol > 1e-8 else 0.0
    }

def optimize_min_variance(
    sigma: np.ndarray,
    w_max: float = 0.15
) -> dict:
    """Find Minimum Variance portfolio."""
    sigma = np.asarray(sigma, dtype=float)
    if sigma.ndim != 2 or sigma.shape[0] != sigma.shape[1] or sigma.shape[0] == 0:
        raise ValueError("sigma must be a non-empty square matrix")
    N = sigma.shape[0]
    _validate_inputs(np.zeros(N), sigma, w_max)
    
    sigma_ann = sigma * 252 + np.eye(N) * 1e-6
    
    def variance(w):
        return w.T @ sigma_ann @ w

    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = tuple((0.0, w_max) for _ in range(N))
    
    w0 = np.ones(N) / N
    res = minimize(
        variance, 
        w0, 
        method='SLSQP', 
        bounds=bounds, 
        constraints=constraints
    )
    
    best_w = _check_solution(res, N, w_max)
    
    return {
        'weights': best_w,
        'volatility': float(np.sqrt(best_w.T @ sigma @ best_w))
    }

def equal_weight(n: int) -> dict:
    """Equal weight portfolio 1/N."""
    return {'weights': np.ones(n) / n}
