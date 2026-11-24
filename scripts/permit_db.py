# permit_db.py
# Holden Bailey, 2026
# 
# An interface that allows data scripts controlled access to the project database.

import datetime
from pathlib import Path
import platform
import getpass
from typing import Union
from geopandas import GeoDataFrame, GeoSeries
import pandas as pd
from pandas import DataFrame
import sqlalchemy
from sqlalchemy import ClauseElement, Column, CursorResult, Date, DateTime, Executable, Insert, Integer, LargeBinary, MetaData, Table, Update, func, insert, select, text, inspect
from sqlalchemy.sql.functions import _FunctionGenerator
from sqlalchemy.sql.expression import Select, FunctionElement
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects import mssql
from sqlalchemy.engine import URL
import geoalchemy2.shape as shp
import log
log.register('Permit DB')

# Construct definitions

class ExecutableClause(Executable, ClauseElement):
    ...

# User-defined function block taken from example in documentation:
# https://docs.sqlalchemy.org/en/21/core/compiler.html
class GeomUnionAggregate(FunctionElement):
    name = 'geometric_union_aggregate'
    inherit_cache = True
    
@compiles(GeomUnionAggregate)
def compile_union(element, compiler, **kw):
    return 'geometry::UnionAggregate(%s)' % compiler.process(element.clauses, **kw)

class STContains(FunctionElement):
    type = Integer()
    inherit_cache = True

@compiles(STContains)
def compile_contains(element, compiler, **kw):
    col, obj = list(element.clauses)
    return '%s.STContains(%s)' % (compiler.process(col, **kw), compiler.process(obj, **kw))

## Engine construction

metadata = MetaData()

# system, platform categories
sys_cat = platform.system()
plat_cat = f'{sys_cat} {platform.release()}'
log.log(f'Building database connection engine for [{plat_cat} {platform.version()}]')

url_map = {
    'Windows 10': lambda: URL.create(
            'mssql+mssqlpython',
            host='localhost\\SQLEXPRESS',
            database='project_permit_db',
            query={
                'TrustServerCertificate':'yes',
                'Trusted_Connection':'yes'
            }
        ),
    'Linux 7.0.0-31-generic': lambda: URL.create(
            'mssql+mssqlpython',
            host='localhost',
            username='sa',
            password=getpass.getpass('Password (not logged): '),
            database='project_permit_db',
            query={
                'TrustServerCertificate':'yes',
                'Authentication':'SqlPassword'
            }
        ),
}
if plat_cat in url_map.keys(): _connect_url = url_map[plat_cat]()
else:
    log.log(f'Couldn\'t find URL creator for {plat_cat} - trying generic system \"{sys_cat}\"')
    for k, v in url_map.items():
        if sys_cat in k:
            _connect_url = v()

_engine = sqlalchemy.create_engine(_connect_url)

log.log('Engine created - testing engine...')

try:
    with _engine.begin() as connection:
        connection.execute(text('SELECT 1'))
except Exception as e:
    log.error(f'Connection failed: {e}')
    raise

log.log('Engine connection test passed')

def table_exists(table: Table) -> bool: return inspect(_engine).has_table(table.name)

def create_table(table_schema: Table):
    log.log(f'Creating table \"{table_schema.name}\"')
    if table_exists(table_schema):
        log.log(f'Table \"{table_schema.name}\" already exists. Dropping for replacement...')
        table_schema.drop(bind=_engine)
    metadata.create_all(_engine, tables=[table_schema])
    if table_exists(table_schema):
        log.log(f'Table \"{table_schema.name}\" created')
    else:
        log.log(f'Table creation unsuccessful!')

def table_to_dataframe(table_schema: Table, index_col: str | None = None) -> DataFrame:
    log.log(f'Fetching table \"{table_schema.name}\" as {DataFrame}')
    if not table_exists(table_schema):
        log.error(f'Fetching failed! No such table named \"{table_schema.name}\"')
        raise ValueError(f'No such table named \"{table_schema.name}\" in database!')
    return pd.read_sql_table(table_schema.name, _engine, index_col=index_col)

