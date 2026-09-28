import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import het_breuschpagan, acorr_ljungbox
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tsa.stattools import adfuller


def compute_diagnostics(
    model_result,
    X: pd.DataFrame
) -> dict:
    """Compute regression diagnostics.
    
    Args:
        model_result: statsmodels OLS RegressionResults object
        X: DataFrame of independent variables (factors)
    
    Returns:
        Dict with:
        - vif: {factor: VIF value} - Variance Inflation Factor (warn if > 10)
        - durbin_watson: DW statistic (autocorrelation, ~2 is ideal)
        - bp_stat, bp_p: Breusch-Pagan test (heteroskedasticity)
        - jb_stat, jb_p: Jarque-Bera test (normality of residuals)
        - adf: {factor: {stat, p_value}} - Augmented Dickey-Fuller (stationarity)
    """
    resid = model_result.resid
    
    # 1. VIF (Variance Inflation Factor)
    vif_dict = {}
    X_array = X.values if hasattr(X, 'values') else np.array(X)
    if X_array.shape[1] > 1:
        for i, col in enumerate(X.columns if hasattr(X, 'columns') else range(X_array.shape[1])):
            try:
                vif_val = variance_inflation_factor(X_array, i)
                vif_dict[str(col)] = float(vif_val)
            except Exception:
                vif_dict[str(col)] = float('nan')
    
    # 2. Durbin-Watson
    dw = float(durbin_watson(resid))
    
    # 3. Breusch-Pagan test for heteroskedasticity
    try:
        bp_stat, bp_p, _, _ = het_breuschpagan(resid, model_result.model.exog)
        bp_stat = float(bp_stat)
        bp_p = float(bp_p)
    except Exception:
        bp_stat = float('nan')
        bp_p = float('nan')
    
    # 4. Jarque-Bera test for normality
    try:
        jb_stat, jb_p, skew, kurt = jarque_bera(resid)
        jb_stat = float(jb_stat)
        jb_p = float(jb_p)
    except Exception:
        jb_stat = float('nan')
        jb_p = float('nan')
    
    # 5. ADF test for stationarity of each factor
    adf_dict = {}
    if hasattr(X, 'columns'):
        for col in X.columns:
            try:
                adf_result = adfuller(X[col].dropna(), autolag='AIC')
                adf_dict[str(col)] = {
                    'stat': float(adf_result[0]),
                    'p_value': float(adf_result[1])
                }
            except Exception:
                adf_dict[str(col)] = {'stat': float('nan'), 'p_value': float('nan')}
    
    return {
        'vif': vif_dict,
        'durbin_watson': dw,
        'bp_stat': bp_stat,
        'bp_p': bp_p,
        'jb_stat': jb_stat,
        'jb_p': jb_p,
        'adf': adf_dict
    }
