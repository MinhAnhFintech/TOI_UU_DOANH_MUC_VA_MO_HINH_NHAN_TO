import pandas as pd
import numpy as np
from typing import Optional


def _get_rebalance_dates(trading_dates: pd.DatetimeIndex, frequency_months: int) -> list[pd.Timestamp]:
    if frequency_months < 1 or frequency_months > 12:
        raise ValueError('rebalance_freq_months must be between 1 and 12.')
    if trading_dates.empty:
        return []

    first_date, last_date = trading_dates.min(), trading_dates.max()
    dates = []
    if 12 % frequency_months == 0:
        # Fama-French annual portfolios are formed at the end of June;
        # shorter intervals retain June as the anchor (e.g. June/December).
        months = [month for month in range(1, 13) if (month - 6) % frequency_months == 0]
        for year in range(first_date.year, last_date.year + 1):
            for month in months:
                candidates = trading_dates[
                    (trading_dates.year == year) & (trading_dates.month == month)
                ]
                if len(candidates):
                    dates.append(candidates[-1])
        return dates

    current = first_date + pd.offsets.MonthEnd(0)
    while current <= last_date:
        candidates = trading_dates[
            (trading_dates.year == current.year) & (trading_dates.month == current.month)
        ]
        if len(candidates):
            dates.append(candidates[-1])
        current += pd.DateOffset(months=frequency_months)
    return dates


def _get_latest_fundamental(
    fundamentals: pd.DataFrame,
    as_of_date: pd.Timestamp,
    column: str
) -> pd.Series:
    """Get the latest available fundamental data for each ticker as of a given date.
    
    Uses report_date + 1 month lag to prevent look-ahead bias.
    Reference: Fama & French (1993), Journal of Financial Economics.
    """
    fund = fundamentals.copy()
    fund['report_date'] = pd.to_datetime(fund['report_date'])
    # Only use data where report was published at least 1 month before as_of_date
    fund['available_date'] = fund['report_date'] + pd.DateOffset(months=1)
    available = fund[fund['available_date'] <= as_of_date].copy()
    
    if available.empty:
        return pd.Series(dtype=float)
    
    # Get the latest available report for each ticker
    latest_idx = available.groupby('ticker')['available_date'].idxmax()
    latest = available.loc[latest_idx]
    return latest.set_index('ticker')[column]


def _compute_portfolio_return(
    returns: pd.DataFrame,
    market_caps: pd.DataFrame,
    tickers: list,
    date: pd.Timestamp,
    value_weighted: bool = True
) -> float:
    """Compute value-weighted or equal-weighted return for a portfolio of tickers on a date."""
    available_tickers = [t for t in tickers if t in returns.columns]
    if not available_tickers:
        return np.nan
    
    rets = returns.loc[date, available_tickers] if date in returns.index else pd.Series(dtype=float)
    if rets.empty or rets.isna().all():
        return np.nan
    
    if value_weighted:
        # Get market caps for weighting
        if date in market_caps.index:
            valid_tickers = rets.dropna().index
            caps = market_caps.loc[date, valid_tickers]
            if caps.notna().all() and (caps > 0).all() and caps.sum() > 0:
                w = caps / caps.sum()
                return float((w * rets[valid_tickers]).sum())
            return np.nan
        else:
            return np.nan
    else:
        return float(rets.dropna().mean()) if not rets.dropna().empty else np.nan


