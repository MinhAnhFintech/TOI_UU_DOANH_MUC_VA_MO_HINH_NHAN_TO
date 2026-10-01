# VN30 Factor Optimizer

> **Tối ưu danh mục và mô hình nhân tố trên thị trường Việt Nam (VN30)**
> Portfolio Optimization & Factor Models on VN30

Dự án nghiên cứu kiểm định các mô hình nhân tố (CAPM, Fama-French 3 và 5 nhân tố, cùng các bản mở rộng với thanh khoản, biến động và khối ngoại), xây dựng đường biên hiệu quả Markowitz và backtest danh mục có tính phí giao dịch trên rổ 30 mã VN30. Giao diện web có phần hướng dẫn đọc kết quả ở từng tab, để người chưa quen tài chính định lượng vẫn dùng được.

> Công cụ phục vụ học tập và nghiên cứu, **không phải khuyến nghị đầu tư**.

---

## Mục lục

- [Dự án làm gì](#dự-án-làm-gì)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Chuẩn bị dữ liệu](#chuẩn-bị-dữ-liệu)
- [Chạy ứng dụng](#chạy-ứng-dụng)
- [Thứ tự sử dụng các tab](#thứ-tự-sử-dụng-các-tab)
- [Phương pháp](#phương-pháp)
- [Tham số mặc định](#tham-số-mặc-định)
- [Giới hạn của nghiên cứu](#giới-hạn-của-nghiên-cứu)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Công nghệ](#công-nghệ)
- [Làm việc nhóm với Git](#làm-việc-nhóm-với-git)
- [Xử lý sự cố](#xử-lý-sự-cố)
- [Tài liệu tham khảo](#tài-liệu-tham-khảo)

---

## Dự án làm gì

Dự án trả lời bốn câu hỏi nghiên cứu, và trang **Kết luận** tự tổng hợp câu trả lời từ số liệu bạn đã chạy:

| Câu hỏi | Nội dung |
|---|---|
| **RQ1** | Mô hình nhân tố nào giải thích lợi suất cổ phiếu VN30 tốt nhất (Adj R², AIC, \|α\|)? |
| **RQ2** | Mô hình có giải thích đầy đủ lợi suất không (kiểm định GRS)? |
| **RQ3** | Các giả thuyết H1–H5 về FF3 so với CAPM, FF5 so với FF3, và vai trò của LIQ, FOR, VOL có được dữ liệu ủng hộ không? |
| **RQ4** | Danh mục tối ưu Markowitz có vượt VN30 và danh mục chia đều trong giai đoạn kiểm tra không? |

Tám nhân tố: **MKT, SMB, HML, RMW, CMA** (Fama-French) cộng **LIQ** (thanh khoản), **FOR** (khối ngoại), **VOL** (biến động).
Bảy mô hình: **CAPM, FF3, FF5, FF5_LIQ, FF5_VOL, FF5_FOR, FF5_ALL**.

---

## Yêu cầu hệ thống

| Yêu cầu | Phiên bản |
|---|---|
| Python | 3.10 trở lên |
| Node.js | 18 trở lên |
| npm | 9 trở lên |
| Cơ sở dữ liệu | PostgreSQL (Supabase), hoặc SQLite để chạy thử |

---

## Cài đặt

### 1. Lấy mã nguồn

```bash
git clone <đường-dẫn-repo>
cd <thư-mục-dự-án>
```

### 2. Backend (Python)

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Cấu hình `backend/.env`

Tạo file `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASS@HOST:PORT/DBNAME
DATA_START=2021-01-01
DATA_END=2025-12-31
TRAIN_END=2024-12-31
RF_SOURCE=constant
SEED=42
API_HOST=0.0.0.0
API_PORT=8000
```

> **Bảo mật:** file `.env` chứa mật khẩu cơ sở dữ liệu. **Không commit file này lên GitHub** (đã có trong `.gitignore`). Nếu lỡ đẩy lên, hãy đổi mật khẩu ngay.

### 4. Frontend (React)

```bash
cd frontend
npm install
```

---

## Chuẩn bị dữ liệu

Chạy trong thư mục `backend` (đã bật `.venv`), **theo đúng thứ tự**. Nếu cơ sở dữ liệu của nhóm đã có dữ liệu thì có thể bỏ qua phần này.

| Bước | Lệnh | Việc làm |
|---|---|---|
| 1 | `python collect_real_data.py` | Tải giá 30 mã VN30 và chỉ số VN30 từ vnstock, ghi lãi suất phi rủi ro cố định 5%/năm |
| 2 | `python collect_fundamentals.py` | Tải số liệu cơ bản theo quý và số cổ phiếu lưu hành, tính vốn hoá (cho SMB, HML, RMW, CMA). Có thể nhập từ CSV bằng `--csv data/fundamentals_quarterly.csv` |
| 3 | `python collect_foreign.py` | Tỷ lệ sở hữu nước ngoài cho nhân tố FOR. Có thể nhập lịch sử thật bằng `--csv data/foreign_daily.csv` |
| 4 | `python build_real_factors.py` | Tính 8 nhân tố từ dữ liệu đã lưu. Nhân tố nào thiếu đầu vào thì để trống, không tự bịa số |

Bước 3 mặc định chỉ có **ảnh chụp tỷ lệ hiện tại**, vì nguồn miễn phí không có lịch sử sở hữu nước ngoài theo ngày. Xem phần [Giới hạn](#giới-hạn-của-nghiên-cứu).

---

## Chạy ứng dụng

Mở hai terminal riêng.

**Terminal 1: Backend**

```bash
cd backend
.\.venv\Scripts\Activate.ps1      # Windows; macOS/Linux: source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

Kiểm tra: mở `http://localhost:8000/api/v1/health`, phải thấy trạng thái `ok`.

**Terminal 2: Frontend**

```bash
cd frontend
npm run dev
```

Mở `http://localhost:5173/`.

---

## Thứ tự sử dụng các tab

Thanh bên trái có 9 tab. Mỗi tab có thẻ **hướng dẫn đọc** có thể thu gọn, và nhiều tab có phần **nhận xét tự động** tính từ dữ liệu.

| # | Tab | Việc cần làm |
|---|---|---|
| 1 | **Chất lượng Dữ liệu** | Xem số mã, khoảng thời gian, tỷ lệ thiếu dữ liệu và giá chuẩn hoá (cơ sở 100) |
| 2 | **Phân tích Nhân tố** | Xem lợi suất tích luỹ, thống kê mô tả và tương quan của 8 nhân tố |
| 3 | **Hồi quy Chuỗi thời gian** | Chọn **tần suất dữ liệu** (Ngày/Tuần/Tháng), **sai số chuẩn** (HAC/OLS) và giai đoạn Train, rồi chạy. Đây là bước tạo ra số liệu cho tab 4, 5 và trang Kết luận |
| 4 | **So sánh Mô hình** | Bảng Adj R², GRS và kiểm định H1–H5 của 7 mô hình |
| 5 | **Hồi quy Phân vị** | Xem hệ số thay đổi theo phân vị (tau 0,1 đến 0,9) của từng cổ phiếu và nhân tố |
| 6 | **Đường biên Hiệu quả** | Chọn mô hình, estimator rủi ro, w_max rồi chạy. Hiển thị các danh mục ngẫu nhiên, đường biên và danh mục Max Sharpe |
| 7 | **Tỷ trọng Danh mục** | Tỷ trọng tối ưu từng mã, lợi suất kỳ vọng, độ lệch chuẩn và ngành |
| 8 | **Kiểm định (Backtest)** | Chạy backtest ngoài mẫu: đường vốn, drawdown, Sharpe cuốn chiếu, bảng chỉ số, có chọn phí và tần suất tái cân bằng |
| 9 | **Kết luận** | Tổng hợp RQ1–RQ4 kèm lý do, thông số lần chạy, danh mục đề xuất và giới hạn |

Phí mua/bán chỉ hiển thị ở tab Backtest, vì các tab Hồi quy, Đường biên và Tỷ trọng không dùng đến phí.

**Thứ tự chạy khuyến nghị:** Hồi quy (tab 3) → Tỷ trọng Danh mục (tab 7) → Backtest (tab 8) → Kết luận (tab 9).

> **Lưu ý quan trọng:** mỗi lần chạy tạo một kết quả riêng, và các trang luôn đọc **lần chạy gần nhất**. Nếu bạn chạy lại Hồi quy với cài đặt khác mà không chạy lại Tỷ trọng và Backtest, các phần của trang Kết luận sẽ lấy từ các lần chạy khác cấu hình nhau. Hãy chốt một cấu hình rồi chạy lại đủ ba bước.
>
> Ô chọn mô hình ở góc trên bên phải của trang chỉ đổi mô hình dùng để lập danh mục (tab 6, 7) và hộp mô tả ở trang Kết luận. Nó không làm đổi bảng so sánh mô hình hay GRS.

---

## Phương pháp

- **Hồi quy chuỗi thời gian:** mỗi cổ phiếu được hồi quy lợi suất vượt trội (trừ lãi suất phi rủi ro) theo các nhân tố của từng mô hình. Sai số chuẩn dùng HAC (Newey-West, lag 5 với dữ liệu ngày) hoặc OLS thường. Với dữ liệu Tuần/Tháng, lợi suất được cộng gộp theo kỳ (tuần kết thúc thứ Sáu, hoặc cuối tháng).
- **Chọn mô hình (RQ1):** xếp hạng ưu tiên Adj R² trung bình cao hơn; nếu bằng nhau mới xét GRS p-value cao hơn, rồi AIC thấp hơn, rồi \|α\| trung bình thấp hơn. Đây là thứ tự ưu tiên, không phải điểm tổng hợp.
- **GRS (RQ2):** kiểm định Gibbons-Ross-Shanken, H₀ là alpha của tất cả cổ phiếu cùng bằng 0. p-value trên 0,05 nghĩa là chưa đủ bằng chứng bác bỏ H₀, không phải bằng chứng mô hình đúng.
- **Giả thuyết (RQ3):** H1, H2, H5 dùng kiểm định t ghép cặp trên chênh lệch Adj R² của từng mã; H3, H4 dùng kiểm định nhị thức xem tỷ lệ cổ phiếu có hệ số LIQ hoặc FOR có ý nghĩa 5% có cao hơn mức ngẫu nhiên 5% hay không.
- **Lợi suất kỳ vọng:** μ = Rf + Σ β·λ, trong đó λ là phần bù nhân tố trung bình năm của giai đoạn Train. Không cộng alpha vào μ để tránh học quá khớp quá khứ.
- **Tối ưu:** Markowitz (Max Sharpe hoặc Min Variance), chỉ mua, tổng tỷ trọng 100%, mỗi mã tối đa w_max. Ma trận hiệp phương sai chọn một trong ba: mẫu (Sample), Ledoit-Wolf, bán phương sai (Semi-Covariance). Markowitz có thể gán 0% cho nhiều mã, đó là hành vi bình thường.
- **Backtest (RQ4):** huấn luyện trên giai đoạn Train, kiểm tra ngoài mẫu trên giai đoạn Test, có trừ phí giao dịch; so với chỉ số VN30 và danh mục chia đều. Các chỉ số: CAGR, biến động, Sharpe, Sortino, Max Drawdown, Calmar, vòng quay danh mục.

---

## Tham số mặc định

| Tham số | Giá trị | Ghi chú |
|---|---|---|
| Rổ | VN30 (30 mã) | |
| Giai đoạn Train | 2021-01-01 đến 2024-12-31 | Đổi được ở tab Hồi quy |
| Giai đoạn Test | 2025 | Backtest ngoài mẫu |
| Lãi suất phi rủi ro | 5%/năm cố định | Quy đổi ngày: (1+r)^(1/252) − 1 |
| w_max | 15% | Chỉ mua, tổng tỷ trọng 100% |
| Phí mua | 0,15% | Đổi được ở tab Backtest |
| Phí bán | 0,25% | Đổi được ở tab Backtest |
| HAC lag | 5 | Dữ liệu ngày; Tuần 2, Tháng 1 |
| Estimator rủi ro | Ledoit-Wolf | Có thể chọn Sample hoặc Semi-Covariance |
| Mục tiêu tối ưu | Tối đa hoá Sharpe | Hoặc tối thiểu hoá phương sai |

---

## Giới hạn của nghiên cứu

- Mẫu chỉ gồm 30 mã VN30, không đại diện cho toàn thị trường.
- Nhân tố **FOR** dùng tỷ lệ sở hữu nước ngoài **hiện tại** cho mọi ngày (nguồn miễn phí không có lịch sử), nên kết luận H4 chỉ mang tính tham khảo.
- Ngày công bố báo cáo tài chính được **ước tính** (cuối quý cộng 45 ngày; quý 4 cộng 90 ngày) để tránh dùng thông tin chưa công bố.
- Lãi suất phi rủi ro là hằng số 5%/năm, không phải chuỗi lãi suất thật theo ngày.
- Kiểm tra ngoài mẫu chỉ trên **một giai đoạn** (2025). Kết quả có thể do may rủi và không đảm bảo lặp lại trong tương lai.
- Kết quả hồi quy và GRS phụ thuộc tần suất dữ liệu và kiểu sai số chuẩn; nên chạy thêm bản Tuần hoặc Tháng làm kiểm tra độ vững.
- Danh mục tối ưu có thể tập trung vào một ngành (ví dụ ngân hàng); trang Kết luận có cảnh báo khi tỷ trọng một ngành từ 50% trở lên.

---

## Cấu trúc dự án

```
.
├── backend/                     # FastAPI + SQLAlchemy (async)
│   ├── app/
│   │   ├── api/                 # data, factors, regression, portfolio, backtest, jobs, export
│   │   ├── backtest/            # engine, benchmarks, metrics
│   │   ├── collectors/          # prices, index, fundamentals, foreign, riskfree
│   │   ├── factors/             # SMB/HML/RMW/CMA (2x3), LIQ, VOL, FOR
│   │   ├── models/              # regression (OLS + HAC), GRS, selection (xếp hạng + H1-H5)
│   │   ├── optimize/            # markowitz, frontier, covariance
│   │   ├── schemas/             # pydantic
│   │   └── core/                # config, database
│   ├── alembic/                 # migration
│   ├── data/                    # file CSV mẫu cho fundamentals và foreign
│   ├── collect_real_data.py     # bước 1: giá và chỉ số
│   ├── collect_fundamentals.py  # bước 2: số liệu cơ bản, vốn hoá
│   ├── collect_foreign.py       # bước 3: sở hữu nước ngoài
│   ├── build_real_factors.py    # bước 4: tính nhân tố
│   └── requirements.txt
├── frontend/                    # React + TypeScript + Vite
│   └── src/
│       ├── pages/               # 9 trang (Data, Factors, Regression, Models, Quantile, Frontier, Weights, Backtest, Conclusion)
│       ├── components/          # ConfigPanel, DataTable, các thẻ hướng dẫn (…Guide)
│       ├── api/                 # API client và hook TanStack Query
│       └── hooks/               # zustand store
└── README.md
```

---

## Công nghệ

**Backend:** FastAPI, SQLAlchemy 2.0 (async), PostgreSQL (Supabase), statsmodels (OLS, HAC), scipy (tối ưu SLSQP), scikit-learn (Ledoit-Wolf), pandas, numpy, vnstock.

**Frontend:** React 18, TypeScript, Vite, TailwindCSS, ECharts, TanStack Query, TanStack Table, zustand.

---

## Làm việc nhóm với Git

Không đẩy trực tiếp lên nhánh `main`. Quy trình khuyến nghị:

```bash
git checkout -b ten-nhanh-cua-ban
git add .
git status            # kiểm tra KHÔNG có .env trong danh sách
git commit -m "Mô tả ngắn thay đổi"
git push -u origin ten-nhanh-cua-ban
```

Sau đó vào GitHub, tạo **Pull Request** vào `main` để người phụ trách xem và gộp. Không dùng `git push --force` trên kho chung.

---

## Xử lý sự cố

| Vấn đề | Cách xử lý |
|---|---|
| `ModuleNotFoundError` | Chưa bật `.venv`. Chạy lại lệnh kích hoạt ở bước cài đặt |
| Backend không kết nối được cơ sở dữ liệu | Kiểm tra `DATABASE_URL` trong `backend/.env` |
| Frontend trắng trang | Mở DevTools (F12), xem tab Console |
| Vite báo "Failed to resolve import" | Thiếu hoặc sai tên file component. Kiểm tra file nằm đúng thư mục và đúng tên |
| VS Code báo gạch đỏ sau khi dán file | Lưu file, rồi Ctrl+Shift+P, chọn `Restart TS Server` |
| Sửa code backend mà web không đổi | Tắt uvicorn (Ctrl+C) và chạy lại; với frontend thì bấm Ctrl+F5 |
| Trang Kết luận thiếu phần | Cần chạy đủ Hồi quy, Tỷ trọng và Backtest |
| Cột Ngành hiện N/A | Cập nhật `backend/app/api/portfolio.py` bản có bảng ngành mặc định |
| Hồi quy chạy lâu | Dữ liệu ngày với 7 mô hình và 30 mã mất khoảng nửa phút trở lên |

---

## Tài liệu tham khảo

- Markowitz, H. (1952). *Portfolio Selection.* Journal of Finance, 7(1), 77–91.
- Fama, E.F. & French, K.R. (1993). *Common risk factors in the returns on stocks and bonds.* Journal of Financial Economics, 33(1), 3–56.
- Fama, E.F. & French, K.R. (2015). *A five-factor asset pricing model.* Journal of Financial Economics, 116(1), 1–22.
- Gibbons, M.R., Ross, S.A. & Shanken, J. (1989). *A test of the efficiency of a given portfolio.* Econometrica, 57(5), 1121–1152.
- Ledoit, O. & Wolf, M. (2004). *A well-conditioned estimator for large-dimensional covariance matrices.* Journal of Multivariate Analysis, 88(2), 365–411.
