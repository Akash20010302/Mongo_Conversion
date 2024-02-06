from loguru import logger
from sqlmodel import create_engine
from sqlmodel import Session
from sqlalchemy.exc import PendingRollbackError

# eng = r'/home/ubuntu/trace_backend/database.db'
# sqlite_url = f'sqlite:///{eng}'
# engine = create_engine(sqlite_url)
# session = Session(bind=engine)
username = "admin"
password = "trace_admin"
#host = "trace-database.cp624e0cixqq.ap-south-1.rds.amazonaws.com"
host = "dev-trace-database.cp624e0cixqq.ap-south-1.rds.amazonaws.com"
port = 3306
database_name = "database"

# try:# MySQL connection string
#     mysql_url = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}"
#     engine = create_engine(mysql_url)
#     session = Session(bind=engine)
# except Exception as e:
#     print(e)
eng2 = r'/home/ubuntu/trace_analytics/analytics.db'
sqlite_url2 = f'sqlite:///{eng2}'
analytics_engine = create_engine(sqlite_url2)
analytics_session = Session(bind=analytics_engine)

mysql_url = f"mysql://{username}:{password}@{host}:{port}/{database_name}"

engine = create_engine(
    mysql_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False
)

def get_db_db()->Session:
    db = Session(engine)
    try:
        logger.debug(f"DB: {db}")
        yield db
    except PendingRollbackError as pre:
        logger.debug("Session RollBack Error Occured.")
        logger.error(f"RollBack Error : {pre}")
        db.rollback()
        yield from get_db_db(engine)
    except Exception as e:
        import traceback
        logger.debug(traceback.format_exc())
        logger.debug("Session Can't Be Created.")
        logger.error(f"Error : {e}")
    finally:
        db.close()