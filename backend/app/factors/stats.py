import pandas as pd
import numpy as np
from statsmodels.stats.stattools import durbin_watson
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
import warnings


def compute_factor_stats(
    factors_df: pd.DataFrame,
    trading_days: int = 252
) -> list[dict]:
    """Compute descriptive statistics and t-test for factor premium.
    
    For each factor:
    - mean, std (daily)
    - annualized mean (x252), annualized std (x sqrt(252))
    - t-statistic for H0: mean=0 using Newey-West standard errors
    - p-value
    - skewness, kurtosis
    
    Args:
        factors_df: DataFrame indexed by date with columns for each factor
        trading_days: Number of trading days per year
    
    Returns:
        List of dicts with statistics for each factor
    """
    results = []
    
    for col in factors_df.columns:
        series = factors_df[col].dropna()
        if len(series) < 10:
            continue
        
        mean_val = series.mean()
        std_val = series.std()
        ann_mean = mean_val * trading_days
        ann_std = std_val * np.sqrt(trading_days)
        
        # Newey-West t-test for H0: mean = 0
        try:
            y = series.values
            X = np.ones((len(y), 1))
            model = OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 5})
            t_stat = model.tvalues[0]
            p_value = model.pvalues[0]
        except Exception:
            t_stat = mean_val / (std_val / np.sqrt(len(series))) if std_val > 0 else 0
            p_value = 2 * (1 - __import__('scipy').stats.t.cdf(abs(t_stat), len(series) - 1))
        
        results.append({
            'factor': col,
            'mean': float(mean_val),
            'std': float(std_val),
            'ann_mean': float(ann_mean),
            'ann_std': float(ann_std),
            't_stat': float(t_stat),
            'p_value': float(p_value),
            'skew': float(series.skew()),
            'kurt': float(series.kurtosis()),
            'n_obs': len(series)
        })
    
    return results


def compute_correlation_matrix(
    factors_df: pd.DataFrame
) -> dict:
    """Compute correlation matrix between factors.
    
    Warns if any pair has correlation > 0.8 (multicollinearity risk).
    
    Returns:
        Dict with 'factors' (list of names) and 'matrix' (2D list)
    """
    corr = factors_df.corr()
    
    # Check for high correlations
    warnings_list = []
    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            if abs(corr.iloc[i, j]) > 0.8:
                warnings_list.append(
                    f"High correlation ({corr.iloc[i, j]:.3f}) between "
                    f"{corr.columns[i]} and {corr.columns[j]}: multicollinearity risk"
                )
    
    if warnings_list:
        warnings.warn("\n".join(warnings_list))
    
    return {
        'factors': corr.columns.tolist(),
        'matrix': corr.values.tolist(),
        'warnings': warnings_list
    }


def compute_cumulative_returns(
    factors_df: pd.DataFrame,
    base: float = 100.0
) -> pd.DataFrame:
    """Compute cumulative returns for each factor (base=100)."""
    cumulative = (1 + factors_df).cumprod() * base
    return cumulative


def compare_with_ken_french(
    vn_factors: pd.DataFrame,
    kf_factors: pd.DataFrame,
    common_factors: list[str] = None
) -> list[dict]:
    """Compare VN factors with Ken French factors.
    
    Computes correlation between VN and KF for each common factor.
    """
    if common_factors is None:
        vn_cols = set(vn_factors.columns)
        kf_cols = set(kf_factors.columns)
        common_factors = list(vn_cols.intersection(kf_cols))
    
    results = []
    for factor in common_factors:
        if factor not in vn_factors.columns or factor not in kf_factors.columns:
            continue
        
        # Align dates
        common_dates = vn_factors.index.intersection(kf_factors.index)
        if len(common_dates) < 10:
            continue
        
        vn_series = vn_factors.loc[common_dates, factor]
        kf_series = kf_factors.loc[common_dates, factor]
        
        # Drop NaN
        mask = vn_series.notna() & kf_series.notna()
        corr = vn_series[mask].corr(kf_series[mask])
        
        results.append({
            'factor': factor,
            'correlation': float(corr) if not np.isnan(corr) else 0.0,
            'n_common_dates': int(mask.sum()),
            'vn_mean': float(vn_series[mask].mean()),
            'kf_mean': float(kf_series[mask].mean())
        })
    
    return results
