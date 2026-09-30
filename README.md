# VN30 Factor Optimizer

> **Tối ưu danh mục và mô hình nhân tố trên thị trường Việt Nam (VN30)**  
> Portfolio Optimization & Factor Models on VN30

Đề án nghiên cứu kiểm định CAPM, Fama-French 3 & 5 nhân tố, xây dựng đường biên hiệu quả Markowitz, và backtest cuốn chiếu có tính phí giao dịch trên rổ VN30.

---

## 📋 Mục lục

- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt nhanh](#-cài-đặt-nhanh-5-phút)
- [Chạy ứng dụng](#-chạy-ứng-dụng)
- [Hướng dẫn sử dụng](#-hướng-dẫn-sử-dụng-từng-tab)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Công nghệ sử dụng](#-công-nghệ-sử-dụng)

---

## 💻 Yêu cầu hệ thống

| Yêu cầu | Phiên bản |
|----------|-----------|
| **Python** | >= 3.10 |
| **Node.js** | >= 18.0 |
| **npm** | >= 9.0 |
| **PostgreSQL** | Database Supabase (đã cấu hình sẵn) |

---

## 🚀 Cài đặt nhanh (5 phút)

### Bước 1: Clone/Tải về dự án

```bash
# Giải nén hoặc clone dự án vào thư mục
cd Mo_hình
```

### Bước 2: Cài đặt Backend (Python)

```bash
# Tạo virtual environment (chỉ lần đầu)
python -m venv .venv

# Kích hoạt virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# Cài đặt thư viện Python
cd backend
pip install -r requirements.txt
```

Nếu chưa có file `requirements.txt`, cài trực tiếp:

```bash
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg pydantic pydantic-settings pandas numpy scipy statsmodels scikit-learn openpyxl python-dotenv alembic loguru
```

### Bước 3: Cấu hình Database

Tạo file `backend/.env` (hoặc sửa file có sẵn):

```env
DATABASE_URL=postgresql+asyncpg://USER:PASS@HOST:PORT/DBNAME
DATA_START=2021-01-01
DATA_END=2025-12-31
TRAIN_END=2024-12-31
RF_SOURCE=gov_bond_1y
SEED=42
API_HOST=0.0.0.0
API_PORT=8000
```

> ⚠️ **Thay `USER`, `PASS`, `HOST`, `PORT`, `DBNAME`** bằng thông tin Supabase thực. File `.env` đã có sẵn trong dự án.

### Bước 4: Cài đặt Frontend (React)

```bash
cd frontend
npm install
```

---

## ▶️ Chạy ứng dụng

### Mở 2 terminal riêng biệt:

**Terminal 1 — Backend API (Python):**

```bash
cd backend
# Kích hoạt venv nếu chưa
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

Khi thấy dòng `Uvicorn running on http://0.0.0.0:8000` là backend đã sẵn sàng.

**Terminal 2 — Frontend (React):**

```bash
cd frontend
npm run dev
```

Khi thấy dòng `Local: http://localhost:5173/` → mở trình duyệt tại địa chỉ đó.

### Kiểm tra nhanh:

- Backend health: Mở `http://localhost:8000/api/v1/health` → phải thấy `{"data":{"status":"ok"}}`
- Frontend: Mở `http://localhost:5173/` → thấy giao diện VN30 Optimizer

---

## 📖 Hướng dẫn sử dụng từng Tab

### Tab 1: 📊 Chất lượng Dữ liệu
Xem tổng quan dữ liệu VN30: số mã, phạm vi ngày, tỷ lệ missing, biểu đồ giá chuẩn hóa.

### Tab 2: 📈 Phân tích Nhân tố
- **Biểu đồ Lợi suất Tích lũy:** Xem hiệu suất tích lũy của 8 nhân tố (MKT, SMB, HML, RMW, CMA, LIQ, FOR, VOL).
- **Bảng Thống kê mô tả:** Mean, Std, t-stat cho mỗi nhân tố (Newey-West).
- **Ma trận Tương quan:** Kiểm tra đa cộng tuyến giữa các nhân tố.

### Tab 3: 📐 Hồi quy Chuỗi thời gian
1. Chọn mô hình ở **Bảng Cấu Hình** bên phải (CAPM, FF3, FF5, FF5_ALL,...).
2. Bấm **"Chạy thuật toán"** → chờ thanh tiến trình hoàn thành.
3. Xem bảng kết quả: Alpha, Beta cho từng cổ phiếu, Adj R², t-stat.
4. Chuyển qua lại giữa các mô hình bằng dropdown phía trên bảng.

### Tab 4: ⚖️ So sánh Mô hình
- Bảng so sánh tất cả mô hình: Avg Adj R², GRS, mean|α|.
- Kết quả GRS test cho từng mô hình.
- Giả thuyết H1–H5: FF3>CAPM? FF5>FF3? LIQ/FOR/VOL có ý nghĩa?

### Tab 5: 📉 Hồi quy Phân vị
- Chọn **mã cổ phiếu** và **nhân tố** từ dropdown.
- Biểu đồ cho thấy hệ số thay đổi theo phân vị (tau 0.1→0.9).
- Đường liền = hệ số, đường đứt nét đỏ = khoảng tin cậy 95%.

### Tab 6: 🎯 Đường biên Hiệu quả
1. Chọn **mô hình** và **estimator** (Ledoit-Wolf khuyến nghị).
2. Điều chỉnh **w_max** (tỷ trọng tối đa/mã, mặc định 15%).
3. Bấm **"Chạy thuật toán"** → xem biểu đồ:
   - Đám mây xanh = 3000 danh mục ngẫu nhiên
   - Đường vàng = đường biên hiệu quả
   - ⭐ Sao đỏ = danh mục Tiếp tuyến (Max Sharpe)

> **💡 Mẹo:** Giảm w_max xuống 5-10% để buộc danh mục phải phân tán vào nhiều mã hơn.

### Tab 7: 📊 Tỷ trọng Danh mục
- Biểu đồ thanh ngang hiển thị tỷ trọng từng mã.
- Bảng chi tiết: tỷ trọng, lợi suất kỳ vọng, độ lệch chuẩn.
- **Lưu ý:** Markowitz tự động gán 0% cho các mã không hiệu quả. Đây là hành vi đúng, không phải lỗi.

### Tab 8: 🧪 Kiểm định Backtest
1. Bấm **"Chạy thuật toán"** ở bảng cấu hình.
2. Xem 4 sub-tab:
   - **Equity Curve:** NAV tích lũy 3 danh mục (VN30, Equal Weight, Proposed)
   - **Drawdown:** Độ sụt giảm từ đỉnh
   - **Rolling Sharpe:** Sharpe 60 ngày cuốn chiếu
   - **Metrics:** CAGR, Sharpe, Sortino, MaxDD, Calmar, Turnover

### Tab 9: 🔍 Phân tích Độ nhạy
*(Đang phát triển)* — Phân tích ảnh hưởng của thay đổi tham số đến kết quả.

### Tab 10: 📝 Kết Luận
- Tóm tắt 4 câu hỏi nghiên cứu chính (RQ1–RQ4).
- Bảng so sánh hiệu suất danh mục vs benchmarks.
- Phát hiện chính và giới hạn nghiên cứu.
- Tự động cập nhật theo dữ liệu đã chạy.

---

## 📁 Cấu trúc dự án

```
Mo_hình/
├── backend/                  # Backend Python (FastAPI)
│   ├── app/
│   │   ├── api/              # API endpoints (REST)
│   │   │   ├── backtest.py   # POST /backtest/run, GET /backtest/equity,...
│   │   │   ├── factors.py    # GET /factors, /factors/stats,...
│   │   │   ├── portfolio.py  # POST /portfolio/optimize, GET /portfolio/weights,...
│   │   │   └── regression.py # POST /regression/run, GET /regression/results,...
│   │   ├── backtest/         # Logic backtest
│   │   │   ├── engine.py     # NAV calculation với phí giao dịch
│   │   │   ├── benchmarks.py # VN30 Index & Equal Weight benchmarks
│   │   │   └── metrics.py    # CAGR, Sharpe, Sortino, MaxDD, Calmar
│   │   ├── factors/          # Xây dựng nhân tố Fama-French
│   │   │   ├── sorts_2x3.py  # SMB, HML, RMW, CMA (2×3 sorts)
│   │   │   ├── liq.py        # Nhân tố Thanh khoản (Amihud)
│   │   │   ├── vol.py        # Nhân tố Biến động
│   │   │   └── foreign.py    # Nhân tố Khối ngoại
│   │   ├── models/           # Mô hình tài chính
│   │   │   ├── regression.py # OLS + Newey-West HAC
│   │   │   ├── grs.py        # Gibbons-Ross-Shanken test
│   │   │   └── selection.py  # Chọn mô hình tốt nhất + H1-H5
│   │   ├── optimize/         # Tối ưu danh mục
│   │   │   ├── markowitz.py  # Max Sharpe & Min Variance
│   │   │   ├── frontier.py   # Đường biên hiệu quả + CML
│   │   │   └── covariance.py # Ledoit-Wolf shrinkage
│   │   └── core/             # Config, database, logging
│   └── .env                  # Database connection string
│
├── frontend/                 # Frontend React (TypeScript + Vite)
│   ├── src/
│   │   ├── pages/            # 10 trang ứng dụng
│   │   ├── components/       # UI components tái sử dụng
│   │   ├── api/              # API client + TanStack Query hooks
│   │   └── hooks/            # Zustand global store
│   └── package.json
│
└── README.md                 # File này
```

---

## 🔧 Công nghệ sử dụng

### Backend
| Thư viện | Vai trò |
|----------|---------|
| FastAPI | REST API framework |
| SQLAlchemy 2.0 | ORM + async database |
| PostgreSQL (Supabase) | Lưu trữ dữ liệu |
| statsmodels | Hồi quy OLS + Newey-West HAC |
| scipy.optimize | Markowitz optimization (SLSQP) |
| scikit-learn | Ledoit-Wolf covariance shrinkage |
| pandas / numpy | Xử lý dữ liệu |

### Frontend
| Thư viện | Vai trò |
|----------|---------|
| React 18 + TypeScript | UI framework |
| Vite | Build tool |
| TailwindCSS | Styling |
| ECharts | Biểu đồ tương tác |
| TanStack Query | Data fetching + caching |
| TanStack Table | Bảng dữ liệu |
| Zustand | Global state management |

### Tham số mặc định

| Tham số | Giá trị | Ghi chú |
|---------|---------|---------|
| Universe | VN30 (30 mã) | Rổ cuối cùng |
| Train | 2021-01 → 2024-12 | 4 năm |
| Test | 2025-01 → 2025-12 | 1 năm |
| Risk-free | TPCP 1 năm | Quy đổi: (1+r)^(1/252)-1 |
| w_max | 15% | Long-only, Σw=1 |
| Phí mua | 0.15% | |
| Phí bán | 0.25% | Gồm thuế 0.1% |
| HAC lag | 5 | Newey-West |
| Covariance | Ledoit-Wolf | Shrinkage estimator |

---

## ❓ Xử lý sự cố

| Vấn đề | Giải pháp |
|--------|-----------|
| `ModuleNotFoundError` | Kiểm tra đã kích hoạt `.venv` chưa: `.\.venv\Scripts\Activate.ps1` |
| Backend lỗi kết nối DB | Kiểm tra `DATABASE_URL` trong `backend/.env` |
| Frontend trắng trang | Mở DevTools (F12) → Console xem lỗi |
| Thuật toán chạy chậm | Hồi quy ~30 giây cho 7 mô hình × 30 mã. Đường biên ~10-15 giây |
| Dữ liệu biến mất khi chuyển tab | Đã fix! Dữ liệu được lưu trong localStorage |
| Biểu đồ không đổi khi chọn model | Phải bấm "Chạy thuật toán" để tính lại với model mới |

---

## 📚 Tài liệu tham khảo

- Markowitz, H. (1952). *Portfolio Selection.* Journal of Finance.
- Fama, E.F. & French, K.R. (1993). *Common risk factors in the returns on stocks and bonds.* JFE.
- Fama, E.F. & French, K.R. (2015). *A five-factor asset pricing model.* JFE.
- Gibbons, M.R., Ross, S.A., & Shanken, J. (1989). *A test of the efficiency of a given portfolio.* Econometrica.
