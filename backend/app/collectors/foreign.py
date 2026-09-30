import pandas as pd

class ForeignCollector:
    """Return an empty, typed result until a historical foreign-data source is configured."""

    def collect(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        columns = [
            "date", "ticker", "foreign_owned_pct", "room_total_pct",
            "room_remaining_pct", "net_foreign_buy_value",
        ]
        return pd.DataFrame(columns=columns)
