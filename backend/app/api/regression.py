from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
import uuid
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import math

from app.schemas.common import APIResponse
from app.schemas.regression import RegressionRunRequest
from app.db.models import (
    PriceDaily, FactorsDaily, RegressionResult as DBRegressionResult, 
    Job, GRSResult as DBGRSResult, HypothesisResult as DBHypothesisResult
)
from app.core.database import get_db, AsyncSessionLocal
from app.models.regression import run_regression
from app.models.registry import get_model_factors

router = APIRouter()
logger = logging.getLogger(__name__)


def _compute_grs_for_model(
    excess_returns: pd.DataFrame,
    factors: pd.DataFrame,
    factor_columns: List[str],
    tickers: Optional[List[str]] = None,
) -> Optional[dict]:
    """Compute GRS on one common, complete observation panel for all assets."""
    from app.models.grs import grs_test

    tickers = [ticker for ticker in (tickers or excess_returns.columns) if ticker in excess_returns.columns]
    if len(tickers) < 2:
        return None
    panel = pd.concat([factors[factor_columns], excess_returns[tickers]], axis=1)
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna()
    factor_values = panel[factor_columns].to_numpy(dtype=float)
    return_values = panel[tickers].to_numpy(dtype=float)
    n_observations, n_assets = return_values.shape
    n_factors = factor_values.shape[1]
    if n_observations < 30 or n_observations <= n_assets + n_factors:
        return None

    design = np.column_stack([np.ones(n_observations), factor_values])
    if np.linalg.matrix_rank(design) < design.shape[1]:
        return None
    coefficients = np.linalg.lstsq(design, return_values, rcond=None)[0]
    residuals = return_values - design @ coefficients
    return grs_test(coefficients[0], residuals, factor_values)


async def _update_job_progress(job_id: str, progress: float) -> None:
    async with AsyncSessionLocal() as progress_session:
        progress_job = await progress_session.get(Job, job_id)
        if progress_job and progress_job.status == 'running':
            progress_job.progress = progress
            await progress_session.commit()


