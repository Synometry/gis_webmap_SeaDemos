# main.py
# Holden Bailey 2026
#
# Calls each dataset-specific script in sequence

import permit_db
import config
import tract_data_script
import sodp_data_script
import bls_data_script
import processing_scripts

def main():
    # Data acquisition
    # - Census tracts
    tract_data_script.reset_tables()
    tract_data_script.fetch_data()
    tract_data_script.upload_to_db()
    # - CRAs
    tract_data_script.dissolve_tracts()
    # - Inflation factors
    bls_data_script.reset_tables()
    bls_data_script.fetch_data()
    bls_data_script.upload_to_db()
    # - Permits
    sodp_data_script.reset_tables()
    sodp_data_script.fetch_data()
    sodp_data_script.upload_to_db()

    # Adjusting for inflation
    processing_scripts.calculate_adj_est()

    # Calculate spatial relationships
    processing_scripts.permit_poly_ids()

if __name__ == '__main__':
    main()