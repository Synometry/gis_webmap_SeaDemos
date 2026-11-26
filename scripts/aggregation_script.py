# aggregation_script.py
# Holden Bailey 2026
#
# Script to aggregate permit data by year

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
register('Aggregation Script')

## Data Definitions

log('Building table schema')

t_name_m_aggs = 'monthly_aggregates'

m_agg_table = Table(
    t_name_m_aggs,
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

def reset_tables():
    tables = [m_agg_table]
    log('Submitting table schemata for reset:', ', '.join([f'\"{t.name}\"' for t in tables]))
    [permit_db.create_table(table) for table in tables]

"""SQL
SELECT TOP (1000) COUNT([permitnum]) AS permitcount
      ,SUM([housingunits]) AS housingunits_tot
      ,AVG(CAST([housingunits] AS FLOAT)) AS housingunits_avg
      ,SUM([housingunitsremoved]) AS housingunitsremoved_tot
      ,AVG(CAST([housingunitsremoved] AS FLOAT)) AS housingunitsremoved_avg
      ,SUM([housingunitsadded]) AS housingunitsadded_tot
      ,AVG(CAST([housingunitsadded] AS FLOAT)) AS housingunitsadded_avg
      ,SUM([estprojectcost]) AS estprojectcost_tot
      ,AVG([estprojectcost]) AS estprojectcost_avg
      ,SUM([adjestcost]) AS adjestcost_tot
      ,AVG([adjestcost]) AS adjestcost_avg
      ,SUM([estprojectcost])/SUM([housingunits]) AS estcost_pernetunit
      ,SUM([estprojectcost])/SUM([housingunitsgross]) AS estcost_pergrossunit
      ,SUM([adjestcost])/SUM([housingunits]) AS adjcost_pernetunit
      ,SUM([adjestcost])/SUM([housingunitsgross]) AS adjcost_pergrossunit
      ,FORMAT([monthdate], 'yyyy-MM') AS [month]
  FROM [project_permit_db].[dbo].[seattle_permits]
  GROUP BY monthdate
  ORDER BY monthdate ASC"""