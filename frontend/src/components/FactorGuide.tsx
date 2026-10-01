import { useState } from 'react';

const clean = (f: string) => f.replace(/_$/, '').toUpperCase();

const FACTORS: [string, string, string][] = [
  ['MKT', 'Thị trường', 'Lợi suất VN30 trừ lãi suất phi rủi ro. Phần thưởng khi chấp nhận rủi ro thị trường.'],
  ['SMB', 'Quy mô', 'Cổ phiếu vốn hoá nhỏ trừ cổ phiếu vốn hoá lớn. Dương: nhóm nhỏ chạy tốt hơn nhóm lớn.'],
  ['HML', 'Giá trị', 'Cổ phiếu giá rẻ so với sổ sách (B/M cao) trừ cổ phiếu đắt. Dương: cổ phiếu giá trị chạy tốt hơn.'],
  ['RMW', 'Lợi nhuận', 'Cổ phiếu có ROE cao trừ cổ phiếu ROE thấp. Dương: doanh nghiệp sinh lời tốt được thưởng.'],
  ['CMA', 'Đầu tư', 'Doanh nghiệp đầu tư thận trọng trừ doanh nghiệp mở rộng mạnh (tăng tài sản nhanh).'],
  ['LIQ', 'Thanh khoản', 'Cổ phiếu khó giao dịch trừ cổ phiếu dễ giao dịch. Dương: người chịu kém thanh khoản được bù đắp.'],
  ['FOR', 'Sở hữu nước ngoài', 'Nhóm tỷ lệ sở hữu nước ngoài cao trừ nhóm thấp. Lưu ý: dùng tỷ lệ hiện tại cho mọi ngày.'],
  ['VOL', 'Biến động', 'Cổ phiếu biến động mạnh trừ cổ phiếu biến động yếu.'],
];

const COLS: [string, string][] = [
  ['Trung bình', 'Lợi suất trung bình mỗi ngày của nhân tố.'],
  ['Độ lệch chuẩn', 'Mức dao động mỗi ngày. Càng lớn nhân tố càng "thất thường".'],
  ['TB Năm', 'Lợi suất trung bình quy ra một năm (trung bình ngày x 252 phiên).'],
  ['t-stat', 'Trung bình có khác 0 một cách đáng tin không. Trị tuyệt đối từ 2 trở lên là đáng tin.'],
  ['p-value', 'Xác suất thấy kết quả này chỉ do may rủi. Dưới 0,05 là có ý nghĩa thống kê; dưới 0,01 là rất rõ.'],
  ['Skew', 'Độ lệch. Âm: thỉnh thoảng có ngày giảm rất mạnh; dương: thỉnh thoảng có ngày tăng rất mạnh.'],
  ['Kurtosis', 'Độ "đuôi dày". Trên 3 nghĩa là hay có ngày biến động cực đoan hơn bình thường.'],
  ['N', 'Số ngày có dữ liệu để tính. Chênh nhau chút giữa các nhân tố là bình thường.'],
];

