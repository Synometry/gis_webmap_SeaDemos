import urllib
from pathlib import Path
#import sqlalchemy

# parameters = urllib.parse.quote_plus(
#     'DRIVER={ODBC Driver 18 for SQL Server};'
#     'SERVER=SKIZZIK/SQLEXPRESS;'
#     'DATABASE=project_permit_db;'
#     'Trusted_Connection=yes;'
#     'Encrypt=yes;'
#     'TrustServerCertificate=yes;'
# )

# print(parameters)

#engine = sqlalchemy.create_engine(f'mssql+prodbc://SQLEXPRESS/project_permit_db?')

p = Path('./cache/cu.data.1.AllItems')
with p.open() as f:
    print(''.join(f.readlines()))