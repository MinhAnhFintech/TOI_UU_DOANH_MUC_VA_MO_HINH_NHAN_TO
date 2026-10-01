import { useState } from 'react';

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

export default function FrontierGuide({ frontier, tangency }: { frontier?: any[]; tangency?: any }) {
  const [open, setOpen] = useState(true);
  const pts = Array.isArray(frontier) ? frontier.filter((p) => p && p.vol != null && p.ret != null) : [];
  const minVol = pts.length ? pts.reduce((a, b) => (b.vol < a.vol ? b : a)) : null;
  const maxRet = pts.length ? pts.reduce((a, b) => (b.ret > a.ret ? b : a)) : null;
  const hasTan = tangency && tangency.vol != null && tangency.ret != null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200">
      <button type="button" onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-4 py-3 text-left">
        <span className="text-base font-semibold text-slate-800">Hướng dẫn đọc trang Đường biên Hiệu quả</span>
        <span className="text-sm text-navy-600">{open ? 'Thu gọn ▲' : 'Mở rộng ▼'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-5 text-sm text-slate-700 leading-relaxed">
          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Đường biên hiệu quả là gì?</h4>
            <p>
              Có vô số cách chia tiền cho 30 cổ phiếu. Với mỗi mức rủi ro bạn chấp nhận, chỉ có <b>một</b> cách chia cho lợi suất kỳ vọng cao nhất. Nối tất cả các cách chia tốt nhất đó lại ta được
              <b> đường biên hiệu quả</b> (đường vàng). Mọi danh mục nằm dưới đường này đều "kém": cùng rủi ro nhưng lãi thấp hơn. Không có danh mục khả thi nào nằm trên đường này.
            </p>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách đọc biểu đồ</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li><b>Trục ngang: Rủi ro (biến động)</b>, tính theo năm. Càng sang phải càng rủi ro (giá lên xuống mạnh hơn).</li>
              <li><b>Trục dọc: Lợi suất kỳ vọng</b>, tính theo năm, ước lượng từ mô hình nhân tố bạn chọn. Càng lên cao càng lãi nhiều.</li>
              <li><b>Điểm đầu bên trái của đường vàng:</b> danh mục <b>rủi ro thấp nhất</b> có thể đạt được (rủi ro tối thiểu). Dịch sang phải là chấp nhận rủi ro hơn để đổi lấy lợi suất cao hơn.</li>
              <li><b>Điểm đỏ (Danh mục Tiếp tuyến):</b> danh mục có <b>chỉ số Sharpe cao nhất</b>, tức là lãi trên mỗi đơn vị rủi ro tốt nhất. Đây là danh mục mà công cụ chọn cho bước Tỷ trọng và Backtest.</li>
              <li>Đường vàng cong dần và thoải ra ở bên phải: càng chấp nhận thêm rủi ro, lợi suất tăng thêm càng ít.</li>
              <li>Di chuột lên một điểm để xem chính xác rủi ro và lợi suất của nó.</li>
            </ul>
          </section>

          {(minVol || hasTan) && (
            <section className="rounded-md bg-slate-50 border border-slate-200 p-3">
              <h4 className="font-semibold text-slate-800 mb-1">Nhận xét tự động từ số liệu hiện tại</h4>
              <ul className="list-disc pl-5 space-y-1">
                {minVol && <li>Danh mục rủi ro thấp nhất: rủi ro <b>{pct(minVol.vol)}</b>/năm, lợi suất kỳ vọng <b>{pct(minVol.ret)}</b>/năm.</li>}
                {hasTan && (
                  <li>
                    Danh mục Sharpe cao nhất (điểm đỏ): rủi ro <b>{pct(tangency.vol)}</b>, lợi suất kỳ vọng <b>{pct(tangency.ret)}</b>
                    {tangency.sharpe != null && <>, Sharpe <b>{Number(tangency.sharpe).toFixed(2)}</b></>}.
                  </li>
                )}
                {maxRet && <li>Điểm cao nhất của đường biên: rủi ro {pct(maxRet.vol)}, lợi suất {pct(maxRet.ret)}.</li>}
              </ul>
              <p className="mt-2 text-slate-600">Đây là lợi suất kỳ vọng ước lượng từ dữ liệu quá khứ (giai đoạn Train), thường lạc quan hơn thực tế. Hãy kiểm tra ở tab Backtest.</p>
            </section>
          )}

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách dùng bảng cấu hình bên phải</h4>
            <ol className="list-decimal pl-5 space-y-1">
              <li><b>Mô hình:</b> mô hình nhân tố dùng để ước lượng lợi suất kỳ vọng (gợi ý: FF5 hoặc FF5_ALL, xem tab So sánh Mô hình).</li>
              <li><b>Ước lượng rủi ro:</b> cách tính mức biến động và tương quan giữa các cổ phiếu. Người mới nên chọn <b>Ledoit-Wolf</b> vì ổn định hơn khi có 30 cổ phiếu.</li>
              <li><b>Tỷ trọng tối đa mỗi mã (w_max):</b> trần tỷ trọng cho một cổ phiếu, mặc định 15%. Trần càng thấp thì danh mục càng phân tán nhưng đường biên bị thấp xuống và lệch sang phải.</li>
              <li><b>Bắt đầu / Kết thúc Train:</b> chọn 01/01/2021 đến 31/12/2024 (để dành 2025 kiểm tra).</li>
              <li>Bấm <b>Chạy thuật toán</b>, đợi thanh tiến trình xong, đường biên sẽ hiện ra.</li>
            </ol>
            <p className="mt-2 text-slate-600">
              Phí mua/bán không có ở đây vì việc tìm danh mục tối ưu chỉ cần lợi suất và rủi ro; phí chỉ phát sinh khi mua bán thật nên được tính ở tab Backtest.
              Lãi suất phi rủi ro dùng để tính Sharpe đang đặt cố định 5%/năm.
            </p>
          </section>

          <section className="rounded-md bg-amber-50 border border-amber-200 p-3 text-amber-900">
            <h4 className="font-semibold mb-1">Lưu ý</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>Danh mục tối ưu rất nhạy với dữ liệu đầu vào: thay đổi nhỏ trong lợi suất kỳ vọng có thể làm tỷ trọng đổi nhiều. Vì vậy cần giới hạn w_max và kiểm tra bằng Backtest.</li>
              <li>Quá khứ không đảm bảo tương lai. Đây là công cụ học tập, không phải khuyến nghị đầu tư.</li>
              <li>Bước tiếp theo: sang tab <b>Tỷ trọng Danh mục</b> để xem cụ thể nên chia tiền cho từng cổ phiếu bao nhiêu.</li>
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
