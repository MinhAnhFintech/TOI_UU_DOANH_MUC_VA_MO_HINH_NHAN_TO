import { useMemo, useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { useGlobalStore } from '../hooks/useGlobalStore';
import { usePortfolioWeights, useOptimizePortfolio } from '../api/queries';
import DataTable from '../components/DataTable';
import ChartCard from '../components/ChartCard';
import ConfigPanel, { ConfigValues } from '../components/ConfigPanel';
import { Spinner, JobProgress } from '../components/UI';
import { useJob } from '../hooks/useJob';

export default function WeightsPage() {
  const { runId, setRunId } = useGlobalStore();
  const [jobId, setJobId] = useState<string | null>(null);
  const { progress, status, error, runId: newRunId, isDone } = useJob(jobId);
  const { mutate, isPending } = useOptimizePortfolio();

  const { data, isLoading } = usePortfolioWeights(runId || 'default');

  useEffect(() => {
    if (isDone && newRunId && newRunId !== runId) {
      setRunId(newRunId);
    }
  }, [isDone, newRunId, runId, setRunId]);

  const handleRun = (formData: ConfigValues) => {
    mutate({
      model: formData.model,
      cov_estimator: formData.estimator,
      w_max: formData.w_max,
      rf: 0.05,
      objective: 'max_sharpe',
      train_start: formData.train_start,
      train_end: formData.train_end,
    }, {
      onSuccess: (res) => setJobId(res.data.job_id)
    });
  };

  const columns = useMemo(() => [
    { header: 'Mã CP', accessorKey: 'ticker' },
    { header: 'Tỷ trọng', accessorKey: 'weight', cell: (info: any) => `${((info.getValue() ?? 0) * 100).toFixed(2)}%` },
    { header: 'Lợi suất Kỳ vọng', accessorKey: 'expected_return', cell: (info: any) => info.getValue() != null ? `${(info.getValue() * 100).toFixed(2)}%` : 'N/A' },
    { header: 'Biến động', accessorKey: 'volatility', cell: (info: any) => info.getValue() != null ? `${(info.getValue() * 100).toFixed(2)}%` : 'N/A' },
  ], []);

  const chartOption = useMemo(() => {
    if (!data?.data || !Array.isArray(data.data) || data.data.length === 0) return null;
    const sorted = [...data.data].sort((a, b) => b.weight - a.weight).filter(w => w.weight > 0);
    if (sorted.length === 0) return null;
    return {
      tooltip: { trigger: 'axis', formatter: (params: any) => `${params[0].name}: ${(params[0].value * 100).toFixed(2)}%` },
      xAxis: { type: 'value', axisLabel: { formatter: (v: number) => `${(v * 100).toFixed(0)}%` } },
      yAxis: { type: 'category', data: sorted.map(d => d.ticker).reverse() },
      series: [{ type: 'bar', data: sorted.map(d => d.weight).reverse(), itemStyle: { color: '#1F2A4A' } }]
    };
  }, [data]);

  return (
    <div className="flex gap-6">
      <div className="flex-1 space-y-6">
        <JobProgress progress={progress} status={status} error={error} />
        <div className="p-4 bg-blue-50 text-blue-800 rounded-lg text-sm mb-4 border border-blue-100">
          <strong>Lưu ý:</strong> Thuật toán Markowitz sẽ tự động loại bỏ các mã cổ phiếu không hiệu quả (gán tỷ trọng 0%). Để ép danh mục phải mua nhiều mã hơn nhằm phân tán rủi ro, hãy giảm <strong>Tỷ trọng tối đa / mã (w_max)</strong> ở bảng cấu hình bên phải rồi chạy lại thuật toán.
        </div>
        <ChartCard title="Tỷ trọng Danh mục Tối ưu">
          {isLoading ? (
            <Spinner />
          ) : chartOption ? (
            <ReactECharts option={chartOption} style={{ height: '500px' }} />
          ) : (
            <div className="flex items-center justify-center h-64 text-slate-400 bg-white rounded-lg border border-slate-200 shadow-sm">
              Chưa có dữ liệu tỷ trọng. Vui lòng bấm "Chạy thuật toán" bên phải.
            </div>
          )}
        </ChartCard>
        
        {(!isLoading && chartOption) && (
          <DataTable columns={columns} data={data?.data || []} title="Chi tiết Tỷ trọng" />
        )}
      </div>
      <div className="w-80">
        <ConfigPanel onSubmit={handleRun} isLoading={isPending || status === 'running'} />
      </div>
    </div>
  );
}
