"""Thu thập dữ liệu cơ bản theo quý + số cổ phiếu lưu hành, rồi tính vốn hoá.

Chạy (trong thư mục backend, đã bật .venv):

    python collect_fundamentals.py                      # tải từ vnstock (VCI)
    python collect_fundamentals.py --csv data/fundamentals_quarterly.csv   # nhập từ file CSV

File CSV (nếu dùng) có các cột:
    ticker,fiscal_year,quarter,report_date,book_equity,total_assets,net_income,roe,shares_outstanding
(report_date có thể bỏ trống -> tự ước lượng; roe dạng thập phân 0.18 hoặc phần trăm 18).

Kết quả:
  * bảng fundamentals_quarterly (cho SMB, HML, RMW, CMA);
  * cột shares_outstanding và market_cap của price_daily (cho SMB, trọng số, LIQ, VOL, FOR).
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.collectors.fundamentals import (  # noqa: E402
    FundamentalsCollector, estimate_report_date, finalize_quarterly, normalize_units,
)
from app.core.config import settings  # noqa: E402
from app.core.universe import VN30_TICKERS  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.bulk import bulk_upsert  # noqa: E402
from app.db.models import FundamentalsQuarterly, PriceDaily  # noqa: E402

DB_COLUMNS = ["ticker", "fiscal_year", "quarter", "report_date",
              "book_equity", "total_assets", "net_income", "roe"]


def read_csv(path: str) -> dict:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    missing = {"ticker", "fiscal_year", "quarter", "book_equity"} - set(df.columns)
    if missing:
        raise SystemExit(f"File CSV thiếu cột bắt buộc: {', '.join(sorted(missing))}")
    for col in ("total_assets", "net_income", "roe", "shares_outstanding", "bvps"):
        if col not in df.columns:
            df[col] = np.nan
    out = {}
    for ticker, g in df.groupby(df["ticker"].str.upper().str.strip()):
        g = g.sort_values(["fiscal_year", "quarter"]).reset_index(drop=True)
        g["fiscal_year"] = g["fiscal_year"].astype(int)
        g["quarter"] = g["quarter"].astype(int)
        if "report_date" in g.columns:
            g["report_date"] = pd.to_datetime(g["report_date"], errors="coerce")
        out[ticker] = g
    return out


def price_scale(session_engine) -> float:
    """vnstock trả giá theo nghìn đồng (vd. 25.5). Trả hệ số đưa giá về VND."""
    close = pd.read_sql("SELECT close FROM price_daily WHERE close IS NOT NULL LIMIT 5000", session_engine)
    if close.empty:
        return 1.0
    med = pd.to_numeric(close["close"], errors="coerce").median()
    return 1000.0 if med < 1000 else 1.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", help="Nhập từ file CSV thay vì tải từ vnstock")
    parser.add_argument("--tickers", nargs="*", help="Chỉ tải một số mã (mặc định: 30 mã VN30)")
    parser.add_argument("--limit", type=int, default=40, help="Số quý tối đa mỗi mã (mặc định 40)")
    args = parser.parse_args()
    tickers = [t.upper() for t in (args.tickers or VN30_TICKERS)]

    db_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=240)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        scale = price_scale(engine)
        last_close = pd.read_sql(
            "SELECT p.ticker, p.close FROM price_daily p JOIN "
            "(SELECT ticker, MAX(date) AS d FROM price_daily GROUP BY ticker) m "
            "ON p.ticker = m.ticker AND p.date = m.d", engine)
        last_close = {r.ticker: float(r.close) * scale for r in last_close.itertuples() if pd.notna(r.close)}

        if args.csv:
            print(f"1. Đọc dữ liệu từ {args.csv} ...", flush=True)
            raw = read_csv(args.csv)
        else:
            print("1. Tải báo cáo tài chính theo quý từ vnstock (mỗi mã ~15 giây, tổng ~10 phút)...", flush=True)
            raw = FundamentalsCollector(limit=args.limit).collect(tickers)
        if not raw:
            raise SystemExit(
                "Không lấy được dữ liệu cơ bản của mã nào. Hãy dùng phương án CSV: "
                "python collect_fundamentals.py --csv data/fundamentals_quarterly.csv")

        print("2. Chuẩn hoá đơn vị và ghi vào database...", flush=True)
        db_rows, quarterly = [], {}
        for ticker, df in raw.items():
            df = df.copy()
            df, factor = normalize_units(df, last_close.get(ticker))
            if factor != 1.0:
                print(f"   ℹ️ {ticker}: đã đổi đơn vị vốn chủ/tài sản/lợi nhuận (x{factor:g}) cho khớp vốn hoá")
            if "report_date" in df.columns and df["report_date"].notna().any():
                df = df.copy()
                ticker_df = finalize_quarterly(df, ticker)
                given = pd.to_datetime(df["report_date"], errors="coerce")
                ticker_df["report_date"] = [
                    g.date() if pd.notna(g) else e for g, e in zip(given, ticker_df["report_date"])]
            else:
                ticker_df = finalize_quarterly(df, ticker)
            quarterly[ticker] = ticker_df
            db_rows.extend(ticker_df[DB_COLUMNS].to_dict("records"))
        n = bulk_upsert(session, engine, FundamentalsQuarterly.__table__, db_rows)
        print(f"   ✅ Đã ghi {n} dòng vào fundamentals_quarterly cho {len(quarterly)} mã.")

        # Nhân tố SMB/HML/RMW/CMA chỉ bắt đầu từ kỳ tái cân bằng (tháng 6/12) đầu tiên có báo cáo đã công bố.
        first_report = min(pd.Timestamp(d) for q in quarterly.values() for d in q["report_date"])
        usable_from = first_report + pd.DateOffset(months=1)
        train_start = pd.Timestamp(settings.DATA_START)
        print(f"   Báo cáo sớm nhất đã công bố: {first_report.date()} -> nhân tố SMB/HML/RMW/CMA có từ ~{usable_from.date()}.")
        if usable_from > train_start + pd.DateOffset(months=6):
            print("   ⚠️ Lịch sử báo cáo còn ngắn so với giai đoạn Train (bắt đầu {}). ".format(settings.DATA_START)
                  + "Nếu cần đủ 2021-2024, hãy bổ sung từ 2020 bằng file CSV (--csv).")

        print("3. Tính số cổ phiếu lưu hành và vốn hoá theo ngày...", flush=True)
        prices = pd.read_sql("SELECT date, ticker, close FROM price_daily ORDER BY ticker, date", engine)
        prices["date"] = pd.to_datetime(prices["date"])
        prices["close"] = pd.to_numeric(prices["close"], errors="coerce")
        updates, no_shares = [], []
        for ticker, q in quarterly.items():
            shares = pd.to_numeric(q["shares_outstanding"], errors="coerce")
            if shares.notna().sum() == 0:
                no_shares.append(ticker)
                continue
            qend = [pd.Timestamp(year=int(y), month=int(m) * 3, day=1) + pd.offsets.MonthEnd(0)
                    for y, m in zip(q["fiscal_year"], q["quarter"])]
            ref = pd.DataFrame({"qend": qend, "shares": shares.values}).dropna().sort_values("qend")
            daily = prices[prices["ticker"] == ticker].sort_values("date")
            if daily.empty:
                continue
            merged = pd.merge_asof(daily, ref, left_on="date", right_on="qend", direction="backward")
            # Ngày trước quý đầu tiên có dữ liệu: dùng số cổ phiếu của quý đầu tiên.
            merged["shares"] = merged["shares"].fillna(ref["shares"].iloc[0])
            for r in merged.itertuples(index=False):
                if pd.isna(r.shares) or r.shares <= 0:
                    continue
                cap = float(r.close) * scale * float(r.shares) if pd.notna(r.close) else None
                updates.append({"date": r.date.date(), "ticker": ticker,
                                "shares_outstanding": int(round(r.shares)), "market_cap": cap})
        if updates:
            m = bulk_upsert(session, engine, PriceDaily.__table__, updates,
                            update_cols=["shares_outstanding", "market_cap"], chunk_size=1000)
            print(f"   ✅ Đã cập nhật số cổ phiếu và vốn hoá cho {m:,} dòng giá.")
        if no_shares:
            print(f"   ⚠️ Không có số cổ phiếu lưu hành cho: {', '.join(no_shares)} "
                  "(thiếu vốn hoá -> SMB/HML/RMW/CMA thiếu các mã này).")
        print("Hoàn tất. Bước tiếp theo: python collect_foreign.py rồi python build_real_factors.py")
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
