import { useState } from 'react';

export default function QuantileGuide({ model }: { model?: string }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200">
      <button type="button" onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-4 py-3 text-left">
        <span className="text-base font-semibold text-slate-800">Hướng dẫn đọc trang Hồi quy Phân vị</span>
        <span className="text-sm text-navy-600">{open ? 'Thu gọn ▲' : 'Mở rộng ▼'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-5 text-sm text-slate-700 leading-relaxed">
          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Trang này để làm gì?</h4>
            <p>
              Hồi quy ở tab trước chỉ cho biết cổ phiếu phản ứng với nhân tố <b>"trung bình"</b> thế nào. Hồi quy phân vị cho thấy phản ứng đó
              <b> có đổi khác khi thị trường rất xấu hay rất tốt không</b>. Ví dụ một cổ phiếu có thể nhạy với thị trường hơn nhiều vào những ngày giảm mạnh, và đó là rủi ro mà hồi quy thường không thấy.
              Đây là phần phân tích bổ sung, không bắt buộc cho bước tối ưu danh mục.
            </p>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Các từ cần biết</h4>
            <dl className="space-y-2">
              <div>
                <dt className="font-medium text-slate-800">Phân vị (tau)</dt>
                <dd className="text-slate-600">
                  Chia các ngày theo lợi suất của cổ phiếu từ thấp đến cao. <b>0,1</b> là nhóm 10% ngày tệ nhất (cổ phiếu giảm mạnh), <b>0,5</b> là ngày bình thường (trung vị),
                  <b> 0,9</b> là nhóm 10% ngày tốt nhất (cổ phiếu tăng mạnh). Trục ngang của biểu đồ chính là tau.
                </dd>
              </div>
              <div>
                <dt className="font-medium text-slate-800">Đường xanh đậm (Hệ số)</dt>
                <dd className="text-slate-600">Hệ số (beta) của nhân tố đang chọn ở từng phân vị. Nếu đường nằm ngang, nhân tố tác động như nhau trong mọi hoàn cảnh. Nếu đường dốc lên hoặc xuống, tác động thay đổi giữa ngày xấu và ngày tốt.</dd>
              </div>
              <div>
                <dt className="font-medium text-slate-800">Hai đường đỏ nét đứt (Biên dưới/trên của khoảng tin cậy)</dt>
                <dd className="text-slate-600">Khoảng mà hệ số thật nhiều khả năng nằm trong. Khoảng <b>càng hẹp</b> thì ước lượng càng chắc. Nếu khoảng này <b>chứa số 0</b> (đường đỏ trên và dưới nằm hai phía của đường 0), nhân tố đó chưa có tác động rõ rệt ở phân vị đó.</dd>
              </div>
            </dl>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách dùng</h4>
            <ol className="list-decimal pl-5 space-y-1">
              <li>Chọn <b>mã cổ phiếu</b> ở ô thứ nhất.</li>
              <li>Chọn <b>nhân tố</b> ở ô thứ hai (mô hình hiện tại là <b>{model || 'FF5'}</b>, đổi mô hình ở ô góc trên bên phải). Người mới nên bắt đầu với <b>MKT</b> (thị trường).</li>
              <li>Xem hình dạng đường xanh theo cách đọc ở dưới.</li>
            </ol>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách đọc hình dạng</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li><b>Beta MKT cao ở tau 0,1 và thấp ở tau 0,9:</b> cổ phiếu "giảm theo thị trường mạnh hơn lúc xấu" hơn là "tăng theo lúc tốt". Rủi ro chiều giảm lớn, nên thận trọng khi để tỷ trọng cao.</li>
              <li><b>Đường gần như nằm ngang:</b> beta ổn định, hồi quy thường là mô tả đủ tốt cho mã đó.</li>
              <li><b>Khoảng đỏ rộng ở hai đầu (0,1 và 0,9):</b> bình thường, vì ngày cực đoan ít nên ước lượng kém chắc hơn.</li>
            </ul>
          </section>

          <section className="rounded-md bg-slate-50 border border-slate-200 p-3">
            <h4 className="font-semibold text-slate-800 mb-1">Về lựa chọn "CONST" (hằng số)</h4>
            <p>
              CONST là phần cố định của mô hình (tương tự alpha), không phải một nhân tố. Ở hồi quy phân vị, CONST gần như luôn <b>tăng từ âm sang dương</b> khi tau tăng.
              Đó chỉ phản ánh việc các ngày xấu thì lợi suất âm, ngày tốt thì dương, nên <b>không có nghĩa là cổ phiếu có alpha</b>. Để xem tác động của nhân tố, hãy chọn MKT, SMB, HML…
            </p>
          </section>

          <section className="rounded-md bg-amber-50 border border-amber-200 p-3 text-amber-900">
            <h4 className="font-semibold mb-1">Lưu ý</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>Ngày cực đoan ở hai đầu có ít quan sát (khoảng 100 ngày cho mỗi 10% trong giai đoạn Train), nên kết quả ở tau 0,1 và 0,9 dao động nhiều hơn.</li>
              <li>Đây là mô tả quá khứ, không dự báo. Công cụ học tập, không phải khuyến nghị đầu tư.</li>
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
