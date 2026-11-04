# Holden Bailey, 2026

from pathlib import Path
from geopandas import GeoDataFrame
import pandas as pd
from pandas import DataFrame
import sqlalchemy
from sqlalchemy import LargeBinary, MetaData, Table, select, text, inspect
from sqlalchemy.engine import URL

metadata = MetaData()

_connect_url = URL.create(
    'mssql+mssqlpython',
    host='localhost\\SQLEXPRESS',
    database='project_permit_db',
    query={
        'TrustServerCertificate':'yes',
        'Trusted_Connection':'yes'
    }
)

_engine = sqlalchemy.create_engine(_connect_url)

def create_table(table_schema: Table):
    print(table_schema.name)
    if inspect(_engine).has_table(table_schema.name): table_schema.drop(bind=_engine)
    metadata.create_all(_engine, tables=[table_schema])

def table_to_dataframe(table_type, index_col: str | None = None) -> DataFrame:
    return pd.read_sql_table(table_type.__tablename__, _engine, index_col=index_col)

def dataframe_to_table(df:DataFrame, table_name:str) -> None:
    df.to_sql(table_name, _engine, if_exists='delete_rows', index=False)

def geodataframe_to_table(gdf:GeoDataFrame, table_schema:Table) -> None:
    table_name = str(table_schema.name)
    temp_table_name = table_name + '_temp'
    gdf['geom_wkb'] = gdf.geometry.make_valid().to_wkb()
    gdf.drop(columns='geometry')\
        .to_sql(temp_table_name, _engine, if_exists='delete_rows', index=False, dtype={'geom_wkb':LargeBinary})
    col_names = ', '.join([f'{c}' for c in gdf.columns if not c in ['geometry', 'geom_wkb']])
    with _engine.begin() as conn:
        conn.execute(text(\
            f'INSERT INTO {table_name} ({col_names}, [geometry]) '
            f'SELECT {col_names}, geometry::STGeomFromWKB(geom_wkb, 4326).MakeValid() '
            f'FROM {temp_table_name}'
            ))
    Table(temp_table_name, metadata, autoload_with=_engine).drop(bind=_engine)

# I expect to not use this
def table_delete_all_rows(table_schema: Table) -> None:
    if type(table_schema) is not Table: raise TypeError(f'Parameter \'table_schema\': expected type {Table}, got type {type(table_schema)} instead')
    with _engine.begin() as conn:
        #https://learn.microsoft.com/en-us/sql/t-sql/statements/truncate-table-transact-sql?view=sql-server-ver17
        # ^^^ TRUNCATE is faster and cheaper than DELETE
        name = str(table_schema.name)
        conn.execute(text(f'TRUNCATE TABLE {name}'))
    ...

# Example:

# class DummyTable(TableBase):
#     __tablename__ = 'dummy_table'
    
#     id : Mapped[int] = mapped_column(primary_key=True)
#     val1 : Mapped[float]
#     val2 : Mapped[str] = mapped_column(sqlalchemy.String(30))
    
#     def __repr__(self) -> str:
#         return 'DummyEntry(' + ', '.join([f'{x}={self.__dict__[x]!r}' for x in ['id', 'val1', 'val2']]) + ')'

# create_table(DummyTable)