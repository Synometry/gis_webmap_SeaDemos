# Holden Bailey 2026

from io import StringIO, FileIO
from pathlib import Path
import numpy as np
import requests as re
import pandas as pd
import geopandas as gpd

## Data Fetching

raw_data_path = Path('./cache/permitQuery.csv')

# End-point for Bureau of Labor Statistics file I want
soda_url = 'https://data.seattle.gov/api/v3/views/76t5-zqzr/query.csv'

def main():
    file = None
    if raw_data_path.exists():
        file = raw_data_path
    else:
        # u_a = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36'
        u_a = 'H. Bailey @ hobbes3303@gmail.com'
        headers = {
            'User-Agent': u_a, 
            'Accept': 'text/csv;charset=utf-8',
            # 'Accept-Language': 'en-US,en;q=0.5',
            # 'Accept-Encoding': 'gzip, deflate, br',
            # 'Connection': 'keep-alive'
        }
        # SoQL query
        fields_str = ', '.join(['permitnum', 'permitclass', 'permittypedesc', 'description', 
                    'housingunits', 'housingunitsremoved', 'housingunitsadded',
                    'estprojectcost', 'applieddate', 'issueddate', 'expiresdate',
                    'completeddate', 'statuscurrent', 'originaladdress1', 'originalzip',
                    'contractorcompanyname', 'link', 'latitude', 'longitude', 'location1',
                    'zoning', 'dwellingunittype', 'housingcategory'])
        query = f'SELECT {fields_str} WHERE '\
            'caseless_one_of(permitclassmapped, "residential") AND '\
            'caseless_one_of(permittypemapped, "building") AND '\
            'issueddate BETWEEN "2005-01-01T00:00:00" and "2025-12-31T23:59:59" AND '\
            'caseless_one_of(statuscurrent, "approved to occupy", "completed", "inspections completed", "issued", "phase issued") AND '\
            'NOT caseless_starts_with(description, "closed as incomplete") AND '\
            '(housingunitsremoved IS NOT NULL OR housingunitsadded IS NOT NULL) AND '\
            'NOT (housingunitsremoved == 0 AND housingunitsadded == 0) AND '\
            'parentpermitnum IS NULL'
        post_json = {
            'query':query,
            'includeSynthetic': False,
        }
        response = re.post(soda_url, headers=headers, json=post_json)
        assert response.status_code == 200, f'Post failed: {response.content}'
        print('Response content type:', response.headers['Content-type'], '\nPreview:', response.text[:100])
        file = StringIO(response.text)
        with raw_data_path.open('w', encoding='utf-8') as cached_data:
            cached_data.write(response.text)
    df = pd.read_csv(file)
    print(df.head(5))
    
if __name__ == '__main__':
    main()