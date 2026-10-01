import os
import sys
import pandas as pd
from datetime import date
import time
from sqlalchemy import create_engine, inspect as sa_inspect
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db.models import PriceDaily, IndexDaily, RiskFree, Stock
from vnstock.api.quote import Quote
from app.db.base import Base

def run():
    print("🚀 Bắt đầu thu thập DỮ LIỆU THẬT từ thị trường...")
    from app.core.config import settings
    db_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    # pool_pre_ping: tự kiểm tra và nối lại nếu server đã ngắt kết nối.
    engine = create_engine(db_url, pool_pre_ping=True, pool_recycle=240)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    print("1. Đang cập nhật dữ liệu; các quan sát hiện có sẽ được giữ lại.")

    def _clean(value):
        """Đổi kiểu numpy sang kiểu Python và NaN sang None để lưu vào database."""
        if hasattr(value, "item") and not isinstance(value, (str, bytes)):
            try:
                value = value.item()
            except Exception:
                pass
        if isinstance(value, float) and value != value:
            return None
        return value

    def _bulk_upsert(records, chunk_size=500):
        """Ghi hàng loạt (INSERT ... ON CONFLICT DO UPDATE) thay vì từng dòng một."""
        records = list(records)
        if not records:
            return
        table = sa_inspect(type(records[0])).local_table
        columns = [c.name for c in table.columns]
        pk = [c.name for c in table.primary_key.columns]
        insert = sqlite_insert if engine.dialect.name == "sqlite" else pg_insert
        rows = [{c: _clean(getattr(r, c)) for c in columns} for r in records]
        for i in range(0, len(rows), chunk_size):
            stmt = insert(table).values(rows[i:i + chunk_size])
            update_cols = {c: stmt.excluded[c] for c in columns if c not in pk}
            if update_cols:
                stmt = stmt.on_conflict_do_update(index_elements=pk, set_=update_cols)
            else:
                stmt = stmt.on_conflict_do_nothing(index_elements=pk)
            session.execute(stmt)
        session.commit()

    def upsert(records):
        records = list(records)
        for attempt in (1, 2):
            try:
                _bulk_upsert(records)
                return
            except Exception:
                session.rollback()      # bắt buộc: nếu không, mọi lệnh sau sẽ lỗi dây chuyền
                if attempt == 2:
                    raise
                time.sleep(2)           # lần 1 lỗi (vd. mất kết nối): thử lại 1 lần

    vn30_tickers = [
        "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG", 
        "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB", 
        "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE"
    ]
    
    start_date = "2020-01-01"
    end_date = "2026-12-31"
    
    existing_stocks = {
        stock.ticker: stock
        for stock in session.query(Stock).filter(Stock.ticker.in_(vn30_tickers)).all()
    }
    # Older runs filled fabricated labels and listing dates; clear only those
    # exact placeholders and leave user-supplied metadata intact.
    for ticker, stock in existing_stocks.items():
        if (
            stock.company_name == f"Công ty {ticker}"
            and stock.sector == "N/A"
            and stock.listing_date == date(2010, 1, 1)
        ):
            stock.company_name = None
            stock.sector = None
            stock.listing_date = None
    session.add_all([Stock(ticker=ticker) for ticker in vn30_tickers if ticker not in existing_stocks])
    session.commit()
    print("Đã thêm danh sách 30 mã cổ phiếu VN30.")

    print("2. Tải dữ liệu Giá cổ phiếu VN30 (DỮ LIỆU THẬT)...")
    print("⏳ Lưu ý: Đang dùng chế độ tải chậm (mỗi mã nghỉ 3.5s) để không bị VNStock khoá kết nối (Rate Limit). Sẽ mất khoảng 2 phút...")
    
    for ticker in vn30_tickers:
        print(f" 📥 Đang tải {ticker}...")
        try:
            df = Quote(symbol=ticker, source='VCI').history(start=start_date, end=end_date)
            if df is not None and not df.empty:
                df = df.sort_values('time').copy()
                price_col = 'adj_close' if 'adj_close' in df.columns else 'close'
                df['ret'] = pd.to_numeric(df[price_col], errors='coerce').pct_change()
                rf_daily = (1 + 0.05) ** (1 / 252) - 1
                prices = []
                for _, row in df.iterrows():
                    d = pd.to_datetime(row['time']).date()
                    val = getattr(row, 'value', getattr(row, 'volume', 0) * getattr(row, 'close', 0))
                    ret = row['ret'] if pd.notna(row['ret']) else None
                    shares = row.get('shares_outstanding')
                    market_cap = row.get('market_cap')
                    if pd.isna(shares):
                        shares = None
                    if pd.isna(market_cap) and shares is not None:
                        market_cap = row['close'] * shares
                    if pd.isna(market_cap):
                        market_cap = None
                    prices.append(PriceDaily(
                        date=d,
                        ticker=ticker,
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        adj_close=row[price_col],
                        volume=row['volume'],
                        value=val,
                        shares_outstanding=shares,
                        market_cap=market_cap,
                        ret=ret,
                        excess_ret=(ret - rf_daily) if ret is not None else None
                    ))
                upsert(prices)
                print(f" ✅ Tải thành công {ticker}")
        except Exception as e:
            session.rollback()
            print(f" ❌ Lỗi tải {ticker}: {e}")
            
        # Nghỉ 3.5s để lách luật 20 requests/phút của vnstock
        time.sleep(3.5)

    print("3. Tải dữ liệu VN30 Index (DỮ LIỆU THẬT)...")
    try:
        df_index = Quote(symbol='VN30', source='VCI').history(start=start_date, end=end_date)
        if df_index is not None and not df_index.empty:
            indices = []
            for _, row in df_index.iterrows():
                d = pd.to_datetime(row['time']).date()
                indices.append(IndexDaily(
                    date=d,
                    index_code="VN30",
                    close=row['close']
                ))
            upsert(indices)
            print(" ✅ Tải thành công VN30 Index")
    except Exception as e:
        session.rollback()
        print(f" ❌ Lỗi tải Index: {e}")

    # Use an explicit constant-rate assumption until a historical RF source is configured.
    rf_annual = 0.05
    rf_daily = (1 + rf_annual) ** (1 / 252) - 1
    rf_rows = [RiskFree(date=d.date(), rf_annual=rf_annual, rf_daily=rf_daily,
                        source="assumed constant 5% annual")
               for d in pd.date_range(start_date, end_date, freq='B')]
    upsert(rf_rows)

    print("Hoàn tất thu thập dữ liệu! ✅")
    print("Lưu ý: lợi suất dùng giá đóng cửa đã điều chỉnh nếu nguồn cung cấp; nếu không, dùng giá đóng cửa thường.")
    print("Vui lòng khởi động lại API Server (FastAPI) để dữ liệu mới cập nhật!")

if __name__ == "__main__":
    run()