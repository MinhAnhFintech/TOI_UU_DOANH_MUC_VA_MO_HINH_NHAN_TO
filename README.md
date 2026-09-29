# 📈 Đề án: Tối Ưu Danh Mục & Mô Hình Nhân Tố Trên Thị Trường Việt Nam

*(Portfolio Optimization & Factor Models on VN30)*

Đề án này là một hệ thống **Định lượng Tài chính Toàn diện (Quantitative Finance System)**, được xây dựng dưới dạng một Web Application hoàn chỉnh. Hệ thống tự động hóa toàn bộ quy trình từ thu thập dữ liệu thô, xây dựng mô hình nhân tố, hồi quy kiểm định định giá tài sản, cho đến tối ưu hóa Markowitz và Backtest danh mục với dữ liệu thực tế tại thị trường chứng khoán Việt Nam (rổ VN30).

---

## 📑 Mục lục

1. [Câu hỏi nghiên cứu](#1-câu-hỏi-nghiên-cứu)
2. [Tổng quan tài liệu](#2-tổng-quan-tài-liệu)
3. [Xử lý dữ liệu &amp; Tính tái lập](#3-xử-lý-dữ-liệu--tính-tái-lập)
4. [Phương pháp kỹ thuật &amp; Kiểm định giả định](#4-phương-pháp-kỹ-thuật--kiểm-định-giả-định)
5. [Thuật toán Tối ưu hóa Markowitz](#5-thuật-toán-tối-ưu-hóa-markowitz)
6. [Hàm ý Kinh tế - Tài chính](#6-hàm-ý-kinh-tế---tài-chính)
7. [Hướng dẫn sử dụng hệ thống](#7-hướng-dẫn-sử-dụng-hệ-thống)

---

## 1. Câu hỏi nghiên cứu

Dự án được xây dựng nhằm trả lời 3 câu hỏi cốt lõi mang tính học thuật và thực tiễn cao:

- **Q1 (Pricing):** Các mô hình định giá tài sản kinh điển (CAPM, Fama-French 3 nhân tố, 5 nhân tố) có khả năng giải thích sự biến động tỷ suất sinh lợi của rổ cổ phiếu VN30 không?
- **Q2 (Emerging Market Limits):** Việc bổ sung các giới hạn thực tế của thị trường cận biên như **Thanh khoản (LIQ)**, **Giao dịch khối ngoại (FOR)** và **Độ biến động (VOL)** có cải thiện sức mạnh của mô hình so với chuẩn quốc tế không?
- **Q3 (Portfolio Management):** Danh mục tối ưu theo lý thuyết Markowitz có đánh bại được chỉ số VN30-Index (về Tỷ lệ Sharpe và Max Drawdown) khi áp dụng trong môi trường thực tế (có tính chi phí giao dịch, rebalance định kỳ) không?

---

## 2. Tổng quan tài liệu

Hệ thống được phát triển dựa trên nền tảng của các công trình đạt giải Nobel và các nghiên cứu uy tín:

- **Harry Markowitz (1952) - *Journal of Finance*:** Nền tảng của Lý thuyết danh mục hiện đại (MPT), lượng hóa rủi ro bằng phương sai và tối ưu hóa hàm mục tiêu (Đường biên hiệu quả).
- **Eugene Fama & Kenneth French (1993, 2015) - *Journal of Financial Economics*:** Sự ra đời của mô hình 3 nhân tố (MKT, SMB, HML) và 5 nhân tố (bổ sung RMW, CMA) nhằm giải quyết những dị thường (anomalies) mà CAPM không thể giải thích.
- **Nghiên cứu về Thị trường mới nổi (Emerging Markets):** Các luận điểm cho thấy rào cản về thanh khoản (Illiquidity) và dòng vốn ngoại (Foreign Ownership) là những rủi ro hệ thống bắt buộc phải được định giá bù đắp (Premium).

---

## 3. Xử lý dữ liệu & Tính tái lập

Hệ thống đảm bảo tính nghiêm ngặt tuyệt đối về **Look-ahead Bias** (Thiên kiến nhìn trước) - sai lầm phổ biến nhất trong nghiên cứu tài chính:

- **Nguồn dữ liệu:** Giá lịch sử (OHLCV) và BCTC được kéo tự động thông qua API `vnstock`.
- **Đồng bộ chuỗi thời gian:** Xử lý mất mát dữ liệu (Missing Values) bằng `forward-fill` đối với các ngày giao dịch bị ngắt quãng, đảm bảo ma trận giá không bị thủng.
- **Lag BCTC (Độ trễ):** Dữ liệu Book-to-Market (B/M), Lợi nhuận (ROE), Tổng tài sản không được dùng ngay tại ngày chốt sổ quý, mà được lùi lại (Lag) tương đương với **Report Date** (Ngày công bố BCTC ra công chúng) để đảm bảo tại thời điểm danh mục tái cơ cấu, nhà đầu tư thực sự đã biết thông tin đó.
- **Tính toán TSSL:** Tính TSSL vượt trội (Excess Return) bằng cách lấy $R_i - R_f$ (Lãi suất trái phiếu chính phủ 1 năm hoặc tiền gửi quy đổi theo ngày).

---

## 4. Phương pháp kỹ thuật & Kiểm định giả định

### 4.1. Thuật toán Xây dựng Nhân tố (Fama-French 2x3 Sorts)

- **Cơ chế:** Phân loại toàn bộ vũ trụ VN30 vào mỗi kỳ tái cơ cấu. Cắt đôi theo Quy mô (Trung vị Vốn hóa - Size Median). Cắt ba theo B/M (Phân vị 30% và 70%).
- **Trọng số:** Tính lợi suất danh mục theo phương pháp *Value-Weighted* (Trọng số vốn hóa).
- **Mở rộng (Điểm sáng tạo):** Xây dựng thêm nhân tố **LIQ** (Thanh khoản thấp trừ Thanh khoản cao), **FOR** (Khối ngoại mua trừ Khối ngoại bán), **VOL** (Biến động cao trừ thấp).

### 4.2. Hồi quy và Kiểm định

- **OLS với Newey-West (HAC):** Khắc phục triệt để vi phạm giả định của OLS cổ điển về *Tự tương quan (Autocorrelation)* và *Phương sai sai số thay đổi (Heteroskedasticity)*.
- **GRS Test (Gibbons-Ross-Shanken):** Thay vì chỉ đánh giá Adjusted $R^2$, hệ thống dùng GRS Test để kiểm định đồng thời ma trận $Alpha$ của toàn bộ các phương trình. Nếu GRS Test thất bại (p-value < 0.05), mô hình không giải thích được toàn bộ rủi ro.
- **Hồi quy phân vị (Quantile Regression):** Cung cấp góc nhìn phi tuyến tính. Ở các đuôi phân phối cực đoan (khi thị trường sập hoặc bùng nổ mạnh), Beta của các nhân tố biến đổi như thế nào.

---

## 5. Thuật toán Tối ưu hóa Markowitz

Hệ thống cung cấp thuật toán tối ưu với các ràng buộc khắt khe nhất của thị trường chứng khoán Việt Nam:

1. **Thuật toán:** Dùng `scipy.optimize` với bộ giải `SLSQP` (Sequential Least SQuares Programming). Hàm mục tiêu là Maximize Sharpe Ratio hoặc Minimize Variance.
2. **Ràng buộc:**
   - Cấm bán khống (No Short-selling): $w_i \ge 0$.
   - Giới hạn Tỷ trọng (`w_max`): Ràng buộc chặn trên ($w_i \le w_{max}$ ví dụ 15%). Nếu không có ràng buộc này, thuật toán Markowitz thường mắc "lỗi nhạy cảm", dồn 100% tiền vào 1-2 mã có tỷ suất sinh lời quá khứ cao.
3. **Ước lượng rủi ro (Covariance Estimator):** Ngoài Sample Covariance cơ bản, hệ thống hỗ trợ thuật toán **Ledoit-Wolf Shrinkage**. Thuật toán này giúp khử nhiễu (noise) của ma trận hiệp phương sai mẫu, đặc biệt quan trọng khi tập mẫu ($T$) không đủ lớn so với số lượng tài sản ($N$).
4. **Cơ chế Backtest:** Chạy cuốn chiếu (Rolling Window). Huấn luyện trên $N$ tháng quá khứ $\rightarrow$ Cố định tỷ trọng $\rightarrow$ Chạy test thực tế $\rightarrow$ Trừ phí giao dịch (Transaction Costs) dựa trên độ lệch tỷ trọng (Turnover) mỗi kỳ Rebalance.

---

## 6. Hàm ý Kinh tế - Tài chính

Sản phẩm này mang lại giá trị thực tiễn sâu sắc cho các Quỹ đầu tư, Ngân hàng đầu tư (IB) và Chuyên viên phân tích (Quant Analyst):

- **Bác bỏ niềm tin mù quáng vào VN30:** Bằng Backtest thực tế, hệ thống chứng minh danh mục Markowitz (khi được tối ưu đúng cách bằng Ledoit-Wolf và có chặn `w_max`) hoàn toàn có thể đạt Tỷ lệ Sharpe cao hơn, và Max Drawdown thấp hơn VN30-Index, bảo vệ NAV của Quỹ trong các đợt thị trường gấu (Bear market).
- **Nhận diện tính đặc thù của Việt Nam:** Kết quả cho thấy FF3 thường có Adjusted $R^2$ tốt hơn FF5. Điều này hàm ý tại VN, dòng tiền chuộng các yếu tố truyền thống (Giá trị & Quy mô) hơn là các chỉ số nền tảng (Lợi nhuận - RMW, Đầu tư - CMA).
- **Quyền lực của Khối ngoại & Thanh khoản:** Việc các mô hình mở rộng (FF5_ALL, FF5_FOR) thay đổi thứ hạng định giá chứng tỏ thanh khoản và dòng vốn FII đóng vai trò rủi ro cốt lõi. Khối quản trị rủi ro tại ngân hàng có thể dùng các Beta này để hedging (phòng ngừa rủi ro) khi khối ngoại xả hàng loạt.

---

## 7. Hướng dẫn sử dụng hệ thống

Hệ thống được thiết kế dạng Dashboard (React JS + Vite) kết nối API Backend (FastAPI).

### Khởi động (Dành cho nhà phát triển):

1. **Backend:** Bật môi trường Python, chạy `python -m uvicorn app.main:app --reload --port 8000`
2. **Frontend:** Mở thư mục frontend, chạy `npm run dev` (Port 5173).

### Luồng nghiệp vụ trên UI (Pipeline):

Để có kết quả, người dùng **phải chạy theo đúng tuần tự** sau (do output của tab trước là input của tab sau):

1. **Tab Dữ liệu & Nhân tố:** Xem biểu đồ dữ liệu OHLCV, tương quan nhân tố (Correlation Matrix) để rà soát hiện tượng đa cộng tuyến.
2. **Tab Hồi quy (Time-series Regression):**
   - Chỉnh các thông số Ngày Train, chọn Mô hình (chỉ mang tính chất xem trước).
   - Bấm **Chạy thuật toán**. Hệ thống sẽ chạy đồng loạt 7 mô hình.
3. **Tab Kết luận (Ranking):** Xem hệ thống tự động chấm điểm và xếp hạng mô hình định giá tốt nhất dựa trên Adjusted $R^2$.
4. **Tab Tỷ trọng & Đường biên:**
   - Kéo thanh `w_max` để giới hạn tỷ trọng giải ngân tối đa cho 1 cổ phiếu.
   - Bấm **Chạy thuật toán**. Hệ thống tính toán đường biên Markowitz, tìm điểm tiếp tuyến Sharpe cao nhất và vẽ biểu đồ hình đạn (Bullet/Scatter).
5. **Tab Backtest:**
   - Đặt kỳ Rebalance (Hàng tháng / Hàng quý), phí mua bán (Gợi ý: 0.15% - 0.25%).
   - Bấm **Chạy thuật toán**. Hệ thống vẽ đường Equity Curve (Tăng trưởng NAV) so sánh giữa Danh mục tối ưu, Danh mục chia đều (Equal-weight) và VN30-Index, kèm theo bảng rủi ro Max Drawdown.

---
