import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
port = int(os.getenv("DB_PORT"))
database_name = os.getenv("DB_NAME")
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