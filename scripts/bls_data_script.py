# Holden Bailey 2026

from io import StringIO
from pathlib import Path
import numpy as np
import requests as re
import pandas as pd
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
import permit_db

## Database Definitions

class InflationFactor(permit_db.TableBase):
    __tablename__ = 'inflation_factors'
    
    id : Mapped[int] = mapped_column(primary_key=True)
    iso_date : Mapped[str] = mapped_column(String(10))
    factor : Mapped[float]
    
permit_db.create_table(InflationFactor)

## Data Collection

table_path = Path('./ext_data/inflation.csv')

# Bureau of Labor Statistics file I want
bls_url = 'https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems'
file_name = bls_url.split('/')[-1]

temp_path = Path(f'./cache/{file_name}')

def main():
    file = None
    if temp_path.exists():
        file = temp_path
    else:
        # The user agent my browser uses
        u_a = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36'

        headers = {
            'User-Agent': u_a, 
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

        response = re.get(bls_url, headers=headers)
        assert response.status_code == 200, f'Get failed: {response.content}'
        file = StringIO(response.text)
        with temp_path.open('w') as f:
            f.write(response.text)

    df = pd.read_csv(file, sep='\t')
    df.columns=df.columns.str.strip()                               # Remove tabs from column names
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)   # Same for values
    df['value'] = pd.to_numeric(df['value'], 'coerce')
    df['period'] = df['period'].map(lambda x: int(x[1:3]))          # Convert period string to month number
    print(f'Preview of \'{file_name}\':\n', df.head())

    ## Data Processing

    # Series ID of target series: "All items in U.S. city average, all urban consumers, seasonally adjusted"
    id = 'CUSR0000SA0'

    df = df[df['series_id'] == id]
    # use 2025's average CPI as a stand-in for Oct, 2025, for which no CPI was calculated
    O25 = df[df['year']==2025]['value'].mean() # ignores nans
    df.loc[(df['year']==2025) & (df['period']==10), 'value'] = O25
    # calculate (inverse) ratio of each time's CPI to Jan, 2026 CPI
    base = df.loc[(df['year'] == 2026) & (df['period'] == 1),'value'].values[0]
    df['factor'] = (base / df['value'])
    # restrict data to study period
    df = df[df['year'].between(2005,2025)]
    df['id'] = df['year'] * 100 + df['period']
    df = df.rename(columns={'period':'month'})[['id', 'year', 'month', 'factor']].set_index('id')
    print(df)

    df.to_csv(table_path, float_format='%.3f')
    print('Final dataframe:\n', df)

if __name__ == '__main__':
    main()