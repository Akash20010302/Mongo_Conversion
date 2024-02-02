from loguru import logger
from sqlmodel import Session, select
from models.Form import Form
from models.Tenure import Tenure
from repos.application_repos import get_company_name
from repos.kyc_repos import find_kyc

def convert_to_basic_info(res,res2,session):
    if res.report is not None:
        if res2 is not None and len(res2)>0:
            s = {
                "firstName" : res.firstName,
                "middleName" : res.middleName,
                "lastName" : res.lastName,
                "phone" : res.phone,
                "email" : res.email,
                "age" : res.age,
                "gender" : res.gender,
                "marital_status" : res.marital_status,
                "city" : res.city,
                "role" : (max(res2, key=lambda x: x.to_date)).role,
                "company" : (max(res2, key=lambda x: x.to_date)).company,
                "legalname" : get_company_name(res.id,session),
                "report_date" : res.report
            }
        else:
            s = {
                "firstName" : res.firstName,
                "middleName" : res.middleName,
                "lastName" : res.lastName,
                "phone" : res.phone,
                "email" : res.email,
                "age" : res.age,
                "gender" : res.gender,
                "marital_status" : res.marital_status,
                "city" : res.city,
                "role" : "N/A",
                "company" : "N/A",
                "legalname" : get_company_name(res.id,session),
                "report_date" : res.report
            }
    else:
        if res2 is not None and len(res2)>0:
            s = {
                "firstName" : res.firstName,
                "middleName" : res.middleName,
                "lastName" : res.lastName,
                "phone" : res.phone,
                "email" : res.email,
                "age" : res.age,
                "gender" : res.gender,
                "marital_status" : res.marital_status,
                "city" : res.city,
                "role" : (max(res2, key=lambda x: x.to_date)).role,
                "company" : (max(res2, key=lambda x: x.to_date)).company,
                "legalname" : get_company_name(res.id,session)
            }
        else:
            s = {
                "firstName" : res.firstName,
                "middleName" : res.middleName,
                "lastName" : res.lastName,
                "phone" : res.phone,
                "email" : res.email,
                "age" : res.age,
                "gender" : res.gender,
                "marital_status" : res.marital_status,
                "city" : res.city,
                "role" : "N/A",
                "company" : "N/A",
                "legalname" : get_company_name(res.id,session)
            }
    return s

async def convert_to_identification(res):
    res2 = await find_kyc(res.id)
    # logger.debug(f"RES2: {res2}")
    s = {
        "Aadhar_Number" : res.Aadhar_Number,
        "Pan_Number" : res.Pan_Number.upper(),
        "Extracted_Aadhar_Number" : res.Extracted_Aadhar_Number,
        "Extracted_Pan_Number" : res.Extracted_Pan_Number,
        "aadharurl" : res.aadharurl,
        "panurl" : res.panurl,
        "govt_pan_number" : res2.kyc_details_pan_number if res2 else "N/A",
        "govt_aadhaar_number" : res2.kyc_details_aadhaar_number if res2 else "N/A"
    }
    return s

def get_basic_info(id:int, session:Session):
    statement = select(Form).where(Form.id == id, Form.isDeleted == False)
    res = session.exec(statement).first()
    statement = select(Tenure).where(Tenure.formid == id, Tenure.isDeleted == False)
    res2 = session.exec(statement).all()
    if res is not None and res2 is not None:
        res = convert_to_basic_info(res,res2,session)
    return res
    
async def get_identification(id:int, session:Session):
    statement = select(Form).where(Form.id == id, Form.isDeleted == False)
    res = session.exec(statement).first()
    if res is not None:
        # logger.debug(f"RES: {res}")
        res = await convert_to_identification(res)
    return res