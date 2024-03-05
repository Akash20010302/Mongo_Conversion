from loguru import logger
from sqlmodel import Session, select
from models.Form import Form
from models.Tenure import Tenure
from repos.application_repos import get_company_name
from repos.kyc_repos import find_kyc


def convert_to_basic_info(res, res2, session):
    if res.report is not None:
        if res2 is not None and len(res2) > 0:
            s = {
                "firstName": res.firstName,
                "middleName": res.middleName,
                "lastName": res.lastName,
                "phone": res.phone,
                "email": res.email,
                "age": res.age,
                "gender": res.gender,
                "marital_status": res.marital_status,
                "city": res.city,
                "role": (max(res2, key=lambda x: x.to_date)).role,
                "company": (max(res2, key=lambda x: x.to_date)).company,
                "legalname": get_company_name(res.id, session),
                "report_date": res.report,
            }
        else:
            s = {
                "firstName": res.firstName,
                "middleName": res.middleName,
                "lastName": res.lastName,
                "phone": res.phone,
                "email": res.email,
                "age": res.age,
                "gender": res.gender,
                "marital_status": res.marital_status,
                "city": res.city,
                "role": "N/A",
                "company": "N/A",
                "legalname": get_company_name(res.id, session),
                "report_date": res.report,
            }
    else:
        if res2 is not None and len(res2) > 0:
            s = {
                "firstName": res.firstName,
                "middleName": res.middleName,
                "lastName": res.lastName,
                "phone": res.phone,
                "email": res.email,
                "age": res.age,
                "gender": res.gender,
                "marital_status": res.marital_status,
                "city": res.city,
                "role": (max(res2, key=lambda x: x.to_date)).role,
                "company": (max(res2, key=lambda x: x.to_date)).company,
                "legalname": get_company_name(res.id, session),
            }
        else:
            s = {
                "firstName": res.firstName,
                "middleName": res.middleName,
                "lastName": res.lastName,
                "phone": res.phone,
                "email": res.email,
                "age": res.age,
                "gender": res.gender,
                "marital_status": res.marital_status,
                "city": res.city,
                "role": "N/A",
                "company": "N/A",
                "legalname": get_company_name(res.id, session),
            }
    return s


#async def convert_to_identification(res):
#    res2 = await find_kyc(res.id)
#    # logger.debug(f"RES2: {res2}")
#    s = {
#        "Aadhar_Number": res.Aadhar_Number,
#        "Pan_Number": res.Pan_Number.upper() if res.Pan_Number is not None else None,
#        "Extracted_Aadhar_Number": res.Extracted_Aadhar_Number,
#        "Extracted_Pan_Number": res.Extracted_Pan_Number,
#        "aadharurl": res.aadharurl,
#        "panurl": res.panurl,
#        "govt_pan_number": res2.kyc_details_pan_number if res2 else "N/A",
#        "govt_aadhaar_number": res2.kyc_details_aadhaar_number if res2 else "N/A",
#    }
#    return s
async def convert_to_identification(res):
    res2 = await find_kyc(res.id) if res else None
    
    masked_aadhar = None
    masked_pan = None
    masked_extracted_aadhar = None
    masked_extracted_pan = None
    masked_govt_aadhar = None
    masked_govt_pan = None
    
    if res:
        masked_aadhar = "XXXX-XXXX-" + res.Aadhar_Number[-4:] if res.Aadhar_Number else None
        masked_pan = res.Pan_Number[0] + "*" * (len(res.Pan_Number) - 2) + res.Pan_Number[-1] if res.Pan_Number else None    
        masked_extracted_aadhar = "XXXX-XXXX-" + res.Extracted_Aadhar_Number[-4:] if res.Extracted_Aadhar_Number else None
        masked_extracted_pan = res.Extracted_Pan_Number[0] + "*" * (len(res.Extracted_Pan_Number) - 2) + res.Extracted_Pan_Number[-1] if res.Extracted_Pan_Number else None
        
    if res2:
        # masked_govt_aadhar = "XXXX-XXXX-" + res2.kyc_details_aadhaar_number[-4:] if res2.kyc_details_aadhaar_number else "N/A"
        # masked_govt_pan = res2.kyc_details_pan_number[0] + "*" * (len(res2.kyc_details_pan_number) - 2) + res2.kyc_details_pan_number[-1] if res2.kyc_details_pan_number else "N/A"
        masked_govt_aadhar = "XXXX-XXXX-" + res2.aadhaar_aadhaar_number[-4:] if res2.aadhaar_aadhaar_number else "N/A"
        masked_govt_pan = res2.pan_pan[0] + "*" * (len(res2.pan_pan) - 2) + res2.pan_pan[-1] if res2.pan_pan else "N/A"

    s = {
        "Aadhar_Number": masked_aadhar,
        "Pan_Number": masked_pan.upper() if masked_pan else None,
        "Extracted_Aadhar_Number": masked_extracted_aadhar,
        "Extracted_Pan_Number": masked_extracted_pan.upper() if masked_extracted_pan else None,
        "aadharurl": res.aadharurl if res and hasattr(res, 'aadharurl') else None,
        "panurl": res.panurl if res and hasattr(res, 'panurl') else None,
        "govt_pan_number": masked_govt_pan,
        "govt_aadhaar_number": masked_govt_aadhar
    }
    return s


def get_basic_info(id: int, session: Session):
    statement = select(Form).where(Form.id == id, Form.isDeleted == False)
    res = session.exec(statement).first()
    statement = select(Tenure).where(Tenure.formid == id, Tenure.isDeleted == False)
    res2 = session.exec(statement).all()
    if res is not None and res2 is not None:
        res = convert_to_basic_info(res, res2, session)
    return res


async def get_identification(id: int, session: Session):
    statement = select(Form).where(Form.id == id, Form.isDeleted == False)
    res = session.exec(statement).first()
    if res is not None:
        # logger.debug(f"RES: {res}")
        res = await convert_to_identification(res)
    return res
