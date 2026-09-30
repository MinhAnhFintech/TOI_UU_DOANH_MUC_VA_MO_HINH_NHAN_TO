import { useGlobalStore } from '../hooks/useGlobalStore';
import { useBestModel, useMetrics, useModelComparison, useGRS, useHypotheses } from '../api/queries';
import { Spinner } from '../components/UI';
import { formatPercent } from '../lib/utils';

const MODEL_DESCRIPTIONS: Record<string, { name: string; factors: string; desc: string }> = {
  'CAPM': {
    name: 'Capital Asset Pricing Model',
    factors: 'MKT',
    desc: 'Mô hình cơ bản nhất: lợi suất vượt trội của cổ phiếu phụ thuộc vào rủi ro thị trường (beta). Alpha nhỏ cho thấy mô hình còn ít lợi suất bất thường chưa giải thích.'
  },
  'FF3': {
    name: 'Fama-French 3 Factors',
    factors: 'MKT + SMB + HML',
    desc: 'Bổ sung nhân tố Quy mô (SMB: Small-Big) và Giá trị (HML: High-Low B/M). Giải thích hiện tượng cổ phiếu nhỏ và cổ phiếu giá trị sinh lời cao hơn.'
  },
  'FF5': {
    name: 'Fama-French 5 Factors',
    factors: 'MKT + SMB + HML + RMW + CMA',
    desc: 'Thêm nhân tố Lợi nhuận (RMW: Robust-Weak) và Đầu tư (CMA: Conservative-Aggressive). Phản ánh công ty lợi nhuận cao và đầu tư bảo thủ sinh lời tốt hơn.'
  },
  'FF5_LIQ': {
    name: 'FF5 + Thanh khoản',
    factors: 'MKT + SMB + HML + RMW + CMA + LIQ',
    desc: 'Bổ sung nhân tố Thanh khoản (LIQ: Illiquid-Liquid). Cổ phiếu kém thanh khoản có premium bù đắp rủi ro không bán được.'
  },
  'FF5_FOR': {
    name: 'FF5 + Khối ngoại',
    factors: 'MKT + SMB + HML + RMW + CMA + FOR',
    desc: 'Bổ sung nhân tố Khối ngoại (FOR: High-Low Foreign). Phản ánh tác động của dòng vốn ngoại đến lợi suất cổ phiếu Việt Nam.'
  },
  'FF5_VOL': {
    name: 'FF5 + Biến động',
    factors: 'MKT + SMB + HML + RMW + CMA + VOL',
    desc: 'Bổ sung nhân tố Biến động (VOL: High-Low Volatility). Kiểm tra hiệu ứng "low volatility anomaly" trên thị trường Việt Nam.'
  },
  'FF5_ALL': {
    name: 'FF5 + LIQ + FOR + VOL (Mở rộng)',
    factors: 'MKT + SMB + HML + RMW + CMA + LIQ + FOR + VOL',
    desc: 'Mô hình đầy đủ nhất, kết hợp tất cả nhân tố quốc tế (FF5) và đặc thù thị trường Việt Nam (LIQ, FOR, VOL). Kiểm tra mức cải thiện so với FF5 gốc.'
  },
};

