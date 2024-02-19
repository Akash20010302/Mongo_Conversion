import os
from loguru import logger
from sqlmodel import create_engine
from sqlmodel import Session
from sqlalchemy.exc import PendingRollbackError
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = int(os.getenv("DB_PORT"))
database_name = os.getenv("DB_NAME")
analytics_database_name = os.getenv("ANALYTICS_DB_NAME")


mysql_url = f"mysql://{username}:{password}@{host}:{port}/{database_name}"
mysql_url_analytics=f"mysql://{username}:{password}@{host}:{port}/{analytics_database_name}"

analytics_engine = create_engine(
    mysql_url_analytics,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False
)
engine = create_engine(
    mysql_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False
)


def get_db_analytics():
    with Session(analytics_engine) as db:
        try:
            logger.debug(f"DB: {db}")
            yield db
        except PendingRollbackError as pre:
            logger.debug("Session RollBack Error Occured.")
            logger.error(f"RollBack Error : {pre}")
            db.rollback()
            yield from get_db_analytics(analytics_engine)
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.debug("Session Can't Be Created.")
            logger.error(f"Error : {e}")
        finally:
            db.close()

def get_db_backend(): # type: ignore
    db = Session(engine)
    try:
        logger.debug(f"DB: {db}")
        yield db
    except PendingRollbackError as pre:
        logger.debug("Session RollBack Error Occured.")
        logger.error(f"RollBack Error : {pre}")
        db.rollback()
        yield from get_db_backend(engine)
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.debug("Session Can't Be Created.")
        logger.error(f"Error : {e}")
    finally:
        db.close()
