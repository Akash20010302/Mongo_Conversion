import datetime
from pydantic import validator
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from models.Company import CompanyList
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")

class AdminUser(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    firstName: str
    lastName: str
    role: Optional[str]
    email: str
    phone: str = Field(min_length=10, max_length=10)
    company: Optional[CompanyList] = Relationship()
    companyid: int = Field(foreign_key='companylist.id')
    password: str
    status: str = "Invited"
    createddate: Optional[datetime.datetime] = (datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30))
    createdby: Optional[int]
    updateddate: Optional[datetime.datetime]
    updatedby: Optional[int]
    lastlogin: Optional[datetime.datetime]
    isDeleted: Optional[bool] = False
    DeletedBy: Optional[int]
    
    @validator('phone', pre=True, always=True)
    def validate_phone(cls, v, values):
        if len(v) != 10:
            raise ValueError("Phone number must be 10 digits long")
        if not v.isdigit():
            raise ValueError("Phone number must consist of digits only")
        return v
    
    class Config:
        from_attributes = True