# processing_scripts.py
# Holden Bailey 2026
#
# A group of scripts for processing data in the sql server

import permit_db
from sqlalchemy import func, select, insert, update, case
import sodp_data_script
import tract_data_script
import bls_data_script
from log import log, error, register
register()

def calculate_adj_est():
    
    perm_table = sodp_data_script.permit_table
    iss_date_col = perm_table.c.issueddate
    est_cost_col = perm_table.c.estprojectcost
    adj_est_col = perm_table.c.adjestcost
    
    log(f'Calculating column \"{adj_est_col.name}\" of table \"{perm_table}\"')
    
    infl_table = bls_data_script.inflation_table
    monthid_col = infl_table.c.month_id
    factor_col = infl_table.c.factor
    
    cond = func.concat(func.year(iss_date_col), func.FORMAT(func.month(iss_date_col), '00')) == monthid_col

    upd = update(perm_table).where(cond).values(adjestcost=est_cost_col * factor_col)
    
    log('Applying inflation factors to estimated costs...')
    permit_db.execute(upd)
    log(f'Completed calculation of column \"{adj_est_col.name}\"')

# Determine the ids of the polygons that a permit point falls within
def permit_poly_ids():
    # Stage 1.1 -- attach geoid20's to contained permits
    # Draws from correlated subquery example:
    # https://docs.sqlalchemy.org/en/20/tutorial/data_update.html#correlated-updates
    """SQL
    UPDATE seattle_permits
    SET tractid = (
        SELECT TOP 1 census_tracts.geoid20
        FROM census_tracts
        WHERE census_tracts.geometry.STContains(seattle_permits.geometry) = 1
    )
    """
    perm_table = sodp_data_script.permit_table
    log(f'Calculating point-in-polygon fields for \"{perm_table}\"')
    geom_col = perm_table.c.geometry
    
    tract_table = tract_data_script.tract_table
    tract_geom_col = tract_table.c.geometry
    tract_id_col = tract_table.c.geoid20
    
    cond1 = permit_db.STContains(tract_geom_col, geom_col) == 1
    
    subq1 = select(tract_id_col).where(cond1).limit(1).scalar_subquery()
    
    upd1 = update(perm_table).values(tractid = subq1)
    
    log(f'Calculating id of containing tract (field \"{perm_table.c.tractid}\")')
    permit_db.execute(upd1)
    
    # Stage 1.2 -- set outside to TRUE if tactid is NULL
    """SQL
    UPDATE seattle_permits
    SET outside = CASE WHEN tractid IS NULL THEN ! ELSE 0
    """
    perm_tractid_col = perm_table.c.tractid
    
    upd2 = update(perm_table).values(outside=case((perm_tractid_col.is_(None), 1), else_=0))
    
    log(f'Assigning \"outside\" status (field \"{perm_table.c.outside}\")')
    permit_db.execute(upd2)
    
    # Stage 2 -- attach geoid20's of nearest tracts to permits
    """SQL
    UPDATE seattle_permits
    SET tractid = (
        SELECT TOP 1 census_tracts.geoid20
        FROM census_tracts
        ORDER BY seattle_permits.geometry.STDistance(census_tracts.geometry) ASC
    )
    WHERE tractid IS NULL
    """
    cond3 = perm_tractid_col.is_(None)
    
    subq3 = select(tract_id_col).order_by(permit_db.STDistance(tract_geom_col, geom_col).asc()).limit(1).scalar_subquery()
    
    upd3 = update(perm_table).where(cond3).values(tractid = subq3)
    
    log(f'Calculating id of nearest tract (field \"{perm_table.c.tractid}\")')
    permit_db.execute(upd3)

    # Stage 3 -- use permit's tractid to find its cra
    """SQL
    UPDATE seattle_permits
    SET craid = (
        SELECT TOP 1 reporting_areas.geoid20
        FROM census_tracts, reporting_areas
        WHERE seattle_permits.tractid = census_tracts.geoid20 AND census_tracts.gen_alias = reporting_areas.gen_alias
    )
    """
    tract_alias_col = tract_table.c.gen_alias
    cra_table = tract_data_script.cra_table
    cra_id_col = cra_table.c.geoid20
    cra_alias_col = cra_table.c.gen_alias
    
    subq4 = select(cra_id_col).where(perm_tractid_col == tract_id_col, tract_alias_col == cra_alias_col).limit(1).scalar_subquery()
    
    upd4 = update(perm_table).values(craid = subq4)
    
    log(f'Calculating id of associated cra (field \"{perm_table.c.craid}\")')
    permit_db.execute(upd4)
    log(f'Completed point-in-polygon calculations')
    

if __name__ == '__main__':
    calculate_adj_est()
    permit_poly_ids()