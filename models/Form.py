import datetime
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel, Index
from models.Application import ApplicationList
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")

class Form(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    appid: int = Field(foreign_key='applicationlist.id')
    app:Optional[ApplicationList] = Relationship()
    firstName: str
    middleName: Optional[str]
    lastName: str
    phone: Optional[str]
    email: Optional[str]
    dob: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    marital_status: Optional[str]
    education:Optional[str]
    experience: Optional[int]
    city: Optional[str]
    salary: Optional[str]
    home: Optional[bool] = False
    homeLoan: Optional[bool] = False
    car: Optional[bool] = False
    carLoan: Optional[bool] = False
    twoWheeler: Optional[bool] = False
    twoWheelerLoan: Optional[bool] = False
    creditCard: Optional[bool] = False
    personalLoan: Optional[bool] = False
    stocks: Optional[bool] = False
    realEstate: Optional[bool] = False
    spousefirstName: Optional[str]
    spousemiddleName: Optional[str]
    spouselastName: Optional[str]
    spousedob: Optional[str]
    spouseAge: Optional[int]
    spouseEducation: Optional[str]
    spouseExperience: Optional[int]
    kids: Optional[bool] = False
    totalkids: Optional[int]
    adultsdependent: Optional[bool] = False
    totaladults: Optional[int]
    panurl: Optional[str]
    aadharurl: Optional[str]
    resumeurl: Optional[str]
    itrusername: Optional[str]
    itrmessage: Optional[str]
    uannumber: Optional[str]
    uanmessage: Optional[str]
    last_page: Optional[int]
    formcompletion: Optional[bool] = False
    isDeleted: Optional[bool] = False
    DeletedBy: Optional[int]
    startdate: Optional[datetime.datetime] = datetime.datetime.utcnow() + datetime.timedelta(hours=5,minutes=30)
    agreement: Optional[bool] = False
    Aadharnum: Optional[str]
    Pannum: Optional[str]
    formcompletiondate: Optional[datetime.datetime]
    Aadhar_Number: Optional[str]
    Pan_Number: Optional[str]
    Extracted_Aadhar_Number: Optional[str]
    Extracted_Pan_Number: Optional[str]
    report: Optional[datetime.datetime]
    reset: Optional[bool] = False
    
    class Config:
        indexes = [Index("idx_form_appid", "appid"), Index("idx_form_id", "id")]