async def regression_task(job_id: str, request: RegressionRunRequest):
    async with AsyncSessionLocal() as session:
        try:
            job = await session.get(Job, job_id)
            if not job:
                return
            job.status = 'running'
            job.progress = 5.0
            await session.commit()

            # 1. Fetch data
            stmt = select(PriceDaily.date, PriceDaily.ticker, PriceDaily.excess_ret).where(
                PriceDaily.date >= request.start,
                PriceDaily.date <= request.end
            )
            if request.tickers:
                stmt = stmt.where(PriceDaily.ticker.in_(request.tickers))
            res = await session.execute(stmt)
            prices = res.all()
            df_prices = pd.DataFrame(prices, columns=['date', 'ticker', 'excess_ret'])
            if df_prices.empty:
                raise ValueError("No price data found for the given dates/tickers.")
            excess_returns = df_prices.pivot(index='date', columns='ticker', values='excess_ret')
            excess_returns = excess_returns.replace([np.inf, -np.inf], np.nan)

            stmt_f = select(FactorsDaily).where(
                FactorsDaily.date >= request.start,
                FactorsDaily.date <= request.end
            )
            res_f = await session.execute(stmt_f)
            
            factors = []
            for r in res_f.scalars().all():
                d = dict(r.__dict__)
                d.pop('_sa_instance_state', None)
                factors.append(d)
                
            df_factors = pd.DataFrame(factors)
            if df_factors.empty:
                raise ValueError("No factor data found for the given dates.")
            df_factors.rename(columns={'for_factor': 'for_'}, inplace=True)
            df_factors.set_index('date', inplace=True)
            df_factors = df_factors.replace([np.inf, -np.inf], np.nan)
            
            run_id = job_id
            model_factors = {name: get_model_factors(name) for name in request.models}
            all_reg_results = {}
            
            # Delete old results for this run_id to prevent duplicates
            from sqlalchemy import delete
            await session.execute(delete(DBRegressionResult).where(DBRegressionResult.run_id == run_id))
            
            for model_index, model_name in enumerate(request.models):
                factor_cols = model_factors[model_name]
                missing = [name for name in factor_cols if name not in df_factors.columns]
                if missing:
                    raise ValueError(f"{model_name} requires missing factors: {', '.join(missing)}")
                X = df_factors[factor_cols]
                if X.dropna().shape[0] < 30:
                    raise ValueError(f"{model_name} has fewer than 30 complete factor observations in the selected period.")

                results = await asyncio.to_thread(
                    run_regression, excess_returns, X, model_name, request.cov_type
                )
                if not results:
                    raise ValueError(f"{model_name} could not be estimated: no ticker has enough complete observations.")
                all_reg_results[model_name] = results
                
                for r in results:
                    db_res = DBRegressionResult(
                        run_id=run_id,
                        model=model_name,
                        ticker=r['ticker'],
                        alpha=r.get('alpha'),
                        alpha_t=r.get('alpha_t'),
                        alpha_p=r.get('alpha_p'),
                        r2=r.get('r2'),
                        adj_r2=r.get('adj_r2'),
                        aic=r.get('aic'),
                        bic=r.get('bic'),
                        n_obs=r.get('n_obs')
                    )
                    for f in factor_cols:
                        result_name = 'for' if f == 'for_' else f
                        setattr(db_res, f'beta_{result_name}', r.get(f'beta_{result_name}'))
                        setattr(db_res, f'beta_{result_name}_t', r.get(f'beta_{result_name}_t'))
                        setattr(db_res, f'beta_{result_name}_p', r.get(f'beta_{result_name}_p'))
                    
                    session.add(db_res)
                await _update_job_progress(
                    job_id,
                    10 + 40 * (model_index + 1) / len(request.models),
                )
            job.progress = 55.0
            await session.flush()
            await session.commit()

            # === Compute GRS for each model ===
            await session.execute(delete(DBGRSResult).where(DBGRSResult.run_id == run_id))
            
            for model_index, model_name in enumerate(request.models):
                try:
                    grs_res = await asyncio.to_thread(
                        _compute_grs_for_model,
                        excess_returns,
                        df_factors,
                        model_factors[model_name],
                        [row['ticker'] for row in all_reg_results[model_name]],
                    )
                    if grs_res is not None:
                        db_grs = DBGRSResult(
                            run_id=run_id,
                            model=model_name,
                            universe='selected',
                            grs_stat=grs_res['grs_stat'],
                            p_value=grs_res['p_value'],
                            mean_abs_alpha=grs_res['mean_abs_alpha']
                        )
                        session.add(db_grs)
                except (ValueError, np.linalg.LinAlgError, ZeroDivisionError):
                    logger.exception("Could not compute GRS for %s in run %s", model_name, run_id)
                await _update_job_progress(
                    job_id,
                    55 + 25 * (model_index + 1) / len(request.models),
                )

            job.progress = 80.0
            await session.flush()
            await session.commit()

            # === Compute Hypotheses H1-H5 ===
            await _update_job_progress(job_id, 90.0)
            try:
                from app.models.selection import test_hypotheses
                # Build GRS results dict
                grs_dict = {}
                grs_stmt = select(DBGRSResult).where(DBGRSResult.run_id == run_id)
                grs_rows = (await session.execute(grs_stmt)).scalars().all()
                for g in grs_rows:
                    grs_dict[g.model] = {'grs_stat': g.grs_stat, 'p_value': g.p_value, 'mean_abs_alpha': g.mean_abs_alpha}
                
                hypotheses = await asyncio.to_thread(test_hypotheses, all_reg_results, grs_dict)
                
                await session.execute(delete(DBHypothesisResult).where(DBHypothesisResult.run_id == run_id))
                for h in hypotheses:
                    db_h = DBHypothesisResult(
                        run_id=run_id,
                        hypothesis=h.get('id', h.get('statement', '')),
                        statistic=h.get('statistic', 0),
                        p_value=h.get('p_value', 0),
                        verdict=h.get('verdict', ''),
                        note=h.get('note', '')
                    )
                    session.add(db_h)
            except Exception:
                logger.exception("Could not compute hypotheses for regression run %s", run_id)

            job.status = 'done'
            job.progress = 100.0
            job.run_id = run_id
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            job = await session.get(Job, job_id)
            if job:
                job.status = 'error'
                job.error = str(e)
                await session.commit()

