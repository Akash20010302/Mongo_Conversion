from fastapi import APIRouter, HTTPException
from loguru import logger
from db.db import session
from starlette.status import HTTP_400_BAD_REQUEST
from auth.auth import AuthHandler
from endpoints.career_endpoints import get_career_summary
from endpoints.contact_endpoints import get_combined_info
from endpoints.identification_endpoints import iden_info
from models.Form import Form
from models.Summary import AsyncGenerator, SummaryBasicInfo
from repos.application_repos import find_application
from repos.as_repos import find_business, find_salary
from repos.form_repos import get_basic_info

summary_router = APIRouter()
auth_handler = AuthHandler()

@summary_router.get("/basic-info/{id}", response_model=SummaryBasicInfo,tags=['Summary'])
async def basic_info(id:int):
    basic = await get_basic_info(id)
    basic = SummaryBasicInfo(**basic)
    return basic

@summary_router.get("/application-journey/{id}", tags=['Summary'])
async def journey_info(id:int):
    form = session.get(Form,id)
    appl = await find_application(id)
    if form.report is None :
        return {"application_initiated":appl.createddate,"application_completed":form.formcompletiondate,"report_generated":"Under Progress","form_initiation_to_complete":(form.formcompletiondate - appl.createddate).days}
    return {"application_initiated":appl.createddate,"application_completed":form.formcompletiondate,"report_generated":form.report,"form_initiation_to_complete":(form.formcompletiondate - appl.createddate).days,"form_complete_to_report":(form.report - form.formcompletiondate).days}

