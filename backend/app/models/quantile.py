import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.quantile_regression import QuantReg


def run_quantile_regression(
    excess_returns: pd.Series,
    factors: pd.DataFrame,
    taus: list[float] = None
) -> list[dict]:
    """Run quantile regression at specified quantiles.
    
    Estimates the conditional quantile function of excess returns
    given factor exposures. Useful for understanding how factor
    sensitivities vary across the return distribution.
    
    Args:
        excess_returns: Series of excess returns for a single stock
        factors: DataFrame of factor values (aligned with returns)
        taus: List of quantiles (default: [0.1, 0.25, 0.5, 0.75, 0.9])
    
    Returns:
        List of dicts with tau, factor name, coefficient, and confidence interval
    """
    if taus is None:
        taus = [0.1, 0.25, 0.5, 0.75, 0.9]
    
    taus = [float(tau) for tau in taus]
    if not taus or any(not 0 < tau < 1 for tau in taus):
        raise ValueError('Each quantile must be strictly between 0 and 1.')
    taus = sorted(set(taus))

    clean_factors = factors.replace([np.inf, -np.inf], np.nan)
    panel = pd.concat([excess_returns.rename('_y'), clean_factors], axis=1)
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna()
    if len(panel) < max(30, clean_factors.shape[1] + 3):
        raise ValueError('At least 30 complete observations are required for quantile regression.')
    y = panel['_y'].to_numpy(dtype=float)
    X = sm.add_constant(panel.drop(columns='_y'), has_constant='add')
    if np.linalg.matrix_rank(X.to_numpy(dtype=float)) < X.shape[1]:
        raise ValueError('Quantile regression factors are collinear on the selected sample.')
    
    results = []
    
    for tau in taus:
        try:
            res = QuantReg(y, X).fit(q=tau, max_iter=1000)
        except Exception as exc:
            raise RuntimeError(f'Quantile regression failed for tau={tau:g}: {exc}') from exc

        conf_int = np.asarray(res.conf_int(alpha=0.05), dtype=float)
        params = np.asarray(res.params, dtype=float)
        t_values = np.asarray(res.tvalues, dtype=float)
        p_values = np.asarray(res.pvalues, dtype=float)
        for i, factor in enumerate(X.columns):
            results.append({
                'tau': float(tau),
                'factor': str(factor),
                'coef': float(params[i]),
                'ci_low': float(conf_int[i, 0]),
                'ci_high': float(conf_int[i, 1]),
                't_stat': float(t_values[i]),
                'p_value': float(p_values[i]),
            })
    
    return results
