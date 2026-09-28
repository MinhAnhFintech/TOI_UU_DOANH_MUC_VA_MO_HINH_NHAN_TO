import { useMemo, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { useDataQuality, usePrices, useStocks } from '../api/queries';
import DataTable from '../components/DataTable';
import ChartCard from '../components/ChartCard';
import { Spinner } from '../components/UI';

export default function DataPage() {
  const [selectedTicker, setSelectedTicker] = useState('ACB');
  const { data: qualityData, isLoading: qualityLoading } = useDataQuality();
  const { data: stocksData } = useStocks();
  const { data: pricesData, isLoading: pricesLoading } = usePrices(selectedTicker, '2020-01-01', '2026-12-31');

  const tickers = useMemo(() => {
    if (!stocksData?.data || !Array.isArray(stocksData.data)) return [];
    return stocksData.data.map((s: any) => s.ticker);
  }, [stocksData]);

  const qualityCols = useMemo(() => [
    { header: 'Mã CP', accessorKey: 'ticker' },
    { header: '% Dữ liệu thiếu', accessorKey: 'missing_pct', cell: (info: any) => `${((info.getValue() ?? 0) * 100).toFixed(2)}%` }
  ], []);

  const chartOption = useMemo(() => {
    if (!pricesData?.data || !Array.isArray(pricesData.data) || pricesData.data.length === 0) return null;
    const dates = pricesData.data.map((d: any) => d.date);
    const basePrice = pricesData.data[0]?.close || 1;
    const normalized = pricesData.data.map((d: any) => ((d.close / basePrice) * 100).toFixed(2));
    return {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', name: 'Giá (Cơ sở 100)', min: 'dataMin' },
      series: [{ name: selectedTicker, type: 'line', data: normalized, showSymbol: false, lineStyle: { color: '#1F2A4A' } }]
    };
  }, [pricesData, selectedTicker]);

  return (
    <div className="space-y-6">
      {/* Info cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm text-center">
          <div className="text-2xl font-bold text-navy-900">{tickers.length}</div>
          <div className="text-sm text-slate-500">Số mã CP VN30</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm text-center">
          <div className="text-2xl font-bold text-navy-900">2020 - 2026</div>
          <div className="text-sm text-slate-500">Khoảng thời gian</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm text-center">
          <div className="text-2xl font-bold text-navy-900">
            {pricesData?.data ? pricesData.data.length : '...'}
          </div>
          <div className="text-sm text-slate-500">Số phiên giao dịch ({selectedTicker})</div>
        </div>
      </div>

      {/* Ticker selector */}
      <div className="bg-white p-4 rounded-lg shadow-sm">
        <label className="text-sm font-medium text-slate-700 mr-2">Chọn mã cổ phiếu:</label>
        <select
          value={selectedTicker}
          onChange={(e) => setSelectedTicker(e.target.value)}
          className="border rounded px-3 py-1 text-sm"
        >
          {tickers.map((t: string) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ChartCard title={`Giá Chuẩn hóa - ${selectedTicker} (Cơ sở 100)`}>
          {pricesLoading ? <Spinner /> : chartOption ? (
            <ReactECharts option={chartOption} style={{ height: '400px', width: '100%' }} />
          ) : (
            <div className="flex items-center justify-center h-64 text-slate-400">Chưa có dữ liệu giá</div>
          )}
        </ChartCard>
        <div className="bg-white p-4 rounded-lg shadow-sm">
          {qualityLoading ? <Spinner /> : (
            <DataTable columns={qualityCols} data={qualityData?.data && Array.isArray(qualityData.data) ? qualityData.data : []} title="Báo cáo Chất lượng Dữ liệu" />
          )}
        </div>
      </div>
    </div>
  );
}
