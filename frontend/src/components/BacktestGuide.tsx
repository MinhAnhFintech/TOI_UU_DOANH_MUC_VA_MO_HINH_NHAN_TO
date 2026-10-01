import { useState } from 'react';

const pct = (v: number, d = 1) => `${(v * 100).toFixed(d)}%`;
const NAME: Record<string, string> = { proposed: 'Danh mục tối ưu', vn30: 'Chỉ số VN30', equal: 'Chia đều (1/N)' };

export default function BacktestGuide({ metrics }: { metrics?: any[] }) {
  const [open, setOpen] = useState(true);
  const rows = Array.isArray(metrics) ? metrics : [];
  const get = (k: string) => rows.find((r) => r && r.portfolio === k);
  const prop = get('proposed');
  const vn = get('vn30');
  const eq = get('equal');

  const compare = (label: string, other: any) => {
    if (!prop || !other) return null;
    const dCagr = prop.cagr - other.cagr;
    const dSharpe = prop.sharpe - other.sharpe;
    return (
      <li key={label}>
        So với <b>{label}</b>: lợi suất năm {dCagr >= 0 ? 'cao hơn' : 'thấp hơn'} {pct(Math.abs(dCagr))}, Sharpe {dSharpe >= 0 ? 'cao hơn' : 'thấp hơn'} {Math.abs(dSharpe).toFixed(2)},
        sụt giảm tối đa {pct(Math.abs(prop.max_dd))} so với {pct(Math.abs(other.max_dd))}.
      </li>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200">
      <button type="button" onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-4 py-3 text-left">
        <span className="text-base font-semibold text-slate-800">Hướng dẫn đọc trang Kiểm định (Backtest)</span>
        <span className="text-sm text-navy-600">{open ? 'Thu gọn ▲' : 'Mở rộng ▼'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-5 text-sm text-slate-700 leading-relaxed">
          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Backtest là gì?</h4>
            <p>
              Là bài kiểm tra "nếu năm 2025 tôi đã đầu tư theo danh mục này thì kết quả ra sao?". Danh mục được chọn bằng dữ liệu <b>Train (2021–2024)</b>, rồi thử trên giai đoạn <b>Test (2025)</b>
              mà thuật toán chưa từng nhìn thấy. Đây là phép thử gần thực tế nhất trong công cụ, vì danh mục tối ưu trên quá khứ chưa chắc tốt trong tương lai.
            </p>
            <p className="mt-1">
              Hệ thống mô phỏng mua danh mục theo tỷ trọng đã tối ưu, định kỳ (hàng tháng hoặc hàng quý) bán mua lại để đưa về đúng tỷ trọng, và <b>trừ phí giao dịch</b> mỗi lần mua bán. Kết quả được so với hai mốc: <b>chỉ số VN30</b> và <b>danh mục chia đều</b> (mỗi cổ phiếu 1/30).
            </p>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách dùng (làm theo thứ tự)</h4>
            <ol className="list-decimal pl-5 space-y-1">
              <li>Vào tab <b>Tỷ trọng Danh mục</b>, đặt Train 01/01/2021 → 31/12/2024 và bấm <b>Chạy thuật toán</b> trước. Nếu chưa có danh mục, nút ở đây sẽ báo "Hãy tạo danh mục trước".</li>
              <li>Quay lại tab này. Đặt <b>Bắt đầu Backtest</b> 01/01/2025 và <b>Kết thúc Backtest</b> 31/12/2025. Ngày bắt đầu Backtest phải <b>sau</b> ngày kết thúc Train, nếu không hệ thống báo lỗi "must start after the portfolio training period ends"; khi đó hãy tối ưu lại danh mục với Train đến 31/12/2024.</li>
              <li>Phí mua mặc định 0,0015 (0,15%) và phí bán 0,0025 (0,25%); hãy kiểm tra không bị nhập nhầm thành số lớn như 0,1 (tức 10%).</li>
              <li>Chọn <b>Tần suất tái cân bằng</b>: hàng tháng hoặc hàng quý. Càng thường xuyên thì phí giao dịch càng cao.</li>
              <li>Bấm <b>Chạy thuật toán</b>, đợi thanh tiến trình, rồi xem kết quả ở ba phần bên dưới.</li>
            </ol>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách đọc từng phần</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li><b>Đường cong vốn (Equity Curve):</b> mỗi đường là giá trị tài khoản, bắt đầu từ 100. Đường "Đề xuất" là danh mục tối ưu; VN30 và Equal Weight là hai mốc so sánh. Đường nào cuối kỳ cao hơn thì lãi nhiều hơn. Di chuột lên để xem giá trị từng ngày.</li>
              <li><b>Độ sụt giảm (Drawdown):</b> mức tài khoản đang thấp hơn đỉnh gần nhất (ví dụ -9% là đang thấp hơn đỉnh 9%). Vùng càng sâu và càng dài là giai đoạn càng khó chịu. Kéo thanh trượt phía dưới để phóng to một khoảng thời gian.</li>
              <li><b>Bảng chỉ số hiệu suất:</b> xem giải thích ở dưới.</li>
            </ul>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Các chỉ số trong bảng</h4>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2">
              {[
                ['CAGR (Năm)', 'Lợi suất bình quân mỗi năm. Càng cao càng tốt.'],
                ['Rủi ro (Năm)', 'Mức dao động của danh mục, tính theo năm. Càng thấp càng ổn định.'],
                ['Sharpe', 'Lãi trên mỗi đơn vị rủi ro, sau khi trừ lãi suất phi rủi ro 5%. Cao hơn là tốt hơn; âm nghĩa là kém hơn gửi tiết kiệm.'],
                ['Max Drawdown', 'Mức giảm sâu nhất từ đỉnh xuống đáy. Số càng gần 0 càng tốt.'],
                ['Vòng quay (Turnover)', 'Mức độ mua bán lại danh mục. Càng cao thì phí càng nhiều.'],
                ['Tổng Phí GD (Cost)', 'Tổng phí giao dịch đã trừ trong cả giai đoạn, tính theo % tài khoản.'],
              ].map(([t, d]) => (
                <div key={t}><dt className="font-medium text-slate-800">{t}</dt><dd className="text-slate-600">{d}</dd></div>
              ))}
            </dl>
          </section>

          {prop && (vn || eq) && (
            <section className="rounded-md bg-slate-50 border border-slate-200 p-3">
              <h4 className="font-semibold text-slate-800 mb-1">Nhận xét tự động từ kết quả hiện tại</h4>
              <ul className="list-disc pl-5 space-y-1">
                <li>{NAME.proposed}: lợi suất {pct(prop.cagr)}/năm, rủi ro {pct(prop.vol)}, Sharpe {prop.sharpe.toFixed(2)}, sụt giảm tối đa {pct(Math.abs(prop.max_dd))}.</li>
                {compare(NAME.vn30, vn)}
                {compare(NAME.equal, eq)}
                {vn && prop.sharpe < vn.sharpe && (
                  <li className="text-amber-800">Danh mục tối ưu chưa vượt chỉ số VN30 về Sharpe trong giai đoạn Test này. Điều này xảy ra thường xuyên: tối ưu trên quá khứ không đảm bảo thắng trong tương lai, nên đây là kết quả cần trung thực nêu ra chứ không phải lỗi.</li>
                )}
              </ul>
            </section>
          )}

          <section className="rounded-md bg-amber-50 border border-amber-200 p-3 text-amber-900">
            <h4 className="font-semibold mb-1">Lưu ý</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>Chỉ kiểm tra trên <b>một năm</b> (2025) nên kết quả có thể do may rủi; đừng kết luận chắc chắn từ một lần chạy.</li>
              <li>Tỷ trọng danh mục được giữ cố định từ giai đoạn Train; chưa tính trượt giá, thuế, hay việc cổ phiếu khó mua bán.</li>
              <li>Quá khứ không đảm bảo tương lai. Đây là công cụ học tập, <b>không phải khuyến nghị đầu tư</b>.</li>
              <li>Bước tiếp theo: sang tab <b>Kết luận</b> để tổng hợp.</li>
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
