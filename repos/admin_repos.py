from pydantic import EmailStr
from sqlmodel import Session, select
from models.Admin import AdminUser

def find_admin_filtered(email:EmailStr,session:Session):
    statement = select(AdminUser).where(AdminUser.email == email, AdminUser.isDeleted == False)
    res= session.exec(statement).first()
    return res