def build_smb_hml(
    prices: pd.DataFrame,
    fundamentals: pd.DataFrame,
    rebalance_freq_months: int = 12,
    value_weighted: bool = True
) -> pd.DataFrame:
    """Build SMB and HML using 2x3 sorts (Fama & French 1993).
    
    Algorithm:
    1. At each rebalance date, sort stocks into:
       - 2 Size groups by MEDIAN market cap: Small (S), Big (B)
       - 3 B/M groups by 30th/70th percentile: Low (L), Medium (M), High (H)
    2. Form 6 value-weighted portfolios: SL, SM, SH, BL, BM, BH
    3. SMB = 1/3(SL + SM + SH) - 1/3(BL + BM + BH)
       HML = 1/2(SH + BH) - 1/2(SL + BL)
    
    CRITICAL: Book equity is lagged by report_date + 1 month to prevent look-ahead bias.
    With 30 stocks, portfolios will have approximately 9-12 stocks each.
    
    References:
        Fama, E.F. & French, K.R. (1993). Common risk factors in the returns on stocks
        and bonds. Journal of Financial Economics, 33(1), 3-56.
    
    Args:
        prices: DataFrame with columns [date, ticker, ret, market_cap, close]
        fundamentals: DataFrame with columns [ticker, fiscal_year, quarter, report_date, book_equity]
        rebalance_freq_months: Rebalance frequency in months (default 12; June formation)
        value_weighted: Use value-weighted returns (True) or equal-weighted (False)
    
    Returns:
        DataFrame with columns [date, smb, hml] indexed by date
    """
    # Pivot returns and market_caps to wide format: index=date, columns=tickers
    prices = prices.copy()
    prices['date'] = pd.to_datetime(prices['date'])
    
    ret_wide = prices.pivot_table(index='date', columns='ticker', values='ret')
    cap_wide = prices.pivot_table(index='date', columns='ticker', values='market_cap')
    cap_wide_lagged = cap_wide.shift(1)
    
    trading_dates = ret_wide.index.sort_values()
    
    # Annual portfolios are formed at June month-end; alternate frequencies
    # use the same June calendar anchor.
    rebalance_dates = _get_rebalance_dates(trading_dates, rebalance_freq_months)
    
    # Build portfolio assignments at each rebalance date
    portfolio_assignments = {}  # date -> {ticker: portfolio_name}
    
    for reb_date in rebalance_dates:
        # Get market caps at rebalance date
        if reb_date not in cap_wide.index:
            continue
        caps = cap_wide.loc[reb_date].dropna()
        if len(caps) < 6:  # Need minimum stocks
            continue
        
        # Get latest available book equity (lagged by report_date + 1 month)
        be = _get_latest_fundamental(fundamentals, reb_date, 'book_equity')
        
        # Intersect tickers
        common_tickers = caps.index.intersection(be.index)
        common_tickers = common_tickers[caps[common_tickers] > 0]  # Positive market cap
        common_tickers = common_tickers[be[common_tickers] > 0]    # Positive book equity
        
        if len(common_tickers) < 6:
            continue
        
        # B/M ratio = Book Equity / Market Cap
        bm = be[common_tickers] / caps[common_tickers]
        
        # Size breakpoint: MEDIAN
        size_median = caps[common_tickers].median()
        
        # B/M breakpoints: 30th and 70th percentile
        bm_30 = bm.quantile(0.3)
        bm_70 = bm.quantile(0.7)
        
        # Assign to portfolios
        assignments = {}
        for ticker in common_tickers:
            size = 'S' if caps[ticker] <= size_median else 'B'
            if bm[ticker] <= bm_30:
                bm_group = 'L'
            elif bm[ticker] <= bm_70:
                bm_group = 'M'
            else:
                bm_group = 'H'
            assignments[ticker] = size + bm_group  # SL, SM, SH, BL, BM, BH
        
        portfolio_assignments[reb_date] = assignments
    
    # Compute daily SMB and HML
    results = []
    sorted_reb_dates = sorted(portfolio_assignments.keys())
    
    for i, reb_date in enumerate(sorted_reb_dates):
        # Determine the period this assignment is valid for
        if i + 1 < len(sorted_reb_dates):
            next_reb = sorted_reb_dates[i + 1]
        else:
            next_reb = trading_dates[-1] + pd.Timedelta(days=1)
        
        period_dates = trading_dates[(trading_dates > reb_date) & (trading_dates <= next_reb)]
        assignments = portfolio_assignments[reb_date]
        
        # Group tickers by portfolio
        portfolios = {'SL': [], 'SM': [], 'SH': [], 'BL': [], 'BM': [], 'BH': []}
        for ticker, port in assignments.items():
            if port in portfolios:
                portfolios[port].append(ticker)
        
        for date in period_dates:
            port_rets = {}
            for port_name, tickers in portfolios.items():
                port_rets[port_name] = _compute_portfolio_return(
                    ret_wide, cap_wide_lagged, tickers, date, value_weighted
                )

            if not np.isfinite(list(port_rets.values())).all():
                results.append({'date': date, 'smb': np.nan, 'hml': np.nan})
                continue
            
            # SMB = 1/3(SL + SM + SH) - 1/3(BL + BM + BH)
            smb = (1/3) * (port_rets['SL'] + port_rets['SM'] + port_rets['SH']) \
                - (1/3) * (port_rets['BL'] + port_rets['BM'] + port_rets['BH'])
            
            # HML = 1/2(SH + BH) - 1/2(SL + BL)
            hml = 0.5 * (port_rets['SH'] + port_rets['BH']) \
                - 0.5 * (port_rets['SL'] + port_rets['BL'])
            
            results.append({'date': date, 'smb': smb, 'hml': hml})
    
    if not results:
        return pd.DataFrame(columns=['date', 'smb', 'hml'])
    
    return pd.DataFrame(results).set_index('date')


