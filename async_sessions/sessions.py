from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
username = "admin"
password = "trace_admin"
host = "dev-trace-database.cp624e0cixqq.ap-south-1.rds.amazonaws.com"
#host = "trace-database.cp624e0cixqq.ap-south-1.rds.amazonaws.com"
port = 3306
database_name = "database"
# mysql_url = f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database_name}"
mysql_url = f"mysql+aiomysql://{username}:{password}@{host}:{port}/{database_name}"

async_engine = create_async_engine('sqlite+aiosqlite:////home/ubuntu/trace_analytics/analytics.db')  
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession)

async_engine_backend = create_async_engine(mysql_url)  
AsyncSessionLocal_backend = sessionmaker(autocommit=False, autoflush=False, bind=async_engine_backend, class_=AsyncSession)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_db_backend():
    async with AsyncSessionLocal_backend() as session:
        yield session