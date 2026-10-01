import { useState } from 'react';

const pct = (v: number, d = 1) => `${(v * 100).toFixed(d)}%`;

export default function WeightsGuide({ weights }: { weights?: any[] }) {
  const [open, setOpen] = useState(true);
  const rows = Array.isArray(weights) ? weights.filter((w) => w && w.weight != null) : [];
  const held = rows.filter((w) => w.weight > 0.0005).sort((a, b) => b.weight - a.weight);
  const total = held.reduce((s, w) => s + w.weight, 0);
  const maxW = held.length ? held[0].weight : 0;
  const atCap = held.filter((w) => maxW > 0 && w.weight >= maxW - 0.0005);
  const bySector: Record<string, number> = {};
  held.forEach((w) => {
    const k = w.sector || 'Khác';
    bySector[k] = (bySector[k] || 0) + w.weight;
  });
  const sectors = Object.entries(bySector).sort((a, b) => b[1] - a[1]);
  const topSector = sectors.length ? sectors[0] : null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200">
      <button type="button" onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-4 py-3 text-left">
        <span className="text-base font-semibold text-slate-800">Hướng dẫn đọc trang Tỷ trọng Danh mục</span>
        <span className="text-sm text-navy-600">{open ? 'Thu gọn ▲' : 'Mở rộng ▼'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-5 text-sm text-slate-700 leading-relaxed">
          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Trang này cho bạn biết điều gì?</h4>
            <p>
              Đây là <b>kết quả chính của công cụ</b>: nếu có một khoản tiền, nên chia bao nhiêu phần trăm cho mỗi cổ phiếu VN30 để được danh mục có <b>tỷ lệ lãi trên rủi ro (Sharpe) cao nhất</b>,
              theo mô hình nhân tố và giai đoạn Train bạn chọn. Đây chính là danh mục "điểm đỏ" ở tab Đường biên Hiệu quả.
            </p>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách đọc biểu đồ và bảng</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li><b>Biểu đồ cột:</b> mỗi cột là một cổ phiếu được chọn, độ dài là tỷ trọng. Cổ phiếu không có cột nghĩa là thuật toán gán 0% (không mua).</li>
              <li><b>Tổng các tỷ trọng luôn bằng 100%</b> (không bán khống, không vay thêm).</li>
              <li><b>Bảng "Chi tiết Tỷ trọng":</b> Ngành của mã; Tỷ trọng; <b>Lợi suất kỳ vọng (năm)</b> do mô hình ước lượng; <b>Độ lệch chuẩn (năm)</b> là mức biến động của riêng mã đó.</li>
              <li>Nhiều mã có tỷ trọng đúng bằng mức trần (ví dụ 15%) nghĩa là thuật toán còn muốn mua nhiều hơn nhưng bị giới hạn bởi w_max.</li>
              <li>Cách đổi ra tiền: với 100 triệu đồng, mã có tỷ trọng 15% tương ứng 15 triệu đồng. Cổ phiếu mua theo lô 100 cổ phiếu nên số tiền thực tế sẽ lệch chút.</li>
            </ul>
          </section>

          {held.length > 0 && (
            <section className="rounded-md bg-slate-50 border border-slate-200 p-3">
              <h4 className="font-semibold text-slate-800 mb-1">Nhận xét tự động từ danh mục hiện tại</h4>
              <ul className="list-disc pl-5 space-y-1">
                <li>Danh mục có <b>{held.length}</b> cổ phiếu (tổng tỷ trọng {pct(total, 0)}). Lớn nhất: {held.slice(0, 3).map((w) => `${w.ticker} ${pct(w.weight)}`).join(', ')}.</li>
                {atCap.length > 1 && <li>{atCap.length} mã ({atCap.map((w) => w.ticker).join(', ')}) đang chạm mức trần {pct(maxW)}.</li>}
                {topSector && <li>Ngành chiếm nhiều nhất: <b>{topSector[0]}</b> với {pct(topSector[1])}.{topSector[1] >= 0.5 && ' Tập trung vào một ngành là rủi ro lớn: nếu ngành đó giảm, cả danh mục giảm theo.'}</li>}
                {held.length < 10 && <li>Chỉ có {held.length} mã nên mức phân tán còn thấp. Có thể giảm w_max (ví dụ 10%) để buộc thuật toán chia đều cho nhiều mã hơn.</li>}
              </ul>
            </section>
          )}

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách dùng bảng cấu hình bên phải</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li><b>w_max (trần mỗi mã):</b> kéo thanh trượt để đổi. 15% là mặc định. Hạ xuống 10% thì danh mục có ít nhất 10 mã và phân tán hơn, nhưng lãi kỳ vọng thường thấp hơn một chút.</li>
              <li><b>Mô hình, Ước lượng rủi ro, Train:</b> như ở tab Đường biên Hiệu quả. Bấm <b>Chạy thuật toán</b> để tính lại.</li>
              <li>Mỗi lần chạy sẽ thay danh mục được dùng ở tab <b>Kiểm định (Backtest)</b>. Hãy chạy với Train 2021-01-01 → 2024-12-31 trước khi Backtest năm 2025.</li>
            </ul>
          </section>

          <section className="rounded-md bg-amber-50 border border-amber-200 p-3 text-amber-900">
            <h4 className="font-semibold mb-1">Lưu ý quan trọng</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>Danh mục này tính từ dữ liệu quá khứ (Train) nên chưa chắc tốt trong tương lai. Hãy xem tab Backtest để kiểm tra bằng dữ liệu chưa dùng khi tính.</li>
              <li>Tỷ trọng tối ưu rất nhạy với ước lượng đầu vào; chỉ đổi nhẹ mô hình cũng có thể làm danh mục khác đi nhiều. Có thể tự thử bằng cách đổi w_max hoặc mô hình rồi chạy lại để xem danh mục thay đổi thế nào.</li>
              <li>Kết quả chưa tính thuế, trượt giá, hay giới hạn thanh khoản khi mua bán thật. Đây là công cụ học tập, <b>không phải khuyến nghị đầu tư</b>.</li>
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
