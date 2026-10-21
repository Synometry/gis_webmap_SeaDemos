from pathlib import Path
import sqlalchemy
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Session

class TableBase(DeclarativeBase):
    ...

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

def add_table(table_obj: TableBase):
    assert issubclass(type(table_obj), TableBase), f'table_obj, {type(table_obj)} is not a subclass of \'TableBase\'!'
    with Session(_engine) as session, session.begin():
        session.cr

# connection.

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

# p = Path('./cache/cu.data.1.AllItems')
# with p.open() as f:
#     print(''.join(f.readlines()))

add_table(1)