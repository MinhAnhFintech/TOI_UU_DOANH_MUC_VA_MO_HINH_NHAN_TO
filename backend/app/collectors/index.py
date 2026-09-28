import pandas as pd
from vnstock import Vnstock
from tenacity import retry, stop_after_attempt, wait_exponential

class IndexCollector:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def collect(self, codes: list[str], start: str, end: str) -> pd.DataFrame:
        dfs = []
        for code in codes:
            # For indices, use Vnstock API
            stock = Vnstock().stock(symbol=code, source='VCI')
            df = stock.quote.history(start=start, end=end, resolution='1D')
            if df is not None and not df.empty:
                df = df.rename(columns={"time": "date"})
                if "ticker" not in df.columns:
                    df["ticker"] = code
                dfs.append(df)
                
        if not dfs:
            return pd.DataFrame()
            
        result = pd.concat(dfs, ignore_index=True)
        result['date'] = pd.to_datetime(result['date'])
        return result
