import { useState } from 'react';

const TERMS: [string, string][] = [
  ['Hồi quy chuỗi thời gian', 'Với mỗi cổ phiếu, tìm công thức: lợi suất vượt lãi suất phi rủi ro = alpha + beta1 x nhân tố 1 + beta2 x nhân tố 2 + … + sai số. Máy tự tìm alpha và các beta khớp nhất với dữ liệu quá khứ.'],
  ['Alpha', 'Phần lợi suất vượt trội mỗi kỳ mà các nhân tố không giải thích được. Số nằm trên dòng đầu, số trong ngoặc là t-stat. Alpha 0,001 ở dữ liệu ngày tương đương 0,1%/ngày. Alpha dương và |t| ≥ 2 là dấu hiệu cổ phiếu "làm tốt hơn mức nhân tố giải thích".'],
  ['Beta (từng nhân tố)', 'Độ nhạy của cổ phiếu với nhân tố đó. Beta MKT 1,2: thị trường tăng 1% thì cổ phiếu tăng khoảng 1,2%. Beta SMB dương: cổ phiếu hành xử giống nhóm vốn hoá nhỏ; âm: giống nhóm vốn hoá lớn. Beta HML dương: giống cổ phiếu giá trị; âm: giống cổ phiếu tăng trưởng.'],
  ['Số trong ngoặc (t-stat)', 'Hệ số có đáng tin không. |t| từ 2 trở lên là đáng tin (tương đương p < 0,05). Rê chuột lên ô để xem p-value chính xác.'],
  ['Adj R²', 'Mô hình giải thích được bao nhiêu phần biến động của cổ phiếu (0 đến 1, đã điều chỉnh theo số nhân tố). Ví dụ 0,65 nghĩa là khoảng 65% biến động được giải thích. Càng cao càng tốt.'],
  ['Số quan sát', 'Số kỳ (ngày/tuần/tháng) thực sự dùng để ước lượng cho mã đó. Mã niêm yết muộn sẽ ít hơn.'],
];

export default function RegressionGuide() {
  const [open, setOpen] = useState(true);
  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200">
      <button type="button" onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-4 py-3 text-left">
        <span className="text-base font-semibold text-slate-800">Hướng dẫn đọc trang Hồi quy Chuỗi thời gian</span>
        <span className="text-sm text-navy-600">{open ? 'Thu gọn ▲' : 'Mở rộng ▼'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-5 text-sm text-slate-700 leading-relaxed">
          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Trang này để làm gì?</h4>
            <p>
              Cho biết <b>mỗi cổ phiếu VN30 chịu ảnh hưởng của những nhân tố nào, mạnh hay yếu</b>. Kết quả (beta, alpha) là đầu vào để so sánh mô hình
              ở tab sau và để ước lượng lợi suất kỳ vọng khi tối ưu danh mục.
            </p>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách dùng (làm theo thứ tự)</h4>
            <ol className="list-decimal pl-5 space-y-1">
              <li>Ở bảng cấu hình bên phải, chọn <b>Bắt đầu Train</b> = 01/01/2021 và <b>Kết thúc Train</b> = 31/12/2024 (giai đoạn học, để dành 2025 kiểm tra).</li>
              <li>Chọn <b>Tần suất dữ liệu</b> và <b>Sai số chuẩn</b> (giải thích ở dưới). Người mới cứ để mặc định: <b>Ngày</b> và <b>HAC</b>.</li>
              <li>Bấm <b>Chạy thuật toán</b> và đợi thanh tiến trình chạy xong. Hệ thống luôn tính cả 7 mô hình (CAPM, FF3, FF5, FF5_LIQ, FF5_FOR, FF5_VOL, FF5_ALL) để tab So sánh Mô hình dùng.</li>
              <li>Dùng ô <b>Chọn mô hình xem</b> để đổi bảng giữa các mô hình. Mô hình có nhiều nhân tố hơn thì bảng có thêm cột beta.</li>
              <li>Sang tab <b>So sánh Mô hình</b> để biết mô hình nào phù hợp nhất.</li>
            </ol>
            <p className="mt-2 text-slate-600">Phí mua/bán và tỷ trọng tối đa không có ở đây vì hồi quy chỉ đo mối quan hệ giữa lợi suất và nhân tố; các thiết lập đó dùng ở các tab tối ưu danh mục và Backtest.</p>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Hai lựa chọn mới trong bảng cấu hình</h4>
            <dl className="space-y-2">
              <div>
                <dt className="font-medium text-slate-800">Tần suất dữ liệu: Ngày / Tuần / Tháng</dt>
                <dd className="text-slate-600">
                  Lợi suất được gộp (nhân dồn) theo tuần hoặc tháng trước khi hồi quy. <b>Ngày</b> cho nhiều quan sát nhất (khoảng 1000 điểm cho 4 năm) nên ổn định nhất.
                  <b> Tuần</b> (~210 điểm) và <b>Tháng</b> (48 điểm) giảm nhiễu giao dịch ngắn hạn nhưng ít điểm hơn, nên hệ số kém chắc chắn hơn; với tháng, các mô hình nhiều nhân tố
                  (như FF5_ALL) có thể không đủ điểm để chạy kiểm định GRS. Chú ý: alpha tính theo kỳ đã chọn, nên alpha ngày, tuần, tháng khác nhau về độ lớn và không so trực tiếp được.
                </dd>
              </div>
              <div>
                <dt className="font-medium text-slate-800">Sai số chuẩn: HAC (Newey-West) / OLS (Thường)</dt>
                <dd className="text-slate-600">
                  Quyết định cách tính t-stat và p-value (hệ số beta, alpha không đổi). <b>OLS thường</b> giả định các sai số đều nhau và độc lập; dữ liệu chứng khoán thường vi phạm
                  điều này nên t-stat có thể quá lạc quan. <b>HAC</b> điều chỉnh cho sai số thay đổi và tương quan theo thời gian, nên t-stat thận trọng hơn. Khuyến nghị dùng HAC; chọn OLS khi muốn đối chiếu với kết quả sách giáo khoa.
                </dd>
              </div>
            </dl>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách đọc bảng kết quả</h4>
            <dl className="space-y-2">
              {TERMS.map(([term, desc]) => (
                <div key={term}>
                  <dt className="font-medium text-slate-800">{term}</dt>
                  <dd className="text-slate-600">{desc}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="rounded-md bg-amber-50 border border-amber-200 p-3 text-amber-900">
            <h4 className="font-semibold mb-1">Lưu ý</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>Hệ số chỉ mô tả quá khứ. Beta của một cổ phiếu thay đổi theo thời gian.</li>
              <li>Thấy beta lớn nhưng t-stat nhỏ (dưới 2) thì không nên tin hệ số đó.</li>
              <li>Cùng một mã, thêm nhân tố vào mô hình có thể làm các beta khác thay đổi vì các nhân tố tương quan với nhau; đây là bình thường.</li>
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
