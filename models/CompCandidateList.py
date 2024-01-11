import datetime
from pydantic import validator
from sqlmodel import SQLModel, Field, Relationship, Index
from typing import Optional
from models.Candidate import CandidateUser
from models.Company import CompanyList
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")

class CompCanList(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    firstName: str
    lastName: str
    role: Optional[str] = "Candidate"
    email: str
    phone: str = Field(min_length=10, max_length=10)
    company: Optional[CompanyList] = Relationship()
    companyid: int = Field(foreign_key='companylist.id')
    verified: Optional[bool] = False
    appactive: Optional[bool] = False
    createddate: Optional[datetime.datetime] = datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30)
    createdby: Optional[int]
    updateddate: Optional[datetime.datetime]
    updatedby: Optional[int]
    lastlogin: Optional[datetime.datetime]
    isDeleted: Optional[bool] = False
    DeletedBy: Optional[int]
    CanId: int = Field(foreign_key='candidateuser.id')
    candidate: Optional[CandidateUser] = Relationship()
    currentctc: Optional[str] = None
    rolebudget: Optional[str] = None
    offeredctc: Optional[str] = None
    
    @validator('phone', pre=True, always=True)
    def validate_phone(cls, v, values):
        if len(v) != 10:
            raise ValueError("Phone number must be 10 digits long")
        if not v.isdigit():
            raise ValueError("Phone number must consist of digits only")
        return v
    
    class Config:
        indexes = [Index("idx_comcanlist_companyid", "companyid"), Index("idx_comcanlist_CanId", "CanId"), Index("idx_comcanlist_id", "id")]