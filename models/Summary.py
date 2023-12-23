import datetime
from typing import Optional
from pydantic import EmailStr
from sqlmodel import SQLModel
from async_sessions.sessions import get_db, get_db_backend

class SummaryBasicInfo(SQLModel):
    firstName: str = 'N/A'
    middleName : str = 'N/A'
    lastName : str = 'N/A'
    phone : str = 'N/A'
    email : EmailStr = 'N/A'
    age : int = 'N/A'
    gender : str = 'N/A'
    marital_status : str = 'N/A'
    city : str = 'N/A'
    role : str = 'N/A'
    company : str = 'N/A'
    legalname : str = 'N/A'
    report_date : Optional[datetime.datetime] = datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30)
    
    class Config:
        from_attributes = True
        
class AsyncGenerator():
    def __init__(self):
        self.backend = get_db_backend()
        self.analytics = get_db()