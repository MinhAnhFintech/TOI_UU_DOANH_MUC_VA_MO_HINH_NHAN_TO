import asyncio
import random
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.models import Base, Stock, PriceDaily, IndexDaily, FactorsDaily
from app.core.config import settings

async def seed():
    engine = create_async_engine(settings.DATABASE_URL.replace("postgresql+psycopg", "postgresql+asyncpg") if "postgresql" in settings.DATABASE_URL else settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    Session = async_sessionmaker(engine)
    async with Session() as session:
        # Check if already seeded
        res = await session.execute(Stock.__table__.select().limit(1))
        if res.first():
            print("Already seeded.")
            return

        print("Seeding mock data...")
        # 1. Stocks
        tickers = ["FPT", "HPG", "VNM", "VIC", "VHM", "TCB", "MBB", "VPB", "MWG", "PNJ"]
        for t in tickers:
            session.add(Stock(ticker=t, company_name=f"Cong ty {t}", sector="Ban le" if t in ["MWG", "PNJ"] else "Ngan hang", listing_date=date(2010, 1, 1)))
        
        # 2. Daily Prices & Index & Factors (last 30 days)
        base_date = date.today() - timedelta(days=30)
        
        nav = 1000.0
        for i in range(30):
            d = base_date + timedelta(days=i)
            # Index
            nav *= (1 + random.uniform(-0.02, 0.02))
            session.add(IndexDaily(date=d, index_code="VN30", close=nav))
            
            # Factors
            session.add(FactorsDaily(
                date=d,
                mkt=random.uniform(-0.02, 0.02),
                smb=random.uniform(-0.01, 0.01),
                hml=random.uniform(-0.01, 0.01),
                rmw=random.uniform(-0.01, 0.01),
                cma=random.uniform(-0.01, 0.01),
                liq=random.uniform(-0.01, 0.01),
                for_factor=random.uniform(-0.01, 0.01),
                vol=random.uniform(-0.01, 0.01)
            ))
            
            # Prices
            for t in tickers:
                p = random.uniform(10, 100)
                session.add(PriceDaily(
                    date=d,
                    ticker=t,
                    open=p,
                    high=p*1.02,
                    low=p*0.98,
                    close=p*1.01,
                    adj_close=p*1.01,
                    volume=random.randint(10000, 1000000),
                    value=p * 100000,
                    shares_outstanding=100000000,
                    market_cap=p * 100000000,
                    ret=random.uniform(-0.05, 0.05),
                    excess_ret=random.uniform(-0.05, 0.05)
                ))
        
        await session.commit()
        print("Mock data seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())

