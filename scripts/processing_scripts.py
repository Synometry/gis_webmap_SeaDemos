# processing_scripts.py
# Holden Bailey 2026
#
# A group of scripts for processing data in the sql server

import permit_db
from sqlalchemy import func, select, insert, update
import sodp_data_script
import bls_data_script
from log import log, error, register
register()

def calculate_adj_est():
    
    perm_table = sodp_data_script.permit_table
    app_date_col = perm_table.c.applieddate
    est_cost_col = perm_table.c.estprojectcost
    adj_est_col = perm_table.c.adjestcost
    
    log(f'Calculating column \"{adj_est_col.name}\" of table \"{perm_table}\"')
    
    infl_table = bls_data_script.inflation_table
    monthid_col = infl_table.c.month_id
    factor_col = infl_table.c.factor
    
    join_con = func.concat(func.year(app_date_col), func.FORMAT(func.month(app_date_col), '00')) == monthid_col

    upd = update(perm_table).where(join_con).values(adjestcost=est_cost_col * factor_col)
    
    log('Applying inflation factors to estimated costs...')
    permit_db.execute(upd)
    log(f'Completed calculation of column \"{adj_est_col.name}\"')
    
if __name__ == '__main__':
    calculate_adj_est()