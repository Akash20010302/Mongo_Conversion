import datetime
from pydantic import EmailStr
from sqlmodel import SQLModel, Field, Relationship, Index
from typing import List, Optional
from models.Application import ApplicationList
from models.Form import Form
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")

class Share(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    sharedid: Optional[str]
    appid: int = Field(foreign_key='applicationlist.id')
    app:Optional[ApplicationList] = Relationship()
    formid: int = Field(foreign_key='form.id')
    form: Optional[Form] = Relationship()
    email: str
    shared: datetime.datetime
    expiry: datetime.datetime
    status: Optional[str] = "Active"
    isDeleted: Optional[bool] = False
    DeletedBy: Optional[int]
    lastlogin: Optional[datetime.datetime]
    shared_url: Optional[str]
    email_status: Optional[bool] = False
    
    class Config:
        indexes = [Index("idx_Share_appid", "appid"),Index("idx_Share_formid", "formid"),Index("idx_Share_id", "id")]
        
class ShareEmail(SQLModel):
    email: List[EmailStr]
    emailBody: Optional[str]
    emailSubject: Optional[str]
    expiry_date: int
    id: List[int]
    url: str
    
    class Config:
        from_attributes = True
        
class StopShare(SQLModel):
    id: int
    
    class Config:
        from_attributes = True 
        
class GetShare(SQLModel):
    token: Optional[str] = None
    
    class Config:
        from_attributes = True
        
class ReShare(SQLModel):
    id: int
    expiry: Optional[int]
    
    class Config:
        from_attributes = True