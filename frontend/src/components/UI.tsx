import { cn } from '../lib/utils';

export function Badge({ children, significant }: { children: React.ReactNode, significant?: boolean }) {
  return (
    <span className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium", significant ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800")}>
      {children}
    </span>
  );
}

export function Spinner() {
  return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy-600"></div>;
}

export function JobProgress({ progress, status, error }: { progress: number; status?: string; error?: string | null }) {
  if ((!status || status === 'done') && !error) return null;
  const statusLabels: Record<string, string> = {
    pending: 'Đang chờ',
    running: 'Đang chạy',
    error: 'Thất bại',
  };
  const boundedProgress = Math.max(0, Math.min(100, progress));
  const displayProgress = Math.round(boundedProgress);
  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 my-4">
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium text-slate-700">Trạng thái: {status ? statusLabels[status] || status : 'Không kết nối được'}</span>
        {status !== 'error' && status !== 'done' && <span className="text-sm font-medium text-slate-700">{displayProgress}%</span>}
      </div>
      {status !== 'error' && status !== 'done' && <div className="w-full bg-slate-200 rounded-full h-2.5">
        <div className="bg-navy-600 h-2.5 rounded-full transition-all duration-500" style={{ width: `${displayProgress}%` }}></div>
      </div>}
      {error && <p role="alert" className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}

export function RequestError({ error }: { error: unknown }) {
  if (!error) return null;
  const value = error as any;
  const raw = value.response?.data?.error?.message
    || value.response?.data?.detail
    || value.message
    || String(error);
  const message = typeof raw === 'string'
    ? raw
    : Array.isArray(raw)
      ? raw.map((item) => item?.msg || String(item)).join('; ')
      : JSON.stringify(raw);
  return <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{message}</div>;
}
