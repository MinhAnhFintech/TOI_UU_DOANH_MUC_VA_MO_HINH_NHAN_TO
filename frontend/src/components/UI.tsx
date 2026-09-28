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
  if (!status || status === 'done') return null;
  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 my-4">
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium text-slate-700">Trạng thái: {status}</span>
        <span className="text-sm font-medium text-slate-700">{progress}%</span>
      </div>
      <div className="w-full bg-slate-200 rounded-full h-2.5">
        <div className="bg-navy-600 h-2.5 rounded-full transition-all duration-500" style={{ width: `${progress}%` }}></div>
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
