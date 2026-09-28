import { useState, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { useGlobalStore } from '../hooks/useGlobalStore';
import { useQuantileResults, useStocks } from '../api/queries';
import ChartCard from '../components/ChartCard';
import { Spinner } from '../components/UI';

export default function QuantilePage() {
  const { selectedModel } = useGlobalStore();
  const [ticker, setTicker] = useState('ACB');
  const { data: stocksData } = useStocks();
  const { data, isLoading } = useQuantileResults(selectedModel, ticker);

  const tickers = useMemo(() => {
    if (!stocksData?.data || !Array.isArray(stocksData.data)) return [];
    return stocksData.data.map((s: any) => s.ticker);
  }, [stocksData]);

  const chartOption = useMemo(() => {
    if (!data?.data || !Array.isArray(data.data) || data.data.length === 0) return null;
    const taus = data.data.map((d: any) => d.tau);
    
    // Check if coefficients exists and has keys
    if (!data.data[0].coefficients) return null;
    const keys = Object.keys(data.data[0].coefficients);
    if (keys.length === 0) return null;
    
    const factor = keys[0]; // plot the first factor (usually mkt)
    const coefs = data.data.map((d: any) => d.coefficients[factor]);
    const lower = data.data.map((d: any) => d.lower_ci?.[factor] || 0);
    const upper = data.data.map((d: any) => d.upper_ci?.[factor] || 0);

    return {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: taus, name: 'Phân vị (tau)' },
      yAxis: { type: 'value', name: `Hệ số (${factor.toUpperCase()})` },
      series: [
        { name: 'Hệ số', type: 'line', data: coefs, lineStyle: { color: '#1F2A4A', width: 2 } },
        { name: 'Biên dưới (CI)', type: 'line', data: lower, lineStyle: { type: 'dashed', color: '#ef4444' }, showSymbol: false },
        { name: 'Biên trên (CI)', type: 'line', data: upper, lineStyle: { type: 'dashed', color: '#ef4444' }, showSymbol: false },
      ]
    };
  }, [data]);

  return (
    <div className="space-y-6">
      <div className="bg-white p-4 rounded-lg shadow-sm flex items-center space-x-4 mb-4">
        <label className="text-sm font-medium text-slate-700">Chọn mã cổ phiếu:</label>
        <select
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          className="border rounded px-3 py-1 text-sm"
        >
          {tickers.map((t: string) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>
      <ChartCard title={`Hồi quy Phân vị mã ${ticker} (Mô hình ${selectedModel})`}>
        {isLoading ? <Spinner /> : chartOption ? (
          <ReactECharts option={chartOption} style={{ height: '500px' }} />
        ) : (
          <div className="flex items-center justify-center h-64 text-slate-400">
            Chưa có kết quả phân vị. Xin hãy đảm bảo dữ liệu hồi quy đã chạy thành công.
          </div>
        )}
      </ChartCard>
    </div>
  );
}
