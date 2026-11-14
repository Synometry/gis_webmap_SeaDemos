# tract_data_script.py
# Holden Bailey 2026

from io import StringIO
from pathlib import Path
import numpy as np
import requests as re
import pandas as pd
import geopandas as gpd
from sqlalchemy import BigInteger, CheckConstraint, Column, String, Table, Integer, Float, func
from geoalchemy2 import Geography, Geometry
from common import base_from_url
from log import log, register
import permit_db

register('Tract Data Script')

## Data Definitions

log('Building & submitting table schema')

t_name_tracts = 'census_tracts'

tract_table = Table(
    t_name_tracts,
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

t_name_regions = 'tract_regions'

region_table = Table(
    t_name_regions,
    permit_db.metadata,
    Column('gen_alias', String(63)),
    Column('geoid20', BigInteger, primary_key=True, autoincrement=False),
    Column('gross_acres', Float),
    Column('land_acres', Float),
    Column('water_acres', Float),
    Column('geometry', Geometry(geometry_type='GEOMETRY', srid=4326)),
    CheckConstraint('geometry.STIsValid() = 1')
)

permit_db.create_table(region_table)

## Data Fetching

raw_data_path = Path('./cache/tractQuery.geojson')

# End-point for ArcGIS Online layer I want
arc_url = 'https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/2020_Census_Tracts_Seattle/FeatureServer/3/query'

def fetch_data():
    log('Beginning to fetch census tract data')
    if not raw_data_path.exists():
        log(f'Cached data not found - downloading from {base_from_url(arc_url)}')
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
        log('Submitting POST request...')
        response = re.post(arc_url, headers=headers, params=post_json)
        log(f'Response code {response.status_code}')
        if response.status_code != 200:
            log(f'Post failed: {response.content}')
            exit(1)
        log('Response content type:', response.headers['Content-type'])
        log('Preview:', response.text[:50])
        with raw_data_path.open('w', encoding='utf-8') as cached_data:
            cached_data.write(response.text)
        log(f'Wrote response data to cache @ \"{raw_data_path}\"')
    else: log('Found cached data!')

def upload_to_db():
    log('Moving tract data to database')
    gdf = gpd.read_file(raw_data_path)
    log(f'Entries in data prior to upload: {len(gdf)}', '\nPreview:\n', gdf.head(5))
    log('Uploading to database...')
    permit_db.geodataframe_to_table(gdf, tract_table)
    log('Verifying data in database...')
    gdf = permit_db.table_to_geodataframe(tract_table)
    log(f'Entries in database data: {len(gdf)}', '\nPreview:\n', gdf.head(5))
    
def dissolve_tracts():
    agg = ([
        (tract_table.c.geoid20, func.min, region_table.c.geoid20),
        (tract_table.c.gross_acres, func.sum, region_table.c.gross_acres),
        (tract_table.c.land_acres, func.sum, region_table.c.land_acres),
        (tract_table.c.water_acres, func.sum, region_table.c.water_acres)
    ])
    permit_db.spatial_union(tract_table, region_table, tract_table.c.gen_alias, agg)
    
if __name__ == '__main__':
    fetch_data()
    upload_to_db()
    dissolve_tracts()