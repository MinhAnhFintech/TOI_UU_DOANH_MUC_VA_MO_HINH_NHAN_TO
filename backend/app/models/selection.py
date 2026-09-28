import numpy as np
import pandas as pd
from scipy import stats


def select_best_model(
    regression_results: dict,
    grs_results: dict
) -> dict:
    """Select the best model based on multiple criteria.
    
    Criteria (in order of priority):
    1. Average Adj R-squared (higher is better)
    2. GRS test p-value (higher is better, i.e., cannot reject alpha=0)
    3. AIC (lower is better)
    4. Mean |alpha| (lower is better)
    
    Args:
        regression_results: {model_name: list of per-stock regression dicts}
        grs_results: {model_name: grs_test dict}
    
    Returns:
        Dict with best_model name, criteria breakdown, and full ranking
    """
    ranking = []
    
    for model_name, results_list in regression_results.items():
        if not results_list:
            continue
        
        avg_adj_r2 = np.mean([r['adj_r2'] for r in results_list if r.get('adj_r2') is not None])
        avg_aic = np.mean([r['aic'] for r in results_list if r.get('aic') is not None])
        avg_bic = np.mean([r['bic'] for r in results_list if r.get('bic') is not None])
        mean_abs_alpha = np.mean([abs(r['alpha']) for r in results_list if r.get('alpha') is not None])
        
        grs = grs_results.get(model_name, {})
        grs_p = grs.get('p_value', 0)
        grs_stat = grs.get('grs_stat', float('inf'))
        
        # Composite score (higher is better)
        # Normalize each criterion to [0, 1] range later for ranking
        ranking.append({
            'model': model_name,
            'avg_adj_r2': float(avg_adj_r2),
            'grs_stat': float(grs_stat),
            'grs_p': float(grs_p),
            'avg_aic': float(avg_aic),
            'avg_bic': float(avg_bic),
            'mean_abs_alpha': float(mean_abs_alpha)
        })
    
    if not ranking:
        return {'best_model': None, 'criteria': {}, 'ranking': []}
    
    # Sort by: adj_r2 desc, grs_p desc, aic asc, mean_abs_alpha asc
    ranking.sort(key=lambda x: (-x['avg_adj_r2'], -x['grs_p'], x['avg_aic'], x['mean_abs_alpha']))
    
    best = ranking[0]
    
    return {
        'best_model': best['model'],
        'criteria': {
            'avg_adj_r2': best['avg_adj_r2'],
            'grs_stat': best['grs_stat'],
            'grs_p': best['grs_p'],
            'avg_aic': best['avg_aic'],
            'mean_abs_alpha': best['mean_abs_alpha']
        },
        'ranking': ranking
    }


def test_hypotheses(
    regression_results: dict,
    grs_results: dict
) -> list[dict]:
    """Test research hypotheses H1-H5.
    
    H1: FF3 better than CAPM
    H2: FF5 better than FF3
    H3: LIQ is statistically significant
    H4: FOR is statistically significant
    H5: VOL improves Adj R-squared
    
    Methods:
    - Paired t-test on Adj R-squared differences
    - F-test for nested models (Wald test)
    - Proportion of stocks with significant coefficient at 5%
    
    Args:
        regression_results: {model_name: list of per-stock regression dicts}
        grs_results: {model_name: grs_test dict}
    
    Returns:
        List of hypothesis result dicts
    """
    hypotheses = []
    
    # Helper: get adj_r2 by ticker for a model
    def get_adj_r2_by_ticker(model_name):
        if model_name not in regression_results:
            return {}
        return {r['ticker']: r['adj_r2'] for r in regression_results[model_name] if 'ticker' in r}
    
    def get_coef_significance(model_name, coef_name):
        """Get proportion of stocks where coefficient is significant at 5%."""
        if model_name not in regression_results:
            return 0, 0, 0
        results = regression_results[model_name]
        total = len(results)
        p_key = f'{coef_name}_p' if f'{coef_name}_p' in (results[0] if results else {}) else None
        if p_key is None:
            # Try nested structure
            sig_count = sum(1 for r in results 
                          if r.get('p_values', {}).get(coef_name, 1) < 0.05)
        else:
            sig_count = sum(1 for r in results if r.get(p_key, 1) < 0.05)
        return sig_count, total, sig_count / total if total > 0 else 0
    
    # H1: FF3 > CAPM
    r2_capm = get_adj_r2_by_ticker('capm')
    r2_ff3 = get_adj_r2_by_ticker('ff3')
    common = set(r2_capm.keys()) & set(r2_ff3.keys())
    if common:
        diffs = [r2_ff3[t] - r2_capm[t] for t in common]
        t_stat, p_val = stats.ttest_1samp(diffs, 0)
        delta = np.mean(diffs)
        hypotheses.append({
            'id': 'H1',
            'statement': 'FF3 is better than CAPM',
            'statistic': float(t_stat),
            'p_value': float(p_val),
            'verdict': 'Accept' if p_val < 0.05 and delta > 0 else 'Reject',
            'note': f'Mean ΔAdj R² = {delta:.4f}'
        })
    
    # H2: FF5 > FF3
    r2_ff5 = get_adj_r2_by_ticker('ff5')
    common = set(r2_ff3.keys()) & set(r2_ff5.keys())
    if common:
        diffs = [r2_ff5[t] - r2_ff3[t] for t in common]
        t_stat, p_val = stats.ttest_1samp(diffs, 0)
        delta = np.mean(diffs)
        hypotheses.append({
            'id': 'H2',
            'statement': 'FF5 is better than FF3',
            'statistic': float(t_stat),
            'p_value': float(p_val),
            'verdict': 'Accept' if p_val < 0.05 and delta > 0 else 'Reject',
            'note': f'Mean ΔAdj R² = {delta:.4f}'
        })
    
    # H3: LIQ is significant
    sig, total, pct = get_coef_significance('ff5_liq', 'beta_liq')
    hypotheses.append({
        'id': 'H3',
        'statement': 'LIQ factor is statistically significant',
        'statistic': float(pct),
        'p_value': float(1 - pct),  # Proportion as proxy
        'verdict': 'Accept' if pct > 0.5 else 'Reject',
        'note': f'{sig}/{total} stocks ({pct:.1%}) have significant LIQ at 5%'
    })
    
    # H4: FOR is significant
    sig, total, pct = get_coef_significance('ff5_liq_for', 'beta_for')
    hypotheses.append({
        'id': 'H4',
        'statement': 'FOR factor is statistically significant',
        'statistic': float(pct),
        'p_value': float(1 - pct),
        'verdict': 'Accept' if pct > 0.5 else 'Reject',
        'note': f'{sig}/{total} stocks ({pct:.1%}) have significant FOR at 5%'
    })
    
    # H5: VOL improves Adj R-squared
    r2_without = get_adj_r2_by_ticker('ff5_liq_for')
    r2_with = get_adj_r2_by_ticker('ff5_liq_for_vol')
    common = set(r2_without.keys()) & set(r2_with.keys())
    if common:
        diffs = [r2_with[t] - r2_without[t] for t in common]
        t_stat, p_val = stats.ttest_1samp(diffs, 0)
        delta = np.mean(diffs)
        hypotheses.append({
            'id': 'H5',
            'statement': 'VOL factor improves Adj R-squared',
            'statistic': float(t_stat),
            'p_value': float(p_val),
            'verdict': 'Accept' if p_val < 0.05 and delta > 0 else 'Reject',
            'note': f'Mean ΔAdj R² = {delta:.4f}'
        })
    
    return hypotheses
