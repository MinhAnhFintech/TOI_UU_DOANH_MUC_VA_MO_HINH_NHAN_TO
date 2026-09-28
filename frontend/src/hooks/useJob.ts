import { useJobStatus } from '../api/queries';

export function useJob(jobId: string | null) {
  const { data, isLoading, error } = useJobStatus(jobId);
  const status = data?.data?.status;
  return {
    status,
    progress: data?.data?.progress || 0,
    runId: data?.data?.run_id || null,
    error: data?.data?.error || error?.message || null,
    isLoading: status === 'pending' || status === 'running' || isLoading,
    isDone: status === 'done',
    isFailed: status === 'failed',
  };
}
