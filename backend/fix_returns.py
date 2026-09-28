import sqlite3
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import PriceDaily

engine = create_engine('sqlite:///./vn30.db')
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

df = pd.read_sql('SELECT date, ticker, close FROM price_daily', engine)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by=['ticker', 'date'])

df['ret'] = df.groupby('ticker')['close'].pct_change().fillna(0.0)
rf_daily = (1 + 0.05)**(1/252) - 1
df['excess_ret'] = df['ret'] - rf_daily

# Convert back to dict for update
updates = []
for _, row in df.iterrows():
    updates.append({
        'date': row['date'].date(),
        'ticker': row['ticker'],
        'ret': row['ret'],
        'excess_ret': row['excess_ret']
    })

print('Updating PriceDaily in database...')
session.bulk_update_mappings(PriceDaily, updates)
session.commit()
print('Done!')

