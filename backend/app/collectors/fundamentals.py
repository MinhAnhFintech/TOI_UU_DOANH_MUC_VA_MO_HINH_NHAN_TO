import pandas as pd
from vnstock.api.financial import Finance
from tenacity import retry, stop_after_attempt, wait_exponential

class FundamentalsCollector:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_ticker(self, ticker: str) -> pd.DataFrame:
        try:
            fin = Finance(symbol=ticker, source='VCI')
            df_ratio = fin.ratio(period='quarterly')
            df_balance = fin.balance_sheet(period='quarterly')
            df_income = fin.income_statement(period='quarterly')
            
            # Combine logic here - implementation depends on exact vnstock dataframe outputs
            # Assuming we can merge them on year and quarter
            # Note: actual report_date is crucial to prevent look-ahead bias
            # In vnstock, we might have to infer report_date as end of quarter + 30 days
            
            # Dummy combination for structure
            if df_balance is not None and not df_balance.empty:
                df = df_balance.copy()
                df['ticker'] = ticker
                # add estimated report date (e.g. 30 days after quarter end)
                # This needs proper implementation based on vnstock columns
                
                return df
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    def collect(self, tickers: list[str]) -> pd.DataFrame:
        dfs = []
        for ticker in tickers:
            df = self._fetch_ticker(ticker)
            if not df.empty:
                dfs.append(df)
                
        if not dfs:
            return pd.DataFrame()
            
        return pd.concat(dfs, ignore_index=True)