@router.post("/run", response_model=APIResponse)
async def run_regression_endpoint(
    request: RegressionRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    new_job = Job(job_id=job_id, type="regression", status="pending", progress=0.0, created_at=datetime.utcnow())
    db.add(new_job)
    await db.commit()
    
    background_tasks.add_task(regression_task, job_id, request)
    return APIResponse(data={"job_id": job_id})

@router.get("/results", response_model=APIResponse)
async def get_results(
    model: Optional[str] = None,
    ticker: Optional[str] = None,
    run_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DBRegressionResult)
    if run_id: stmt = stmt.where(DBRegressionResult.run_id == run_id)
    if model: stmt = stmt.where(DBRegressionResult.model == model)
    if ticker: stmt = stmt.where(DBRegressionResult.ticker == ticker)
    
    res = await db.execute(stmt)
    data = []
    for row in res.scalars().all():
        data.append({
            "ticker": row.ticker,
            "model": row.model,
            "alpha": row.alpha,
            "alpha_t": row.alpha_t,
            "alpha_p": row.alpha_p,
            "betas": {k: getattr(row, f"beta_{k}") for k in ["mkt", "smb", "hml", "rmw", "cma", "liq", "for", "vol"] if getattr(row, f"beta_{k}") is not None},
            "t_stats": {k: getattr(row, f"beta_{k}_t") for k in ["mkt", "smb", "hml", "rmw", "cma", "liq", "for", "vol"] if getattr(row, f"beta_{k}_t") is not None},
            "p_values": {k: getattr(row, f"beta_{k}_p") for k in ["mkt", "smb", "hml", "rmw", "cma", "liq", "for", "vol"] if getattr(row, f"beta_{k}_p") is not None},
            "adj_r2": row.adj_r2,
            "aic": row.aic,
            "bic": row.bic,
            "n_obs": row.n_obs
        })
    return APIResponse(data=data)

@router.get("/diagnostics", response_model=APIResponse)
async def get_diagnostics(
    model: Optional[str] = None,
    run_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    # Regression date ranges and residuals are not persisted, so an on-demand
    # diagnostic here would silently use a different sample than the model fit.
    return APIResponse(data=[], error={
        "code": 501,
        "message": "Diagnostics are unavailable because the regression sample is not stored.",
    })

@router.get("/compare", response_model=APIResponse)
async def compare_models(
    run_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    if not run_id:
        return APIResponse(data=[])
        
    stmt = select(DBRegressionResult).where(DBRegressionResult.run_id == run_id)
    res = await db.execute(stmt)
    records = res.scalars().all()
    if not records:
        return APIResponse(data=[])
        
    # Aggregate by model
    models = {}
    for r in records:
        if r.model not in models:
            models[r.model] = {"adj_r2": [], "abs_alpha": [], "aic": []}
        if r.adj_r2 is not None:
            models[r.model]["adj_r2"].append(r.adj_r2)
        if r.alpha is not None:
            models[r.model]["abs_alpha"].append(abs(r.alpha))
        if r.aic is not None:
            models[r.model]["aic"].append(r.aic)
    
    # Fetch GRS results
    grs_stmt = select(DBGRSResult).where(DBGRSResult.run_id == run_id)
    grs_res = await db.execute(grs_stmt)
    grs_dict = {}
    for g in grs_res.scalars().all():
        grs_dict[g.model] = {"grs_stat": g.grs_stat, "p_value": g.p_value, "mean_abs_alpha": g.mean_abs_alpha}
            
    data = []
    for m, vals in models.items():
        avg_r2 = sum(vals["adj_r2"]) / len(vals["adj_r2"]) if vals["adj_r2"] else None
        mean_abs_alpha = sum(vals["abs_alpha"]) / len(vals["abs_alpha"]) if vals["abs_alpha"] else None
        avg_aic = sum(vals["aic"]) / len(vals["aic"]) if vals["aic"] else None
        grs_info = grs_dict.get(m, {})
        data.append({
            "model": m,
            "avg_adj_r2": avg_r2,
            "delta_adj_r2": 0.0,
            "avg_aic": avg_aic,
            "grs_stat": grs_info.get("grs_stat"),
            "grs_p": grs_info.get("p_value"),
            "mean_abs_alpha": mean_abs_alpha
        })
        
    # Sort by R2
    data.sort(key=lambda x: x["avg_adj_r2"] if x["avg_adj_r2"] is not None else float('-inf'), reverse=True)
    if len(data) > 1:
        for i in range(1, len(data)):
            if data[i]["avg_adj_r2"] is not None and data[0]["avg_adj_r2"] is not None:
                data[i]["delta_adj_r2"] = data[i]["avg_adj_r2"] - data[0]["avg_adj_r2"]
            
    return APIResponse(data=data)

@router.get("/grs", response_model=APIResponse)
async def get_grs(run_id: Optional[str] = None, universe: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    if not run_id:
        return APIResponse(data=[])
    
    # First check if we have pre-computed GRS results
    stmt = select(DBGRSResult).where(DBGRSResult.run_id == run_id)
    if universe:
        stmt = stmt.where(DBGRSResult.universe == universe)
    res = await db.execute(stmt)
    records = res.scalars().all()
    if records:
        return APIResponse(data=[{"model": r.model, "grs_stat": r.grs_stat, "p_value": r.p_value, "mean_abs_alpha": r.mean_abs_alpha} for r in records])
    
    # Do not rebuild this from all available dates: the run's sample bounds
    # are not persisted, so that would report a different statistical test.
    return APIResponse(data=[])

@router.get("/hypotheses", response_model=APIResponse)
async def get_hypotheses(run_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    if not run_id:
        return APIResponse(data=[])
    stmt = select(DBHypothesisResult).where(DBHypothesisResult.run_id == run_id)
    res = await db.execute(stmt)
    records = res.scalars().all()
    if not records:
        return APIResponse(data=[])  # Don't return fake data!
    statements = {
        'H1': 'Adj R² của FF3 cao hơn CAPM trên cùng mẫu ngày.',
        'H2': 'Adj R² của FF5 cao hơn FF3 trên cùng mẫu ngày.',
        'H3': 'Nhân tố LIQ có ý nghĩa thống kê trong FF5_LIQ.',
        'H4': 'Nhân tố FOR có ý nghĩa thống kê trong FF5_FOR.',
        'H5': 'VOL cải thiện Adj R² so với FF5 trên cùng mẫu ngày.',
    }
    data = []
    for row in records:
        data.append({
            "id": row.hypothesis,
            "statement": statements.get(row.hypothesis, row.hypothesis),
            "statistic": row.statistic,
            "p_value": row.p_value,
            "verdict": row.verdict,
            "note": row.note,
        })
    return APIResponse(data=data)

@router.get("/quantile", response_model=APIResponse)
async def get_quantile(
    model: Optional[str] = None,
    ticker: Optional[str] = None,
    taus: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    if not ticker or not model:
        return APIResponse(data=[])
        
    try:
        from app.models.quantile import run_quantile_regression
        
        # 1. Fetch price data for the ticker
        stmt = select(PriceDaily.date, PriceDaily.excess_ret).where(PriceDaily.ticker == ticker)
        prices_res = await db.execute(stmt)
        prices = [{"date": r.date, "excess_ret": r.excess_ret} for r in prices_res.all()]
        if not prices:
            return APIResponse(data=[])
            
        df_prices = pd.DataFrame(prices).set_index("date")
        excess_returns = df_prices["excess_ret"]
        
        # 2. Fetch factors
        stmt_f = select(FactorsDaily)
        factors_res = await db.execute(stmt_f)
        factors_data = []
        for r in factors_res.scalars().all():
            d = dict(r.__dict__)
            d.pop('_sa_instance_state', None)
            factors_data.append(d)
            
        df_factors = pd.DataFrame(factors_data)
        if df_factors.empty:
            return APIResponse(data=[])
        df_factors.rename(columns={'for_factor': 'for_'}, inplace=True)
        df_factors.set_index("date", inplace=True)

        factor_cols = get_model_factors(model)
        missing = [factor for factor in factor_cols if factor not in df_factors.columns]
        if missing:
            raise ValueError(f"{model} requires missing factors: {', '.join(missing)}")
        X = df_factors[factor_cols]
        
        # 3. Parse taus
        tau_list = [0.1, 0.25, 0.5, 0.75, 0.9]
        if taus:
            tau_list = list(dict.fromkeys(float(t) for t in taus.split(",")))
            if any(not math.isfinite(tau) or not 0 < tau < 1 for tau in tau_list):
                raise ValueError("Each quantile must be a finite number between 0 and 1.")
            
        # 4. Run quantile regression
        raw_results = await asyncio.to_thread(run_quantile_regression, excess_returns, X, tau_list)
        
        # 5. Format to match frontend schema
        # Frontend expects: tau, factor, coefficients (dict), lower_ci (dict), upper_ci (dict)
        # But wait, frontend QuantileResult is: tau, factor, coef, ci_low, ci_high
        # Ah, in types.ts it is: tau: number, coefficients: Record<string, number>, lower_ci: Record<string, number>, upper_ci: Record<string, number>
        # Let's map it to match types.ts
        grouped = {}
        for r in raw_results:
            t = r['tau']
            f = r['factor']
            if t not in grouped:
                grouped[t] = {"tau": t, "coefficients": {}, "lower_ci": {}, "upper_ci": {}}
            if r['coef'] is not None and not np.isnan(r['coef']):
                grouped[t]["coefficients"][f] = r['coef']
                grouped[t]["lower_ci"][f] = r['ci_low']
                grouped[t]["upper_ci"][f] = r['ci_high']
                
        data = list(grouped.values())
        data.sort(key=lambda x: x['tau'])
        
        return APIResponse(data=data)
        
    except Exception as e:
        return APIResponse(data=[], error={"code": 500, "message": str(e)})

@router.get("/best", response_model=APIResponse)
async def get_best_model(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    from app.models.selection import select_best_model

    result_rows = (await db.execute(
        select(DBRegressionResult).where(DBRegressionResult.run_id == run_id)
    )).scalars().all()
    grs_rows = (await db.execute(
        select(DBGRSResult).where(DBGRSResult.run_id == run_id)
    )).scalars().all()
    regression_results = {}
    for row in result_rows:
        regression_results.setdefault(row.model, []).append({
            'ticker': row.ticker,
            'alpha': row.alpha,
            'adj_r2': row.adj_r2,
            'aic': row.aic,
            'bic': row.bic,
        })
    grs_results = {
        row.model: {'grs_stat': row.grs_stat, 'p_value': row.p_value}
        for row in grs_rows
    }
    selection = select_best_model(regression_results, grs_results)
    return APIResponse(data={
        'model': selection['best_model'],
        'criteria': selection['criteria'],
        'ranking': selection['ranking'],
    })
