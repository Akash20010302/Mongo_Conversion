import datetime
from sqlmodel import Relationship, SQLModel, Field, Index
from typing import Optional
from models.CompCandidateList import CompCanList
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")

class ApplicationList(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    compid: Optional[int] = Field(foreign_key='compcanlist.id')
    compc: Optional[CompCanList] = Relationship()
    candidatetype: str
    applicationtype: str
    expiry_date: Optional[datetime.datetime]
    status: Optional[str] = "1 - Request Sent"
    createddate: Optional[datetime.datetime] = (datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30))
    createdby: Optional[int]
    updateddate: Optional[datetime.datetime]
    updatedby: Optional[int]
    isDeleted: Optional[bool] = False
    DeletedBy: Optional[int]
    report: Optional[datetime.datetime]
    
    class Config:
        indexes = [Index("idx_applicationlist_comcanid", "compid"),Index("idx_applicationlist_id", "id")]
