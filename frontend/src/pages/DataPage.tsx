import { useMemo, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { useDataQuality, usePrices, useStocks } from '../api/queries';
import DataTable from '../components/DataTable';
import ChartCard from '../components/ChartCard';
import { Spinner } from '../components/UI';
import DataGuide from '../components/DataGuide';

export default function DataPage() {
  const [selectedTicker, setSelectedTicker] = useState('ACB');
  const { data: qualityData, isLoading: qualityLoading } = useDataQuality();
  const { data: stocksData } = useStocks();
  const { data: pricesData, isLoading: pricesLoading } = usePrices(selectedTicker, '2020-01-01', '2026-12-31');

  // Chỉ tính các phiên có giá và khối lượng thật (loại dòng rỗng/giữ chỗ cuối kỳ).
  const rows = useMemo(() => {
    if (!pricesData?.data || !Array.isArray(pricesData.data)) return [];
    const valid = pricesData.data.filter((d: any) => d.close > 0 && d.volume > 0);
    // Bỏ các phiên cuối chưa đầy đủ: khối lượng dưới 20% mức trung vị của 60 phiên trước đó
    // (thường là dòng dữ liệu dở dang của ngày mới nhất).
    while (valid.length > 61) {
      const recent = valid.slice(-61, -1).map((d: any) => d.volume).sort((a: number, b: number) => a - b);
      const median = recent[Math.floor(recent.length / 2)];
      if (valid[valid.length - 1].volume < 0.2 * median) valid.pop();
      else break;
    }
    return valid;
  }, [pricesData]);

  const tickers = useMemo(() => {
    if (!stocksData?.data || !Array.isArray(stocksData.data)) return [];
    return stocksData.data.map((s: any) => s.ticker);
  }, [stocksData]);

  const qualityCols = useMemo(() => [
    { header: 'Mã CP', accessorKey: 'ticker' },
    { header: '% Dữ liệu thiếu', accessorKey: 'missing_pct', cell: (info: any) => `${((info.getValue() ?? 0) * 100).toFixed(2)}%` }
  ], []);

  const chartOption = useMemo(() => {
    if (rows.length === 0) return null;
    const dates = rows.map((d: any) => d.date);
    const basePrice = rows[0]?.close || 1;
    const normalized = rows.map((d: any) => ((d.close / basePrice) * 100).toFixed(2));
    return {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: dates, axisLabel: { showMaxLabel: true, hideOverlap: true } },
      yAxis: { type: 'value', name: 'Giá (Cơ sở 100)', min: 'dataMin' },
      series: [{ name: selectedTicker, type: 'line', data: normalized, showSymbol: false, lineStyle: { color: '#1F2A4A' } }]
    };
  }, [rows, selectedTicker]);

  return (
    <div className="space-y-6">
      <DataGuide />

      {/* Info cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm text-center">
          <div className="text-2xl font-bold text-navy-900">{tickers.length}</div>
          <div className="text-sm text-slate-500">Số mã CP VN30</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm text-center">
          <div className="text-2xl font-bold text-navy-900">
            {rows.length
              ? `${rows[0].date} – ${rows[rows.length - 1].date}`
              : '—'}
          </div>
          <div className="text-sm text-slate-500">Khoảng thời gian</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm text-center">
          <div className="text-2xl font-bold text-navy-900">
            {pricesData?.data ? rows.length : '...'}
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
