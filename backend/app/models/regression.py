import pandas as pd
import numpy as np
import statsmodels.api as sm

def run_regression(
    excess_returns: pd.DataFrame,  # columns = tickers, index = date
    factors: pd.DataFrame,         # columns = factor names, index = date
    model_name: str,
    hac_lag: int = 5
) -> list[dict]:
    """Run OLS time-series regression for each stock."""
    # Align data
    common_dates = excess_returns.index.intersection(factors.index)
    Y = excess_returns.loc[common_dates]
    X = factors.loc[common_dates]
    X = sm.add_constant(X)
    
    results = []
    for ticker in Y.columns:
        y = Y[ticker].dropna()
        x = X.loc[y.index]
        
        if len(y) < 30: # Need minimum observations
            continue
            
        model = sm.OLS(y, x).fit(cov_type='HAC', cov_kwds={'maxlags': hac_lag})
        
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
        
        for factor in factors.columns:
            if factor in model.params:
                res[f'beta_{factor}'] = model.params[factor]
                res[f'beta_{factor}_t'] = model.tvalues[factor]
                res[f'beta_{factor}_p'] = model.pvalues[factor]
                
        results.append(res)
        
    return results
