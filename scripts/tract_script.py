# tract_script.py
# Holden Bailey 2026

from io import StringIO
from pathlib import Path
import numpy as np
import requests as re
import pandas as pd
import geopandas as gpd
from sqlalchemy import CheckConstraint, Column, String, Table, Integer, Float
import permit_db

## Data Definitions

t_name = 'census_tracts'

tract_table = Table(
    t_name,
    permit_db.metadata,
    Column('geoid20', Integer, primary_key=True, autoincrement=False),
    Column('gross_acres', Float),
    Column('land_acres', Float),
    Column('water_acres', Float),
    Column('gen_alias', String(63)),
    Column('detl_names', String(127)),
    Column('geometry', ),
    CheckConstraint('geometry.STIsValid() = 1')
)

class CensusTracts(permit_db.TableBase):
    __tablename__ = t_name
    
    geoid20 : Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    gross_acres : Mapped[float]
    land_acres : Mapped[float]
    water_acres : Mapped[float]
    gen_alias : Mapped[str] = mapped_column(String(63))
    detl_names : Mapped[str] = mapped_column(String(127))
    
    def __repr__(self):
        return 'CensusTract('+', '.join([f'{x}:{self.__dict__[x]!r}' for x in ['geoid20', 'gross_acres', 'land_acres', 'water_acres',
                               'gen_alias', 'detl_names']])+')'
    
permit_db.create_table(CensusTracts)

## Data Fetching

raw_data_path = Path('./cache/tractQuery.geojson')

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
            'f': 'geojson'
        }
        response = re.post(arc_url, headers=headers, params=post_json)
        assert response.status_code == 200, f'Post failed: {response.content}'
        print('Response content type:', response.headers['Content-type'], '\nPreview:', response.text[:100])
        file = StringIO(response.text)
        with raw_data_path.open('w', encoding='utf-8') as cached_data:
            cached_data.write(response.text)

def upload_to_db():
    gdf = gpd.read_file(raw_data_path)
    gdf['geometry'] = gdf.geometry.make_valid()
    
    df = pd.DataFrame(gdf.drop(columns=['geometry']))
    df['geometry'] = gdf.geometry.to_wkb()
    
    ...
    
if __name__ == '__main__':
    main()