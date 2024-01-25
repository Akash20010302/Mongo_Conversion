from sqlmodel import create_engine
from sqlmodel import Session

# eng = r'/home/ubuntu/trace_backend/database.db'
# sqlite_url = f'sqlite:///{eng}'
# engine = create_engine(sqlite_url)
# session = Session(bind=engine)
username = "admin"
password = "trace_admin"
#host = "trace-database.cp624e0cixqq.ap-south-1.rds.amazonaws.com"
# host = "dev-trace-database.cp624e0cixqq.ap-south-1.rds.amazonaws.com"
hostdemo = "demo-trace-database.cp624e0cixqq.ap-south-1.rds.amazonaws.com"
port = 3306
database_name = "database"

try:# MySQL connection string
    mysql_url = f"mysql+pymysql://{username}:{password}@{hostdemo}:{port}/{database_name}"
    engine = create_engine(mysql_url)
    session = Session(bind=engine)
except Exception as e:
    print(e)
eng2 = r'/home/ubuntu/trace_analytics/analytics.db'
sqlite_url2 = f'sqlite:///{eng2}'
analytics_engine = create_engine(sqlite_url2)
analytics_session = Session(bind=analytics_engine)
