from sqlmodel import Session, select
from db.db import engine
from models.Admin import AdminUser

async def find_admin_filtered(email):
    with Session(engine) as session:
        statement = select(AdminUser).where(AdminUser.email == email, AdminUser.isDeleted == False)
        res= session.exec(statement).first()
        return res