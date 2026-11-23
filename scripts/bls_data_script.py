# Holden Bailey 2026

from io import StringIO
from pathlib import Path
import numpy as np
import requests as re
import pandas as pd
from sqlalchemy import Table, Column, Integer, Float
from common import base_from_url
from log import error, register, log
import permit_db

register('BLS Data Script')

## Data Definitions

log('Building & submitting table schema')

t_name = 'inflation_factors'

inflation_table = Table(
    t_name,
    permit_db.metadata,
    Column('month_id', Integer, primary_key=True, autoincrement=False),
    Column('year', Integer),
    Column('month', Integer),
    Column('factor', Float)
)
    
def reset_tables():
    log(f'Resetting table \"{inflation_table}\"')
    permit_db.create_table(inflation_table)

## Data Fetching

table_path = Path('./ext_data/inflation.csv')

# Bureau of Labor Statistics file I want
bls_url = 'https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems'
file_name = bls_url.split('/')[-1]

temp_path = Path(f'./cache/{file_name}')

def fetch_data():
    log('Beginning to fetch inflation data')
    file = None
    if temp_path.exists():
        log('Found cached data!')
        file = temp_path
    else:
        log(f'Cached data not found - downloading from {base_from_url(bls_url)}')
        # The user agent my browser uses
        u_a = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36'

        headers = {
            'User-Agent': u_a, 
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

        log('Sending GET request...')
        response = re.get(bls_url, headers=headers)
        log(f'Response code {response.status_code}')
        if response.status_code != 200:
            log(f'GET failed: {response.content}')
            exit(1)
        log('Response content type:', response.headers['Content-type'])
        log('Preview:', response.text[:50])
        file = StringIO(response.text)
        with temp_path.open('w') as f:
            f.write(response.text)
        log(f'Wrote response data to cache @ \"{temp_path}\"')

    log('Rearranging CPI data into inflation figures...')
    # Cleaning data :(
    df = pd.read_csv(file, sep='\t')
    df.columns=df.columns.str.strip()                               # Remove tabs from column names
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)   # Same for values
    df['value'] = pd.to_numeric(df['value'], 'coerce')
    log(f'Preview of cached \'{file_name}\':\n', df.head())
    df['period'] = df['period'].map(lambda x: int(x[1:3]) if isinstance(x, str) else 'NAN') # Convert period string to month number

    ## Data Processing

    # Series ID of target series: "All items in U.S. city average, all urban consumers, seasonally adjusted"
    id = 'CUSR0000SA0'

    df = df[df['series_id'] == id]
    # use geometric interpolation of Sept/Nov CPI as a stand-in for Oct, 2025, for which no CPI was calculated
    S25 = df.loc[(df['year']==2025) & (df['period']==9), 'value'].array[0]
    N25 = df.loc[(df['year']==2025) & (df['period']==11), 'value'].array[0]
    O25 = np.sqrt(S25 * N25)
    df.loc[(df['year']==2025) & (df['period']==10), 'value'] = O25
    # calculate ratio of each period's CPI to Jan, 2026 CPI
    base = df.loc[(df['year'] == 2026) & (df['period'] == 1),'value'].iloc[0]
    df['factor'] = (base / df['value'])
    # restrict data to study period
    df = df[df['year'].between(2005,2025)]
    df['month_id'] = df['year'] * 100 + df['period']
    df = df.rename(columns={'period':'month'})[['month_id', 'year', 'month', 'factor']]

    df.to_csv(table_path, float_format='%.3f', index=False)
    log(f'Wrote data to cache @ \"{table_path}\"')
    log('Final data preview:\n', df.head())
    
def upload_to_db():
    log('Moving inflation data to database')
    df = pd.read_csv(table_path)
    log(f'Entries in data prior to upload: {len(df)}', '\nPreview:\n', df.head(5))
    log('Uploading to database...')
    permit_db.dataframe_to_table(df, t_name)
    log('Verifying data in database...')
    df = permit_db.table_to_dataframe(inflation_table)
    if df is None: error('Database is None!')
    else: log(f'Entries in database data: {len(df)}', '\nPreview:\n', df.head(5))

if __name__ == '__main__':
    reset_tables()
    fetch_data()
    #upload_to_db()