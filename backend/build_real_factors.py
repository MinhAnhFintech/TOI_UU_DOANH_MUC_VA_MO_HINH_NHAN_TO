"""Build only factors supported by the observations currently stored in the DB.

Unavailable inputs stay missing. In particular, this script never fabricates
factor returns from random noise or from unrelated factors.
"""
import os
import sys

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.config import settings
from app.db.models import FactorsDaily, PriceDaily
from app.cleaning.quality import compute_returns
from app.factors.foreign import build_for
from app.factors.liq import build_liq
from app.factors.mkt import build_mkt
from app.factors.sorts_2x3 import build_rmw_cma, build_smb_hml
from app.factors.vol import build_vol


def _series_frame(series: pd.Series, name: str) -> pd.DataFrame:
    if series is None or series.empty:
        return pd.DataFrame(columns=[name], index=pd.DatetimeIndex([], name="date"))
    result = series.rename(name).to_frame()
    result.index = pd.to_datetime(result.index)
    result.index.name = "date"
    return result


def build_factors():
    db_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        prices = pd.read_sql(
            "SELECT date, ticker, close, adj_close, volume, value, shares_outstanding, market_cap "
            "FROM price_daily ORDER BY ticker, date", engine
        )
        indices = pd.read_sql(
            "SELECT date, index_code, close FROM index_daily WHERE index_code='VN30' ORDER BY date",
            engine,
        )
        rf = pd.read_sql("SELECT date, rf_daily FROM risk_free ORDER BY date", engine)
        fundamentals = pd.read_sql("SELECT * FROM fundamentals_quarterly", engine)
        foreign = pd.read_sql("SELECT * FROM foreign_daily", engine)
        if prices.empty or indices.empty:
            raise ValueError("Price and VN30 index history are required to build factors")
        if rf.empty:
            raise ValueError("Risk-free observations are missing; refusing to assume a rate")

        for column in ("close", "adj_close", "volume", "value", "shares_outstanding", "market_cap"):
            if column in prices:
                prices[column] = pd.to_numeric(prices[column], errors="coerce")
        for frame in (fundamentals, foreign):
            for column in frame.select_dtypes(include="object").columns:
                if column not in {"ticker", "report_date", "date"}:
                    frame[column] = pd.to_numeric(frame[column], errors="coerce")
        indices["close"] = pd.to_numeric(indices["close"], errors="coerce")
        rf["rf_daily"] = pd.to_numeric(rf["rf_daily"], errors="coerce")

        prices["date"] = pd.to_datetime(prices["date"])
        indices["date"] = pd.to_datetime(indices["date"])
        rf["date"] = pd.to_datetime(rf["date"])
        prices["adj_close"] = prices["adj_close"].fillna(prices["close"])
        prices = compute_returns(prices, rf)

        index_input = indices.rename(columns={"index_code": "ticker"})
        index_input["ticker"] = "VN30"
        factors = _series_frame(build_mkt(index_input, rf), "mkt")

        if not fundamentals.empty:
            for frame in (
                build_smb_hml(prices, fundamentals),
                build_rmw_cma(prices, fundamentals),
            ):
                if not frame.empty:
                    frame.index = pd.to_datetime(frame.index)
                    factors = factors.join(frame, how="outer")

        if {"value", "market_cap"}.issubset(prices.columns):
            factors = factors.join(_series_frame(build_liq(prices), "liq"), how="outer")
        if not foreign.empty:
            factors = factors.join(_series_frame(build_for(prices, foreign), "for_"), how="outer")
        factors = factors.join(_series_frame(build_vol(prices), "vol"), how="outer")
        factors = factors.sort_index()
        if factors.empty or "mkt" not in factors or factors["mkt"].notna().sum() < 30:
            raise ValueError("Fewer than 30 valid market-factor observations were produced")

        # Prepare all rows before replacing stored factors, so an input error
        # never erases the last successfully built factor set.
        records = []
        for day, row in factors.iterrows():
            values = {}
            for name in ("mkt", "smb", "hml", "rmw", "cma", "liq", "for_", "vol"):
                value = row.get(name)
                values[name] = float(value) if pd.notna(value) and np.isfinite(value) else None
            records.append(FactorsDaily(
                date=pd.Timestamp(day).date(),
                mkt=values["mkt"], smb=values["smb"], hml=values["hml"],
                rmw=values["rmw"], cma=values["cma"], liq=values["liq"],
                for_factor=values["for_"], vol=values["vol"],
            ))

        return_updates = []
        for row in prices[["date", "ticker", "ret", "excess_ret"]].itertuples(index=False):
            ret = float(row.ret) if pd.notna(row.ret) and np.isfinite(row.ret) else None
            excess = float(row.excess_ret) if pd.notna(row.excess_ret) and np.isfinite(row.excess_ret) else None
            return_updates.append({"date": pd.Timestamp(row.date).date(), "ticker": row.ticker,
                                  "ret": ret, "excess_ret": excess})

        session.execute(update(PriceDaily), return_updates)
        session.query(FactorsDaily).delete()
        session.bulk_save_objects(records)
        session.commit()
        available = [name for name in factors.columns if factors[name].notna().any()]
        print(f"Saved {len(records)} factor dates. Available observed factors: {', '.join(available)}")
        if len(available) < 5:
            print("Some requested models will remain unavailable until their source data is collected.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    build_factors()
