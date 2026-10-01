import { useMemo, useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { useGlobalStore } from '../hooks/useGlobalStore';
import { useFrontier, useOptimizePortfolio } from '../api/queries';
import ChartCard from '../components/ChartCard';
import ConfigPanel, { ConfigValues } from '../components/ConfigPanel';
import { Spinner, JobProgress, RequestError } from '../components/UI';
import { useJob } from '../hooks/useJob';
import FrontierGuide from '../components/FrontierGuide';

export default function FrontierPage() {
  const { portfolioRunId, setPortfolioRunId } = useGlobalStore();
  const [jobId, setJobId] = useState<string | null>(null);
  const { progress, status, error, runId: newRunId, isDone } = useJob(jobId);
  const { mutate, isPending, error: submitError } = useOptimizePortfolio();
  
  const { data, isLoading } = useFrontier(portfolioRunId || '');

  useEffect(() => {
    if (isDone && newRunId && newRunId !== portfolioRunId) {
      setPortfolioRunId(newRunId);
    }
  }, [isDone, newRunId, portfolioRunId, setPortfolioRunId]);

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

  const chartOption = useMemo(() => {
    if (!data?.data) return null;
    const d = data.data;

    const random = d.random || [];
    const frontier = d.frontier || [];
    const tangency = d.tangency;

    if (random.length === 0 && frontier.length === 0 && !tangency?.ret) return null;

    const series: any[] = [];
    if (random.length > 0) {
      series.push({
        name: 'Danh mục ngẫu nhiên',
        type: 'scatter',
        symbolSize: 4,
        data: random.map((p: any) => [p.vol, p.ret, p.sharpe]),
        itemStyle: { color: '#93c5fd', opacity: 0.5 }
      });
    }
    if (frontier.length > 0) {
      series.push({
        name: 'Đường biên Hiệu quả',
        type: 'line',
        smooth: true,
        data: frontier.map((p: any) => [p.vol, p.ret]),
        lineStyle: { color: '#B8973A', width: 3 },
        symbol: 'none'
      });
    }
    if (tangency) {
      series.push({
        name: 'Danh mục Tiếp tuyến',
        type: 'scatter',
        symbol: 'star',
        symbolSize: 15,
        itemStyle: { color: 'red' },
        data: [[tangency.vol, tangency.ret, tangency.sharpe]]
      });
    }

    return {
      tooltip: { formatter: (params: any) => `Rủi ro: ${(params.value[0]*100).toFixed(2)}%<br/>Lợi suất: ${(params.value[1]*100).toFixed(2)}%` },
      xAxis: { type: 'value', name: 'Rủi ro (Biến động)', axisLabel: { formatter: (v: number) => `${(v*100).toFixed(1)}%` } },
      yAxis: { type: 'value', name: 'Lợi suất Kỳ vọng', axisLabel: { formatter: (v: number) => `${(v*100).toFixed(1)}%` } },
      series
    };
  }, [data]);

  return (
    <div className="flex gap-6">
      <div className="flex-1 space-y-6">
        <JobProgress progress={progress} status={status} error={error} />
        <RequestError error={submitError} />
        <FrontierGuide frontier={data?.data?.frontier} tangency={data?.data?.tangency} />

        <ChartCard title="Đường biên Hiệu quả Markowitz">
          {isLoading ? (
            <Spinner />
          ) : chartOption ? (
            <ReactECharts option={chartOption} style={{ height: '600px' }} />
          ) : (
            <div className="flex items-center justify-center h-64 text-slate-400 bg-white rounded-lg border border-slate-200 shadow-sm">
              Chưa có dữ liệu Đường biên Hiệu quả. Vui lòng bấm "Chạy thuật toán" bên phải.
            </div>
          )}
        </ChartCard>
      </div>
      <div className="w-80">
        <ConfigPanel hideFees onSubmit={handleRun} isLoading={isPending || status === 'pending' || status === 'running' || (!!jobId && !isDone && !error)} />
      </div>
    </div>
  );
}