@summary_router.get("/summary/{id}", tags=['Summary'])
async def summary(id:int):
    form = session.get(Form,id)
    if form is None:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Form Not Found")
    data = {}
    data["Highlights"] = []
    data["Profile"]={}
    data["Contact_Consistency"]={}
    data["Identification"]={}
    data["External_Involvement"] = {}
    data["Income_Non_Declaration"] = {}
    data["Lack_Of_Trust"] = {}
    data["Lack_Of_Trust"]["Discripency"] = data["Lack_Of_Trust"]["Red_Flag"] = 0
    data["External_Involvement"]["DIN"] = data["External_Involvement"]["External_Affiliations"] = 0
    data["External_Involvement"]["Score"] = 1
    data["Identification"]["Discripency"]=[]
    data["Identification"]["Consistency"]=[]
    data["Contact_Consistency"]["Discripency"]=[]
    data["Contact_Consistency"]["Consistency"]=[]
    data["Profile"]["Current_Take_Home"] = data["Profile"]["Current_Household_Take_Home"] = form.salary
    data["Profile"]["Score"] = round((((int(form.salary)*12)-1200000)/1600000)*100,2) if (int(form.salary)*12)>=1200000 and (int(form.salary)*12)<=2800000 else 100 if (int(form.salary)*12)>2800000 else 0
    if data["Profile"]["Score"] < 20.0:
        data["Highlights"].append(f"{form.firstName} is currently in the Very Low salary range based on his role, location and experience.")
    elif 20.0 <= data["Profile"]["Score"] < 40.0:
        data["Highlights"].append(f"{form.firstName} is currently in the Low salary range based on his role, location and experience.")
    elif 40.0 <= data["Profile"]["Score"] < 60.0:
        data["Highlights"].append(f"{form.firstName} is currently in the Mid salary range based on his role, location and experience.")
    elif 60.0 <= data["Profile"]["Score"] < 80.0:
        data["Highlights"].append(f"{form.firstName} is currently in the High salary range based on his role, location and experience.")
    else:
        data["Highlights"].append(f"{form.firstName} is currently in the Very High salary range based on his role, location and experience.")
    data["Profile"]["Score"] = int(data["Profile"]["Score"]/20) if int(data["Profile"]["Score"]/20) >0 else 1
    temp = await iden_info(id)
    if temp["Aadhar_Status"] == 'Concern':
        data["Identification"]["Discripency"].append("Aadhar")
    else:
        data["Identification"]["Consistency"].append("Aadhar")
    if temp["Pan_Status"] == 'Concern':
        data["Identification"]["Discripency"].append("PAN")
    else:
        data["Identification"]["Consistency"].append("PAN")
    data["Identification"]["Score"] = temp["meter"]
    if len(data["Identification"]["Discripency"]) == 2:
        data["Highlights"].append(f'{form.firstName}’s {data["Identification"]["Discripency"][0]} number and {data["Identification"]["Discripency"][1]} number from the card submitted did not match the number provided. This needs to be reviewed and corrected.')
    elif len(data["Identification"]["Discripency"]) == 1:
        data["Highlights"].append(f'{form.firstName}’s {data["Identification"]["Discripency"][0]} number from the card submitted did not match the number provided. This needs to be reviewed and corrected.')
    data["Income_Non_Declaration"]["Salary"] = (await find_salary(id))[0]
    data["Income_Non_Declaration"]["Business"] = (await find_business(id))[0]
    data["Income_Non_Declaration"]["Score"] = min(5,data["Income_Non_Declaration"]["Business"] if data["Income_Non_Declaration"]["Business"]>0 else 1 )
    if data["Income_Non_Declaration"]["Business"] !=0:
        data["Highlights"].append(f'There are additional Contract/Business income identified for {form.firstName} that needs to be declared for compliance.')
    f = AsyncGenerator()
    async for backend_session in f.backend:
        break
    async for analytics_session in f.analytics:
        break
    try:
        contact = await get_combined_info(id=id, db_1=backend_session, db_2=analytics_session)
        if contact is not None :
            if contact.name.flag == False:
                data["Contact_Consistency"]["Discripency"].append("Name")
            else:
                data["Contact_Consistency"]["Consistency"].append("Name")
            if contact.mobile.flag == False:
                data["Contact_Consistency"]["Discripency"].append("Mobile")
            else:
                data["Contact_Consistency"]["Consistency"].append("Mobile")
            if contact.email.flag == False:
                data["Contact_Consistency"]["Discripency"].append("Email")
            else:
                data["Contact_Consistency"]["Consistency"].append("Email")
            if contact.address.flag == False:
                data["Contact_Consistency"]["Discripency"].append("Address")
            else:
                data["Contact_Consistency"]["Consistency"].append("Address")
            data["Contact_Consistency"]["Score"] = contact.index.meter
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Contact Info not found.")
        career = await get_career_summary(person_id=id, db=analytics_session, db_backend=backend_session)
        if career is not None:
            data["Lack_Of_Trust"]["Discripency"]= career.discrepancies
            data["Lack_Of_Trust"]["Red_Flag"] = career.red_flag
            data["Lack_Of_Trust"]["Score"] = career.meter
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Carrer Info not found.")
    except Exception as e:
        logger.debug(e)
    finally:
        await backend_session.close()
        await analytics_session.close()
    if data["Lack_Of_Trust"]["Red_Flag"] > 0 and data["Lack_Of_Trust"]["Discripency"] > 0:
        data["Highlights"].append(f'''{form.firstName}’s career journey has {data["Lack_Of_Trust"]["Discripency"]} inconsistencies and {data["Lack_Of_Trust"]["Red_Flag"]} red flags. Red flags are critical and could be an indicator of moonlighting or second job.''')
    elif data["Lack_Of_Trust"]["Red_Flag"] > 0:
        data["Highlights"].append(f'''{form.firstName}’s career journey has {data["Lack_Of_Trust"]["Red_Flag"]} red flags. Red flags are critical and could be an indicator of moonlighting or second job.''')
    elif data["Lack_Of_Trust"]["Discripency"] > 0:
        data["Highlights"].append(f'''{form.firstName}’s career journey has {data["Lack_Of_Trust"]["Discripency"]} inconsistencies. ''')
    else:
        data["Highlights"].append(f'''{form.firstName}’s career journey has no inconsistencies or red flags.''')
    for key in data.keys():
        if data[key] is None:
            data[key] = "N/A"
        else:
            if type(data[key])==dict and key != "Income_Non_Declaration" and key != "Lack_Of_Trust":
                for keys in data[key].keys():
                    if keys != "Score":
                        if type(data[key][keys])!=list:
                            if data[key][keys] is None or data[key][keys] == 0:
                                data[key][keys] = 'N/A'
                        elif type(data[key][keys])==list:
                            if len(data[key][keys]) == 0:
                                data[key][keys].append("N/A")
            
    return data