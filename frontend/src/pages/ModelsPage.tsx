import { useMemo } from 'react';
import { useGlobalStore } from '../hooks/useGlobalStore';
import { useModelComparison, useGRS, useHypotheses } from '../api/queries';
import DataTable from '../components/DataTable';
import { Spinner } from '../components/UI';
import ModelsGuide from '../components/ModelsGuide';

export default function ModelsPage() {
  const { regressionRunId } = useGlobalStore();
  const { data: compareData, isLoading: compareLoading } = useModelComparison(regressionRunId || '');
  const { data: grsData, isLoading: grsLoading } = useGRS(regressionRunId || '');
  const { data: hypData } = useHypotheses(regressionRunId || '');

  const compColumns = useMemo(() => [
    { header: 'Mô hình', accessorKey: 'model' },
    { header: 'Avg Adj R²', accessorKey: 'avg_adj_r2', cell: (info: any) => info.getValue()?.toFixed(4) ?? 'N/A' },
    { header: 'Δ Adj R²', accessorKey: 'delta_adj_r2', cell: (info: any) => info.getValue()?.toFixed(4) ?? 'N/A' },
  ], []);

  const grsColumns = useMemo(() => [
    { header: 'Mô hình', accessorKey: 'model' },
    { header: 'GRS Stat', accessorKey: 'grs_stat', cell: (info: any) => info.getValue()?.toFixed(4) ?? 'N/A' },
    { header: 'p-value', accessorKey: 'p_value', cell: (info: any) => info.getValue()?.toFixed(4) ?? 'N/A' },
    { header: 'Mean |α|', accessorKey: 'mean_abs_alpha', cell: (info: any) => info.getValue()?.toFixed(6) ?? 'N/A' },
  ], []);

  const hypColumns = useMemo(() => [
    { header: 'Mã giả thuyết', accessorKey: 'id' },
    { header: 'Giả thuyết', accessorKey: 'statement' },
    { header: 'Thống kê', accessorKey: 'statistic', cell: (info: any) => info.getValue()?.toFixed(4) ?? 'N/A' },
    { header: 'p-value', accessorKey: 'p_value', cell: (info: any) => info.getValue()?.toFixed(4) ?? 'N/A' },
    { header: 'Kết luận', accessorKey: 'verdict' },
    { header: 'Ghi chú', accessorKey: 'note' },
  ], []);

  if (compareLoading || grsLoading) return <div className="flex justify-center p-8"><Spinner /></div>;

  const hasCompare = compareData?.data && Array.isArray(compareData.data) && compareData.data.length > 0;
  const hasGRS = grsData?.data && Array.isArray(grsData.data) && grsData.data.length > 0;
  const hasHyp = hypData?.data && Array.isArray(hypData.data) && hypData.data.length > 0;

  if (!hasCompare && !hasGRS) {
    return (
      <div className="space-y-6">
        <ModelsGuide />
        <div className="text-center p-8 text-slate-500">
          Chưa có kết quả so sánh mô hình. Vui lòng chạy Hồi Quy trước.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ModelsGuide compare={compareData?.data} grs={grsData?.data} hyp={hypData?.data} />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <DataTable columns={compColumns} data={compareData?.data || []} title="So sánh Mô hình (Sức giải thích)" />
        <DataTable columns={grsColumns} data={grsData?.data || []} title="Kết quả Kiểm định GRS" />
      </div>
      {hasHyp && (
        <DataTable columns={hypColumns} data={hypData?.data || []} title="Kiểm định Giả thuyết H1-H5" />
      )}
    </div>
  );
}
