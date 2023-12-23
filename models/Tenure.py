import datetime
from sqlmodel import SQLModel, Field
from typing import Optional

class Tenure(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    formid: int = Field(foreign_key='form.id')
    tokey: str
    to_date: str
    fromkey: str
    from_date: str
    rolekey: str
    role: str
    companykey: str
    company: str
    isDeleted: Optional[bool] = False
    DeletedBy: Optional[int]
    createdon: Optional[datetime.datetime] = datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30)
    
    class Config:
        from_attributes = True