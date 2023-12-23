from sqlalchemy import text
from sqlmodel import Session
from db.db import analytics_engine

async def find_salary(id:int):
    with Session(analytics_engine) as session:
        statement = text("""
        SELECT
            COUNT(DISTINCT case when "A2(section_1)" LIKE '192%' then deductor_tan_no end) as salary_accounts
        FROM "26as_details"
        WHERE person_id = :person_id""")
        res= session.exec(statement=statement,params={"person_id":id}).first()
        return res
    
async def find_business(id:int):
    with Session(analytics_engine) as session:
        statement = text("""
        SELECT
            COUNT(DISTINCT case when "A2(section_1)" LIKE '194%' then deductor_tan_no end) as salary_accounts
        FROM "26as_details"
        WHERE person_id = :person_id""")
        res= session.exec(statement=statement,params={"person_id":id}).first()
        return res