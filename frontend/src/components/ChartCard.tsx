import React, { useRef } from 'react';
import { Download } from 'lucide-react';
import { toPng } from 'html-to-image';
import { saveAs } from 'file-saver';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  isLoading?: boolean;
  error?: string | null;
  isEmpty?: boolean;
}

export default function ChartCard({ title, subtitle, children, isLoading, error, isEmpty }: ChartCardProps) {
  const chartRef = useRef<HTMLDivElement>(null);

  const exportPNG = () => {
    if (chartRef.current) {
      toPng(chartRef.current, { backgroundColor: '#ffffff' }).then((dataUrl) => {
        saveAs(dataUrl, `${title.replace(/\s+/g, '_')}.png`);
      });
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 flex flex-col h-full">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-medium text-slate-800">{title}</h3>
          {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
        </div>
        <button onClick={exportPNG} className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors" title="Xuất ảnh PNG">
          <Download className="w-4 h-4" />
        </button>
      </div>
      <div className="flex-1 min-h-[300px] relative" ref={chartRef}>
        {isLoading && <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">Loading...</div>}
        {error && <div className="absolute inset-0 flex items-center justify-center text-red-500 z-10">{error}</div>}
        {isEmpty && !isLoading && !error && <div className="absolute inset-0 flex items-center justify-center text-slate-400 z-10">No data available</div>}
        <div className="w-full h-full">
          {children}
        </div>
      </div>
    </div>
  );
}
