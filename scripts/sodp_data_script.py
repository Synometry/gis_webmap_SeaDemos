# Holden Bailey 2026

from io import StringIO, FileIO
from pathlib import Path
from geoalchemy2 import Geometry
import numpy as np
import requests as re
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from sqlalchemy import BigInteger, Column, Float, Integer, SmallInteger, String, Table, Date
from log import log, register, error
import permit_db
register('SODP Data Script')

## Data Definitions

log('Building table schema')

t_name_permits = 'seattle_permits'

# Types intentionally chosen based on ranges of the dataset
permit_table = Table(
    t_name_permits,
    permit_db.metadata,
    Column('permitnum',             String(10), primary_key=True),
    Column('permitclass',           String(20)),
    Column('permittypedesc',        String(36)),
    Column('description',           String(500)),
    Column('housingunits',          SmallInteger),
    Column('housingunitsremoved',   SmallInteger),
    Column('housingunitsadded',     SmallInteger),
    Column('estprojectcost',        Float),
    Column('applieddate',           Date),
    Column('issueddate',            Date),
    Column('expiresdate',           Date),
    Column('completeddate',         Date),
    Column('statuscurrent',         String(21)),
    Column('originaladdress1',      String(32)),
    Column('originalzip',           Integer),
    Column('contractorcompanyname', String(44)),
    Column('link',                  String(80)),
    Column('zoning',                String(25)),
    Column('dwellingunittype',      String(87)),
    Column('housingcategory',       String(23)),
    Column('geometry', Geometry(geometry_type='POINT', srid=4326))
)
# Omitting CheckConstraint under assumption there's no way to screw up a point

def reset_tables():
    log(f'Resetting table \"{permit_table}\"')
    permit_db.create_table(permit_table)

## Data Fetching

raw_data_path = Path('./cache/permitQuery.csv')

# End-point for SODA V3
# soda_url = 'https://data.seattle.gov/api/v3/views/76t5-zqzr/query.csv'
# End-point for SODA V2.1 (no auth required)
soda_url = 'https://data.seattle.gov/resource/76t5-zqzr.csv'

def fetch_data():
    log('Beginning to fetch permit data')
    if not raw_data_path.exists():
        log(f'Cached data not found - downloading from {soda_url}')
        headers = {
            'Accept': 'text/csv;charset=utf-8'
        }
        # SoQL query template
        query = '''SELECT {selectee} WHERE \
            caseless_one_of(permitclassmapped, "residential") AND \
            caseless_one_of(permittypemapped, "building") AND \
            issueddate BETWEEN "2005-01-01T00:00:00" and "2025-12-31T23:59:59" AND \
            caseless_one_of(statuscurrent, "approved to occupy", "completed", "inspections completed", "issued", "phase issued") AND \
            NOT caseless_starts_with(description, "closed as incomplete") AND \
            (housingunitsremoved IS NOT NULL OR housingunitsadded IS NOT NULL) AND \
            NOT (housingunitsremoved == 0 AND housingunitsadded == 0) AND \
            parentpermitnum IS NULL \
            LIMIT {limit}'''
        # Getting row count for limit
        parameters = {
            '$query':query.format(selectee='COUNT(*)', limit='1')
        }
        log('Sending GET request for row count...')
        response = re.get(soda_url, headers=headers, params=parameters)
        if response.status_code != 200:
            error(f'GET failed, response code {response.status_code}: {response.content}')
            return
        log(f'Response code 200: {response.text.replace('\n', '')}')
        limit = (int(response.text.splitlines()[1].replace('\"', '')) // 1000 + 1) * 1000
        log(f'Limit set to: {limit}')
        # Getting data
        fields_str = ', '.join(['permitnum', 'permitclass', 'permittypedesc', 'description', 
                    'housingunits', 'housingunitsremoved', 'housingunitsadded',
                    'estprojectcost', 'applieddate', 'issueddate', 'expiresdate',
                    'completeddate', 'statuscurrent', 'originaladdress1', 'originalzip',
                    'contractorcompanyname', 'link', 'latitude', 'longitude', 'zoning',
                    'dwellingunittype', 'housingcategory'])
        parameters = {
            '$query':query.format(selectee=fields_str, limit=limit)
        }
        log('Sending GET request for data...')
        response = re.get(soda_url, headers=headers, params=parameters)
        if response.status_code != 200:
            error(f'GET failed, response code {response.status_code}: {response.content}')
            return
        log(f'Response code 200: {response.text.replace('\n', '')[:200]}')
        log(f'Writing data to cache...')
        with raw_data_path.open('w', encoding='utf-8') as cached_data:
            cached_data.write(response.text)
        log(f'Cached file: {raw_data_path}')
    else: log('Found cached data!')

def upload_to_db():
    log('Moving permit data to database')
    df = pd.read_csv(raw_data_path)
    gseries = df[['latitude', 'longitude']].apply(lambda row: Point(row['latitude'], row['longitude']), axis=1)
    invalid = df[~gpd.GeoSeries(gseries).is_valid]
    # Those are invalid points. Have 'nan, nan' as coords. Find out why.
    return
    gdf = gpd.GeoDataFrame(df.drop(columns=['latitude', 'longitude']), geometry=gseries)
    log(f'Entries in data prior to upload: {len(gdf)}', '\nPreview:\n', gdf.head(5))
    log('Uploading to database...')
    permit_db.geodataframe_to_table(gdf, permit_table)
    log('Verifying data in database...')
    gdf = permit_db.table_to_geodataframe(permit_table)
    log(f'Entries in database data: {len(gdf)}', '\nPreview:\n', gdf.head(5))

def data_peeker():
    log('Surveying columns in permit data:')
    df = pd.read_csv(raw_data_path)
    namelist = ['name:']
    typelist = ['type:']
    maxlist = ['maximum:']
    uniquelist = ['unique:']
    for (c, t) in zip(df.columns, df.dtypes):
        namelist.append(c)
        typelist.append(t)
        uniquelist.append(df[c].is_unique)
        if isinstance(t, pd.StringDtype):
            maxlist.append(np.max(df[c].str.len()))
        else:
            maxlist.append(np.max(df[c]))
    log(namelist, typelist, maxlist, uniquelist)
    ...
    
if __name__ == '__main__':
    reset_tables()
    fetch_data()
    # data_peeker()
    upload_to_db()