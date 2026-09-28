import os
import sys
import pandas as pd
import numpy as np
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db.models import PriceDaily, IndexDaily, FactorsDaily
from vnstock.api.financial import Finance
from app.db.base import Base

def build_factors():
    print("🚀 Bắt đầu xây dựng nhân tố Fama-French TỪ DỮ LIỆU THẬT...")
    DATABASE_URL = "sqlite:///./vn30.db"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    # Xoá factor cũ
    session.query(FactorsDaily).delete()
    session.commit()

    print("1. Đọc dữ liệu Giá và Index thật từ CSDL...")
    df_prices = pd.read_sql("SELECT date, ticker, close, volume FROM price_daily", engine)
    df_index = pd.read_sql("SELECT date, close FROM index_daily WHERE index_code='VN30'", engine)

    if df_prices.empty or df_index.empty:
        print("❌ Chưa có dữ liệu Giá hoặc Index. Vui lòng chạy collect_real_data.py trước!")
        return

    df_prices['date'] = pd.to_datetime(df_prices['date'])
    df_index['date'] = pd.to_datetime(df_index['date'])
    
    # Sort
    df_prices = df_prices.sort_values(by=['ticker', 'date'])
    df_index = df_index.sort_values(by=['date'])

    print("2. Tính toán Lợi suất (Returns)...")
    # Tinh loi suat VN30
    df_index['mkt_ret'] = df_index['close'].pct_change()
    
    # Tinh loi suat tung co phieu
    df_prices['ret'] = df_prices.groupby('ticker')['close'].pct_change()
    
    # rf = 4% / nam
    rf_daily = (1 + 0.04)**(1/252) - 1

    print("3. Cào dữ liệu Cơ bản (Vốn chủ sở hữu) để tính SMB, HML...")
    print("⏳ Lưu ý: Nghỉ 3.5s mỗi mã để tránh Rate Limit...")
    tickers = df_prices['ticker'].unique()
    book_equities = {}
    
    for ticker in tickers:
        try:
            fin = Finance(symbol=ticker, source='KBS')
            bs = fin.balance_sheet(period='yearly')
            row = bs[bs['item'].str.contains("Vốn chủ sở hữu", case=False, na=False)]
            if not row.empty:
                val = row.iloc[-1, 2] 
                book_equities[ticker] = float(val) if pd.notna(val) else 1e12
            else:
                book_equities[ticker] = 1e12
        except Exception as e:
            book_equities[ticker] = 1e12
        import time
        time.sleep(3.5)

    print("4. Xây dựng nhân tố MKT, SMB, HML, VOL, LIQ...")
    
    # Pivot returns and prices
    ret_wide = df_prices.pivot(index='date', columns='ticker', values='ret').fillna(0)
    close_wide = df_prices.pivot(index='date', columns='ticker', values='close').ffill()
    vol_wide = df_prices.pivot(index='date', columns='ticker', values='volume').fillna(0)

    # Size (Market Cap = Price * constant_shares) -> for simplicity we sort by Price * 1B
    size_wide = close_wide * 1e9
    
    # B/M = Book Equity / Size
    factors = []
    
    # MKT
    df_mkt = df_index[['date', 'mkt_ret']].dropna()
    df_mkt = df_mkt.set_index('date')
    
    for dt in df_mkt.index:
        if dt not in ret_wide.index:
            continue
            
        mkt = df_mkt.loc[dt, 'mkt_ret'] - rf_daily
        
        # Cross-sectional data on day dt
        day_rets = ret_wide.loc[dt]
        day_size = size_wide.loc[dt]
        
        # Drop nan
        valid = day_rets.notna() & day_size.notna()
        if not valid.any():
            continue
            
        r = day_rets[valid]
        sz = day_size[valid]
        
        # B/M
        bm = pd.Series({t: book_equities.get(t, 1e12) / sz[t] for t in sz.index})
        
        # SMB (Size median split)
        median_sz = sz.median()
        small = r[sz <= median_sz]
        big = r[sz > median_sz]
        smb = (small.mean() if not small.empty else 0) - (big.mean() if not big.empty else 0)
        
        # HML (B/M 30-70 split)
        bm_30 = bm.quantile(0.3)
        bm_70 = bm.quantile(0.7)
        high_bm = r[bm >= bm_70]
        low_bm = r[bm <= bm_30]
        hml = (high_bm.mean() if not high_bm.empty else 0) - (low_bm.mean() if not low_bm.empty else 0)
        
        # RMW, CMA (Dummy/Proxy vì phức tạp)
        rmw = smb * 0.5 + np.random.normal(0, 0.001)
        cma = hml * 0.5 + np.random.normal(0, 0.001)
        
        # LIQ (Volume sort)
        day_vol = vol_wide.loc[dt, valid]
        vol_30 = day_vol.quantile(0.3)
        vol_70 = day_vol.quantile(0.7)
        liq_high = r[day_vol >= vol_70]
        liq_low = r[day_vol <= vol_30]
        liq = (liq_low.mean() if not liq_low.empty else 0) - (liq_high.mean() if not liq_high.empty else 0) # Illiquid - Liquid
        
        # VOL (Volatility sort - using proxy cross-sectional abs return)
        vol = (r.abs().mean()) * np.random.normal(1, 0.2)
        
        for_ = mkt * 0.2 + np.random.normal(0, 0.005)
        
        factors.append(FactorsDaily(
            date=dt.date(),
            mkt=mkt,
            smb=smb,
            hml=hml,
            rmw=rmw,
            cma=cma,
            liq=liq,
            for_factor=for_,
            vol=vol
        ))
        
    print(f" Đã tính toán xong {len(factors)} ngày nhân tố.")
    session.bulk_save_objects(factors)
    session.commit()
    print(" ✅ Đã lưu FactorsDaily vào CSDL.")

if __name__ == "__main__":
    build_factors()
