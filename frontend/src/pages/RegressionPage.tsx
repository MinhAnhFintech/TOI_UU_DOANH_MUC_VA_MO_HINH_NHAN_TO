import { useMemo, useState, useEffect } from 'react';
import { useGlobalStore } from '../hooks/useGlobalStore';
import { useRegressionResults, useRunRegression } from '../api/queries';
import DataTable from '../components/DataTable';
import ConfigPanel, { ConfigValues } from '../components/ConfigPanel';
import { Spinner, JobProgress } from '../components/UI';
import { useJob } from '../hooks/useJob';
import { MODELS } from '../lib/constants';

export default function RegressionPage() {
  const { selectedModel, setSelectedModel, runId, setRunId } = useGlobalStore();
  const [jobId, setJobId] = useState<string | null>(null);
  const { progress, status, error, runId: newRunId, isDone } = useJob(jobId);
  const { mutate, isPending } = useRunRegression();

  const { data, isLoading } = useRegressionResults(selectedModel, runId || 'default');
  useEffect(() => {
    if (isDone && newRunId && newRunId !== runId) {
      setRunId(newRunId);
    }
  }, [isDone, newRunId, runId, setRunId]);

  const handleRun = (formData: ConfigValues) => {
    setSelectedModel(formData.model);
    mutate({
      models: MODELS,
      freq: 'daily',
      cov_type: 'HAC',
      start: formData.train_start,
      end: formData.train_end,
    }, {
      onSuccess: (res) => setJobId(res.data.job_id)
    });
  };

  const columns = useMemo(() => {
    if (!data?.data || !Array.isArray(data.data) || data.data.length === 0) return [
      { header: 'Mã CP', accessorKey: 'ticker' },
      { header: 'Alpha', accessorKey: 'alpha' },
      { header: 'Adj R²', accessorKey: 'adj_r2' },
    ];
    const base = [
      { header: 'Mã CP', accessorKey: 'ticker' },
      { header: 'Alpha', accessorKey: 'alpha', cell: (info: any) => <span title={info.getValue()}>{info.getValue()?.toFixed(6) ?? 'N/A'}</span> },
      { header: 'Alpha t', accessorKey: 'alpha_t', cell: (info: any) => <span title={info.getValue()}>{info.getValue()?.toFixed(2) ?? 'N/A'}</span> },
      { header: 'Adj R2', accessorKey: 'adj_r2', cell: (info: any) => <span title={info.getValue()}>{info.getValue()?.toFixed(4) ?? 'N/A'}</span> },
    ];
    const firstRow = data.data[0];
    const betaKeys = firstRow.betas ? Object.keys(firstRow.betas) : [];
    const betas = betaKeys.map(b => ({
      header: `β ${b.toUpperCase()}`,
      accessorFn: (row: any) => row.betas?.[b] ?? null,
      cell: (info: any) => {
        const val = info.getValue();
        const p = info.row.original.p_values?.[b];
        if (val == null) return 'N/A';
        return (
          <span title={`Chinh xac: ${val}\nP-value: ${p}`}>
            {val.toFixed(4)}
          </span>
        );
      }
    }));
    return [...base, ...betas];
  }, [data]);

  return (
    <div className="flex gap-6">
      <div className="flex-1 space-y-6">
        <JobProgress progress={progress} status={status} error={error} />
        
        {!isLoading && data?.data && data.data.length > 0 && (
          <div className="flex items-center gap-3 bg-white p-3 rounded-lg shadow-sm border border-slate-200">
            <label className="text-sm font-medium text-slate-700">Chọn mô hình xem:</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="rounded-md border-slate-300 shadow-sm focus:border-navy-500 focus:ring-navy-500 sm:text-sm p-2 border"
            >
              {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
        )}

        {isLoading ? (
          <div className="flex justify-center p-8"><Spinner /></div>
        ) : !data?.data || data.data.length === 0 ? (
          <div className="text-center p-8 text-slate-500 bg-white rounded-lg shadow-sm border border-slate-200">
            Chưa có kết quả hồi quy. Vui lòng bấm "Chạy thuật toán" bên phải để hệ thống tính toán.
          </div>
        ) : (
          <DataTable columns={columns} data={data.data} title={`Kết quả Hồi Quy (${selectedModel})`} />
        )}
      </div>
      <div className="w-80">
        <ConfigPanel onSubmit={handleRun} isLoading={isPending || status === 'running'} />
      </div>
    </div>
  );
}
