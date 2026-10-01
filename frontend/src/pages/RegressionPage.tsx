import { useMemo, useState, useEffect } from 'react';
import { useGlobalStore } from '../hooks/useGlobalStore';
import { useRegressionResults, useRunRegression } from '../api/queries';
import DataTable from '../components/DataTable';
import ConfigPanel, { ConfigValues } from '../components/ConfigPanel';
import { Spinner, JobProgress, RequestError } from '../components/UI';
import { useJob } from '../hooks/useJob';
import { MODELS } from '../lib/constants';
import RegressionGuide from '../components/RegressionGuide';

export default function RegressionPage() {
  const { selectedModel, setSelectedModel, regressionRunId, setRegressionRunId } = useGlobalStore();
  const [jobId, setJobId] = useState<string | null>(null);
  const { progress, status, error, runId: newRunId, isDone } = useJob(jobId);
  const { mutate, isPending, error: submitError } = useRunRegression();

  const { data, isLoading } = useRegressionResults(selectedModel, regressionRunId || '');
  useEffect(() => {
    if (isDone && newRunId && newRunId !== regressionRunId) {
      setRegressionRunId(newRunId);
    }
  }, [isDone, newRunId, regressionRunId, setRegressionRunId]);

  const handleRun = (formData: ConfigValues) => {
    setSelectedModel(formData.model);
    mutate({
      models: MODELS,
      freq: formData.data_freq,
      cov_type: formData.cov_type,
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
      { header: 'Alpha', accessorFn: (row: any) => row, cell: (info: any) => {
          const row = info.getValue();
          if (row.alpha == null) return 'N/A';
          return (
            <div title={`Alpha: ${row.alpha}\nT-Stat: ${row.alpha_t}\nP-value: ${row.alpha_p}`} className="flex flex-col items-start">
              <span className="font-medium">{row.alpha.toFixed(6)}</span>
              <span className="text-xs text-slate-500">({row.alpha_t?.toFixed(2)})</span>
            </div>
          )
        }
      },
      { header: 'Adj R2', accessorKey: 'adj_r2', cell: (info: any) => <span title={info.getValue()}>{info.getValue()?.toFixed(4) ?? 'N/A'}</span> },
    ];
    const firstRow = data.data[0];
    const betaKeys = firstRow.betas ? Object.keys(firstRow.betas) : [];
    const betas = betaKeys.map(b => ({
        header: `Beta ${b.toUpperCase()}`,
        accessorFn: (row: any) => row,
        cell: (info: any) => {
          const row = info.getValue();
          const val = row.betas?.[b];
          const t = row.t_stats?.[b];
          const p = row.p_values?.[b];
          if (val == null) return 'N/A';
          return (
            <div title={`Hệ số: ${val}\nT-Stat: ${t}\nP-value: ${p}`} className="flex flex-col items-start">
              <span className="font-medium">{val.toFixed(4)}</span>
              <span className="text-xs text-slate-500">({t?.toFixed(2)})</span>
            </div>
          );
        }
      }));
    return [...base, ...betas];
  }, [data]);

  return (
    <div className="flex gap-6">
      <div className="flex-1 space-y-6">
        <RegressionGuide />
        <JobProgress progress={progress} status={status} error={error} />
        <RequestError error={submitError} />
        
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
        <ConfigPanel regressionMode onSubmit={handleRun} isLoading={isPending || status === 'pending' || status === 'running' || (!!jobId && !isDone && !error)} />
      </div>
    </div>
  );
}
