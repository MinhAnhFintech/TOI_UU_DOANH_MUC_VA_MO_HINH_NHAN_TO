import os
import sys
import pandas as pd
from datetime import date
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db.models import PriceDaily, IndexDaily, RiskFree, Stock
from vnstock.api.quote import Quote
from app.db.base import Base

def run():
    print("🚀 Bắt đầu thu thập DỮ LIỆU THẬT từ thị trường...")
    DATABASE_URL = "sqlite:///./vn30.db"
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    print("1. Đang dọn dẹp dữ liệu cũ (Mock data)...")
    session.query(PriceDaily).delete()
    session.query(IndexDaily).delete()
    session.query(RiskFree).delete()
    session.query(Stock).delete()
    session.commit()

    vn30_tickers = [
        "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG", 
        "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB", 
        "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE"
    ]
    
    start_date = "2020-01-01"
    end_date = "2026-12-31"
    
    for t in vn30_tickers:
        session.add(Stock(ticker=t, company_name=f"Công ty {t}", sector="N/A", listing_date=date(2010, 1, 1)))
    session.commit()
    print("Đã thêm danh sách 30 mã cổ phiếu VN30.")

    print("2. Tải dữ liệu Giá cổ phiếu VN30 (DỮ LIỆU THẬT)...")
    print("⏳ Lưu ý: Đang dùng chế độ tải chậm (mỗi mã nghỉ 3.5s) để không bị VNStock khoá kết nối (Rate Limit). Sẽ mất khoảng 2 phút...")
    
    for ticker in vn30_tickers:
        print(f" 📥 Đang tải {ticker}...")
        try:
            df = Quote(symbol=ticker, source='VCI').history(start=start_date, end=end_date)
            if df is not None and not df.empty:
                prices = []
                for _, row in df.iterrows():
                    d = pd.to_datetime(row['time']).date()
                    val = getattr(row, 'value', getattr(row, 'volume', 0) * getattr(row, 'close', 0))
                    prices.append(PriceDaily(
                        date=d,
                        ticker=ticker,
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        adj_close=row['close'],
                        volume=row['volume'],
                        value=val,
                        shares_outstanding=1000000000, 
                        market_cap=row['close'] * 1000000000,
                        ret=0.0,
                        excess_ret=0.0
                    ))
                session.bulk_save_objects(prices)
                session.commit()
                print(f" ✅ Tải thành công {ticker}")
        except Exception as e:
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
            session.bulk_save_objects(indices)
            session.commit()
            print(" ✅ Tải thành công VN30 Index")
    except Exception as e:
        print(f" ❌ Lỗi tải Index: {e}")

    print("Hoàn tất thu thập dữ liệu! ✅")
    print("Vui lòng khởi động lại API Server (FastAPI) để dữ liệu mới cập nhật!")

if __name__ == "__main__":
    run()

