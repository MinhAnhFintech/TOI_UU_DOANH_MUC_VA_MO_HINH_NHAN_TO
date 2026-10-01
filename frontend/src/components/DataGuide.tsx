import { useState } from 'react';

const STEPS = [
  { tab: '1. Dữ liệu', text: 'Kiểm tra dữ liệu giá 30 mã VN30 đã đầy đủ chưa (trang này).' },
  { tab: '2. Phân tích nhân tố', text: 'Xem các "nhân tố" (Thị trường, Quy mô, Giá trị, Lợi nhuận, Đầu tư, Thanh khoản, Nước ngoài, Biến động) đã tạo ra lợi suất ra sao.' },
  { tab: '3. Hồi quy', text: 'Với mỗi cổ phiếu, đo xem lợi suất của nó "nhạy" với từng nhân tố thế nào (hệ số beta) và có lợi suất vượt trội (alpha) không.' },
  { tab: '4. So sánh mô hình', text: 'So CAPM, FF3, FF5... xem mô hình nào giải thích lợi suất tốt hơn (Adj R² cao hơn, AIC thấp hơn, alpha nhỏ hơn là tốt).' },
  { tab: '5. Biên hiệu quả / Tỷ trọng', text: 'Bấm "Chạy thuật toán" để máy tính ra tỷ trọng tiền nên chia cho từng cổ phiếu (tối ưu danh mục).' },
  { tab: '6. Backtest', text: 'Thử xem nếu đã đầu tư theo tỷ trọng đó trong năm 2025 thì kết quả thế nào, đã trừ phí giao dịch.' },
  { tab: '7. Kết luận', text: 'Tổng hợp để đọc kết quả cuối cùng.' },
];

const GLOSSARY: [string, string][] = [
  ['Giá chuẩn hoá (cơ sở 100)', 'Đưa giá ngày đầu tiên về 100 để so sánh các mã với nhau. Đường lên 250 nghĩa là giá đã tăng 2,5 lần so với ngày đầu.'],
  ['Giá điều chỉnh', 'Giá đã loại ảnh hưởng của chia cổ tức/tách cổ phiếu, nên không bị "rơi" giả tạo khi mã chia cổ tức.'],
  ['% Dữ liệu thiếu', 'Tỷ lệ ngày VN30 có giao dịch nhưng mã đó không có giá. Càng gần 0% càng tốt. Mã niêm yết sau (ví dụ SSB) chỉ tính từ ngày niêm yết nên có thể còn vài %.'],
  ['Lợi suất', 'Phần trăm lãi/lỗ trong một giai đoạn. Ví dụ +12% trong năm.'],
  ['Biến động (rủi ro)', 'Giá dao động mạnh hay yếu. Biến động càng cao, rủi ro càng lớn.'],
  ['Sharpe', 'Lãi nhận được trên mỗi đơn vị rủi ro, sau khi trừ lãi suất phi rủi ro. Tham khảo: >1 là tốt, 0,5–1 là tạm ổn, <0 là kém hơn gửi tiết kiệm.'],
  ['Sụt giảm tối đa (Max Drawdown)', 'Mức lỗ lớn nhất từ đỉnh xuống đáy. -30% nghĩa là có lúc tài khoản mất 30% so với đỉnh.'],
  ['Beta', 'Độ nhạy với thị trường. Beta 1,2 nghĩa là thị trường tăng 1% thì cổ phiếu thường tăng ~1,2%.'],
  ['Alpha', 'Lợi suất vượt trội mà các nhân tố không giải thích được. Alpha dương và có ý nghĩa thống kê (p < 0,05) là dấu hiệu tốt.'],
  ['Adj R²', 'Mô hình giải thích được bao nhiêu phần biến động của giá (0–1). Càng cao càng tốt.'],
  ['w_max', 'Tỷ trọng tối đa cho mỗi mã (mặc định 15%) để không dồn quá nhiều tiền vào một cổ phiếu.'],
  ['Train / Test', 'Train (2021–2024) là giai đoạn máy "học" để chọn tỷ trọng. Test (2025) là giai đoạn kiểm tra bằng dữ liệu máy chưa từng thấy, gần với thực tế hơn.'],
];

