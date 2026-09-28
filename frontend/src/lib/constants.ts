export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const COLORS = {
  primary: '#1F2A4A',
  accent: '#B8973A',
  success: '#10b981',
  danger: '#ef4444',
  warning: '#f59e0b',
  info: '#3b82f6',
};

export const MODELS = ['CAPM', 'FF3', 'FF5', 'FF5_LIQ', 'FF5_FOR', 'FF5_VOL', 'FF5_ALL'];
export const FACTORS = ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'LIQ', 'FOR', 'VOL'];