def dataframe_to_table(df:DataFrame, table_name:str) -> None:
    log.log(f'Inserting data into database table \"{table_name}\"')
    df.to_sql(table_name, _engine, if_exists='delete_rows', index=False)
    log.log('Insert complete')

def geodataframe_to_table(gdf:GeoDataFrame, table_schema:Table) -> None:
    log.log(f'Beginning insertion of GeoDataFrame into table \"{table_schema.name}\"...')
    table_name = table_schema.name
    temp_table_name = table_name + '_temp'
    invalids = ~gdf.geometry.is_valid
    gdf.loc[invalids, 'geometry'] = gdf.loc[invalids, 'geometry'].make_valid()
    gdf['geom_wkb'] = gdf.geometry.to_wkb()
    log.log(f'Inserting data into temporary table \"{temp_table_name}\"')
    gdf.drop(columns='geometry')\
        .to_sql(temp_table_name, _engine, if_exists='delete_rows', index=False, dtype={'geom_wkb':LargeBinary})
    col_names = ', '.join([f'{c}' for c in gdf.columns if not c in ['geometry', 'geom_wkb']])
    table_delete_all_rows(table_schema)
    log.log(f'Converting geometry and moving data into table \"{table_schema}\"')
    with _engine.begin() as conn:
        conn.execute(text(\
            f'INSERT INTO {table_name} ({col_names}, [geometry]) '
            f'SELECT {col_names}, geometry::STGeomFromWKB(geom_wkb, 4326).MakeValid() '
            f'FROM {temp_table_name}'
            ))
    log.log(f'Dropping temporary table')
    Table(temp_table_name, metadata, autoload_with=_engine).drop(bind=_engine)
    log.log('Insertion complete')

def table_to_geodataframe(table_schema: Table, index_col: str | None = None) -> GeoDataFrame:
    log.log(f'Fetching table \"{table_schema.name}\" as {GeoDataFrame}')
    if not table_exists(table_schema):
        e = ValueError(f'No such table named \"{table_schema.name}\" in database!')
        log.error(f'Fetching failed: {e}')
        raise e
    df = pd.read_sql_table(table_schema.name, _engine, index_col)
    gseries = GeoSeries([shp.to_shape(geom) for geom in df['geometry']], df.index)
    gdf = GeoDataFrame(df, geometry=gseries)
    return gdf

# I expect to not use this
def table_delete_all_rows(table_schema: Table) -> None:
    log.log(f'Deleting all rows of table \"{table_schema}\"')
    if type(table_schema) is not Table:
        e = TypeError(f'Parameter \'table_schema\': expected type {Table}, got type {type(table_schema)} instead')
        log.error(e)
        raise e
    try:
        with _engine.begin() as conn:
            #https://learn.microsoft.com/en-us/sql/t-sql/statements/truncate-table-transact-sql?view=sql-server-ver17
            # ^^^ TRUNCATE is faster and cheaper than DELETE
            name = str(table_schema.name)
            conn.execute(text(f'TRUNCATE TABLE {name}'))
    except Exception as e:
        log.error(f'Delete all rows failed: {e}')
        raise

# ╭────────────╮
# │ PROCESSING │
# ╰────────────╯

def execute(statement: Update | Select | Insert) -> DataFrame | None:
    comp = statement.compile(_engine, compile_kwargs={'literal_binds': True})
    log.log(f'Executing freeform SQLAlchemy statement:\n\"{comp}\"')
    try:
        with _engine.begin() as conn:
            res = conn.execute(statement)
            msg = f'Statement execution succeeded'
            if res.returns_rows:
                df = pd.DataFrame(res)
                msg += ' - returning rows'
            else: df = None
            log.log(msg)
        return df
    except Exception as e:
        log.error(f'Statement execution failed: {e}')
        raise
    ...

