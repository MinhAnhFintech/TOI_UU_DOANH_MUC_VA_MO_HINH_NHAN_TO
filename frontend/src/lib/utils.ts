import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number, decimals: number = 2) {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatNumber(value: number, decimals: number = 2) {
  return value.toFixed(decimals);
}

export function significanceStars(pValue: number) {
  if (pValue < 0.01) return '***';
  if (pValue < 0.05) return '**';
  if (pValue < 0.1) return '*';
  return '';
}
