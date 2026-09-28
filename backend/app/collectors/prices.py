import pandas as pd
from vnstock import Vnstock
from tenacity import retry, stop_after_attempt, wait_exponential
import os

class PriceCollector:
    def __init__(self, cache_dir: str = "cache/prices"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_ticker(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        stock = Vnstock().stock(symbol=ticker, source='VCI')
        df = stock.quote.history(start=start, end=end, resolution='1D')
        if df is None or df.empty:
            return pd.DataFrame()
        
        # vnstock returns columns like time, open, high, low, close, volume, ticker
        df = df.rename(columns={"time": "date"})
        if "ticker" not in df.columns:
            df["ticker"] = ticker
            
        # Select required columns and standardise
        cols_to_keep = ["date", "ticker", "open", "high", "low", "close", "volume"]
        available_cols = [c for c in cols_to_keep if c in df.columns]
        df = df[available_cols]
        
        # approximate value if not present
        if "value" not in df.columns and "close" in df.columns and "volume" in df.columns:
            df["value"] = df["close"] * df["volume"]
            
        return df

    def collect(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        dfs = []
        for ticker in tickers:
            cache_file = os.path.join(self.cache_dir, f"{ticker}_{start}_{end}.parquet")
            if os.path.exists(cache_file):
                df = pd.read_parquet(cache_file)
            else:
                df = self._fetch_ticker(ticker, start, end)
                if not df.empty:
                    df.to_parquet(cache_file)
            dfs.append(df)
            
        if not dfs:
            return pd.DataFrame()
            
        result = pd.concat(dfs, ignore_index=True)
        result['date'] = pd.to_datetime(result['date'])
        return result
