import pandas as pd
import numpy as np
import statsmodels.api as sm
from app.models.registry import get_factor_result_name

def run_regression(
    excess_returns: pd.DataFrame,  # columns = tickers, index = date
    factors: pd.DataFrame,         # columns = factor names, index = date
    model_name: str,
    cov_type: str = 'HAC',
    hac_lag: int = 5,
) -> list[dict]:
    """Run OLS time-series regression for each stock."""
    # Align data
    common_dates = excess_returns.index.intersection(factors.index)
    Y = excess_returns.loc[common_dates]
    X = factors.loc[common_dates]
    
    results = []
    for ticker in Y.columns:
        aligned = pd.concat([Y[ticker].rename('_y'), X], axis=1).dropna()
        y = aligned['_y']
        x = sm.add_constant(aligned.drop(columns='_y'), has_constant='add')
        
        if len(y) < max(30, x.shape[1] + 2):
            continue
        fit_options = {'cov_type': cov_type}
        if cov_type.upper() == 'HAC':
            fit_options['cov_kwds'] = {'maxlags': min(hac_lag, len(y) - 1)}
        model = sm.OLS(y, x).fit(**fit_options)
        
        res = {
            'ticker': ticker,
            'alpha': model.params['const'],
            'alpha_t': model.tvalues['const'],
            'alpha_p': model.pvalues['const'],
            'r2': model.rsquared,
            'adj_r2': model.rsquared_adj,
            'aic': model.aic,
            'bic': model.bic,
            'n_obs': int(model.nobs)
        }
        # Kept in memory for paired model comparisons; this field is not stored
        # in the database and prevents comparing fits from different dates.
        res['_sample_dates'] = tuple(str(value) for value in aligned.index)
        
        for factor in factors.columns:
            if factor in model.params:
                result_name = get_factor_result_name(factor)
                res[f'beta_{result_name}'] = model.params[factor]
                res[f'beta_{result_name}_t'] = model.tvalues[factor]
                res[f'beta_{result_name}_p'] = model.pvalues[factor]
                
        results.append(res)
        
    return results
