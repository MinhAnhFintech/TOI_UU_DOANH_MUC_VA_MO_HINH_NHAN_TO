"""Thu thập tỷ lệ sở hữu nước ngoài cho nhân tố FOR.

    python collect_foreign.py                              # ảnh chụp hiện tại từ vnstock
    python collect_foreign.py --csv data/foreign_daily.csv # lịch sử thật từ file CSV

Lưu ý: vnstock miễn phí không có lịch sử sở hữu nước ngoài theo ngày. Chế độ mặc định dùng
tỷ lệ hiện tại cho mọi ngày (xem app/collectors/foreign.py). Nên ghi rõ hạn chế này trong báo cáo.
"""
import argparse
import os
import sys

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.collectors.foreign import expand_snapshot, fetch_ownership_snapshot, read_foreign_csv  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.universe import VN30_TICKERS  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.bulk import bulk_upsert  # noqa: E402
from app.db.models import ForeignDaily  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", help="Nhập lịch sử sở hữu nước ngoài từ file CSV")
    args = parser.parse_args()

    db_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=240)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        if args.csv:
            print(f"1. Đọc lịch sử sở hữu nước ngoài từ {args.csv} ...", flush=True)
            frame = read_foreign_csv(args.csv)
        else:
            print("1. Lấy tỷ lệ sở hữu nước ngoài hiện tại từ vnstock...", flush=True)
            snapshot = fetch_ownership_snapshot(VN30_TICKERS)
            if snapshot.empty:
                raise SystemExit(
                    "Không lấy được sở hữu nước ngoài từ vnstock. Hãy chuẩn bị file CSV "
                    "(date,ticker,foreign_owned_pct) rồi chạy: python collect_foreign.py --csv <file>")
            days = pd.read_sql("SELECT date, ticker FROM price_daily", engine)
            days["date"] = pd.to_datetime(days["date"]).dt.date
            frame = expand_snapshot(snapshot, days)
            print("   ⚠️ Chỉ có ảnh chụp hiện tại -> dùng cho mọi ngày (FOR là long-short theo mức sở hữu hiện tại).")
        print(f"2. Ghi {len(frame):,} dòng vào foreign_daily (theo lô)...", flush=True)
        n = bulk_upsert(session, engine, ForeignDaily.__table__, frame.to_dict("records"), chunk_size=1000)
        print(f"   ✅ Đã ghi {n:,} dòng, {frame['ticker'].nunique()} mã.")
        print("Hoàn tất. Bước tiếp theo: python build_real_factors.py")
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
