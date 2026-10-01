import { ReactNode } from 'react';
import { useGlobalStore } from '../hooks/useGlobalStore';
import {
  useBestModel, useMetrics, useModelComparison, useGRS, useHypotheses,
  usePortfolioWeights, usePortfolioConfig, useEquity,
} from '../api/queries';
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


const ESTIMATOR_LABEL: Record<string, string> = {
  sample: 'Hiệp phương sai mẫu (Sample)',
  ledoit_wolf: 'Ledoit-Wolf Shrinkage',
  semi: 'Bán phương sai (Semi-Covariance)',
};
const OBJECTIVE_LABEL: Record<string, string> = {
  max_sharpe: 'Tối đa hóa Sharpe',
  min_variance: 'Tối thiểu hóa phương sai',
};

const pct = (v: number | null | undefined, d = 1) => (v == null || !isFinite(v) ? 'N/A' : `${(v * 100).toFixed(d)}%`);
const pp = (v: number) => `${(Math.abs(v) * 100).toFixed(1)} điểm phần trăm`;
const modelName = (item: any) => (typeof item === 'string' ? item : item?.model);

function Reading({ conclusion, why, caution }: { conclusion: ReactNode; why?: ReactNode; caution?: ReactNode }) {
  return (
    <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm space-y-1.5">
      <p><span className="font-semibold text-navy-800">Kết luận:</span> {conclusion}</p>
      {why && <p><span className="font-semibold text-navy-800">Vì sao:</span> {why}</p>}
      {caution && <p className="text-amber-800"><span className="font-semibold">Mức chắc chắn / lưu ý:</span> {caution}</p>}
    </div>
  );
}

function Card({ id, title, children }: { id?: string; title: string; children: ReactNode }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
      <h3 className="text-lg font-bold text-navy-900 mb-3 flex items-center">
        {id && <span className="bg-navy-100 text-navy-700 text-xs font-semibold px-2 py-1 rounded mr-2">{id}</span>}
        {title}
      </h3>
      {children}
    </div>
  );
}

