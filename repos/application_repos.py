from loguru import logger
from sqlmodel import Session, select
from models.Application import ApplicationList
from models.CompCandidateList import CompCanList
from models.Company import CompanyList

def find_application(id:int,session:Session):
    statement = select(ApplicationList).where(ApplicationList.id == id, ApplicationList.isDeleted == False)
    res= session.exec(statement).first()
    return res
    
def get_company_name(id:int,session:Session):
    statement = select(ApplicationList).where(ApplicationList.id == id, ApplicationList.isDeleted == False)
    res= session.exec(statement).first()
    res= session.get(CompCanList,res.compid).companyid
    return session.get(CompanyList,res).legalname

def select_all_appid(coid:list,session:Session)->list:
    statement=select(ApplicationList.id)
    statement=statement.where(ApplicationList.isDeleted == False)
    statement=statement.where(ApplicationList.compid.in_(coid))
    res = session.exec(statement).all()
    return res