def build_rmw_cma(
    prices: pd.DataFrame,
    fundamentals: pd.DataFrame,
    rebalance_freq_months: int = 12,
    value_weighted: bool = True
) -> pd.DataFrame:
    """Build RMW and CMA using 2x3 sorts (Fama & French 2015).
    
    RMW (Robust Minus Weak):
    - Profitability proxy: ROE (use ROE instead of operating profit for banks)
    - RMW = 1/2(SR + BR) - 1/2(SW + BW)
    
    CMA (Conservative Minus Aggressive):
    - Investment proxy: Total asset growth YoY
    - CMA = 1/2(SC + BC) - 1/2(SA + BA)
    
    Same 2x3 sort methodology as SMB/HML.
    Uses report_date + 1 month lag to prevent look-ahead bias.
    
    References:
        Fama, E.F. & French, K.R. (2015). A five-factor asset pricing model.
        Journal of Financial Economics, 116(1), 1-22.
    """
    prices = prices.copy()
    prices['date'] = pd.to_datetime(prices['date'])
    
    ret_wide = prices.pivot_table(index='date', columns='ticker', values='ret')
    cap_wide = prices.pivot_table(index='date', columns='ticker', values='market_cap')
    cap_wide_lagged = cap_wide.shift(1)
    
    trading_dates = ret_wide.index.sort_values()
    
    # Compute asset growth for CMA
    fund = fundamentals.copy()
    fund['report_date'] = pd.to_datetime(fund['report_date'])
    fund = fund.sort_values(['ticker', 'fiscal_year', 'quarter'])
    fund['total_assets_lag'] = fund.groupby('ticker')['total_assets'].shift(4)  # YoY (4 quarters)
    fund['asset_growth'] = (fund['total_assets'] / fund['total_assets_lag']) - 1
    
    rebalance_dates = _get_rebalance_dates(trading_dates, rebalance_freq_months)
    
    results = []
    
    for i, reb_date in enumerate(rebalance_dates):
        caps = cap_wide.loc[reb_date].dropna() if reb_date in cap_wide.index else pd.Series(dtype=float)
        if len(caps) < 6:
            continue
        
        # Get latest ROE and asset_growth
        roe = _get_latest_fundamental(fundamentals, reb_date, 'roe')
        ag = _get_latest_fundamental(fund, reb_date, 'asset_growth')
        
        # --- RMW portfolios ---
        common_rmw = caps.index.intersection(roe.dropna().index)
        common_rmw = common_rmw[caps[common_rmw] > 0]
        
        rmw_assignments = {}
        if len(common_rmw) >= 6:
            size_median = caps[common_rmw].median()
            roe_30 = roe[common_rmw].quantile(0.3)
            roe_70 = roe[common_rmw].quantile(0.7)
            for t in common_rmw:
                size = 'S' if caps[t] <= size_median else 'B'
                if roe[t] <= roe_30:
                    prof = 'W'  # Weak
                elif roe[t] <= roe_70:
                    prof = 'N'  # Neutral
                else:
                    prof = 'R'  # Robust
                rmw_assignments[t] = size + prof
        
        # --- CMA portfolios ---
        common_cma = caps.index.intersection(ag.dropna().index)
        common_cma = common_cma[caps[common_cma] > 0]
        
        cma_assignments = {}
        if len(common_cma) >= 6:
            size_median_c = caps[common_cma].median()
            ag_30 = ag[common_cma].quantile(0.3)
            ag_70 = ag[common_cma].quantile(0.7)
            for t in common_cma:
                size = 'S' if caps[t] <= size_median_c else 'B'
                if ag[t] <= ag_30:
                    inv = 'C'  # Conservative (low growth)
                elif ag[t] <= ag_70:
                    inv = 'N'  # Neutral
                else:
                    inv = 'A'  # Aggressive (high growth)
                cma_assignments[t] = size + inv
        
        # Determine period
        if i + 1 < len(rebalance_dates):
            next_reb = rebalance_dates[i + 1]
        else:
            next_reb = trading_dates[-1] + pd.Timedelta(days=1)
        period_dates = trading_dates[(trading_dates > reb_date) & (trading_dates <= next_reb)]
        
        # Group tickers
        rmw_ports = {'SR': [], 'SN': [], 'SW': [], 'BR': [], 'BN': [], 'BW': []}
        for t, p in rmw_assignments.items():
            if p in rmw_ports:
                rmw_ports[p].append(t)
        
        cma_ports = {'SC': [], 'SN': [], 'SA': [], 'BC': [], 'BN': [], 'BA': []}
        for t, p in cma_assignments.items():
            if p in cma_ports:
                cma_ports[p].append(t)
        
        for date in period_dates:
            # RMW = 1/2(SR + BR) - 1/2(SW + BW)
            rmw_r = {}
            for pn, tickers in rmw_ports.items():
                rmw_r[pn] = _compute_portfolio_return(ret_wide, cap_wide_lagged, tickers, date, value_weighted)
            rmw = 0.5 * (rmw_r['SR'] + rmw_r['BR']) - 0.5 * (rmw_r['SW'] + rmw_r['BW'])
            
            # CMA = 1/2(SC + BC) - 1/2(SA + BA)
            cma_r = {}
            for pn, tickers in cma_ports.items():
                cma_r[pn] = _compute_portfolio_return(ret_wide, cap_wide_lagged, tickers, date, value_weighted)
            cma = 0.5 * (cma_r['SC'] + cma_r['BC']) - 0.5 * (cma_r['SA'] + cma_r['BA'])
            
            results.append({'date': date, 'rmw': rmw, 'cma': cma})
    
    if not results:
        return pd.DataFrame(columns=['date', 'rmw', 'cma'])
    
    return pd.DataFrame(results).set_index('date')
