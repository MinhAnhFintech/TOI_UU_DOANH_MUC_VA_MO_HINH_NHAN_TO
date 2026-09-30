import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import binomtest


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
    # Normalize keys to uppercase
    regression_results = {k.upper(): v for k, v in regression_results.items()}
    grs_results = {k.upper(): v for k, v in grs_results.items()}
    
    ranking = []
    
    for model_name, results_list in regression_results.items():
        if not results_list:
            continue

        def finite_values(key, transform=lambda value: value):
            values = [transform(row[key]) for row in results_list if row.get(key) is not None]
            return [float(value) for value in values if np.isfinite(value)]

        adj_r2_values = finite_values('adj_r2')
        if not adj_r2_values:
            continue
        aic_values = finite_values('aic')
        bic_values = finite_values('bic')
        alpha_values = finite_values('alpha', abs)
        avg_adj_r2 = float(np.mean(adj_r2_values))
        avg_aic = float(np.mean(aic_values)) if aic_values else None
        avg_bic = float(np.mean(bic_values)) if bic_values else None
        mean_abs_alpha = float(np.mean(alpha_values)) if alpha_values else None
        
        grs = grs_results.get(model_name, {})
        grs_p = grs.get('p_value')
        grs_stat = grs.get('grs_stat')
        
        # Composite score (higher is better)
        # Normalize each criterion to [0, 1] range later for ranking
        ranking.append({
            'model': model_name,
            'avg_adj_r2': float(avg_adj_r2),
            'grs_stat': float(grs_stat) if grs_stat is not None and np.isfinite(grs_stat) else None,
            'grs_p': float(grs_p) if grs_p is not None and np.isfinite(grs_p) else None,
            'avg_aic': avg_aic,
            'avg_bic': avg_bic,
            'mean_abs_alpha': mean_abs_alpha
        })
    
    if not ranking:
        return {'best_model': None, 'criteria': {}, 'ranking': []}
    
    # Sort by: adjusted R² desc; when tied, prefer a valid higher GRS p-value,
    # then lower AIC and lower absolute alpha.
    ranking.sort(key=lambda x: (
        -x['avg_adj_r2'],
        -(x['grs_p'] if x['grs_p'] is not None else -1.0),
        x['avg_aic'] if x['avg_aic'] is not None else float('inf'),
        x['mean_abs_alpha'] if x['mean_abs_alpha'] is not None else float('inf'),
    ))
    
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
    - Proportion of stocks with significant coefficient at 5%
    
    Args:
        regression_results: {model_name: list of per-stock regression dicts}
        grs_results: {model_name: grs_test dict}
    
    Returns:
        List of hypothesis result dicts
    """
    # Normalize keys to uppercase
    regression_results = {k.upper(): v for k, v in regression_results.items()}
    grs_results = {k.upper(): v for k, v in grs_results.items()}
    
    hypotheses = []
    
    # Pair models only when each ticker was estimated on the exact same dates.
    def paired_adj_r2_test(model_a, model_b):
        by_ticker_a = {
            row['ticker']: row for row in regression_results.get(model_a, [])
            if row.get('ticker') and row.get('adj_r2') is not None
        }
        by_ticker_b = {
            row['ticker']: row for row in regression_results.get(model_b, [])
            if row.get('ticker') and row.get('adj_r2') is not None
        }
        differences = []
        for ticker in by_ticker_a.keys() & by_ticker_b.keys():
            left, right = by_ticker_a[ticker], by_ticker_b[ticker]
            sample_a, sample_b = left.get('_sample_dates'), right.get('_sample_dates')
            if not sample_a or sample_a != sample_b:
                continue
            difference = float(right['adj_r2']) - float(left['adj_r2'])
            if np.isfinite(difference):
                differences.append(difference)
        if len(differences) < 2:
            return None
        delta = float(np.mean(differences))
        if np.allclose(differences, 0):
            return 0.0, 1.0, delta
        test = stats.ttest_1samp(differences, 0)
        if not np.isfinite(test.statistic) or not np.isfinite(test.pvalue):
            return None
        return float(test.statistic), float(test.pvalue), delta
    
    def get_coef_significance(model_name, coef_name):
        """Get proportion of stocks where coefficient is significant at 5%."""
        if model_name not in regression_results:
            return 0, 0, 0
        results = regression_results[model_name]
        p_key = f'{coef_name}_p' if f'{coef_name}_p' in (results[0] if results else {}) else None
        values = []
        for row in results:
            value = row.get(p_key) if p_key else row.get('p_values', {}).get(coef_name)
            if value is not None and np.isfinite(value):
                values.append(float(value))
        total = len(values)
        sig_count = sum(value < 0.05 for value in values)
        return sig_count, total, sig_count / total if total > 0 else 0
    
    # H1: FF3 > CAPM
    paired = paired_adj_r2_test('CAPM', 'FF3')
    if paired:
        t_stat, p_val, delta = paired
        hypotheses.append({
            'id': 'H1',
            'statement': 'FF3 is better than CAPM',
            'statistic': float(t_stat),
            'p_value': float(p_val),
            'verdict': 'Supported' if p_val < 0.05 and delta > 0 else 'Not supported',
            'note': f'Mean ΔAdj R² = {delta:.4f}'
        })
    
    # H2: FF5 > FF3
    paired = paired_adj_r2_test('FF3', 'FF5')
    if paired:
        t_stat, p_val, delta = paired
        hypotheses.append({
            'id': 'H2',
            'statement': 'FF5 is better than FF3',
            'statistic': float(t_stat),
            'p_value': float(p_val),
            'verdict': 'Supported' if p_val < 0.05 and delta > 0 else 'Not supported',
            'note': f'Mean ΔAdj R² = {delta:.4f}'
        })
    
    # H3: LIQ is significant
    sig, total, pct = get_coef_significance('FF5_LIQ', 'beta_liq')
    if total > 0:
        p_val_h3 = float(binomtest(sig, total, 0.05, alternative='greater').pvalue)
        hypotheses.append({
            'id': 'H3',
            'statement': 'LIQ factor is statistically significant',
            'statistic': float(pct),
            'p_value': p_val_h3,
            'verdict': 'Supported' if p_val_h3 < 0.05 else 'Not supported',
            'note': f'{sig}/{total} stocks ({pct:.1%}) have significant LIQ at 5%'
        })
    
    # H4: FOR is significant (using FF5_ALL which includes for_)
    sig, total, pct = get_coef_significance('FF5_FOR', 'beta_for')
    if total > 0:
        p_val_h4 = float(binomtest(sig, total, 0.05, alternative='greater').pvalue)
        hypotheses.append({
            'id': 'H4',
            'statement': 'FOR factor is statistically significant',
            'statistic': float(pct),
            'p_value': p_val_h4,
            'verdict': 'Supported' if p_val_h4 < 0.05 else 'Not supported',
            'note': f'{sig}/{total} stocks ({pct:.1%}) have significant FOR at 5%'
        })
    
    # H5: Isolate the VOL effect by comparing FF5_VOL with the base FF5 model.
    paired = paired_adj_r2_test('FF5', 'FF5_VOL')
    if paired:
        t_stat, p_val, delta = paired
        hypotheses.append({
            'id': 'H5',
            'statement': 'VOL improves Adj R-squared over FF5',
            'statistic': float(t_stat),
            'p_value': float(p_val),
            'verdict': 'Supported' if p_val < 0.05 and delta > 0 else 'Not supported',
            'note': f'Mean ΔAdj R² = {delta:.4f} (FF5_VOL vs FF5)'
        })
    
    return hypotheses
