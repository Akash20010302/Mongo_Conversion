import datetime
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel

from models.Application import ApplicationList

class Form(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    appid: int = Field(foreign_key='applicationlist.id')
    app:Optional[ApplicationList] = Relationship()
    firstName: str
    middleName: Optional[str]
    lastName: str
    phone: Optional[str] = Field(foreign_key='candidateuser.phone')
    email: Optional[str] = Field(foreign_key='candidateuser.email')
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
    
    class Config:
        from_attributes = True

class GetForm(SQLModel):
    id: int
    
    class Config:
        from_attributes = True