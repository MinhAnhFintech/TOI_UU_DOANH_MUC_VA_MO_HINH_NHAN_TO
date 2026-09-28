import numpy as np
from scipy.optimize import minimize
from .markowitz import optimize_max_sharpe, optimize_min_variance


def compute_frontier(
    mu: np.ndarray,
    sigma: np.ndarray,
    rf: float,
    w_max: float = 0.15,
    n_points: int = 50,
    n_random: int = 5000,
    seed: int = 42,
    tickers: list[str] = None
) -> dict:
    """Generate the Efficient Frontier, tangency portfolio, CML, and random portfolios.

    Algorithm:
    1. Find minimum variance portfolio
    2. Find maximum return achievable under constraints
    3. Generate n_points on the frontier (minimize variance for each target return)
    4. Find tangency (max Sharpe) portfolio
    5. Compute Capital Market Line (CML) from Rf through tangency
    6. Generate n_random Monte Carlo random portfolios for visualization

    Reference: Markowitz, H. (1952). Portfolio Selection. Journal of Finance, 7(1), 77-91.

    Args:
        mu: (N,) expected returns (annualized)
        sigma: (N, N) covariance matrix (annualized)
        rf: Annual risk-free rate
        w_max: Maximum weight per asset (default 15%)
        n_points: Number of frontier points
        n_random: Number of random portfolios for Monte Carlo cloud
        seed: Random seed for reproducibility
        tickers: List of ticker names

    Returns:
        Dict with frontier, tangency, cml, random, assets
    """
    N = len(mu)
    if tickers is None:
        tickers = [f'Stock_{i}' for i in range(N)]

    # Scale to annualized for numerical stability
    mu_ann = mu * 252
    sigma_ann = sigma * 252 + np.eye(N) * 1e-6
    rf_ann = ((1 + rf)**252 - 1) if rf < 0.01 else rf

    # 1. Tangency portfolio (Max Sharpe) - Pass daily, since it scales internally
    tangency = optimize_max_sharpe(mu, sigma, rf, w_max)
    # Scale tangency output to annual
    tangency['expected_return'] *= 252
    tangency['volatility'] *= np.sqrt(252)
    tangency['sharpe'] = (tangency['expected_return'] - rf_ann) / tangency['volatility'] if tangency['volatility'] > 0 else 0

    # 2. Minimum variance portfolio - Pass daily
    min_var = optimize_min_variance(sigma, w_max)
    min_var['volatility'] *= np.sqrt(252)
    min_var_ret = float(np.sum(min_var['weights'] * mu_ann))
    min_var['expected_return'] = min_var_ret
    min_var['sharpe'] = float((min_var_ret - rf_ann) / min_var['volatility']) if min_var['volatility'] > 0 else 0

    # 3. Frontier points: minimize variance for each target return
    min_ret = min_var_ret
    max_ret = float(np.max(mu_ann))
    target_returns = np.linspace(min_ret, max_ret, n_points)

    frontier = []
    for target_ret in target_returns:
        def variance(w):
            return w.T @ sigma_ann @ w

        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
            {'type': 'eq', 'fun': lambda w, tr=target_ret: np.sum(w * mu_ann) - tr}
        ]
        bounds = tuple((0.0, w_max) for _ in range(N))
        w0 = np.ones(N) / N

        try:
            res = minimize(variance, w0, method='SLSQP', bounds=bounds,
                           constraints=constraints, options={'ftol': 1e-12, 'maxiter': 1000})
            best_w = res.x if res.success or not np.isnan(res.fun) else w0
            best_w = np.clip(best_w, 0, w_max)
            best_w /= np.sum(best_w)
            
            vol = float(np.sqrt(best_w.T @ sigma_ann @ best_w))
            ret = float(np.sum(best_w * mu_ann))
            sharpe = float((ret - rf_ann) / vol) if vol > 0 else 0
            frontier.append({
                'ret': ret,
                'vol': vol,
                'sharpe': sharpe,
                'weights': {tickers[i]: float(best_w[i]) for i in range(N)}
            })
        except Exception:
            continue

    # 4. CML: line from Rf through tangency point
    cml = []
    tang_ret = tangency['expected_return']
    tang_vol = tangency['volatility']
    if tang_vol > 0:
        slope = (tang_ret - rf) / tang_vol
        for v in np.linspace(0, tang_vol * 1.5, 20):
            cml.append({'ret': float(rf + slope * v), 'vol': float(v)})

    # 5. Random portfolios (Monte Carlo cloud)
    np.random.seed(seed)
    random_portfolios = []
    for _ in range(n_random):
        w = np.random.random(N)
        w = np.minimum(w, w_max)        # Enforce w_max
        w = w / w.sum()                  # Normalize to sum=1

        ret = float(np.sum(w * mu))
        vol = float(np.sqrt(w.T @ sigma @ w))
        sharpe = float((ret - rf) / vol) if vol > 0 else 0
        random_portfolios.append({'ret': ret, 'vol': vol, 'sharpe': sharpe})

    # 6. Individual assets
    assets = []
    for i in range(N):
        vol = float(np.sqrt(sigma[i, i]))
        assets.append({
            'ticker': tickers[i],
            'ret': float(mu[i]),
            'vol': vol
        })

    return {
        'frontier': frontier,
        'tangency': {
            'ret': tangency['expected_return'],
            'vol': tangency['volatility'],
            'sharpe': tangency['sharpe'],
            'weights': {tickers[i]: float(tangency['weights'][i]) for i in range(N)}
        },
        'cml': cml,
        'random': random_portfolios,
        'assets': assets
    }