export default function ConclusionPage() {
  const { regressionRunId, backtestRunId, portfolioRunId, selectedModel } = useGlobalStore();
  const rid = regressionRunId || '';
  const { data, isLoading } = useBestModel(rid);
  const { data: metricsData } = useMetrics(backtestRunId || '');
  const { data: compareData } = useModelComparison(rid);
  const { data: grsData } = useGRS(rid);
  const { data: hypData } = useHypotheses(rid);
  const { data: weightsData } = usePortfolioWeights(portfolioRunId || '');
  const { data: configData } = usePortfolioConfig(portfolioRunId || '');
  const { data: equityData } = useEquity(backtestRunId || '');

  if (isLoading) return <div className="flex justify-center p-8"><Spinner /></div>;

  const bestModel = data?.data?.model || null;
  const ranking: any[] = data?.data?.ranking || [];
  const metrics = metricsData?.data || [];
  const proposed: any = metrics.find((m: any) => m.portfolio === 'proposed');
  const vn30: any = metrics.find((m: any) => m.portfolio === 'vn30');
  const equal: any = metrics.find((m: any) => m.portfolio === 'equal');
  const comparisons: any[] = compareData?.data || [];
  const grs: any[] = grsData?.data || [];
  const hypotheses: any[] = hypData?.data || [];
  const config: Record<string, any> = (configData?.data as any) || {};
  const weights: any[] = Array.isArray(weightsData?.data) ? (weightsData!.data as any[]) : [];
  const equityDates: string[] = (equityData?.data as any)?.dates || [];

  const hasRegData = ranking.length > 0 || comparisons.length > 0;
  const hasBacktestData = proposed != null;
  const currentModelInfo = MODEL_DESCRIPTIONS[selectedModel] || MODEL_DESCRIPTIONS['FF5_ALL'];

  // ---------- Phân tích RQ1 / RQ2 ----------
  const rankObjs = ranking.filter((r) => typeof r === 'object' && r.avg_adj_r2 != null);
  const best: any = rankObjs[0];
  const second: any = rankObjs[1];
  const capm: any = rankObjs.find((r) => modelName(r) === 'CAPM');
  const grsRows = rankObjs.length ? rankObjs.filter((r) => r.grs_p != null) : grs.map((g) => ({ model: g.model, grs_p: g.p_value }));
  const grsPass = grsRows.filter((r: any) => r.grs_p >= 0.05).map((r: any) => modelName(r));
  const grsFail = grsRows.filter((r: any) => r.grs_p < 0.05).map((r: any) => modelName(r));
  const bestPasses = best ? best.grs_p != null && best.grs_p >= 0.05 : null;
  const bestPassingModel: any = rankObjs.find((r) => r.grs_p != null && r.grs_p >= 0.05);

  // ---------- Phân tích RQ4 ----------
  const sectors: Record<string, number> = {};
  weights.filter((w) => w.weight > 0.0005).forEach((w) => {
    const k = w.sector || 'Khác';
    sectors[k] = (sectors[k] || 0) + w.weight;
  });
  const sectorList = Object.entries(sectors).sort((a, b) => b[1] - a[1]);
  const held = weights.filter((w) => w.weight > 0.0005).sort((a, b) => b.weight - a.weight);
  const topSector = sectorList[0];

  let rq4Conclusion: ReactNode = null;
  let rq4Why: ReactNode = null;
  if (proposed && vn30) {
    const dRet = proposed.cagr - vn30.cagr;
    const dVol = proposed.vol - vn30.vol;
    const dSh = proposed.sharpe - vn30.sharpe;
    if (dSh > 0) {
      rq4Conclusion = <>Danh mục tối ưu có Sharpe <b>cao hơn</b> VN30 ({proposed.sharpe.toFixed(3)} so với {vn30.sharpe.toFixed(3)}) trong giai đoạn kiểm tra.</>;
    } else if (dRet < 0 && dVol > 0) {
      rq4Conclusion = <>Danh mục tối ưu <b>kém hơn VN30 cả về lãi lẫn rủi ro</b> trong giai đoạn kiểm tra: lãi thấp hơn nhưng biến động cao hơn.</>;
    } else {
      rq4Conclusion = <>Danh mục tối ưu có Sharpe <b>thấp hơn</b> VN30 ({proposed.sharpe.toFixed(3)} so với {vn30.sharpe.toFixed(3)}) trong giai đoạn kiểm tra.</>;
    }
    rq4Why = (
      <>
        Lợi suất mỗi năm {dRet >= 0 ? 'cao hơn' : 'thấp hơn'} VN30 {pp(dRet)} ({pct(proposed.cagr, 2)} so với {pct(vn30.cagr, 2)});
        biến động {dVol >= 0 ? 'cao hơn' : 'thấp hơn'} {pp(dVol)}; sụt giảm tối đa {pct(Math.abs(proposed.max_dd), 1)} so với {pct(Math.abs(vn30.max_dd), 1)}.
        {equal && <> So với danh mục chia đều: Sharpe {proposed.sharpe >= equal.sharpe ? 'cao hơn' : 'thấp hơn'} ({proposed.sharpe.toFixed(3)} so với {equal.sharpe.toFixed(3)}).</>}
      </>
    );
  }

  const testPeriod = equityDates.length ? `${equityDates[0]} → ${equityDates[equityDates.length - 1]}` : null;

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
            <p className="text-xs text-blue-600 mt-2">Hộp này chỉ mô tả mô hình bạn chọn ở thanh trên cùng. Các kết luận bên dưới lấy từ lần chạy Hồi quy và Backtest gần nhất, không đổi theo ô chọn này.</p>
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
          {/* Tóm tắt 30 giây */}
          <div className="bg-white p-6 rounded-lg shadow-sm border-2 border-gold-400">
            <h3 className="text-lg font-bold text-navy-900 mb-3">Kết luận trong 30 giây</h3>
            <ul className="space-y-2 text-sm text-slate-700 list-disc pl-5">
              {best && (
                <li>
                  <b>RQ1 (mô hình nào giải thích tốt nhất):</b> {best.model} có Adj R² trung bình cao nhất ({pct(best.avg_adj_r2)})
                  {capm && best.model !== 'CAPM' && <>, hơn CAPM {pp(best.avg_adj_r2 - capm.avg_adj_r2)}</>}.
                </li>
              )}
              {grsRows.length > 0 && (
                <li>
                  <b>RQ2 (có còn lợi suất chưa giải thích):</b> {grsPass.length}/{grsRows.length} mô hình qua kiểm định GRS
                  {grsPass.length > 0 && <> ({grsPass.join(', ')})</>}
                  {bestPasses === false && best && <>; riêng {best.model} <b>không</b> qua</>}.
                </li>
              )}
              {hypotheses.length > 0 && (
                <li>
                  <b>RQ3 (giả thuyết H1–H5):</b> {hypotheses.filter((h: any) => h.verdict === 'Supported').length}/{hypotheses.length} được dữ liệu ủng hộ
                  {hypotheses.some((h: any) => h.verdict !== 'Supported') && <> (chưa ủng hộ: {hypotheses.filter((h: any) => h.verdict !== 'Supported').map((h: any) => h.hypothesis || h.id).join(', ')})</>}.
                </li>
              )}
              {rq4Conclusion && <li><b>RQ4 (danh mục tối ưu so với VN30):</b> {rq4Conclusion}</li>}
            </ul>
            <p className="text-xs text-slate-500 mt-3">Các dòng trên được tạo tự động từ số liệu hiện có. Đọc phần giải thích từng mục bên dưới để hiểu lý do và mức chắc chắn.</p>
          </div>

          {/* Thông số lần chạy */}
          <Card title="Thông số của lần chạy này">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1 text-sm text-slate-700">
              {config.model && <div>Mô hình dùng để lập danh mục: <b>{String(config.model).toUpperCase()}</b></div>}
              {config.cov_estimator && <div>Ước lượng rủi ro: <b>{ESTIMATOR_LABEL[config.cov_estimator] || config.cov_estimator}</b></div>}
              {config.w_max != null && <div>Tỷ trọng tối đa mỗi mã (w_max): <b>{pct(config.w_max, 0)}</b></div>}
              {config.objective && <div>Mục tiêu tối ưu: <b>{OBJECTIVE_LABEL[config.objective] || config.objective}</b></div>}
              {config.rf != null && <div>Lãi suất phi rủi ro dùng khi tối ưu: <b>{pct(config.rf, 1)}/năm</b></div>}
              {config.train_start && <div>Giai đoạn Train (học): <b>{config.train_start} → {config.train_end}</b></div>}
              {testPeriod && <div>Giai đoạn Test (backtest): <b>{testPeriod}</b></div>}
              <div>Ràng buộc: chỉ mua (không bán khống), tổng tỷ trọng = 100%</div>
            </div>
            {!config.model && <p className="text-sm text-slate-500">Chưa có danh mục được lưu. Hãy chạy tab Tỷ trọng Danh mục trước.</p>}
            <p className="text-xs text-slate-500 mt-3">
              Tần suất tái cân bằng, phí mua/bán của Backtest và kiểu hồi quy (Ngày/Tuần/Tháng, HAC/OLS) chưa được lưu cùng lần chạy; hãy xem lại cài đặt ở các tab tương ứng khi trình bày.
              Mặc định là tái cân bằng hàng tháng, phí mua 0,15% và phí bán 0,25%.
            </p>
            {config.model && best && String(config.model).toUpperCase() !== best.model && (
              <p className="text-sm text-amber-800 mt-2">
                Lưu ý: danh mục được lập bằng mô hình <b>{String(config.model).toUpperCase()}</b>, không phải mô hình xếp hạng cao nhất ở RQ1 (<b>{best.model}</b>). Hai kết quả này không mâu thuẫn nhưng không cùng một mô hình.
              </p>
            )}
          </Card>

          {/* RQ1 */}
          {hasRegData && (
            <Card id="RQ1" title="Sức giải thích của các mô hình nhân tố trên VN30">
              <p className="text-slate-700 mb-3 text-sm">
                <strong>Câu hỏi:</strong> CAPM, FF3, FF5 và các bản mở rộng giải thích lợi suất cổ phiếu VN30 tốt đến đâu? Mô hình nào phù hợp nhất?
              </p>
              <p className="text-xs text-slate-500 mb-3">
                Cách xếp hạng: ưu tiên <b>Adj R² trung bình cao hơn</b>; nếu bằng nhau mới xét GRS p-value cao hơn, rồi AIC thấp hơn, rồi |α| trung bình thấp hơn.
                Đây là thứ tự ưu tiên, không phải điểm tổng hợp.
              </p>

              {ranking.length > 0 && (
                <div className="bg-slate-50 p-4 rounded-md border border-slate-100 mb-4">
                  <h4 className="font-semibold text-slate-900 mb-2 text-sm">Xếp hạng mô hình (theo Adj R² trung bình):</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {ranking.map((item: any, i: number) => {
                      const m = modelName(item);
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

              {best && (
                <Reading
                  conclusion={<><b>{best.model}</b> giải thích lợi suất tốt nhất theo Adj R² ({pct(best.avg_adj_r2, 2)}).</>}
                  why={
                    <>
                      Adj R² là phần biến động của giá mà mô hình giải thích được, đã trừ bớt lợi thế của việc thêm nhân tố. {best.model} đứng đầu
                      {second && <>, hơn {second.model} {pp(best.avg_adj_r2 - second.avg_adj_r2)}</>}
                      {capm && best.model !== 'CAPM' && <> và hơn CAPM (chỉ có thị trường) {pp(best.avg_adj_r2 - capm.avg_adj_r2)}</>}.
                      Nghĩa là thêm các nhân tố ngoài thị trường giúp giải thích thêm khá nhiều biến động của cổ phiếu.
                    </>
                  }
                  caution={
                    <>
                      {second && best.avg_adj_r2 - second.avg_adj_r2 < 0.02 && <>Chênh lệch giữa {best.model} và {second.model} nhỏ (dưới 2 điểm phần trăm) nên chưa chắc có khác biệt thực sự. </>}
                      Đây là sức giải thích trong mẫu (dữ liệu Train); hạng cao chưa có nghĩa danh mục sẽ lãi hơn ngoài mẫu (xem RQ4).
                    </>
                  }
                />
              )}
            </Card>
          )}

          {/* RQ2 */}
          {grs.length > 0 && (
            <Card id="RQ2" title="Kiểm định GRS — Mô hình có giải thích đầy đủ lợi suất?">
              <p className="text-slate-700 mb-3 text-sm">
                <strong>Kiểm định Gibbons-Ross-Shanken (1989):</strong> H₀: tất cả α = 0 (mô hình giải thích đầy đủ).
                Nếu p-value {'>'} 0.05 → chưa đủ bằng chứng bác bỏ H₀; đây không phải bằng chứng khẳng định mô hình đúng.
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {grs.map((g: any) => (
                  <div key={g.model} className={`p-3 rounded border ${g.p_value > 0.05 ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                    <div className="font-semibold text-sm">{g.model}</div>
                    <div className="text-xs text-slate-500 mt-1">GRS = {g.grs_stat?.toFixed(3)}</div>
                    <div className={`text-xs font-medium mt-1 ${g.p_value > 0.05 ? 'text-green-700' : 'text-red-700'}`}>p = {g.p_value?.toFixed(4)}</div>
                    <div className={`text-xs mt-1 ${g.p_value > 0.05 ? 'text-green-600' : 'text-red-600'}`}>
                      {g.p_value > 0.05 ? 'Chưa đủ bằng chứng bác bỏ H₀' : 'Bác bỏ H₀'}
                    </div>
                  </div>
                ))}
              </div>
              <Reading
                conclusion={
                  grsFail.length === 0
                    ? <>Không mô hình nào bị bác bỏ: chưa thấy phần lợi suất bất thường còn sót lại.</>
                    : <>{grsFail.length}/{grs.length} mô hình bị bác bỏ ({grsFail.join(', ')}): còn phần lợi suất mà các nhân tố chưa giải thích hết.</>
                }
                why={
                  <>
                    GRS kiểm tra xem alpha của cả 30 cổ phiếu có <b>cùng bằng 0</b> không. p-value dưới 0,05 nghĩa là alpha chung khác 0 một cách đáng tin, tức là mô hình để sót lợi suất.
                    {bestPasses === false && best && bestPassingModel && <> Ở đây {best.model} có Adj R² cao nhất nhưng không qua GRS, trong khi {bestPassingModel.model} (Adj R² {pct(bestPassingModel.avg_adj_r2)}) qua GRS.</>}
                  </>
                }
                caution={
                  <>
                    {bestPasses === false && <>Hai tiêu chí đo hai điều khác nhau: Adj R² đo mức khớp từng cổ phiếu, GRS đo alpha chung của cả nhóm. Vì vậy không có mô hình nào "hơn" ở mọi mặt; hãy nói rõ lựa chọn của bạn dựa trên tiêu chí nào. </>}
                    p-value gần 0,05 (ví dụ 0,05–0,06) là sát ngưỡng, nên đừng coi qua hay không qua là ranh giới tuyệt đối.
                  </>
                }
              />
            </Card>
          )}

          {/* RQ3 */}
          {hypotheses.length > 0 && (
            <Card id="RQ3" title="Kiểm định Giả thuyết Nghiên cứu (H1–H5)">
              <p className="text-xs text-slate-500 mb-3">
                H1, H2, H5: kiểm định t ghép cặp trên chênh lệch Adj R² của từng mã giữa hai mô hình (cùng mẫu ngày).
                H3, H4: kiểm định nhị thức xem tỷ lệ cổ phiếu có hệ số có ý nghĩa 5% có cao hơn mức ngẫu nhiên 5% hay không. "Được ủng hộ" nghĩa là p-value &lt; 0,05.
              </p>
              <div className="space-y-3">
                {hypotheses.map((h: any) => {
                  const hid = h.hypothesis || h.id;
                  const ok = h.verdict === 'Supported';
                  return (
                    <div key={hid} className={`p-4 rounded border-l-4 ${ok ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}`}>
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <span className="font-bold text-sm">{hid}</span>
                          <span className="text-xs text-slate-500 ml-2">{h.statement}</span>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-bold whitespace-nowrap ${ok ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}`}>
                          {ok ? '✓ Được dữ liệu ủng hộ' : '✗ Chưa được ủng hộ'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 mt-1">{h.note}</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Thống kê: {h.statistic != null ? Number(h.statistic).toFixed(3) : 'N/A'} · p-value: {h.p_value != null ? (h.p_value < 0.0001 ? '< 0.0001' : Number(h.p_value).toFixed(4)) : 'N/A'}
                      </p>
                      {hid === 'H4' && (
                        <p className="text-xs text-amber-800 mt-1">Lưu ý: nhân tố FOR dùng tỷ lệ sở hữu nước ngoài hiện tại cho mọi ngày (nguồn miễn phí không có lịch sử), nên kết luận này chỉ mang tính tham khảo.</p>
                      )}
                    </div>
                  );
                })}
              </div>
              <Reading
                conclusion={<>{hypotheses.filter((h: any) => h.verdict === 'Supported').length}/{hypotheses.length} giả thuyết được dữ liệu ủng hộ.</>}
                why="Mỗi giả thuyết được kiểm bằng một phép thử thống kê riêng (xem ghi chú ở trên); p-value nhỏ nghĩa là kết quả khó xảy ra do may rủi."
                caution="Chỉ có 30 cổ phiếu và một giai đoạn Train, nên kết quả ở mức ý nghĩa 5% có thể thay đổi nếu đổi giai đoạn hoặc cách hồi quy."
              />
            </Card>
          )}

          {/* RQ4 */}
          {hasBacktestData && (
            <Card id="RQ4" title="Hiệu quả danh mục tối ưu Markowitz vs Benchmarks">
              <p className="text-slate-700 mb-3 text-sm">
                <strong>Câu hỏi:</strong> Danh mục Mean-Variance Optimization có vượt trội VN30 Index và Equal-Weight?
                {testPeriod && <> (giai đoạn kiểm tra {testPeriod})</>}
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
              {rq4Conclusion && (
                <Reading
                  conclusion={rq4Conclusion}
                  why={rq4Why}
                  caution={
                    <>
                      Chỉ kiểm tra trên một giai đoạn ngắn, nên kết quả có thể do may rủi; tối ưu trên quá khứ không đảm bảo thắng trong tương lai (sai số ước lượng).
                      {topSector && topSector[1] >= 0.5 && <> Danh mục đang dồn {pct(topSector[1], 0)} vào ngành {topSector[0]}, nên kết quả phụ thuộc nhiều vào ngành này.</>}
                      {' '}VN30 tính từ giá đóng cửa chỉ số, không tính phí giao dịch hay cổ tức riêng, trong khi danh mục tối ưu đã trừ phí.
                    </>
                  }
                />
              )}
            </Card>
          )}

          {/* Danh mục đề xuất */}
          {held.length > 0 && (
            <Card title="Danh mục đề xuất (từ lần tối ưu gần nhất)">
              <p className="text-sm text-slate-700 mb-3">
                Danh mục có <b>{held.length}</b> cổ phiếu. Tỷ trọng là phần trăm tổng số tiền đầu tư dành cho từng mã.
              </p>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 text-left">
                      <th className="px-3 py-2">Mã CP</th>
                      <th className="px-3 py-2">Ngành</th>
                      <th className="px-3 py-2 text-right">Tỷ trọng</th>
                    </tr>
                  </thead>
                  <tbody>
                    {held.map((w: any) => (
                      <tr key={w.ticker} className="border-t border-slate-100">
                        <td className="px-3 py-1.5 font-medium">{w.ticker}</td>
                        <td className="px-3 py-1.5 text-slate-600">{w.sector}</td>
                        <td className="px-3 py-1.5 text-right">{pct(w.weight, 2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {sectorList.length > 0 && (
                <p className="text-xs text-slate-600 mt-3">
                  Theo ngành: {sectorList.map(([k, v]) => `${k} ${pct(v, 0)}`).join(' · ')}.
                  {topSector && topSector[1] >= 0.5 && ' Tập trung vào một ngành là rủi ro lớn: nếu ngành đó giảm, cả danh mục giảm theo.'}
                </p>
              )}
            </Card>
          )}

          {/* Gợi ý hành động */}
          <Card title="Cách hiểu kết quả và nên làm gì tiếp">
            <ul className="text-sm text-slate-700 space-y-2 list-disc pl-5">
              {best && bestPasses === false && bestPassingModel && (
                <li>
                  <b>Chọn mô hình:</b> nếu ưu tiên sức giải thích thì dùng <b>{best.model}</b>; nếu ưu tiên việc mô hình không để sót alpha thì cân nhắc <b>{bestPassingModel.model}</b> (qua GRS, Adj R² {pct(bestPassingModel.avg_adj_r2)}). Nên nêu rõ tiêu chí bạn chọn.
                </li>
              )}
              {best && bestPasses !== false && <li><b>Chọn mô hình:</b> <b>{best.model}</b> vừa đứng đầu về Adj R² vừa không bị GRS bác bỏ, là lựa chọn nhất quán nhất ở lần chạy này.</li>}
              {proposed && vn30 && proposed.sharpe <= vn30.sharpe && (
                <li><b>Về danh mục:</b> trong giai đoạn kiểm tra, danh mục tối ưu chưa đem lại lợi thế so với VN30. Có thể thử hạ w_max (ví dụ 10%) để phân tán hơn, đổi mô hình hoặc estimator, và xem tỷ trọng ngành. Cũng cần chấp nhận rằng tối ưu trên quá khứ không đảm bảo thắng trong tương lai.</li>
              )}
              {proposed && vn30 && proposed.sharpe > vn30.sharpe && (
                <li><b>Về danh mục:</b> danh mục tối ưu có Sharpe cao hơn VN30 trong giai đoạn kiểm tra, nhưng chỉ là một giai đoạn; nên thử thêm cấu hình khác (w_max, tần suất tái cân bằng) để xem kết quả có ổn định không.</li>
              )}
              <li><b>Kiểm tra lại cùng cấu hình:</b> nếu đổi mô hình, Train hoặc w_max thì chạy lại theo thứ tự Hồi quy → Tỷ trọng → Backtest để kết luận ở trang này cập nhật.</li>
              <li>Công cụ phục vụ học tập và phân tích, <b>không phải khuyến nghị đầu tư</b>. Mọi quyết định đầu tư thật cần cân nhắc thêm tình hình cá nhân, thuế, trượt giá và thanh khoản.</li>
            </ul>
          </Card>

          {/* Key Findings Summary */}
          <Card title="Tổng kết phát hiện chính">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <h4 className="font-semibold text-navy-800 text-sm mb-2">📊 Mô hình nhân tố</h4>
                <ul className="text-xs text-slate-700 space-y-1 list-disc pl-4">
                  {bestModel && <li>Mô hình xếp hạng cao nhất theo Adj R²: <strong>{bestModel}</strong></li>}
                  <li>
                    {rankObjs.length >= 2
                      ? `Adj R² tăng từ ${(rankObjs[rankObjs.length - 1].avg_adj_r2 * 100).toFixed(1)}% (${rankObjs[rankObjs.length - 1].model}) lên ${(rankObjs[0].avg_adj_r2 * 100).toFixed(1)}% (${rankObjs[0].model})`
                      : 'Chưa đủ dữ liệu để so sánh mức cải thiện Adj R² giữa các mô hình.'}
                  </li>
                  <li>Sai số chuẩn của hồi quy dùng HAC (Newey-West) hoặc OLS tùy lựa chọn ở tab Hồi quy</li>
                </ul>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <h4 className="font-semibold text-navy-800 text-sm mb-2">🏦 Đặc thù thị trường VN</h4>
                <ul className="text-xs text-slate-700 space-y-1 list-disc pl-4">
                  <li>Biên độ giá ±7% (HOSE) ảnh hưởng đến phân phối lợi suất</li>
                  <li>Thanh khoản (LIQ) và Khối ngoại (FOR) là nhân tố đặc thù được thêm vào các mô hình mở rộng</li>
                  <li>Phí giao dịch mặc định: mua 0,15% + bán 0,25% (đổi được ở tab Backtest)</li>
                </ul>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <h4 className="font-semibold text-navy-800 text-sm mb-2">📈 Tối ưu danh mục</h4>
                <ul className="text-xs text-slate-700 space-y-1 list-disc pl-4">
                  <li>Ràng buộc: chỉ mua, {config.w_max != null ? `w_max = ${pct(config.w_max, 0)}` : 'có giới hạn w_max'}, tổng tỷ trọng = 100%</li>
                  <li>Ma trận hiệp phương sai: {config.cov_estimator ? (ESTIMATOR_LABEL[config.cov_estimator] || config.cov_estimator) : 'theo lựa chọn ở bảng cấu hình'}</li>
                  <li>Lợi suất kỳ vọng: μ = Rf + Σ β·λ, trong đó λ là phần bù nhân tố trung bình năm của giai đoạn Train; không cộng α vào μ để tránh học quá khớp quá khứ</li>
                </ul>
              </div>
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                <h4 className="font-semibold text-navy-800 text-sm mb-2">⚠️ Giới hạn nghiên cứu</h4>
                <ul className="text-xs text-slate-700 space-y-1 list-disc pl-4">
                  <li>Mẫu chỉ gồm 30 mã VN30, không đại diện toàn thị trường</li>
                  <li>Ngày công bố báo cáo tài chính được ước tính (cuối quý + 45 ngày; quý 4 + 90 ngày) để tránh dùng thông tin chưa công bố</li>
                  <li>Nhân tố FOR dùng tỷ lệ sở hữu nước ngoài hiện tại cho mọi ngày</li>
                  <li>Lãi suất phi rủi ro được giả định cố định theo cấu hình (không phải chuỗi lãi suất thật theo ngày)</li>
                  <li>Kiểm tra ngoài mẫu chỉ trên một giai đoạn; μ ước lượng từ quá khứ có thể khác tương lai</li>
                </ul>
              </div>
            </div>
          </Card>

          {/* References */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h3 className="text-lg font-bold text-navy-900 mb-3">Tài liệu tham khảo</h3>
            <ul className="text-xs text-slate-600 space-y-1">
              <li>• Markowitz, H. (1952). <em>Portfolio Selection.</em> Journal of Finance, 7(1), 77–91.</li>
              <li>• Fama, E.F. &amp; French, K.R. (1993). <em>Common risk factors in the returns on stocks and bonds.</em> Journal of Financial Economics, 33(1), 3–56.</li>
              <li>• Fama, E.F. &amp; French, K.R. (2015). <em>A five-factor asset pricing model.</em> Journal of Financial Economics, 116(1), 1–22.</li>
              <li>• Gibbons, M.R., Ross, S.A., &amp; Shanken, J. (1989). <em>A test of the efficiency of a given portfolio.</em> Econometrica, 57(5), 1121–1152.</li>
              <li>• Ledoit, O. &amp; Wolf, M. (2004). <em>A well-conditioned estimator for large-dimensional covariance matrices.</em> Journal of Multivariate Analysis, 88(2), 365–411.</li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