export default function ConclusionPage() {
  const { regressionRunId, backtestRunId, selectedModel } = useGlobalStore();
  const rid = regressionRunId || '';
  const { data, isLoading } = useBestModel(rid);
  const { data: metricsData } = useMetrics(backtestRunId || '');
  const { data: compareData } = useModelComparison(rid);
  const { data: grsData } = useGRS(rid);
  const { data: hypData } = useHypotheses(rid);

  if (isLoading) return <div className="flex justify-center p-8"><Spinner /></div>;

  const bestModel = data?.data?.model || null;
  const ranking = data?.data?.ranking || [];
  const metrics = metricsData?.data || [];
  const proposed = metrics.find((m: any) => m.portfolio === 'proposed');
  const vn30 = metrics.find((m: any) => m.portfolio === 'vn30');
  const equal = metrics.find((m: any) => m.portfolio === 'equal');
  const comparisons = compareData?.data || [];
  const grs = grsData?.data || [];
  const hypotheses = hypData?.data || [];

  const hasRegData = ranking.length > 0 || comparisons.length > 0;
  const hasBacktestData = proposed != null;
  const currentModelInfo = MODEL_DESCRIPTIONS[selectedModel] || MODEL_DESCRIPTIONS['FF5_ALL'];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-gradient-to-r from-navy-900 to-navy-700 p-6 rounded-lg shadow-md text-white">
        <h2 className="text-2xl font-bold mb-1">Kết Luận Nghiên Cứu</h2>
        <p className="text-navy-200 text-sm">Tối ưu danh mục và mô hình nhân tố trên thị trường Việt Nam (VN30)</p>
        <p className="text-navy-300 text-xs mt-1">Markowitz (1952) · Fama &amp; French (1993, 2015)</p>
      </div>

      {/* Current Model Info Box */}
      <div className="bg-blue-50 border border-blue-200 p-5 rounded-lg">
        <div className="flex items-start gap-3">
          <div className="bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded mt-0.5 whitespace-nowrap">{selectedModel}</div>
          <div>
            <h4 className="font-semibold text-blue-900">{currentModelInfo.name}</h4>
            <p className="text-sm text-blue-700 mt-1">Nhân tố: <code className="bg-blue-100 px-1 rounded text-xs">{currentModelInfo.factors}</code></p>
            <p className="text-sm text-blue-800 mt-1">{currentModelInfo.desc}</p>
          </div>
        </div>
      </div>

      {!hasRegData && !hasBacktestData ? (
        <div className="text-center p-10 text-slate-500 bg-white rounded-lg shadow-sm border border-slate-200">
          <p className="text-lg font-medium mb-2">Chưa có dữ liệu phân tích</p>
          <p className="text-sm">Vui lòng chạy <strong>Hồi quy</strong> (tab 3), <strong>Đường biên Hiệu quả</strong> (tab 6), và <strong>Backtest</strong> (tab 8) trước.</p>
        </div>
      ) : (
        <>
          {/* RQ1: Model Comparison */}
          {hasRegData && (
            <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
              <h3 className="text-lg font-bold text-navy-900 mb-3 flex items-center">
                <span className="bg-navy-100 text-navy-700 text-xs font-semibold px-2 py-1 rounded mr-2">RQ1</span>
                Sức giải thích của các mô hình nhân tố trên VN30
              </h3>
              <p className="text-slate-700 mb-3 text-sm">
                <strong>Câu hỏi:</strong> CAPM, FF3, FF5 giải thích lợi suất cổ phiếu VN30 tốt đến đâu? Mô hình nào phù hợp nhất?
              </p>
              {bestModel && (
                <p className="text-slate-700 mb-3">
                  Mô hình <strong className="text-gold-600 text-lg">{bestModel}</strong> cho thấy sức giải thích Adj R² cao nhất, 
                  vượt trội {ranking.length > 1 ? `so với ${ranking.length - 1} mô hình còn lại` : ''}.
                </p>
              )}

              {/* Model ranking grid */}
              {ranking.length > 0 && (
                <div className="bg-slate-50 p-4 rounded-md border border-slate-100 mb-4">
                  <h4 className="font-semibold text-slate-900 mb-2 text-sm">Xếp hạng mô hình (theo Adj R² trung bình):</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {ranking.map((item: any, i: number) => {
                      const m = typeof item === 'string' ? item : item.model;
                      const r2 = typeof item === 'object' ? item.avg_adj_r2 : null;
                      return (
                        <div key={m} className={`p-3 rounded text-center ${i === 0 ? 'bg-gold-100 text-gold-800 font-bold border-2 border-gold-400' : 'bg-white border border-slate-200'}`}>
                          <span className="text-xs text-slate-400">#{i + 1}</span>
                          <div className="font-semibold">{m}</div>
                          {r2 != null && <div className="text-xs text-slate-500 mt-1">R² = {(r2 * 100).toFixed(2)}%</div>}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Comparison table */}
              {comparisons.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-xs">
                    <thead>
                      <tr className="bg-slate-50">
                        <th className="px-3 py-2 text-left">Mô hình</th>
                        <th className="px-3 py-2 text-center">Avg Adj R²</th>
                        <th className="px-3 py-2 text-center">Avg AIC</th>
                        <th className="px-3 py-2 text-center">Mean |α|</th>
                        <th className="px-3 py-2 text-center">GRS Stat</th>
                        <th className="px-3 py-2 text-center">GRS p-value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparisons.map((c: any, i: number) => (
                        <tr key={c.model} className={`border-t ${i === 0 ? 'bg-gold-50 font-semibold' : ''}`}>
                          <td className="px-3 py-2">{c.model}{i === 0 && ' ⭐'}</td>
                          <td className="px-3 py-2 text-center">{c.avg_adj_r2 != null ? `${(c.avg_adj_r2 * 100).toFixed(2)}%` : 'N/A'}</td>
                          <td className="px-3 py-2 text-center">{c.avg_aic?.toFixed(1)}</td>
                          <td className="px-3 py-2 text-center">{c.mean_abs_alpha?.toFixed(6)}</td>
                          <td className="px-3 py-2 text-center">{c.grs_stat?.toFixed(3)}</td>
                          <td className="px-3 py-2 text-center">{c.grs_p?.toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* RQ2: GRS Test */}
          {grs.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
              <h3 className="text-lg font-bold text-navy-900 mb-3 flex items-center">
                <span className="bg-navy-100 text-navy-700 text-xs font-semibold px-2 py-1 rounded mr-2">RQ2</span>
                Kiểm định GRS — Mô hình có giải thích đầy đủ lợi suất?
              </h3>
              <p className="text-slate-700 mb-3 text-sm">
                <strong>Kiểm định Gibbons-Ross-Shanken (1989):</strong> H₀: Tất cả α = 0 (mô hình giải thích đầy đủ). 
                Nếu p-value {'>'} 0.05 → chưa đủ bằng chứng bác bỏ H₀; đây không phải bằng chứng khẳng định mô hình đúng.
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {grs.map((g: any) => (
                  <div key={g.model} className={`p-3 rounded border ${g.p_value > 0.05 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                    <div className="font-semibold text-sm">{g.model}</div>
                    <div className="text-xs text-slate-500 mt-1">GRS = {g.grs_stat?.toFixed(3)}</div>
                    <div className={`text-xs font-medium mt-1 ${g.p_value > 0.05 ? 'text-green-700' : 'text-red-700'}`}>
                      p = {g.p_value?.toFixed(4)}
                    </div>
                    <div className={`text-xs mt-1 ${g.p_value > 0.05 ? 'text-green-600' : 'text-red-600'}`}>
                      {g.p_value > 0.05 ? 'Chưa đủ bằng chứng bác bỏ H₀' : 'Bác bỏ H₀'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* RQ3: Hypotheses H1-H5 */}
          {hypotheses.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
              <h3 className="text-lg font-bold text-navy-900 mb-3 flex items-center">
                <span className="bg-navy-100 text-navy-700 text-xs font-semibold px-2 py-1 rounded mr-2">RQ3</span>
                Kiểm định Giả thuyết Nghiên cứu (H1–H5)
              </h3>
              <div className="space-y-3">
                {hypotheses.map((h: any) => (
                  <div key={h.hypothesis || h.id} className={`p-4 rounded border-l-4 ${h.verdict === 'Supported' ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-bold text-sm">{h.hypothesis || h.id}</span>
                        <span className="text-xs text-slate-500 ml-2">{h.statement}</span>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${h.verdict === 'Supported' ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}`}>
                        {h.verdict === 'Supported' ? '✓ Được dữ liệu ủng hộ' : '✗ Chưa được ủng hộ'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-1">{h.note}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* RQ4: Portfolio Comparison */}
          {hasBacktestData && (
            <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
              <h3 className="text-lg font-bold text-navy-900 mb-3 flex items-center">
                <span className="bg-navy-100 text-navy-700 text-xs font-semibold px-2 py-1 rounded mr-2">RQ4</span>
                Hiệu quả danh mục tối ưu Markowitz vs Benchmarks
              </h3>
              <p className="text-slate-700 mb-3 text-sm">
                <strong>Câu hỏi:</strong> Danh mục Mean-Variance Optimization có vượt trội VN30 Index và Equal-Weight?
              </p>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50">
                      <th className="px-4 py-2 text-left font-semibold">Chỉ số</th>
                      <th className="px-4 py-2 text-center font-semibold text-gold-700">Tối ưu Markowitz</th>
                      <th className="px-4 py-2 text-center font-semibold">VN30 Index</th>
                      <th className="px-4 py-2 text-center font-semibold">Equal Weight (1/N)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { label: 'CAGR (Lợi suất/năm)', key: 'cagr', fmt: formatPercent, better: 'high' },
                      { label: 'Biến động (Volatility)', key: 'vol', fmt: formatPercent, better: 'low' },
                      { label: 'Sharpe Ratio', key: 'sharpe', fmt: (v: number) => v?.toFixed(3), better: 'high' },
                      { label: 'Sortino Ratio', key: 'sortino', fmt: (v: number) => v?.toFixed(3), better: 'high' },
                      { label: 'Max Drawdown', key: 'max_dd', fmt: formatPercent, better: 'low' },
                      { label: 'Calmar Ratio', key: 'calmar', fmt: (v: number) => v?.toFixed(3), better: 'high' },
                    ].map(({ label, key, fmt, better }) => {
                      const pVal = (proposed as any)?.[key];
                      const vVal = (vn30 as any)?.[key];
                      const eVal = (equal as any)?.[key];
                      const isBest = (v: number | undefined) => {
                        if (v == null || pVal == null) return false;
                        if (better === 'high') return pVal >= v;
                        return Math.abs(pVal) <= Math.abs(v);
                      };
                      return (
                        <tr key={key} className="border-t border-slate-100">
                          <td className="px-4 py-2 font-medium text-slate-700 text-xs">{label}</td>
                          <td className={`px-4 py-2 text-center font-semibold ${isBest(vVal) && isBest(eVal) ? 'text-green-700 bg-green-50' : 'text-gold-700'}`}>
                            {pVal != null ? fmt(pVal) : 'N/A'}
                          </td>
                          <td className="px-4 py-2 text-center text-sm">{vVal != null ? fmt(vVal) : 'N/A'}</td>
                          <td className="px-4 py-2 text-center text-sm">{eVal != null ? fmt(eVal) : 'N/A'}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {proposed?.sharpe != null && (
                <div className={`mt-4 p-3 rounded text-sm border ${
                  proposed.sharpe > (vn30?.sharpe || 0)
                    ? 'bg-green-50 text-green-800 border-green-200'
                    : 'bg-amber-50 text-amber-800 border-amber-200'
                }`}>
                  <strong>Nhận xét: </strong>
                  {proposed.sharpe > (vn30?.sharpe || 0)
                    ? `Danh mục Markowitz đạt Sharpe ${proposed.sharpe.toFixed(3)}, vượt trội so với VN30 (${vn30?.sharpe?.toFixed(3) || 'N/A'}) ➜ Tối ưu hóa Mean-Variance có hiệu quả trên VN30.`
                    : 'Danh mục Markowitz chưa vượt VN30 về Sharpe. Có thể do estimation error hoặc cần điều chỉnh tham số (w_max, estimator).'
                  }
                </div>
              )}
            </div>
          )}

          {/* Key Findings Summary */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-lg font-bold text-navy-900 mb-3">Tổng kết phát hiện chính</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <h4 className="font-semibold text-navy-800 text-sm mb-2">📊 Mô hình nhân tố</h4>
                <ul className="text-xs text-slate-700 space-y-1 list-disc pl-4">
                  {bestModel && <li>Mô hình tốt nhất: <strong>{bestModel}</strong></li>}
                  <li>
                    {ranking.length >= 2 && typeof ranking[0] === 'object' && typeof ranking[1] === 'object'
                      ? `Adj R² cải thiện từ ${((ranking[ranking.length-1] as any)?.avg_adj_r2 * 100)?.toFixed(1)}% (${(ranking[ranking.length-1] as any)?.model}) lên ${((ranking[0] as any)?.avg_adj_r2 * 100)?.toFixed(1)}% (${(ranking[0] as any)?.model})`
                      : 'Chưa đủ dữ liệu để so sánh mức cải thiện Adj R² giữa các mô hình.'
                    }
                  </li>
                  <li>Hồi quy sử dụng sai số chuẩn Newey-West (HAC, lag=5) khắc phục tự tương quan</li>
                </ul>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <h4 className="font-semibold text-navy-800 text-sm mb-2">🏦 Đặc thù thị trường VN</h4>
                <ul className="text-xs text-slate-700 space-y-1 list-disc pl-4">
                  <li>Biên độ giá ±7% (HOSE) ảnh hưởng đến phân phối lợi suất</li>
                  <li>Thanh khoản (LIQ) và Khối ngoại (FOR) là nhân tố đặc thù quan trọng</li>
                  <li>Phí giao dịch: mua 0.15% + bán 0.25% (gồm thuế 0.1%)</li>
                </ul>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <h4 className="font-semibold text-navy-800 text-sm mb-2">📈 Tối ưu danh mục</h4>
                <ul className="text-xs text-slate-700 space-y-1 list-disc pl-4">
                  <li>Ràng buộc: Long-only, w_max = 15%, Σw = 1</li>
                  <li>Ma trận hiệp phương sai: Ledoit-Wolf Shrinkage (ổn định hơn Sample)</li>
                  <li>Lợi suất kỳ vọng: μ = Rf + Σ β·λ (không cộng α để tránh overfitting)</li>
                </ul>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <h4 className="font-semibold text-navy-800 text-sm mb-2">⚠️ Giới hạn nghiên cứu</h4>
                <ul className="text-xs text-slate-700 space-y-1 list-disc pl-4">
                  <li>Mẫu chỉ gồm 30 mã VN30, không đại diện toàn thị trường</li>
                  <li>Dữ liệu sách kế toán (Book Equity) bị lag do báo cáo tài chính</li>
                  <li>Estimation error: μ ước lượng từ quá khứ có thể khác tương lai</li>
                </ul>
              </div>
            </div>
          </div>

          {/* References */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-lg font-bold text-navy-900 mb-3">Tài liệu tham khảo</h3>
            <ul className="text-xs text-slate-600 space-y-1">
              <li>• Markowitz, H. (1952). <em>Portfolio Selection.</em> Journal of Finance, 7(1), 77–91.</li>
              <li>• Fama, E.F. & French, K.R. (1993). <em>Common risk factors in the returns on stocks and bonds.</em> Journal of Financial Economics, 33(1), 3–56.</li>
              <li>• Fama, E.F. & French, K.R. (2015). <em>A five-factor asset pricing model.</em> Journal of Financial Economics, 116(1), 1–22.</li>
              <li>• Gibbons, M.R., Ross, S.A., & Shanken, J. (1989). <em>A test of the efficiency of a given portfolio.</em> Econometrica, 57(5), 1121–1152.</li>
              <li>• Ledoit, O. & Wolf, M. (2004). <em>A well-conditioned estimator for large-dimensional covariance matrices.</em> Journal of Multivariate Analysis, 88(2), 365–411.</li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
