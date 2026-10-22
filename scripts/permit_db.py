from pathlib import Path
import pandas as pd
from pandas import DataFrame
import sqlalchemy
from sqlalchemy import select
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

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

def create_table(table_type: type[TableBase]):
    assert issubclass(table_type, TableBase), f'table_obj, {type(table_type)} is not a subclass of \'TableBase\'!'
    with Session(_engine) as session, session.begin():
        TableBase.metadata.create_all(_engine, tables=[table_type.__table__])

def table_to_dataframe(table_type: type[TableBase], index_col: str | None = None) -> DataFrame:
    return pd.read_sql_table(table_type.__tablename__, _engine, index_col=index_col)
    

# Example:

# class DummyTable(TableBase):
#     __tablename__ = 'dummy_table'
    
#     id : Mapped[int] = mapped_column(primary_key=True)
#     val1 : Mapped[float]
#     val2 : Mapped[str] = mapped_column(sqlalchemy.String(30))
    
#     def __repr__(self) -> str:
#         return 'DummyEntry(' + ', '.join([f'{x}={self.__dict__[x]!r}' for x in ['id', 'val1', 'val2']]) + ')'

# create_table(DummyTable)