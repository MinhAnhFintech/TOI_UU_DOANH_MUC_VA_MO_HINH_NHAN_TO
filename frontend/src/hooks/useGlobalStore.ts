import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface GlobalState {
  dateRange: { from: string; to: string };
  selectedModel: string;
  regressionRunId: string | null;
  portfolioRunId: string | null;
  backtestRunId: string | null;
  setDateRange: (from: string, to: string) => void;
  setSelectedModel: (model: string) => void;
  setRegressionRunId: (id: string | null) => void;
  setPortfolioRunId: (id: string | null) => void;
  setBacktestRunId: (id: string | null) => void;
}

export const useGlobalStore = create<GlobalState>()(
  persist(
    (set) => ({
      dateRange: { from: '2020-01-01', to: '2026-12-31' },
      selectedModel: 'FF5_ALL',
      regressionRunId: null,
      portfolioRunId: null,
      backtestRunId: null,
      setDateRange: (from, to) => set({ dateRange: { from, to } }),
      setSelectedModel: (model) => set({ selectedModel: model }),
      setRegressionRunId: (id) => set({ regressionRunId: id }),
      setPortfolioRunId: (id) => set({ portfolioRunId: id }),
      setBacktestRunId: (id) => set({ backtestRunId: id }),
    }),
    {
      name: 'vn30-global-store',
    }
  )
);
