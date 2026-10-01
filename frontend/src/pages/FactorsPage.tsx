import { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { useFactorStats, useFactorCumulative } from '../api/queries';
import DataTable from '../components/DataTable';
import ChartCard from '../components/ChartCard';
import { Spinner } from '../components/UI';
import FactorGuide from '../components/FactorGuide';

export default function FactorsPage() {
  const { data: statsData, isLoading: statsLoading } = useFactorStats();
  const { data: cumData, isLoading: cumLoading } = useFactorCumulative();

  const columns = useMemo(() => [
    { header: 'Nhân tố', accessorKey: 'factor', cell: (info: any) => String(info.getValue() ?? '').replace(/_$/, '').toUpperCase() },
    { header: 'Trung bình', accessorKey: 'mean', cell: (info: any) => info.getValue()?.toFixed(6) ?? 'N/A' },
    { header: 'Độ lệch chuẩn', accessorKey: 'std', cell: (info: any) => info.getValue()?.toFixed(6) ?? 'N/A' },
    { header: 'TB Năm', accessorKey: 'ann_mean', cell: (info: any) => info.getValue() ? `${(info.getValue() * 100).toFixed(2)}%` : 'N/A' },
    { header: 't-stat', accessorKey: 't_stat', cell: (info: any) => info.getValue()?.toFixed(2) ?? 'N/A' },
    { header: 'p-value', accessorKey: 'p_value', cell: (info: any) => { const v = info.getValue(); return v != null ? <span title={v.toString()}>{v.toFixed(4)}</span> : 'N/A'; } },
    { header: 'Skew', accessorKey: 'skew', cell: (info: any) => info.getValue()?.toFixed(4) ?? 'N/A' },
    { header: 'Kurtosis', accessorKey: 'kurt', cell: (info: any) => info.getValue()?.toFixed(4) ?? 'N/A' },
    { header: 'N', accessorKey: 'n_obs' },
  ], []);

  const chartOption = useMemo(() => {
    if (!cumData?.data || !Array.isArray(cumData.data) || cumData.data.length === 0) return null;
    const dates = cumData.data.map((d: any) => d.date);
    const series = Object.keys(cumData.data[0]).filter(k => k !== 'date').map(factor => ({
      name: factor.replace(/_$/, '').toUpperCase(),
      type: 'line' as const,
      data: cumData.data.map((d: any) => d[factor]),
      showSymbol: false,
    }));
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: series.map(s => s.name) },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', name: 'Lợi suất tích lũy' },
      series
    };
  }, [cumData]);

  if (statsLoading) return <div className="flex justify-center p-8"><Spinner /></div>;

  return (
    <div className="space-y-6">
      <FactorGuide stats={statsData?.data} />
      <ChartCard title="Lợi suất Tích lũy các Nhân tố">
        {cumLoading ? <Spinner /> : chartOption ? (
          <ReactECharts option={chartOption} style={{ height: '400px' }} />
        ) : (
          <div className="flex items-center justify-center h-64 text-slate-400">
            Chưa có dữ liệu nhân tố. Vui lòng chạy thu thập dữ liệu trước.
          </div>
        )}
      </ChartCard>
      <DataTable columns={columns} data={statsData?.data || []} title="Thống kê Mô tả Nhân tố" />
    </div>
  );
}


