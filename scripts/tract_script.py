# tract_script.py
# Holden Bailey 2026

from io import StringIO
from pathlib import Path
import numpy as np
import requests as re
import pandas as pd
import geopandas as gpd
from sqlalchemy import BigInteger, CheckConstraint, Column, String, Table, Integer, Float
from geoalchemy2 import Geography, Geometry
import permit_db

## Data Definitions

t_name = 'census_tracts'

tract_table = Table(
    t_name,
    permit_db.metadata,
    Column('geoid20', BigInteger, primary_key=True, autoincrement=False),
    Column('gross_acres', Float),
    Column('land_acres', Float),
    Column('water_acres', Float),
    Column('gen_alias', String(63)),
    Column('detl_names', String(127)),
    Column('geometry', Geometry(geometry_type='GEOMETRY', srid=4326)),
    CheckConstraint('geometry.STIsValid() = 1')
)
    
permit_db.create_table(tract_table)

## Data Fetching

raw_data_path = Path('./cache/tractQuery.geojson')

# End-point for ArcGIS Online layer I want
arc_url = 'https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/2020_Census_Tracts_Seattle/FeatureServer/3/query'

def fetch_data():
    if not raw_data_path.exists():
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
            'f': 'geojson'
        }
        response = re.post(arc_url, headers=headers, params=post_json)
        assert response.status_code == 200, f'Post failed: {response.content}'
        print('Response content type:', response.headers['Content-type'], '\nPreview:', response.text[:100])
        with raw_data_path.open('w', encoding='utf-8') as cached_data:
            cached_data.write(response.text)

def upload_to_db():
    gdf = gpd.read_file(raw_data_path)
    permit_db.geodataframe_to_table(gdf, tract_table)
    
if __name__ == '__main__':
    fetch_data()
    upload_to_db()