export default function FactorGuide({ stats }: { stats?: any[] }) {
  const [open, setOpen] = useState(true);
  const rows = Array.isArray(stats) ? stats.filter((s) => s && s.p_value != null && s.t_stat != null) : [];
  const significant = rows.filter((s) => s.p_value < 0.05);
  const notSig = rows.filter((s) => s.p_value >= 0.05);
  const fmt = (s: any) => `${clean(s.factor)} (${s.t_stat > 0 ? 'dương' : 'âm'}, TB năm ${(s.ann_mean * 100).toFixed(1)}%, p=${s.p_value.toFixed(3)})`;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200">
      <button type="button" onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-4 py-3 text-left">
        <span className="text-base font-semibold text-slate-800">Hướng dẫn đọc trang Phân tích Nhân tố</span>
        <span className="text-sm text-navy-600">{open ? 'Thu gọn ▲' : 'Mở rộng ▼'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-5 text-sm text-slate-700 leading-relaxed">
          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Nhân tố là gì và để làm gì?</h4>
            <p>
              Lợi suất cổ phiếu không chỉ phụ thuộc vào thị trường chung mà còn vào đặc điểm của công ty (nhỏ hay lớn, rẻ hay đắt, sinh lời cao hay thấp…).
              Mỗi <b>nhân tố</b> là một danh mục "mua nhóm này, bán nhóm kia" (long-short) mô phỏng trên VN30. Đường của nhân tố cho biết đặc điểm đó có được thị trường
              "thưởng" hay không. Các bước sau (Hồi quy, So sánh mô hình, Tối ưu danh mục) dùng chính các nhân tố này.
            </p>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">8 nhân tố trong công cụ</h4>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2">
              {FACTORS.map(([code, name, desc]) => (
                <div key={code}>
                  <dt className="font-medium text-slate-800">{code} – {name}</dt>
                  <dd className="text-slate-600">{desc}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách đọc biểu đồ "Lợi suất tích lũy"</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>Mọi đường bắt đầu từ 100. Đường lên 200 nghĩa là nhân tố đã mang lại +100% nếu giữ liên tục; xuống 50 nghĩa là lỗ một nửa.</li>
              <li>Đường đi lên đều: nhân tố được thưởng ổn định. Đường đi ngang hoặc xuống: nhân tố không đem lại lợi suất.</li>
              <li>Bấm vào tên nhân tố ở chú giải phía trên để tắt/bật đường đó. Di chuột lên biểu đồ để xem giá trị từng ngày.</li>
              <li>Các đường là danh mục long-short trên giấy, chưa trừ phí giao dịch và khó thực hiện hết ngoài đời (nhất là bán khống). Dùng chúng để hiểu thị trường, không phải để "mua theo".</li>
            </ul>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách đọc bảng thống kê</h4>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2">
              {COLS.map(([term, desc]) => (
                <div key={term}>
                  <dt className="font-medium text-slate-800">{term}</dt>
                  <dd className="text-slate-600">{desc}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-2">
              <b>Quy tắc nhanh:</b> nhân tố có <b>p-value &lt; 0,05</b> thì lợi suất trung bình của nó khác 0 một cách đáng tin; nếu <b>TB Năm dương</b> thì nhân tố đó
              được thưởng, nếu <b>âm</b> thì bị "phạt" trong giai đoạn này. Nhân tố không có ý nghĩa thống kê vẫn hữu ích trong mô hình vì nó giúp giải thích biến động của cổ phiếu.
            </p>
          </section>

          {rows.length > 0 && (
            <section className="rounded-md bg-slate-50 border border-slate-200 p-3">
              <h4 className="font-semibold text-slate-800 mb-1">Nhận xét tự động từ số liệu hiện tại</h4>
              <ul className="list-disc pl-5 space-y-1">
                <li>{significant.length > 0
                  ? <>Nhân tố có ý nghĩa thống kê (p &lt; 0,05): {significant.map(fmt).join('; ')}.</>
                  : 'Không có nhân tố nào có ý nghĩa thống kê ở mức 5%.'}</li>
                {notSig.length > 0 && <li>Chưa đủ bằng chứng (p ≥ 0,05): {notSig.map((s) => clean(s.factor)).join(', ')}. Nghĩa là lợi suất trung bình của các nhân tố này chưa tách khỏi 0 một cách đáng tin.</li>}
              </ul>
            </section>
          )}

          <section className="rounded-md bg-amber-50 border border-amber-200 p-3 text-amber-900">
            <h4 className="font-semibold mb-1">Lưu ý</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>Đây là thống kê của giai đoạn đã qua, không đảm bảo tương lai. Một nhân tố có thể tăng mạnh vài năm rồi đi ngang.</li>
              <li>VN30 chỉ có 30 mã nên mỗi nhóm nhân tố rất ít cổ phiếu; kết quả dễ bị chi phối bởi vài mã.</li>
              <li>Biểu đồ và bảng này dùng toàn bộ giai đoạn có dữ liệu. Phần Train/Test (2021–2024 / 2025) chỉ áp dụng ở các bước hồi quy và tối ưu phía sau.</li>
              <li>Bước tiếp theo: sang tab <b>Hồi quy Chuỗi thời gian</b> để xem từng cổ phiếu nhạy với các nhân tố này thế nào.</li>
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
