import pandas as pd

class RiskFreeCollector:
    def collect(self, start: str, end: str) -> pd.DataFrame:
        # Fetch 1-year government bond yield or state bank deposit rate
        # For this example, assuming a constant 5% annual rate if no API is available
        
        dates = pd.date_range(start=start, end=end, freq='B')
        rf_annual = 0.05
        # rf_daily = (1 + rf_annual)^(1/252) - 1
        rf_daily = (1 + rf_annual)**(1/252) - 1
        
        df = pd.DataFrame({
            "date": dates,
            "rf_annual": rf_annual,
            "rf_daily": rf_daily
        })
        return df
