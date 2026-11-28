# aggregation_script.py
# Holden Bailey 2026
#
# Script to aggregate permit data by month and year

from io import StringIO
from pathlib import Path
import numpy as np
import requests as re
import pandas as pd
import geopandas as gpd
from sqlalchemy import BigInteger, CheckConstraint, Column, CreateView, String, Table, Integer, Float, func, select
from geoalchemy2 import Geography, Geometry
from sqlalchemy.schema import CreateSchema
import sodp_data_script
from common import base_from_url, survey_data
from log import log, register
import permit_db
register('Aggregation Script')

## Data Definitions

log('Building table views')
agg_schema_name = 'agg'
create_agg_schema = CreateSchema(agg_schema_name)

m_agg_view_name = 'month_aggregated_view'
p_t = sodp_data_script.permit_table
m_agg_sel = select(
    func.count(p_t.c.permitnum).label('permitcount'),
    func.sum(p_t.c.housingunits).label('housingunits_tot'),
    func.avg(p_t.c.housingunits).label('housingunits_avg'),
    func.sum(p_t.c.housingunitsremoved).label('housingunitsremoved_tot'),
    func.avg(p_t.c.housingunitsremoved).label('housingunitsremoved_avg'),
    func.sum(p_t.c.housingunitsadded).label('housingunitsadded_tot'),
    func.avg(p_t.c.housingunitsadded).label('housingunitsadded_avg'),
    func.sum(p_t.c.estprojectcost).label('estprojectcost_tot'),
    func.avg(p_t.c.estprojectcost).label('estprojectcost_avg'),
    func.sum(p_t.c.adjestcost).label('adjestcost_tot'),
    func.avg(p_t.c.adjestcost).label('adjestcost_avg'),
    (func.sum(p_t.c.adjestcost)/func.sum(p_t.c.housingunits)).label('estcost_pernetunit'),
    (func.sum(p_t.c.adjestcost)/func.sum(p_t.c.housingunitsgross)).label('estcost_perunitgross'),
    func.format(p_t.c.monthdate, 'yyyy-MM').label('month'),
).group_by(p_t.c.monthdate).order_by(p_t.c.monthdate.asc())

create_m_agg_view = CreateView(m_agg_sel, m_agg_view_name, or_replace=True, schema=agg_schema_name)

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
      ,SUM([adjestcost])/SUM([housingunitsgross]) AS adjcost_perunitgross
      ,FORMAT([monthdate], 'yyyy-MM') AS [month]
  FROM [project_permit_db].[dbo].[seattle_permits]
  GROUP BY monthdate
  ORDER BY monthdate ASC"""

def setup_db_objects():
    log(f'Creating schema \"{agg_schema_name}\"')
    permit_db.execute(create_agg_schema)
    log(f'Creating view \"{m_agg_view_name}\"')
    permit_db.execute(create_m_agg_view)

if __name__ == '__main__':
    setup_db_objects()