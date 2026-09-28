import pandas as pd
from vnstock import stock_historical_data

class ForeignCollector:
    def collect(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        # In a real implementation, we would fetch foreign ownership data.
        # vnstock might not have direct historical daily foreign ownership.
        # Placeholder for structural compliance.
        dfs = []
        for ticker in tickers:
            # dummy fetch
            df = pd.DataFrame(columns=["date", "ticker", "foreign_owned_pct", "room_total_pct", "room_remaining_pct", "net_foreign_buy_value"])
            dfs.append(df)
        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
