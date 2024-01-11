import datetime
from sqlmodel import SQLModel, Field, Index
from typing import Optional
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")

class CompanyList(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    legalname: str
    displayname: str
    pincode: str
    state: str
    city: str
    address1: Optional[str]
    address2: Optional[str]
    numberofemployees: str
    industryvertical: str
    status: Optional[str] = 'Active'
    createddate: Optional[datetime.datetime] = datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30)
    createdby: Optional[int]
    updateddate: Optional[datetime.datetime]
    updatedby: Optional[int]
    lastlogin: Optional[datetime.datetime]
    isDeleted: Optional[bool] = False
    DeletedBy: Optional[int]
    
    class Config:
        indexes = [Index("idx_companylist_id", "id")]
