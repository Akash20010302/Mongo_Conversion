from loguru import logger
from sqlmodel import Session, select
from db.db import engine
from models.Form import Form
from models.Tenure import Tenure
from repos.application_repos import get_company_name
from repos.kyc_repos import find_kyc

async def convert_to_basic_info(res,res2):
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
                "legalname" : await get_company_name(res.id),
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
                "legalname" : await get_company_name(res.id),
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
                "legalname" : await get_company_name(res.id)
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
                "legalname" : await get_company_name(res.id)
            }
    return s

async def convert_to_identification(res):
    res2 = await find_kyc(res.id)
    if res2 is not None:
        s = {
            "Aadhar_Number" : res.Aadhar_Number,
            "Pan_Number" : res.Pan_Number.upper(),
            "Extracted_Aadhar_Number" : res.Extracted_Aadhar_Number,
            "Extracted_Pan_Number" : res.Extracted_Pan_Number,
            "aadharurl" : res.aadharurl,
            "panurl" : res.panurl,
            "govt_pan_number" : res2.kyc_details_pan_number if res2.kyc_details_pan_number is not None else None,
            "govt_aadhaar_number" : res2.kyc_details_aadhaar_number if res2.kyc_details_aadhaar_number is not None else None
        }
        return s
    else:
        logger.debug(f"No KYC Detail of {res.id}")
        s = {
            "Aadhar_Number" : res.Aadhar_Number,
            "Pan_Number" : res.Pan_Number.upper(),
            "Extracted_Aadhar_Number" : res.Extracted_Aadhar_Number,
            "Extracted_Pan_Number" : res.Extracted_Pan_Number,
            "aadharurl" : res.aadharurl,
            "panurl" : res.panurl,
            "govt_pan_number" : None,
            "govt_aadhaar_number" : None
        }
        return s

async def get_basic_info(id):
    with Session(engine) as session:
        statement = select(Form).where(Form.id == id, Form.isDeleted == False)
        res = session.exec(statement).first()
        statement = select(Tenure).where(Tenure.formid == id, Tenure.isDeleted == False)
        res2 = session.exec(statement).all()
        if res is not None and res2 is not None:
            res = await convert_to_basic_info(res,res2)
        return res
    
async def get_identification(id):
    with Session(engine) as session:
        statement = select(Form).where(Form.id == id, Form.isDeleted == False)
        res = session.exec(statement).first()
        if res is not None:
            res = await convert_to_identification(res)
        return res