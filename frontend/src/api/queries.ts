import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from './client';
import * as T from './types';

// Data Quality
export const useDataQuality = () => useQuery({ queryKey: ['quality'], queryFn: () => apiClient.get<any, T.APIResponse<T.QualityReport[]>>('/data/quality') });
export const useStocks = () => useQuery({ queryKey: ['stocks'], queryFn: () => apiClient.get<any, T.APIResponse<T.StockInfo[]>>('/data/stocks') });
export const usePrices = (ticker: string, from: string, to: string) => useQuery({ queryKey: ['prices', ticker, from, to], queryFn: () => apiClient.get<any, T.APIResponse<T.PriceRecord[]>>('/data/prices', { params: { ticker, from, to } }) });

// Factors
export const useFactors = (from: string, to: string) => useQuery({ queryKey: ['factors', from, to], queryFn: () => apiClient.get<any, T.APIResponse<T.FactorRecord[]>>('/factors', { params: { from, to } }) });
export const useFactorStats = () => useQuery({ queryKey: ['factors', 'stats'], queryFn: () => apiClient.get<any, T.APIResponse<T.FactorStat[]>>('/factors/stats') });
export const useFactorCorrelation = () => useQuery({ queryKey: ['factors', 'correlation'], queryFn: () => apiClient.get<any, T.APIResponse<T.CorrelationMatrix>>('/factors/correlation') });
export const useFactorCumulative = () => useQuery({ queryKey: ['factors', 'cumulative'], queryFn: () => apiClient.get<any, T.APIResponse<T.CumulativeReturn[]>>('/factors/cumulative') });

// Regression
export const useRegressionResults = (model: string, runId: string) => useQuery({ queryKey: ['regression', model, runId], queryFn: () => apiClient.get<any, T.APIResponse<T.RegressionResult[]>>('/regression/results', { params: { model, run_id: runId } }), enabled: !!runId });
export const useDiagnostics = (model: string, runId: string) => useQuery({ queryKey: ['regression', 'diagnostics', model, runId], queryFn: () => apiClient.get<any, T.APIResponse<T.DiagnosticsResult[]>>('/regression/diagnostics', { params: { model, run_id: runId } }), enabled: !!runId });
export const useRunRegression = () => useMutation({ mutationFn: (data: T.RegressionRunRequest) => apiClient.post<any, T.APIResponse<{ job_id: string }>>('/regression/run', data) });

// Models
export const useModelComparison = (runId: string) => useQuery({ queryKey: ['models', 'compare', runId], queryFn: () => apiClient.get<any, T.APIResponse<T.ModelComparison[]>>('/regression/compare', { params: { run_id: runId } }), enabled: !!runId });
export const useGRS = (runId: string) => useQuery({ queryKey: ['models', 'grs', runId], queryFn: () => apiClient.get<any, T.APIResponse<T.GRSResult[]>>('/regression/grs', { params: { run_id: runId } }), enabled: !!runId });
export const useHypotheses = (runId: string) => useQuery({ queryKey: ['models', 'hypotheses', runId], queryFn: () => apiClient.get<any, T.APIResponse<T.HypothesisResult[]>>('/regression/hypotheses', { params: { run_id: runId } }), enabled: !!runId });
export const useBestModel = (runId: string) => useQuery({ queryKey: ['models', 'best', runId], queryFn: () => apiClient.get<any, T.APIResponse<T.BestModel>>('/regression/best', { params: { run_id: runId } }), enabled: !!runId });

// Quantile
export const useQuantileResults = (model: string, ticker: string) => useQuery({ queryKey: ['quantile', model, ticker], queryFn: () => apiClient.get<any, T.APIResponse<T.QuantileResult[]>>('/regression/quantile', { params: { model, ticker } }), enabled: !!model && !!ticker });

// Portfolio
export const usePortfolioWeights = (runId: string) => useQuery({ queryKey: ['portfolio', 'weights', runId], queryFn: () => apiClient.get<any, T.APIResponse<T.PortfolioWeight[]>>('/portfolio/weights', { params: { run_id: runId } }), enabled: !!runId });
export const useFrontier = (runId: string) => useQuery({ queryKey: ['portfolio', 'frontier', runId], queryFn: () => apiClient.get<any, T.APIResponse<T.FrontierResponse>>('/portfolio/frontier', { params: { run_id: runId } }), enabled: !!runId });
export const useOptimizePortfolio = () => useMutation({ mutationFn: (data: T.OptimizeRequest) => apiClient.post<any, T.APIResponse<{ job_id: string }>>('/portfolio/optimize', data) });

// Backtest
export const useEquity = (runId: string) => useQuery({ queryKey: ['backtest', 'equity', runId], queryFn: () => apiClient.get<any, T.APIResponse<T.EquityResponse>>('/backtest/equity', { params: { run_id: runId } }), enabled: !!runId });
export const useMetrics = (runId: string) => useQuery({ queryKey: ['backtest', 'metrics', runId], queryFn: () => apiClient.get<any, T.APIResponse<T.MetricsRecord[]>>('/backtest/metrics', { params: { run_id: runId } }), enabled: !!runId });
export const useRunBacktest = () => useMutation({ mutationFn: (data: T.BacktestRequest) => apiClient.post<any, T.APIResponse<{ job_id: string }>>('/backtest/run', data) });

export const useJobStatus = (jobId: string | null) => useQuery({
  queryKey: ['job', jobId],
  queryFn: () => apiClient.get<any, T.APIResponse<T.JobStatus>>(`/jobs/${jobId}`),
  enabled: !!jobId,
  refetchInterval: (query) => {
    const data = query.state.data;
    if (data?.data?.status === 'pending' || data?.data?.status === 'running') return 2000;
    return false;
  },
});
