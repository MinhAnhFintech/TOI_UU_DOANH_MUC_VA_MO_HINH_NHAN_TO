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
    
    # Align data and drop NaN
    common_idx = excess_returns.dropna().index.intersection(factors.dropna().index)
    y = excess_returns.loc[common_idx].values
    X = sm.add_constant(factors.loc[common_idx])
    
    results = []
    
    for tau in taus:
        try:
            model = QuantReg(y, X)
            res = model.fit(q=tau, max_iter=1000)
            
            # Get confidence intervals
            conf_int = res.conf_int(alpha=0.05)
            
            factor_names = ['const'] + list(factors.columns)
            for i, factor in enumerate(factor_names):
                results.append({
                    'tau': float(tau),
                    'factor': factor,
                    'coef': float(res.params.iloc[i]),
                    'ci_low': float(conf_int.iloc[i, 0]),
                    'ci_high': float(conf_int.iloc[i, 1]),
                    't_stat': float(res.tvalues.iloc[i]),
                    'p_value': float(res.pvalues.iloc[i])
                })
        except Exception as e:
            # If quantile regression fails, add None results
            factor_names = ['const'] + list(factors.columns)
            for factor in factor_names:
                results.append({
                    'tau': float(tau),
                    'factor': factor,
                    'coef': None,
                    'ci_low': None,
                    'ci_high': None,
                    't_stat': None,
                    'p_value': None
                })
    
    return results
