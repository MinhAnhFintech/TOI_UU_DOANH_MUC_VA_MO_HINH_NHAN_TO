import numpy as np
import pandas as pd
from scipy.optimize import minimize

def optimize_max_sharpe(
    mu: np.ndarray,
    sigma: np.ndarray,
    rf: float,
    w_max: float = 0.15,
    n_restarts: int = 10
) -> dict:
    """Find Maximum Sharpe Ratio portfolio."""
    N = len(mu)
    
    # Scale up for numerical stability (annualize internally)
    mu_ann = mu * 252
    sigma_ann = sigma * 252 + np.eye(N) * 1e-6 # Ridge penalty to ensure positive definite
    rf_ann = rf if rf > 0.01 else rf * 252 # If rf is daily, annualize it roughly. Wait, rf passed in portfolio.py is already daily. Let's just use the raw rf passed and scale it.
    rf_ann = ((1 + rf)**252 - 1) if rf < 0.01 else rf # Approximation
    
    def negative_sharpe(w):
        ret = np.sum(w * mu_ann)
        vol = np.sqrt(w.T @ sigma_ann @ w)
        if vol < 1e-8: return 1e5
        return -(ret - rf_ann) / vol

    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # Sum of weights = 1
    ]
    bounds = tuple((0.0, w_max) for _ in range(N))
    
    best_sharpe = float('inf')
    best_w = None
    
    # Random restarts to avoid local minima
    np.random.seed(42)
    for _ in range(n_restarts):
        w0 = np.random.random(N)
        w0 /= np.sum(w0)
        
        res = minimize(
            negative_sharpe, 
            w0, 
            method='SLSQP', 
            bounds=bounds, 
            constraints=constraints,
            options={'ftol': 1e-9, 'maxiter': 1000}
        )
        
        # Accept even if not fully successful but we found a valid w
        if res.fun < best_sharpe and not np.isnan(res.fun):
            best_sharpe = res.fun
            best_w = res.x
            
    if best_w is None:
        best_w = np.ones(N) / N
        
    best_w = np.clip(best_w, 0, w_max)
    best_w /= np.sum(best_w) # normalize again just in case
        
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
    N = sigma.shape[0]
    
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
    
    best_w = res.x if not np.isnan(res.fun) else w0
    best_w = np.clip(best_w, 0, w_max)
    best_w /= np.sum(best_w)
    
    return {
        'weights': best_w,
        'volatility': float(np.sqrt(best_w.T @ sigma @ best_w))
    }

def equal_weight(n: int) -> dict:
    """Equal weight portfolio 1/N."""
    return {'weights': np.ones(n) / n}
