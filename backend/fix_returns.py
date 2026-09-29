import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.models import PriceDaily

from app.core.config import settings
db_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

print('Executing raw SQL update for instant performance...')
sql = """
UPDATE price_daily
SET 
  ret = COALESCE(sub.ret, 0.0),
  excess_ret = COALESCE(sub.ret, 0.0) - (POWER(1.0 + 0.05, 1.0/252.0) - 1.0)
FROM (
  SELECT 
    date, 
    ticker,
    (close - LAG(close) OVER(PARTITION BY ticker ORDER BY date)) / NULLIF(LAG(close) OVER(PARTITION BY ticker ORDER BY date), 0) as ret
  FROM price_daily
) sub
WHERE price_daily.date = sub.date AND price_daily.ticker = sub.ticker;
"""
with engine.begin() as conn:
    conn.execute(text(sql))
print('Done!')

