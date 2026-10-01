import { useState } from 'react';

const MODEL_INFO: [string, string][] = [
  ['CAPM', '1 nhân tố: chỉ thị trường (MKT). Mô hình đơn giản nhất, dùng làm mốc so sánh.'],
  ['FF3', 'CAPM + Quy mô (SMB) + Giá trị (HML).'],
  ['FF5', 'FF3 + Lợi nhuận (RMW) + Đầu tư (CMA).'],
  ['FF5_LIQ / FF5_FOR / FF5_VOL', 'FF5 + lần lượt thêm Thanh khoản, Sở hữu nước ngoài, Biến động.'],
  ['FF5_ALL', 'FF5 + cả ba nhân tố mở rộng (LIQ, FOR, VOL): nhiều nhân tố nhất.'],
];

export default function ModelsGuide({ compare, grs, hyp }: { compare?: any[]; grs?: any[]; hyp?: any[] }) {
  const [open, setOpen] = useState(true);

  const cmp = Array.isArray(compare) ? compare.filter((c) => c && c.avg_adj_r2 != null) : [];
  const g = Array.isArray(grs) ? grs.filter((r) => r && r.p_value != null) : [];
  const h = Array.isArray(hyp) ? hyp : [];

  const bestR2 = cmp.length ? [...cmp].sort((a, b) => b.avg_adj_r2 - a.avg_adj_r2)[0] : null;
  const grsPass = g.filter((r) => r.p_value >= 0.05).map((r) => r.model);
  const grsFail = g.filter((r) => r.p_value < 0.05).map((r) => r.model);
  const bestAlpha = g.length ? [...g].sort((a, b) => a.mean_abs_alpha - b.mean_abs_alpha)[0] : null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200">
      <button type="button" onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-4 py-3 text-left">
        <span className="text-base font-semibold text-slate-800">Hướng dẫn đọc trang So sánh Mô hình</span>
        <span className="text-sm text-navy-600">{open ? 'Thu gọn ▲' : 'Mở rộng ▼'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-5 text-sm text-slate-700 leading-relaxed">
          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Trang này để làm gì?</h4>
            <p>
              Có 7 mô hình, từ đơn giản (CAPM) đến nhiều nhân tố nhất (FF5_ALL). Trang này trả lời: <b>mô hình nào mô tả lợi suất cổ phiếu VN30 tốt nhất?</b>{' '}
              Mô hình tốt hơn cho ước lượng rủi ro và lợi suất kỳ vọng đáng tin hơn ở bước tối ưu danh mục. Kết quả lấy từ lần chạy ở tab Hồi quy (nếu chưa thấy dữ liệu, hãy chạy tab đó trước).
            </p>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">7 mô hình gồm những gì</h4>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2">
              {MODEL_INFO.map(([m, d]) => (
                <div key={m}><dt className="font-medium text-slate-800">{m}</dt><dd className="text-slate-600">{d}</dd></div>
              ))}
            </dl>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Bảng 1: So sánh sức giải thích</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li><b>Avg Adj R²:</b> trung bình, trên 30 cổ phiếu, phần biến động được mô hình giải thích (0 đến 1). <b>Càng cao càng tốt.</b></li>
              <li><b>Δ Adj R²:</b> chênh lệch so với mô hình tốt nhất (dòng đầu = 0). Số âm càng nhỏ (gần 0) thì mô hình càng gần mô hình tốt nhất.</li>
              <li>Thêm nhân tố thì Adj R² thường tăng; Adj R² đã phạt bớt việc thêm nhân tố vô ích, nên tăng lên nghĩa là nhân tố đó thật sự giúp ích.</li>
            </ul>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Bảng 2: Kiểm định GRS (đọc kỹ: p-value thấp là điều KHÔNG tốt)</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>GRS kiểm tra giả thuyết "<b>alpha của cả 30 cổ phiếu cùng bằng 0</b>", tức là mô hình đã giải thích hết lợi suất, không còn phần "dư" nào.</li>
              <li><b>p-value ≥ 0,05:</b> không bác bỏ được, mô hình <b>qua kiểm định</b> (tốt). <b>p-value &lt; 0,05:</b> mô hình để sót lợi suất bất thường, <b>không qua</b>.</li>
              <li><b>Mean |α|:</b> độ lớn trung bình của alpha mỗi ngày. <b>Càng nhỏ càng tốt</b> (0,0018 nghĩa là khoảng 0,18%/ngày).</li>
              <li><b>GRS Stat</b> chỉ là giá trị thống kê để tính p-value, nên bạn nhìn p-value là đủ.</li>
            </ul>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Bảng 3: Kiểm định giả thuyết H1–H5</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>Mỗi dòng là một câu hỏi nghiên cứu: H1 (FF3 hơn CAPM), H2 (FF5 hơn FF3), H3 (LIQ có ý nghĩa), H4 (FOR có ý nghĩa), H5 (VOL cải thiện FF5).</li>
              <li><b>Supported:</b> số liệu ủng hộ giả thuyết ở mức ý nghĩa 5%. Ngược lại là không đủ bằng chứng. Cột Ghi chú cho biết con số cụ thể (ví dụ "13/30 mã có LIQ có ý nghĩa").</li>
            </ul>
          </section>

          {(bestR2 || g.length > 0) && (
            <section className="rounded-md bg-slate-50 border border-slate-200 p-3">
              <h4 className="font-semibold text-slate-800 mb-1">Nhận xét tự động từ số liệu hiện tại</h4>
              <ul className="list-disc pl-5 space-y-1">
                {bestR2 && <li>Mô hình giải thích tốt nhất (Adj R² cao nhất): <b>{bestR2.model}</b> ({bestR2.avg_adj_r2.toFixed(4)}).</li>}
                {g.length > 0 && <li>Qua kiểm định GRS (p ≥ 0,05): <b>{grsPass.length ? grsPass.join(', ') : 'không mô hình nào'}</b>.{grsFail.length > 0 && <> Không qua (p &lt; 0,05): {grsFail.join(', ')}.</>}</li>}
                {bestAlpha && <li>Mean |α| nhỏ nhất: <b>{bestAlpha.model}</b> ({bestAlpha.mean_abs_alpha.toFixed(6)}).</li>}
                {h.length > 0 && <li>Giả thuyết được ủng hộ: {h.filter((x) => String(x.verdict).toLowerCase().startsWith('support')).map((x) => x.id).join(', ') || 'không có'}.</li>}
                {bestR2 && grsFail.includes(bestR2.model) && (
                  <li className="text-amber-800">Lưu ý: mô hình có Adj R² cao nhất ({bestR2.model}) lại không qua GRS. Hai tiêu chí đo hai thứ khác nhau (khớp từng cổ phiếu và alpha chung), nên không có mô hình nào "hơn" ở mọi mặt.</li>
                )}
              </ul>
            </section>
          )}

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Chọn mô hình nào cho bước tối ưu danh mục?</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>Ưu tiên mô hình có <b>Adj R² cao</b> và <b>Mean |α| nhỏ</b>; nếu có mô hình qua GRS thì cân nhắc kỹ hơn.</li>
              <li>Mô hình quá nhiều nhân tố dễ "học thuộc" dữ liệu cũ. Nếu hai mô hình gần nhau, chọn mô hình đơn giản hơn (ví dụ FF5 thay vì FF5_ALL).</li>
              <li>Chọn mô hình ở ô góc trên bên phải của trang, rồi sang tab <b>Đường biên Hiệu quả</b> hoặc <b>Tỷ trọng Danh mục</b>.</li>
            </ul>
          </section>

          <section className="rounded-md bg-amber-50 border border-amber-200 p-3 text-amber-900">
            <h4 className="font-semibold mb-1">Lưu ý</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>Kết quả chỉ đúng với giai đoạn và dữ liệu đã chạy ở tab Hồi quy (mặc định Train 2021–2024); đổi giai đoạn hay tần suất thì kết quả đổi.</li>
              <li>Nhân tố FOR dùng tỷ lệ sở hữu nước ngoài hiện tại cho mọi ngày, nên kết luận H4 chỉ mang tính tham khảo.</li>
              <li>Mẫu chỉ có 30 cổ phiếu và thời gian ngắn, nên các kiểm định thống kê không thật mạnh. Đây là công cụ học tập, không phải khuyến nghị đầu tư.</li>
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
