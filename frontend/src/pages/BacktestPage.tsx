import { useMemo, useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { useGlobalStore } from '../hooks/useGlobalStore';
import { useEquity, useMetrics, useRunBacktest } from '../api/queries';
import DataTable from '../components/DataTable';
import ChartCard from '../components/ChartCard';
import ConfigPanel, { ConfigValues } from '../components/ConfigPanel';
import { Spinner, JobProgress } from '../components/UI';
import { useJob } from '../hooks/useJob';

export default function BacktestPage() {
  const { runId, setRunId } = useGlobalStore();
  const [jobId, setJobId] = useState<string | null>(null);
  const { progress, status, error, runId: newRunId, isDone } = useJob(jobId);
  const { mutate, isPending } = useRunBacktest();

  const { data: equityData, isLoading: equityLoading } = useEquity(runId || 'default');
  const { data: metricsData, isLoading: metricsLoading } = useMetrics(runId || 'default');

  useEffect(() => {
    if (isDone && newRunId && newRunId !== runId) {
      setRunId(newRunId);
    }
  }, [isDone, newRunId, runId, setRunId]);

  const handleRun = (formData: ConfigValues) => {
    mutate({
      run_id: runId || 'default',
      mode: 'rolling',
      rebalance: formData.frequency === 'M' ? 'monthly' : 'quarterly',
      fee_buy: formData.fee_buy,
      fee_sell: formData.fee_sell,
      test_start: formData.test_start,
      test_end: formData.test_end,
    }, {
      onSuccess: (res) => setJobId(res.data.job_id)
    });
  };

  // Backend returns {dates: [], vn30: [], equal: [], proposed: []} — NOT an array
  const equityOption = useMemo(() => {
    const d = equityData?.data;
    if (!d || !d.dates || d.dates.length === 0) return null;
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['VN30', 'Equal Weight', 'Đề xuất'] },
      xAxis: { type: 'category', data: d.dates },
      yAxis: { type: 'value', name: 'NAV' },
      series: [
        { name: 'VN30', type: 'line', data: d.vn30, showSymbol: false },
        { name: 'Equal Weight', type: 'line', data: d.equal, showSymbol: false },
        { name: 'Đề xuất', type: 'line', data: d.proposed, showSymbol: false, lineStyle: { color: '#B8973A', width: 2 } },
      ]
    };
  }, [equityData]);

  const metricCols = [
    { header: 'Danh mục', accessorKey: 'portfolio' },
    { header: 'CAGR', accessorKey: 'cagr', cell: (info: any) => `${(info.getValue() * 100).toFixed(2)}%` },
    { header: 'Biến động', accessorKey: 'vol', cell: (info: any) => `${(info.getValue() * 100).toFixed(2)}%` },
    { header: 'Sharpe', accessorKey: 'sharpe', cell: (info: any) => info.getValue()?.toFixed(4) ?? 'N/A' },
    { header: 'Sortino', accessorKey: 'sortino', cell: (info: any) => info.getValue()?.toFixed(4) ?? 'N/A' },
    { header: 'Max DD', accessorKey: 'max_dd', cell: (info: any) => `${(info.getValue() * 100).toFixed(2)}%` },
    { header: 'Calmar', accessorKey: 'calmar', cell: (info: any) => info.getValue()?.toFixed(4) ?? 'N/A' },
    { header: 'Turnover', accessorKey: 'turnover', cell: (info: any) => info.getValue()?.toFixed(4) ?? 'N/A' },
    { header: 'Chi phí (Cost)', accessorKey: 'cost', cell: (info: any) => info.getValue() != null ? `${(info.getValue() * 100).toFixed(2)}%` : '0.00%' },
  ];

  return (
    <div className="flex gap-6">
      <div className="flex-1 space-y-6">
        <JobProgress progress={progress} status={status} error={error} />
        <ChartCard title="Đường cong Vốn (Equity Curve)">
          {equityLoading ? <Spinner /> : equityOption ? (
            <ReactECharts option={equityOption} style={{ height: '400px' }} />
          ) : (
            <div className="flex items-center justify-center h-64 text-slate-400">
              Chưa có dữ liệu Backtest. Vui lòng cấu hình và chạy Backtest.
            </div>
          )}
        </ChartCard>
        {metricsLoading ? <Spinner /> : (
          <DataTable columns={metricCols} data={metricsData?.data || []} title="Chỉ số Hiệu suất" />
        )}
      </div>
      <div className="w-80">
        <ConfigPanel onSubmit={handleRun} isLoading={isPending || status === 'running'} />
      </div>
    </div>
  );
}
