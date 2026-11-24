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
from common import base_from_url, survey_data
from log import log, register
import permit_db
register('Tract Data Script')

## Data Definitions

log('Building table schemata')

t_name_tracts = 'census_tracts'

tract_table = Table(
    t_name_tracts,
    permit_db.metadata,
    Column('geoid20', BigInteger, primary_key=True, autoincrement=False),
    Column('gross_acres', Float),
    Column('land_acres', Float),
    Column('water_acres', Float),
    Column('gen_alias', String(37)),
    Column('detl_names', String(114)),
    Column('geometry', Geometry(geometry_type='GEOMETRY', srid=4326)),
    CheckConstraint('geometry.STIsValid() = 1')
)
    
t_name_cra = 'reporting_areas'

cra_table = Table(
    t_name_cra,
    permit_db.metadata,
    Column('gen_alias', String(37)),
    Column('geoid20', BigInteger, primary_key=True, autoincrement=False),
    Column('gross_acres', Float),
    Column('land_acres', Float),
    Column('water_acres', Float),
    Column('geometry', Geometry(geometry_type='GEOMETRY', srid=4326)),
    CheckConstraint('geometry.STIsValid() = 1')
)

def reset_tables():
    tables = [cra_table, tract_table]
    log('Submitting table schemata for reset:', ', '.join([f'\"{t.name}\"' for t in tables]))
    [permit_db.create_table(table) for table in tables]
    
## Data Fetching

cache_dir = Path('./cache/')
raw_data_path = cache_dir / Path('tractQuery.geojson')

ext_data_dir = Path('./ext_data/')
out_tracts_path = ext_data_dir / Path('seattle_tracts.geojson')
out_cras_path = ext_data_dir / Path('seattle_cras.geojson')

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
        log('Sending POST request...')
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
        (tract_table.c.geoid20, func.min, cra_table.c.geoid20),
        (tract_table.c.gross_acres, func.sum, cra_table.c.gross_acres),
        (tract_table.c.land_acres, func.sum, cra_table.c.land_acres),
        (tract_table.c.water_acres, func.sum, cra_table.c.water_acres)
    ])
    permit_db.spatial_union(tract_table, cra_table, tract_table.c.gen_alias, agg)
    
def eval_acre_figs():
    log('Evaluating land measurement errors...')
    gdf = gpd.read_file(raw_data_path)
    gdf['error'] = gdf['GROSS_ACRES'] - (gdf['LAND_ACRES'] + gdf['WATER_ACRES'])
    gdf['acreage'] = gdf.to_crs('2926').geometry.area / 43560 # Ft/Acre
    gdf['error2'] = gdf['GROSS_ACRES'] - gdf['acreage']
    log(gdf.drop(columns=['DETL_NAMES', 'GEOID20']).sort_values('error'))
    log(gdf['error2'].describe())

def peek_data():
    gdf = gpd.read_file(raw_data_path)
    survey_data(gdf.drop(columns=['geometry']))
    ...

if __name__ == '__main__':
    # reset_tables()
    # fetch_data()
    # eval_acre_figs()
    peek_data()
    # upload_to_db()
    # dissolve_tracts()
    