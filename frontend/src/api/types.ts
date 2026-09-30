export interface APIResponse<T> {
  data: T;
  meta: any;
  error: any;
}

export interface StockInfo { ticker: string; company_name?: string | null; sector?: string | null; listing_date?: string | null; }
export interface PriceRecord { date: string; ticker: string; open: number; high: number; low: number; close: number; adj_close: number; volume: number; value: number; }
export interface IndexRecord { date: string; index_code: string; close: number; }
export interface QualityReport { ticker: string; missing_pct: number; }

export interface FactorRecord { date: string; [key: string]: string | number; }
export interface FactorStat { factor: string; mean: number; std: number; ann_mean: number; ann_std: number; t_stat: number; p_value: number; skew: number; kurt: number; n_obs: number; }
export interface CorrelationMatrix { factors: string[]; matrix: number[][]; }
export interface CumulativeReturn { date: string; [key: string]: number | string; }

export interface RegressionResult { model: string; ticker: string; alpha: number; alpha_t: number; alpha_p: number; betas: Record<string, number>; t_stats: Record<string, number>; p_values: Record<string, number>; adj_r2: number; aic: number; bic: number; n_obs: number; }
export interface DiagnosticsResult { vif: Record<string, number>; durbin_watson: number; bp_p: number; jb_p: number; adf: Record<string, number>; }
export interface ModelComparison { model: string; avg_adj_r2: number | null; delta_adj_r2: number | null; avg_aic?: number | null; grs_stat: number | null; grs_p: number | null; mean_abs_alpha: number | null; }
export interface GRSResult { model: string; grs_stat: number; p_value: number; mean_abs_alpha: number; }
export interface HypothesisResult { id: string; statement: string; statistic: number; p_value: number; verdict: string; note: string; }
export interface QuantileResult { tau: number; coefficients: Record<string, number>; lower_ci: Record<string, number>; upper_ci: Record<string, number>; }
export interface BestModel { model: string | null; criteria: Record<string, number | null>; ranking: Array<{ model: string; avg_adj_r2: number; grs_p: number | null; avg_aic: number | null; mean_abs_alpha: number | null }>; }

export interface PortfolioWeight { ticker: string; weight: number; expected_return: number; volatility: number; mu: number; sigma: number; }
export interface FrontierPoint { vol: number; ret: number; sharpe: number; weights?: Record<string, number>; }
export interface FrontierResponse { random: FrontierPoint[]; frontier: FrontierPoint[]; tangency: FrontierPoint; cml: FrontierPoint[]; assets: any[]; }

// Backend returns equity as an object, NOT an array
export interface EquityResponse { dates: string[]; vn30: number[]; equal: number[]; proposed: number[]; }
export interface DrawdownResponse { dates: string[]; vn30: number[]; equal: number[]; proposed: number[]; max_dd: Record<string, number>; }
export interface RollingSharpeResponse { dates: string[]; vn30: number[]; equal: number[]; proposed: number[]; }
export interface MetricsRecord { portfolio: string; cagr: number; vol: number; sharpe: number; sortino: number; max_dd: number; calmar: number; turnover: number; cost: number; }
export interface SensitivityRecord { w_max: number; estimator: string; sharpe: number; max_dd: number; fee: number; }

export interface JobStatus { job_id: string; status: 'pending' | 'running' | 'done' | 'error'; progress: number; run_id: string | null; error: string | null; }

export interface OptimizeRequest { model: string; cov_estimator: string; w_max: number; rf: number; train_start: string; train_end: string; objective: string; }
export interface BacktestRequest { run_id: string; mode: string; rebalance: string; fee_buy: number; fee_sell: number; test_start: string; test_end: string; }
export interface RegressionRunRequest { models: string[]; tickers?: string[]; freq: string; cov_type: string; start: string; end: string; }
