import pandas as pd
import pandas_datareader.data as web

class KenFrenchCollector:
    def collect(self) -> pd.DataFrame:
        try:
            # Download daily FF5 factors
            df = web.DataReader('F-F_Research_Data_5_Factors_2x3_daily', 'famafrench')[0]
            # Convert index to datetime and reset index
            df.index = pd.to_datetime(df.index)
            df = df.reset_index().rename(columns={"Date": "date"})
            
            # Convert percentages to decimals
            factor_cols = ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'RF']
            for col in factor_cols:
                if col in df.columns:
                    df[col] = df[col] / 100.0
            
            # Rename columns to standard names
            df = df.rename(columns={
                'Mkt-RF': 'mkt',
                'SMB': 'smb',
                'HML': 'hml',
                'RMW': 'rmw',
                'CMA': 'cma',
                'RF': 'rf'
            })
            
            return df
        except Exception as e:
            print(f"Error fetching Ken French data: {e}")
            return pd.DataFrame()