def spatial_union(table_schema: Table, target_table: Table, groupby: Column | None = None, aggregates: list[tuple[Column, _FunctionGenerator, Column]] | None = None) -> None:
    # Type errors:
    if not isinstance(table_schema, Table):
        # try this out
        log.error(f'TypeError: table_schema: expected {Table} but received {type(table_schema)}')
        raise TypeError(f'table_schema: expected {Table} but received {type(table_schema)}')
    if not isinstance(target_table, Table): raise TypeError(f'table_schema: expected {Table} but received {type(target_table)}')
    if not isinstance(groupby, Column): raise TypeError(f'table_schema: expected {Column} but received {type(Column)}')
    if not (isinstance(aggregates, list) and
            all(isinstance(t, tuple) for t in aggregates) and
            all(len(t) == 3 and
                isinstance(t[0], Column) and
                isinstance(t[1], _FunctionGenerator) and
                isinstance(t[2], Column) for t in aggregates)):
        raise TypeError(f'table_schema: expected {list[tuple[Column, _FunctionGenerator, Column]]} but received {type(table_schema)}')
    
    # Value constraints:
    # table_schema has a 'geometry' column
    if not any(c.name == 'geometry' for c in table_schema.c):
        raise ValueError(f'Missing column: table \"{table_schema.name}\" passed as table_schema lacks a column named \"geometry\"')
    # target_table has a 'geometry' column
    if not any(c.name == 'geometry' for c in target_table.c):
        raise ValueError(f'Missing column: table \"{target_table.name}\" passed as target_table lacks a column named \"geometry\"')
    # groupby is in table_schema
    if groupby is not None and not groupby.table == table_schema:
        raise ValueError(f'Nonexistant column: groupby column \"{groupby.name}\" is not a column of table_schema \"{table_schema.name}\"')
    if aggregates is not None:
        for t in aggregates:
            # aggregates[0] are columns in table_schema
            if t[0].table != table_schema: raise ValueError(f'Nonexistant column: aggregating column \"{t[0].name}\" doesn\'t exist in table_schema \"{table_schema.name}\"')
            # aggregates[2] are columns in target_table
            if t[2].table != target_table: raise ValueError(f'Nonexistant column: target column \"{t[2].name}\" doesn\'t exist in table_schema \"{target_table.name}\"')
            
    sel: Select = select(
        groupby,
        *[t[1](t[0]) for t in aggregates],
        GeomUnionAggregate(table_schema.c.geometry)
    )
    sel = sel.group_by(groupby)
    ins = insert(target_table).from_select(
        [groupby.name] + [t[2].name for t in aggregates] + ['geometry'],
        sel
    )
    try:
        with _engine.begin() as conn:
            conn.execute(ins)
    except Exception as e:
        log.error(f'Spatial union failed: {e}')
        raise
    log.log('Spatial union complete')
    
def month_id(table_schema: Table, date_col: Column) -> None:
    if not isinstance(table_schema, Table):
        e = TypeError(f'table_schema: expected {Table} but received {type(table_schema)}')
        log.error(e)
        raise e
    if not isinstance(date_col, Column):
        e = TypeError(f'date_col: expected {Column} but received {type(date_col)}')
        log.error(e)
        raise e
    if not isinstance(date_col.type, (Date, DateTime)):
        e = ValueError(f'date_col: expected a column with date-like type, but received a column with type {type(date_col.type)}')
        log.error(e)
        raise e
    with _engine.begin() as conn:
        sel = select(func.concat(func.year()))

# ╭─────────╮
# │ EXPORTS │
# ╰─────────╯

def download_as_geojson(table_schema: Table, target_path: Path) -> None:
    log.log(f'Downloading from table \"{table_schema}\" to \"{target_path}\"')
    gdf = table_to_geodataframe(table_schema)
    target_path.write_text(gdf.to_json())
    log.log(f'Data written to \"{target_path}\"')
    ...