import { useMemo, useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { useGlobalStore } from '../hooks/useGlobalStore';
import { useEquity, useDrawdown, useMetrics, useRunBacktest } from '../api/queries';
import DataTable from '../components/DataTable';
import ChartCard from '../components/ChartCard';
import ConfigPanel, { ConfigValues } from '../components/ConfigPanel';
import { Spinner, JobProgress, RequestError } from '../components/UI';
import { useJob } from '../hooks/useJob';
import { formatPercent } from '../lib/utils';

export default function BacktestPage() {
  const { portfolioRunId, backtestRunId, setBacktestRunId } = useGlobalStore();
  const [jobId, setJobId] = useState<string | null>(null);
  const { progress, status, error, runId: newRunId, isDone } = useJob(jobId);
  const { mutate, isPending, error: submitError } = useRunBacktest();

  const { data: equityData, isLoading: equityLoading } = useEquity(backtestRunId || '');
  const { data: ddData, isLoading: ddLoading } = useDrawdown(backtestRunId || '');
  const { data: metricsData, isLoading: metricsLoading } = useMetrics(backtestRunId || '');

  useEffect(() => {
    if (isDone && newRunId && newRunId !== backtestRunId) {
      setBacktestRunId(newRunId);
    }
  }, [isDone, newRunId, backtestRunId, setBacktestRunId]);

  const handleRun = (formData: ConfigValues) => {
    mutate({
      run_id: portfolioRunId || '',
      mode: 'fixed',
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

  const ddOption = useMemo(() => {
    const d = ddData?.data;
    if (!d || !d.dates || d.dates.length === 0) return null;
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['Tối ưu', 'VN30', 'Equal Weight'] },
      xAxis: { type: 'category', data: d.dates },
      yAxis: { type: 'value', axisLabel: { formatter: (val: number) => (val * 100).toFixed(0) + '%' } },
      dataZoom: [{ type: 'inside' }, { type: 'slider' }],
      series: [
        { name: 'Tối ưu', type: 'line', data: d.proposed, showSymbol: false, areaStyle: { color: 'rgba(184, 151, 58, 0.2)' }, lineStyle: { color: '#B8973A', width: 1 } },
        { name: 'VN30', type: 'line', data: d.vn30, showSymbol: false, lineStyle: { color: '#1F2A4A', width: 1 } },
        { name: 'Equal Weight', type: 'line', data: d.equal, showSymbol: false, lineStyle: { color: '#64748b', width: 1 } }
      ]
    };
  }, [ddData]);

    const metricCols = [
    { header: 'Danh mục', accessorKey: 'portfolio', cell: (i: any) => i.getValue() === 'proposed' ? 'Tối ưu (Max Sharpe)' : i.getValue().toUpperCase() },
    { header: 'CAGR (Năm)', accessorKey: 'cagr', cell: (i: any) => formatPercent(i.getValue()) },
    { header: 'Rủi ro (Năm)', accessorKey: 'vol', cell: (i: any) => formatPercent(i.getValue()) },
    { header: 'Sharpe', accessorKey: 'sharpe', cell: (i: any) => i.getValue()?.toFixed(2) },
    { header: 'Max Drawdown', accessorKey: 'max_dd', cell: (i: any) => formatPercent(i.getValue()) },
    { header: 'Vòng quay (Turnover)', accessorKey: 'turnover', cell: (i: any) => i.getValue()?.toFixed(2) },
    { header: 'Tổng Phí GD (Cost)', accessorKey: 'cost', cell: (i: any) => formatPercent(i.getValue()) },
  ];

  return (
    <div className="flex gap-6">
      <div className="flex-1 space-y-6">
        <JobProgress progress={progress} status={status} error={error} />
        <RequestError error={submitError} />
        <ChartCard title="Đường cong Vốn (Equity Curve)">
            {equityLoading ? <Spinner /> : equityOption ? (
              <ReactECharts option={equityOption} style={{ height: '400px' }} />
            ) : (
              <div className="flex items-center justify-center h-64 text-slate-400">
                Chưa có dữ liệu Backtest. Vui lòng cấu hình và chạy Backtest.
              </div>
            )}
          </ChartCard>
          
          <ChartCard title="Độ sụt giảm tài khoản (Drawdown)">
            {ddLoading ? <Spinner /> : ddOption ? (
              <ReactECharts option={ddOption} style={{ height: '300px' }} />
            ) : null}
          </ChartCard>
        {metricsLoading ? <Spinner /> : (
          <DataTable columns={metricCols} data={metricsData?.data || []} title="Chỉ số Hiệu suất" />
        )}
      </div>
      <div className="w-80">
      <ConfigPanel onSubmit={handleRun} showTestDates isLoading={isPending || status === 'pending' || status === 'running' || (!!jobId && !isDone && !error)} disabledReason={!portfolioRunId ? 'Hãy tạo danh mục trước' : undefined} />
      </div>
    </div>
  );
}
