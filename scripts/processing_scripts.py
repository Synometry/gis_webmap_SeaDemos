# processing_scripts.py
# Holden Bailey 2026
#
# A group of scripts for processing data in the sql server

import permit_db
from sqlalchemy import func, select, insert, update
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
    perm_table = sodp_data_script.permit_table
    geom_col = perm_table.c.geometry
    
    tract_table = tract_data_script.tract_table
    tract_geom_col = tract_table.c.geometry
    tract_id_col = tract_table.c.geoid20
    
    cond1 = permit_db.STContains(tract_geom_col, geom_col) == 1
    
    upd1 = update(perm_table).where(cond1).values(tractid = tract_id_col)
    
    permit_db.execute(upd1)
    
    # Stage 1.2 -- set outside to TRUE if tactid is NULL
    """SQL
    UPDATE seattle_permits
    SET outside = CASE WHEN tractid IS NULL THEN ! ELSE 0
    """
    tractid_col = perm_table.c.tractid
    
    upd2 = update(perm_table).values(outside=tractid_col.is_(None))
    
    permit_db.execute(upd2)

if __name__ == '__main__':
    # calculate_adj_est()
    permit_poly_ids()