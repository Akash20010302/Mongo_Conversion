from loguru import logger
from sqlmodel import Session, select
from db.db import engine
from models.Application import ApplicationList
from models.CompCandidateList import CompCanList
from models.Company import CompanyList

async def find_application(id:int):
    with Session(engine) as session:
        statement = select(ApplicationList).where(ApplicationList.id == id, ApplicationList.isDeleted == False)
        res= session.exec(statement).first()
        return res
    
async def get_company_name(id:int):
    with Session(engine) as session:
        statement = select(ApplicationList).where(ApplicationList.id == id, ApplicationList.isDeleted == False)
        res= session.exec(statement).first()
        res= session.get(CompCanList,res.compid).companyid
        return session.get(CompanyList,res).legalname

async def select_all_appid(coid:list)->list:
    with Session(engine) as session:
        statement=select(ApplicationList.id)
        statement=statement.where(ApplicationList.isDeleted == False)
        statement=statement.where(ApplicationList.compid.in_(coid))
        res = session.exec(statement).all()
        return res