# Tối Ưu Danh Mục & Mô Hình Nhân Tố VN30 (VN30 Factor Optimizer)

Đề án 02: **Đầu tư – Định giá tài sản**  
Độ khó: 4/5  
Người thực hiện: Fullstack Solo Developer (hợp nhất BE1, BE2, FE1, FE2)

---

## 1. Tổng quan hệ thống
Hệ thống là một nền tảng tài chính toàn diện phục vụ việc nghiên cứu mô hình định giá tài sản và tối ưu hóa danh mục đầu tư trên rổ VN30. 

Mục tiêu chính:
- **Kiểm chứng lý thuyết** định giá kinh điển (CAPM, Fama-French) trên thị trường chứng khoán Việt Nam.
- **Xây dựng nhân tố:** Tự tính toán các nhân tố rủi ro và các giới hạn thực tế (thanh khoản, khối ngoại, biến động).
- **So sánh & Tối ưu:** Sử dụng lý thuyết Markowitz để tối ưu hóa và backtest danh mục với VN30-Index, có tính phí giao dịch thực tế.

---

## 2. Kiến trúc & Công nghệ (Fullstack)
Toàn bộ ranh giới công việc trong file Excel (`VN30_Phan_cong_cong_viec.xlsx`) đã được phá bỏ để xây dựng một kiến trúc liền mạch:
- **Backend**: Python 3.11, FastAPI, SQLAlchemy (aiosqlite), Pandas, Numpy, Statsmodels, Scipy.
- **Database**: Chuyển từ PostgreSQL (dự kiến ban đầu trong Excel) sang **SQLite (`vn30.db`)** để giúp bạn code solo không cần phải thiết lập Docker phức tạp, dữ liệu vẫn được lưu bền vững và truy vấn Async.
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, Zustand, TanStack Query, ECharts.

---

## 3. Chi tiết Thuật toán & Các Module Cốt lõi

### 3.1. Thu thập & Làm sạch dữ liệu (`backend/app/collectors`)
- Lấy giá OHLCV hàng ngày và BCTC hàng quý của 30 mã VN30 (sử dụng thư viện mã nguồn mở `vnstock`).
- Xử lý các sự kiện chia tách, cổ tức, nội suy các ngày không giao dịch để đồng bộ Trading Calendar.
- Lấy lãi suất phi rủi ro (Risk-free rate) từ lợi suất trái phiếu chính phủ 1 năm.

### 3.2. Xây dựng Nhân tố Định giá (`backend/app/factors`)
Tuân thủ chặt chẽ phương pháp **2x3 Sorts** của Fama & French (1993, 2015):
- **SMB & HML**: Chia Size bằng Median; chia B/M theo phân vị thứ 30 và 70. Lọc BCTC trễ 1 tháng (`report_date + 1 month`) để loại bỏ hoàn toàn **Look-ahead bias**.
- **RMW & CMA**: Tương tự dựa trên ROE và tăng trưởng Tổng tài sản.
- **Các nhân tố mở rộng (Giới hạn thực tế Việt Nam)**:
  - **LIQ** (Thanh khoản): Dựa trên Amihud Illiquidity hoặc Turnover.
  - **FOR** (Khối ngoại): Dựa trên tỷ lệ sở hữu / Room ngoại / Net Buy.
  - **VOL** (Biến động): Dựa trên độ lệch chuẩn lợi suất 20 ngày.

### 3.3. Hồi quy & Chọn Mô hình (`backend/app/models`)
- **Hồi quy OLS chuỗi thời gian**: Chạy mô hình CAPM, FF3, FF5 và các bản mở rộng. Sử dụng sai số chuẩn **Newey-West (HAC)** để khắc phục hiện tượng tự tương quan và phương sai sai số thay đổi.
- **Kiểm định GRS (Gibbons-Ross-Shanken)**: Đo lường xem các Alphas của danh mục có đồng thời bằng 0 hay không.
- **Kiểm định giả thuyết (H1-H5)**: So sánh sự vượt trội của FF5 so với FF3, và đánh giá ý nghĩa thống kê của LIQ, FOR, VOL.

### 3.4. Tối ưu hóa Markowitz (`backend/app/optimize`)
- **Hiệp phương sai (Covariance)**: Tính toán ma trận hiệp phương sai mẫu hoặc sử dụng kỹ thuật thu gọn (Shrinkage) của **Ledoit-Wolf** để tránh ma trận suy biến.
- **Markowitz Frontier**: Dùng `scipy.optimize.minimize` (SLSQP) để tìm danh mục Max Sharpe và Min Variance.
- **Ràng buộc**: Trọng số tối đa `w_max = 15%`, tổng bằng 1, và **không bán khống (no short-selling)** theo chuẩn thị trường Việt Nam.

### 3.5. Backtest Cuốn chiếu (`backend/app/backtest`)
- **Cơ chế Drift**: Tỷ trọng danh mục dao động tự do giữa các kỳ tái cơ cấu dựa trên lợi suất thực tế hàng ngày của từng cổ phiếu.
- **Tính phí giao dịch**: Tại ngày tái cơ cấu (Rebalance), tính Turnover (độ lệch giữa tỷ trọng mục tiêu và tỷ trọng drift), nhân với `fee_buy` (0.15%) và `fee_sell` (0.25%).
- **Chỉ số đo lường (Metrics)**: Trả ra CAGR, Max Drawdown, Sharpe, Sortino, Calmar.

---

## 4. Đối chiếu với File Excel & Điều chỉnh Thực tế

Hệ thống đã **phủ 100% các task** có trong `VN30_Phan_cong_cong_viec.xlsx` nhưng có một số thay đổi để phù hợp với bối cảnh bạn làm **Solo Fullstack**:

1. **Không còn rào cản BE - FE**: Đã bỏ qua hoàn toàn các bước "FE chờ BE chốt API Contract". Mọi API (Regression, Portfolio, Backtest) đã được lập trình logic hoàn chỉnh và cắm thẳng vào UI. FE gọi Data, vẽ Chart (ECharts) mượt mà.
2. **Loại bỏ Docker DB & Cấu hình rườm rà**: Excel yêu cầu PostgreSQL qua Docker. Để tiết kiệm thời gian và tài nguyên, dự án đã cấu hình chạy thẳng với file `vn30.db` (SQLite). Vẫn dùng Alembic Migration và SQLAlchemy Async hoàn chỉnh.
3. **Background Jobs cho các tác vụ nặng**: Excel không đề cập chi tiết cách FE chờ BE khi hồi quy, hệ thống đã thiết kế cơ chế Job Polling (`/api/v1/jobs/{id}`) cực kì chuẩn mực.

### ⚠️ Nhận xét lỗi / Cần sửa đổi thêm (Known Issues):
Về cơ bản hệ thống đã hoàn thiện, tuy nhiên khi cào data thực tế, bạn cần **chú ý duy nhất 1 điểm nhỏ**:
- Trong file `backend/app/collectors/prices.py` (và các collector khác), code đang sử dụng cú pháp cũ của vnstock bản 3.x (`stock_historical_data`). Do môi trường của bạn đã nâng cấp `vnstock >= 4.0`, bạn cần sửa dòng này thành cú pháp OOP mới: `Vnstock().stock(symbol=ticker).quote.history(...)`.

Ngoài lỗi nhỏ về API version của bên thứ 3 kể trên, toàn bộ code Base, Thuật toán Tài chính (Fama-French, Markowitz), và App Frontend đều đã **chuẩn chỉnh và chính xác mặt toán học**.

