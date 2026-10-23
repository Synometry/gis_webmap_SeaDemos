# tract_script.py
# Holden Bailey 2026

from io import StringIO
from pathlib import Path
import numpy as np
import requests as re
import pandas as pd
import geopandas as gpd

## Data Fetching

raw_data_path = Path('./cache/tractQuery.pbf')

# End-point for ArcGIS Online layer I want
arc_url = 'https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/2020_Census_Tracts_Seattle/FeatureServer/3/query'

def main():
    file = None
    if raw_data_path.exists():
        file = raw_data_path
    else:
        # u_a = 'Holden Bailey'
        headers = {
            # 'User-Agent': u_a, 
            'Accept': 'application/geo+json;charset=utf-8'
        }
        fields_str = ','.join(['GEOID20', 'GROSS_ACRES', 'LAND_ACRES', 'WATER_ACRES',
                               'GEN_ALIAS', 'DETL_NAMES'])
        post_json = {
            'where': '1=1',
            'outFields': fields_str,
            'outSR': '4326',
            'f': 'pbf'
        }
        response = re.post(arc_url, headers=headers, params=post_json)
        assert response.status_code == 200, f'Post failed: {response.content}'
        print('Response content type:', response.headers['Content-type'], '\nPreview:', response.text[:100])
        file = StringIO(response.text)
        with raw_data_path.open('w', encoding='utf-8') as cached_data:
            cached_data.write(response.text)

def convert

def upload_to_db():
    
    ...
    
if __name__ == '__main__':
    main()