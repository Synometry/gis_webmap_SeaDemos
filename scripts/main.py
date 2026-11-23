# main.py
# Holden Bailey 2026
#
# Calls each dataset-specific script in sequence

import permit_db
import config
import tract_data_script
import sodp_data_script
import bls_data_script

def main():
    tract_data_script.reset_tables()
    tract_data_script.fetch_data()
    tract_data_script.upload_to_db()
    tract_data_script.dissolve_tracts()
    permit_db.download_as_geojson(tract_data_script.tract_table, config.dir_external_data()/'seattle_tracts.geojson')
    permit_db.download_as_geojson(tract_data_script.cra_table, config.dir_external_data()/'seattle_cras.geojson')
    bls_data_script.reset_tables()
    bls_data_script.fetch_data()
    bls_data_script.upload_to_db()
    sodp_data_script.reset_tables()
    sodp_data_script.fetch_data()
    sodp_data_script.upload_to_db()

if __name__ == '__main__':
    main()