export default function DataGuide() {
  const [open, setOpen] = useState(true);
  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-base font-semibold text-slate-800">Hướng dẫn dành cho người mới (đọc dữ liệu &amp; cách dùng)</span>
        <span className="text-sm text-navy-600">{open ? 'Thu gọn ▲' : 'Mở rộng ▼'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-5 text-sm text-slate-700 leading-relaxed">
          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Công cụ này làm gì?</h4>
            <p>
              Chia số tiền của bạn cho 30 cổ phiếu lớn nhất sàn (VN30) sao cho <b>cùng mức rủi ro thì lãi kỳ vọng cao nhất</b>.
              Công cụ dùng các mô hình nhân tố Fama-French để hiểu cái gì tạo ra lợi suất, rồi tối ưu tỷ trọng và kiểm tra lại trên dữ liệu quá khứ.
            </p>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách đọc trang Dữ liệu</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li><b>Thẻ trên cùng:</b> số mã cổ phiếu; khoảng thời gian dữ liệu thật của mã đang chọn (tính từ phiên đầu đến phiên cuối có giá và khối lượng); và số phiên giao dịch (khoảng 250 phiên/năm).</li>
              <li><b>Biểu đồ giá chuẩn hoá:</b> chọn mã ở ô "Chọn mã cổ phiếu". Đường đi lên là giá tăng; đường dốc xuống mạnh là giai đoạn lỗ. Biểu đồ chỉ để xem quá khứ, không dự báo tương lai.</li>
              <li><b>Báo cáo chất lượng:</b> bảng xếp từ mã thiếu nhiều dữ liệu nhất. Đa số mã gần 0% là dữ liệu tốt. Mã có % cao thường do niêm yết muộn hoặc bị tạm ngừng giao dịch.</li>
            </ul>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cách dùng: đi theo thứ tự các tab</h4>
            <ol className="space-y-1">
              {STEPS.map((s) => (
                <li key={s.tab}><b className="text-navy-700">{s.tab}:</b> {s.text}</li>
              ))}
            </ol>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Cài đặt khuyến nghị cho người mới</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>Train: <b>2021-01-01 → 2024-12-31</b>; Backtest: <b>2025-01-01 → 2025-12-31</b>. Phải tối ưu danh mục trước (tab Tỷ trọng) rồi mới Backtest, và Backtest phải bắt đầu sau khi Train kết thúc.</li>
              <li>Mô hình: dùng <b>FF5_ALL</b> (đầy đủ nhất) hoặc <b>FF5</b> (gọn hơn); CAPM chỉ có một nhân tố thị trường, dùng làm mốc để so sánh.</li>
              <li>Ước lượng rủi ro: <b>Ledoit-Wolf</b> (ổn định hơn với 30 cổ phiếu). Tỷ trọng tối đa mỗi mã: <b>15%</b>. Phí mua 0,15%, phí bán 0,25%.</li>
              <li>Tái cân bằng hàng tháng hoặc hàng quý; càng thường xuyên thì phí giao dịch càng cao.</li>
            </ul>
          </section>

          <section>
            <h4 className="font-semibold text-slate-800 mb-1">Từ điển thuật ngữ</h4>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2">
              {GLOSSARY.map(([term, desc]) => (
                <div key={term}>
                  <dt className="font-medium text-slate-800">{term}</dt>
                  <dd className="text-slate-600">{desc}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="rounded-md bg-amber-50 border border-amber-200 p-3 text-amber-900">
            <h4 className="font-semibold mb-1">Lưu ý quan trọng</h4>
            <ul className="list-disc pl-5 space-y-1">
              <li>Kết quả dựa trên dữ liệu quá khứ; hiệu quả trong quá khứ không đảm bảo cho tương lai. Đây là công cụ học tập và tham khảo, <b>không phải khuyến nghị đầu tư</b>.</li>
              <li>Lãi suất phi rủi ro (Rf) đang giả định cố định 5%/năm.</li>
              <li>Nhân tố nước ngoài (FOR) dùng tỷ lệ sở hữu nước ngoài hiện tại cho mọi ngày vì nguồn miễn phí không có lịch sử.</li>
              <li>Ngày công bố báo cáo tài chính được ước tính (cuối quý + 45 ngày; quý 4 + 90 ngày) để tránh dùng thông tin chưa công bố.</li>
              <li>Chưa tính thuế, trượt giá và giới hạn thanh khoản khi mua bán thật.</li>
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
