import { create } from 'zustand';

interface GlobalState {
  dateRange: { from: string; to: string };
  selectedModel: string;
  runId: string | null;
  setDateRange: (from: string, to: string) => void;
  setSelectedModel: (model: string) => void;
  setRunId: (id: string | null) => void;
}

export const useGlobalStore = create<GlobalState>((set) => ({
  dateRange: { from: '2020-01-01', to: '2026-12-31' },
  selectedModel: 'FF5_ALL',
  runId: null,
  setDateRange: (from, to) => set({ dateRange: { from, to } }),
  setSelectedModel: (model) => set({ selectedModel: model }),
  setRunId: (id) => set({ runId: id }),
}));
