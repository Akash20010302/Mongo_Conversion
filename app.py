import os
import time
from fastapi.responses import JSONResponse
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, FastAPI
from sqlalchemy.sql import text
from sqlmodel import SQLModel, Session
from typing import List, Optional, Tuple
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from db.db import get_db_backend
from endpoints.summary_endpoints import summary_router
from endpoints.identification_endpoints import identification_router
from endpoints.contact_endpoints import contact_router
from endpoints.benchmark_endpoints import benchmark_router
from endpoints.about_endpoints import about_router
from endpoints.career_endpoints import career_router
# from endpoints.share_endpoints import share_router
from endpoints.newhire_endpoints import new_hire_router
from endpoints.credits_endpoints import credits_router
from endpoints.financial_endpoints import financial_router
from endpoints.courtcase_endpoints import courtcase_router
from endpoints.academics_endpoints import academics_router

os.environ['TZ'] = 'Asia/Kolkata'
# time.tzset()

logger.add("logs/logger_log.log",rotation="500 MB",format="{time:DD-MM-YYYY HH:mm:ss} | {level: <8} | {message}", backtrace=True, diagnose=True)

try:
    app = FastAPI()
    logger.success("Report Server StartUp Successful")
except Exception as ex:
    logger.error(ex)
    logger.debug("Cannot Start Report Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(summary_router)
app.include_router(identification_router)
app.include_router(contact_router)
app.include_router(benchmark_router)
app.include_router(about_router)
app.include_router(career_router)
# app.include_router(share_router)
app.include_router(new_hire_router)
app.include_router(credits_router)
app.include_router(financial_router)
app.include_router(courtcase_router)
app.include_router(academics_router)


@app.get("/sessionrollback", tags=["App"])
async def rollback(session: Session = Depends(get_db_backend)):
    session.rollback()
    return JSONResponse(content="Success")


# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run('app:app', host='0.0.0.0', port=8080, reload=True)
