# Holden Bailey 2026

from io import StringIO, FileIO
from pathlib import Path
import numpy as np
import requests as re
import pandas as pd

## Data Collection

table_path = Path('./ext_data/inflation.csv')

# Bureau of Labor Statistics file I want
bls_url = 'https://download.bls.gov/pub/time.series/cu/cu.data.1.AllItems'
file_name = bls_url.split('/')[-1]

temp_path = Path(f'C://tmp/{file_name}')
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
# calculate (inverse) ratio of each time's CPI to Jan, 2026 CPI
base = df.loc[(df['year'] == 2026) & (df['period'] == 1),'value'].values[0]
df['factor'] = (base / df['value'])
# restrict data to study period
df = df[df['year'].between(2005,2025)]
pt = df.pivot(columns='period', index='year', values='factor')

# using 2025's average CPI as stand-in for Oct, 2025, for which no CPI was calculated
Oct2025 = np.mean(df[df['year']==2025]['value'])
pt.loc[2025, 10] = base/Oct2025

pt.to_csv(table_path, float_format='%.3f')
print('Final dataframe:\n', pt)