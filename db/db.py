from sqlmodel import create_engine
from sqlmodel import Session

eng = r'/home/ubuntu/trace_backend/database.db'
sqlite_url = f'sqlite:///{eng}'
engine = create_engine(sqlite_url)
session = Session(bind=engine)
eng2 = r'/home/ubuntu/trace_analytics/analytics.db'
sqlite_url2 = f'sqlite:///{eng2}'
analytics_engine = create_engine(sqlite_url2)
analytics_session = Session(bind=analytics_engine)
