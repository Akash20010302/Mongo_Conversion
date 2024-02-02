from collections import defaultdict
import datetime
import statistics

from sqlmodel import Session
from async_sessions.sessions import AsyncSessionLocal, AsyncSessionLocal_backend, get_db, get_db_backend
from fastapi import APIRouter, HTTPException,Depends
from loguru import logger
from starlette.status import HTTP_400_BAD_REQUEST
from sqlalchemy.sql import text
from auth.auth import AuthHandler
from db.db import get_db_db
from endpoints.career_endpoints import get_career_summary
from endpoints.contact_endpoints import get_combined_info
from endpoints.identification_endpoints import iden_info
from models.Form import Form
from models.Contact_Information import Address, Email, Index, Mobile, Name, contact_info
from models.Summary import AsyncGenerator, ExperienceSummary,Name_,Mobile_,Email_,Address_,contact_information, IncomePosition,Ideal_ctc, Summary, SummaryBasicInfo,offered_past_ctc_summary,declared_household_income_summary,identity_info
from repos.application_repos import find_application
from repos.as_repos import find_business, find_salary
from repos.form_repos import get_basic_info
from tools.benchmark_tools import convert_to_datetime
from tools.career_tools import overlap
from fuzzywuzzy import fuzz
from tools.contact_tools import check_discrepancy, check_discrepancy_1, check_discrepancy_address


summary_router = APIRouter()
auth_handler = AuthHandler()

@summary_router.get("/basic-info/{id}", response_model=SummaryBasicInfo,tags=['Summary'])
async def basic_info(id:int,session: Session = Depends(get_db_db)):
    try:
        basic = get_basic_info(id,session)
        #logger.debug(basic)
        basic = SummaryBasicInfo(**basic)
        return basic
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,detail="No Records Found.")

@summary_router.get("/application-journey/{id}", tags=['Summary'])
async def journey_info(id:int,session: Session = Depends(get_db_db)):
    # session.rollback()
    # session.commit()
    #from 45-49
    form = session.get(Form,id)
    appl = find_application(id,session)
    if form.report is None :
        return {"application_initiated":appl.createddate,"application_completed":form.formcompletiondate,"report_generated":"Under Progress","form_initiation_to_complete":(form.formcompletiondate - appl.createddate).days}
    return {"application_initiated":appl.createddate,"application_completed":form.formcompletiondate,"report_generated":form.report,"form_initiation_to_complete":(form.formcompletiondate - appl.createddate).days,"form_complete_to_report":(form.report - form.formcompletiondate).days}

    



# @summary_router.get("/summary/{id}", tags=['Summary'])
# async def summary(id:int):
#     form = session.get(Form,id)
#     if form is None:
#         raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Form Not Found")
#     data = {}
#     data["Highlights"] = []
#     data["Profile"]={}
#     data["Contact_Consistency"]={}
#     data["Identification"]={}
#     data["External_Involvement"] = {}
#     data["Income_Non_Declaration"] = {}
#     data["Lack_Of_Trust"] = {}
#     data["Lack_Of_Trust"]["Discripency"] = data["Lack_Of_Trust"]["Red_Flag"] = 0
#     data["External_Involvement"]["DIN"] = data["External_Involvement"]["External_Affiliations"] = 0
#     data["External_Involvement"]["Score"] = 1
#     data["Identification"]["Discripency"]=[]
#     data["Identification"]["Consistency"]=[]
#     data["Contact_Consistency"]["Discripency"]=[]
#     data["Contact_Consistency"]["Consistency"]=[]
#     data["Profile"]["Current_Take_Home"] = data["Profile"]["Current_Household_Take_Home"] = form.salary
#     data["Profile"]["Score"] = round((((int(form.salary)*12)-1200000)/1600000)*100,2) if (int(form.salary)*12)>=1200000 and (int(form.salary)*12)<=2800000 else 100 if (int(form.salary)*12)>2800000 else 0
#     if data["Profile"]["Score"] < 20.0:
#         data["Highlights"].append(f"{form.firstName} is currently in the Very Low salary range based on his role, location and experience.")
#     elif 20.0 <= data["Profile"]["Score"] < 40.0:
#         data["Highlights"].append(f"{form.firstName} is currently in the Low salary range based on his role, location and experience.")
#     elif 40.0 <= data["Profile"]["Score"] < 60.0:
#         data["Highlights"].append(f"{form.firstName} is currently in the Mid salary range based on his role, location and experience.")
#     elif 60.0 <= data["Profile"]["Score"] < 80.0:
#         data["Highlights"].append(f"{form.firstName} is currently in the High salary range based on his role, location and experience.")
#     else:
#         data["Highlights"].append(f"{form.firstName} is currently in the Very High salary range based on his role, location and experience.")
#     data["Profile"]["Score"] = int(data["Profile"]["Score"]/20) if int(data["Profile"]["Score"]/20) >0 else 1
#     temp = await iden_info(id)
#     if temp["Aadhar_Status"] == 'Concern':
#         data["Identification"]["Discripency"].append("Aadhar")
#     else:
#         data["Identification"]["Consistency"].append("Aadhar")
#     if temp["Pan_Status"] == 'Concern':
#         data["Identification"]["Discripency"].append("PAN")
#     else:
#         data["Identification"]["Consistency"].append("PAN")
#     data["Identification"]["Score"] = temp["meter"]
#     if len(data["Identification"]["Discripency"]) == 2:
#         data["Highlights"].append(f'{form.firstName}’s {data["Identification"]["Discripency"][0]} number and {data["Identification"]["Discripency"][1]} number from the card submitted did not match the number provided. This needs to be reviewed and corrected.')
#     elif len(data["Identification"]["Discripency"]) == 1:
#         data["Highlights"].append(f'{form.firstName}’s {data["Identification"]["Discripency"][0]} number from the card submitted did not match the number provided. This needs to be reviewed and corrected.')
#     data["Income_Non_Declaration"]["Salary"] = (await find_salary(id))[0]
#     data["Income_Non_Declaration"]["Business"] = (await find_business(id))[0]
#     data["Income_Non_Declaration"]["Score"] = min(5,data["Income_Non_Declaration"]["Business"] if data["Income_Non_Declaration"]["Business"]>0 else 1 )
#     if data["Income_Non_Declaration"]["Business"] !=0:
#         data["Highlights"].append(f'There are additional Contract/Business income identified for {form.firstName} that needs to be declared for compliance.')
#     f = AsyncGenerator()
#     async for backend_session in f.backend:
#         break
#     async for analytics_session in f.analytics:
#         break
#     try:
#         contact = await get_combined_info(id=id, db_1=backend_session, db_2=analytics_session)
#         if contact is not None :
#             if contact.name.flag == False:
#                 data["Contact_Consistency"]["Discripency"].append("Name")
#             else:
#                 data["Contact_Consistency"]["Consistency"].append("Name")
#             if contact.mobile.flag == False:
#                 data["Contact_Consistency"]["Discripency"].append("Mobile")
#             else:
#                 data["Contact_Consistency"]["Consistency"].append("Mobile")
#             if contact.email.flag == False:
#                 data["Contact_Consistency"]["Discripency"].append("Email")
#             else:
#                 data["Contact_Consistency"]["Consistency"].append("Email")
#             if contact.address.flag == False:
#                 data["Contact_Consistency"]["Discripency"].append("Address")
#             else:
#                 data["Contact_Consistency"]["Consistency"].append("Address")
#             data["Contact_Consistency"]["Score"] = contact.index.meter
#         else:
#             raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Contact Info not found.")
#         career = await get_career_summary(person_id=id, db=analytics_session, db_backend=backend_session)
#         if career is not None:
#             data["Lack_Of_Trust"]["Discripency"]= career.discrepancies
#             data["Lack_Of_Trust"]["Red_Flag"] = career.red_flag
#             data["Lack_Of_Trust"]["Score"] = career.meter
#         else:
#             raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Carrer Info not found.")
#     except Exception as e:
#         logger.debug(e)
#     finally:
#         await backend_session.close()
#         await analytics_session.close()
#     if data["Lack_Of_Trust"]["Red_Flag"] > 0 and data["Lack_Of_Trust"]["Discripency"] > 0:
#         data["Highlights"].append(f'''{form.firstName}’s career journey has {data["Lack_Of_Trust"]["Discripency"]} inconsistencies and {data["Lack_Of_Trust"]["Red_Flag"]} red flags. Red flags are critical and could be an indicator of moonlighting or second job.''')
#     elif data["Lack_Of_Trust"]["Red_Flag"] > 0:
#         data["Highlights"].append(f'''{form.firstName}’s career journey has {data["Lack_Of_Trust"]["Red_Flag"]} red flags. Red flags are critical and could be an indicator of moonlighting or second job.''')
#     elif data["Lack_Of_Trust"]["Discripency"] > 0:
#         data["Highlights"].append(f'''{form.firstName}’s career journey has {data["Lack_Of_Trust"]["Discripency"]} inconsistencies. ''')
#     else:
#         data["Highlights"].append(f'''{form.firstName}’s career journey has no inconsistencies or red flags.''')
#     for key in data.keys():
#         if data[key] is None:
#             data[key] = "N/A"
#         else:
#             if type(data[key])==dict and key != "Income_Non_Declaration" and key != "Lack_Of_Trust":
#                 for keys in data[key].keys():
#                     if keys != "Score":
#                         if type(data[key][keys])!=list:
#                             if data[key][keys] is None or data[key][keys] == 0:
#                                 data[key][keys] = 'N/A'
#                         elif type(data[key][keys])==list:
#                             if len(data[key][keys]) == 0:
#                                 data[key][keys].append("N/A")
            
#     return data


@summary_router.get("/summary_details/{person_id}",response_model=Summary, tags=['Summary'])
async def summary(person_id:str,db: AsyncSessionLocal = Depends(get_db),db_backend: AsyncSessionLocal_backend = Depends(get_db_backend), session: Session = Depends(get_db_db)):
    query = text("""
        SELECT
            SUM(CASE WHEN "A2(section_1)" LIKE '192%' THEN CAST("A7(paid_credited_amt)" AS FLOAT) END) AS total_salary,
            SUM(CASE 
                WHEN "A2(section_1)" IN ('194C', '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O')
                THEN
                    CASE
                        WHEN "A2(section_1)" = '206CN' THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.01
                        ELSE CAST("A7(paid_credited_amt)" AS FLOAT)
                    END
            END) AS total_business_income
			
        FROM "26as_details"
        WHERE person_id = :person_id
            AND strftime('%Y-%m-%d', 
                substr("A3(transaction_dt)", 8, 4) || '-' || 
                CASE substr("A3(transaction_dt)", 4, 3)
                    WHEN 'Jan' THEN '01'
                    WHEN 'Feb' THEN '02'
                    WHEN 'Mar' THEN '03'
                    WHEN 'Apr' THEN '04'
                    WHEN 'May' THEN '05'
                    WHEN 'Jun' THEN '06'
                    WHEN 'Jul' THEN '07'
                    WHEN 'Aug' THEN '08'
                    WHEN 'Sep' THEN '09'
                    WHEN 'Oct' THEN '10'
                    WHEN 'Nov' THEN '11'
                    WHEN 'Dec' THEN '12'
                    END || '-' ||
                    substr("A3(transaction_dt)", 1, 2)
            ) >= strftime('%Y-%m-%d', 'now', '-12 months')

    """)
    result = await db.execute(query, {"person_id": person_id})
    summary = result.fetchone()
    #logger.debug(f"SUMMMARY: {summary}")
    total_salary = summary[0] if summary[0] is not None else 0.0
    total_business_income = summary[1] if summary[1] is not None else 0.0
    #total_overseas_income = summary[2] if summary[2] is not None else 0.0
    overseas_income_query = text("""
    SELECT 
        strftime('%Y-%m', formatted_date) as month_year,
        SUM(CASE 
            WHEN B2 = '206CQ' OR B2 = '206CO' THEN 
                CASE 
                    WHEN CAST(B7 AS FLOAT) / 0.05 <= 700000 THEN CAST(B7 AS FLOAT) / 0.05
                    ELSE CAST(B7 AS FLOAT) / 0.20
                END
            ELSE 0 END) as overseas_income_amount,
        deductor_tan_no
    FROM (
        SELECT 
            CASE
                WHEN substr(B3, 4, 3) = 'Jan' THEN substr(B3, 8, 4) || '-01-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Feb' THEN substr(B3, 8, 4) || '-02-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Mar' THEN substr(B3, 8, 4) || '-03-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Apr' THEN substr(B3, 8, 4) || '-04-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'May' THEN substr(B3, 8, 4) || '-05-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Jun' THEN substr(B3, 8, 4) || '-06-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Jul' THEN substr(B3, 8, 4) || '-07-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Aug' THEN substr(B3, 8, 4) || '-08-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Sep' THEN substr(B3, 8, 4) || '-09-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Oct' THEN substr(B3, 8, 4) || '-10-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Nov' THEN substr(B3, 8, 4) || '-11-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Dec' THEN substr(B3, 8, 4) || '-12-' || substr(B3, 1, 2)
            END as formatted_date,
            B2,
            B7,
            deductor_tan_no
        FROM "26as_details"
        WHERE person_id = :person_id AND strftime('%Y-%m-%d', formatted_date) >= strftime('%Y-%m-%d', 'now', '-12 months')
    ) 
    GROUP BY strftime('%Y-%m', formatted_date)  
    """)


    
    overseas_income_result = await db.execute(overseas_income_query, {"person_id": person_id})
    overseas_income_raw_data = overseas_income_result.fetchall()
    total_overseas_income = 0.0
    for row in overseas_income_raw_data:
        month_year, amount, source = row
        total_overseas_income += amount
    total_income = total_salary  + total_business_income + total_overseas_income 

    # Calculate the percentage share of each income type
    salary_percentage = (total_salary / total_income * 100) if total_income > 0 else 0
    business_income_percentage = (total_business_income / total_income * 100) if total_income > 0 else 0
    overseas_income_percentage = (total_overseas_income / total_income * 100) if total_income > 0 else 0
    
    highlights = []
    
    if business_income_percentage + overseas_income_percentage >5:
        highlights.append(f"Additional income is available from other businesses. Since this income is more than 5% of the overall income, it should be declared.")
    elif (business_income_percentage>0 or overseas_income_percentage>0) and business_income_percentage + overseas_income_percentage <=5:
        highlights.append(f"Additional income is available from other businesses. But this income is less than or equal to 5% of the overall income.")
    elif  business_income_percentage<=0 and overseas_income_percentage<=0:
        highlights.append(f"No additional income is available from other businesses.")
        
    if business_income_percentage>salary_percentage:
        highlights.append(f"Business income is more than the Salary. This could lead to the candidate paying more attention to the additional income sources.")
    else:
        highlights.append(f"Salary income is more than the Business income. This has lesser chances of the candidate paying attention to the additional income sources.")
    if salary_percentage<50:
        highlights.append(f"Salary seems to be less than 50% of the candidate's income. Financial needs from Salary income does not sufficiently met. This could be a reason for future attrition.")
    else:
        highlights.append(f"Salary seems to be more than 50% of the candidate's income. Financial needs from Salary income sufficiently met.")
    
    if salary_percentage >=95:
        salary_text="Excellent"
    elif salary_percentage >= 90 and salary_percentage < 95:
        salary_text="Good"
    elif salary_percentage >=80 and salary_percentage <90:
        salary_text="Concern"
    else:
        salary_text="Bad"
    
    income_position = IncomePosition(total_income=round(total_income),
    salary_income=round(total_salary),
    salary_text=salary_text,
    salary_percentage=round(salary_percentage),
    business_income=round(total_business_income),
    business_percentage=round(business_income_percentage),
    overseas_income=round(total_overseas_income),
    overseas_percentage=round(overseas_income_percentage),
    highlights=highlights)
    
    
    
    #govt_docs
    query = text("""
        SELECT company_name,
            passbook_year,
            passbook_month
        FROM
            get_passbook_details
        WHERE person_id = :person_id
        GROUP BY
            company_name, passbook_year, passbook_month
    """
    )
    
    result = await db.execute(query, {"person_id": person_id})
    passbook_raw_data = result.fetchall()
    logger.debug(passbook_raw_data)
    company_data = defaultdict(list)
    if len(passbook_raw_data):
        for exp in passbook_raw_data:
            company_name = exp[0]
            year = exp[1]
            month = exp[2]

            date = await convert_to_datetime(year,month) 
            if date:
                company_data[company_name].append(date)
            else:
                company_data[company_name].append("N/A")
            
    work_exp = []
    overlapping_durations=[]
    gaps=[]
    duration = []
    flag = False
    companies_without_dates = []
    if len(company_data):
        for company_name, dates in company_data.items():
            if dates != ["N/A"]:
                # Parse the start and end dates into datetime objects
                start_date = min(dates)
                end_date = max(dates)
                start_date_formatted = start_date.strftime("%m-%d-%Y")
                end_date_formatted = end_date.strftime("%m-%d-%Y")
                
                # Calculate the difference in months
                total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                
                # Append the data to work_exp with the new "totalMonth" key
                work_exp.append(
                    {
                        "company_name": company_name, 
                        "start_date": start_date_formatted, 
                        "end_date": end_date_formatted,
                        "totalMonth": total_months,  
                        "type": "work_exp"
                    }
                )
                duration.append(total_months)
            else:
                work_exp.append(
                    {
                        "company_name": company_name, 
                        "start_date": "N/A",
                        "end_date": "N/A",
                        "totalMonth": 0,
                        "type":"work_exp"
                        }
                    )
                flag = True
                companies_without_dates.append(company_name)
                
    logger.debug(work_exp)
    logger.debug(duration)
    logger.debug(companies_without_dates)
    total_duration = float(sum(duration)/12) if len(duration) else 0.0
    total_duration = round(total_duration, 0)
    logger.debug(total_duration)
    #median_duration = statistics.median(duration)
    #average_duration = statistics.mean(duration)
    if len(duration):
        median_duration = int(statistics.median(duration))
        average_duration = int(statistics.mean(duration))
    else:
        median_duration = 0
        average_duration = 0
    logger.debug(median_duration)
    logger.debug(average_duration)
    if average_duration < 15:
        risk_duration = "Very High"
    elif 15 <= average_duration < 35:
        risk_duration = "High"
    elif 35 <= average_duration <60:
        risk_duration = "Optimal"    
    else:
        risk_duration = "Low"
    
    if len(work_exp):
        for i, entry1 in enumerate(work_exp):
            # if entry1["end_date"]!="N/A":
            #     end_date1 = convert_to_datetime(entry1["end_date"].split("-")[1], entry1["end_date"].split("-")[0])
            if entry1["end_date"]!="N/A":
                end_date1 = await convert_to_datetime(entry1["end_date"].split("-")[1], entry1["end_date"].split("-")[0])        

                for entry2 in work_exp[i+1:]:
                    # if entry2["start_date"]!="N/A":
                    #     start_date2 = convert_to_datetime(entry2["start_date"].split("-")[1], entry2["start_date"].split("-")[0])
                    if entry2["start_date"]!="N/A":
                        start_date2 = await convert_to_datetime(entry2["start_date"].split("-")[1], entry2["start_date"].split("-")[0])
                        
                        #overlapping
                        
                        if end_date1 > start_date2:
                            start_date_dt = datetime.datetime.strptime(entry2["start_date"], "%m-%d-%Y")
                            end_date_dt = datetime.datetime.strptime(entry1["end_date"], "%m-%d-%Y")
                            total_months = (end_date_dt.year - start_date_dt.year) * 12 + (end_date_dt.month - start_date_dt.month)

                            overlapping_durations.append({
                            "company_name": entry2["company_name"],
                            "start_date": entry2["start_date"],
                            "end_date": entry1["end_date"],
                            "totalMonth": total_months,
                            "type":"overlap"
                            })

                        #gaps
                        
                        if end_date1 < start_date2:
                            end_date1_datetime = datetime.datetime.strptime(end_date1, "%m-%d-%Y")
                            gap_start_date = (end_date1_datetime + datetime.timedelta(days=1)).strftime("%m-%d-%Y")
                            
                            start_date2_datetime = datetime.datetime.strptime(start_date2, "%m-%d-%Y")
                            gap_end_date = (start_date2_datetime - datetime.timedelta(days=1)).strftime("%m-%d-%Y")
                            gaps.append({"start_date": gap_start_date, "end_date": gap_end_date,"type":"gaps"})
    
    logger.debug(overlapping_durations)
    logger.debug(gaps)              
    #tenure
    
    resume_query = text("""
        SELECT company,
            from_date,
            to_date
        FROM
            tenure
        WHERE formid =:formid
    """
    )
    
    result = await db_backend.execute(resume_query, {"formid": person_id})
    resume_raw_data = result.fetchall()
    logger.debug(resume_raw_data)
    company_data = []
    for exp in resume_raw_data:
        company = exp[0]
        from_date = datetime.datetime.strptime(exp[1],"%Y-%m-%d")
        to_date = datetime.datetime.strptime(exp[2],"%Y-%m-%d")
        total_months = (to_date.year - from_date.year) * 12 + (from_date.month - to_date.month)
        
        from_date = from_date.strftime("%m-%d-%Y")
        to_date = to_date.strftime("%m-%d-%Y")
        
        
        
        company_data.append(
            {
                "company_name":company,
                "start_date":from_date,
                "end_date":to_date,
                "totalMonth": total_months,
                "type":"work_exp"
                }
            )
        
    overlapping_durations_tenure=[]
    gaps_tenure = []
    logger.debug(company_data)
    for i, entry1 in enumerate(company_data):
        end_date1 = entry1["end_date"]
        for entry2 in company_data[i+1:]:
            start_date2 = entry2["start_date"]
            if end_date1 > start_date2:
                overlapping_durations_tenure.append({
                        "company_name": entry2["company_name"],
                        "start_date": entry2["start_date"],
                        "end_date": entry1["end_date"],
                        "type":"overlap"
                        })
                
            if end_date1 < start_date2:
                end_date1_datetime = datetime.datetime.strptime(end_date1, "%m-%d-%Y")
                gap_start_date = (end_date1_datetime + datetime.timedelta(days=1)).strftime("%m-%d-%Y")
                
                start_date2_datetime = datetime.datetime.strptime(start_date2, "%m-%d-%Y")
                gap_end_date = (start_date2_datetime - datetime.timedelta(days=1)).strftime("%m-%d-%Y")
                gaps_tenure.append({"start_date": gap_start_date, "end_date": gap_end_date,"type":"gaps"})
    logger.debug(overlapping_durations_tenure)
    logger.debug(gaps_tenure)
    #discrepancies
    
    overlapping_gaps = []
    if len(gaps):
        for gap in gaps:
            gap_start = gap["start_date"]
            gap_end = gap["end_date"]

            for exp in company_data:
                exp_start = exp["start_date"]
                exp_end = exp["end_date"]

                if(await overlap(gap_start, gap_end, exp_start, exp_end)):
                    overlapping_gaps.append(gap)
                    break 
        
    all_exp_govt_docs = work_exp + overlapping_durations + gaps
    
    all_exp_tenure = company_data + overlapping_durations_tenure + gaps_tenure
    
    other_income_query = text("""
                                 SELECT COUNT(distinct "deductor_tan_no") AS NO_OF_SOURCE FROM "26as_details" WHERE "A2(section_1)" IN('194DA', '194I(a)', '194I(b)', '194I', '194LA', '194S', '194M', '194N', '194P', '194Q', '196DA', '206CA', '206CB', '206CC', '206CD', '206CE', '206CF', '206CG', '206CH', '206CI', '206CJ', '206CK', '206CL', '206CM', '206CP', '206CR') AND person_id = :person_id
                                 """)
    
    business_income_query = text("""
                                 SELECT COUNT(distinct "deductor_tan_no") AS NO_OF_SOURCE FROM "26as_details" WHERE "A2(section_1)" IN('194C', '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O') AND person_id = :person_id
                                 """)
    
    overseas_income_query = text("""
                                 SELECT COUNT(distinct "deductor_tan_no") AS NO_OF_SOURCE FROM "26as_details" WHERE "B2" IN('206CQ','206CO') AND person_id = :person_id
                                 """)
    
    personal_income_query = text("""
                                 SELECT COUNT(distinct "deductor_tan_no") AS NO_OF_SOURCE FROM "26as_details" WHERE "A2(section_1)" IN('192A','193', '194', '194A', '194B', '194BB', '194EE', '194F', '194G', '194IA', '194IB', '194K', '194LB', '194LBB', '194LBC', '194S', '194LD') AND person_id = :person_id
                                 """)
    other_income = await db.execute(other_income_query,{"person_id":person_id})
    business_income = await db.execute(business_income_query, {"person_id": person_id})
    overseas_income = await db.execute(overseas_income_query, {"person_id": person_id})
    personal_income = await db.execute(personal_income_query, {"person_id": person_id})
    
    no_of_other_sources = other_income.fetchall()
    no_of_business_sources = business_income.fetchall()
    no_of_overseas_sources = overseas_income.fetchall()
    no_of_personal_sources = personal_income.fetchall()
    
    for i in no_of_other_sources:
        other_count = i[0]
    
    for i in no_of_business_sources:
        business_count = i[0]
        
    for i in no_of_overseas_sources:
        overseas_count = i[0]
    
    for i in no_of_personal_sources:
        personal_count = i[0]
    
    red_flag = len(overlapping_durations) + business_count + other_count + overseas_count + personal_count
    discrepancies = len(overlapping_gaps)
    good_to_know = len(gaps)
    
    if len(all_exp_govt_docs):
        for i in all_exp_govt_docs:
            if i['start_date'] =='N/A' or i['end_date'] =='N/A':
                for j in all_exp_tenure:
                    if fuzz.partial_ratio(i['company_name'],j['company_name']) >= 80:
                        i['start_date'] , i['end_date'], i['totalMonth'] = j['start_date'], j['end_date'], j['totalMonth']
                        flag = False
                        if i['company_name'] in companies_without_dates:
                            companies_without_dates.remove(i['company_name']) 
                            
        #final_exp_govt_docs = list(filter(lambda i: i['start_date'] != 'N/A' and i['end_date'] != 'N/A', all_exp_govt_docs))
        
        #Removing elements with "N/A" dates and checking if still "N/A" exists in multiple "N/A" cases
        final_exp_govt_docs=[]
        for i in all_exp_govt_docs:
            if i['start_date'] != 'N/A' or i['end_date'] !='N/A':
                final_exp_govt_docs.append(i)
            else:
                flag=True
    
    highlight = []
    if good_to_know == 0:
        highlight.append(f"No GAPs are identified that is not reflected in the resume")
    else:
        highlight.append(f"{good_to_know} GAPs are identified that is not reflected in the resume")
        
    if len(overlapping_durations) == 0:
        highlight.append(f"No situation of dual employment found (Red Flag)")
    else:
        highlight.append(f"{len(overlapping_durations)} situation of dual employment found (Red Flag)")
    
    #business_income=business_count+overseas_count+other_count
    
    if business_count == 0:
        business_count = "No"
    if other_count == 0:
        other_count = "No"
    if overseas_count == 0:
        overseas_count = "No"
    if personal_count == 0:
        personal_count = "No"
           
    highlight.append(f"{business_count} situations of Business, {overseas_count} situations of overseas, {personal_count} situations of personal and {other_count} situations of other Income identified that could be related to moonlighting (Red Flag)" ) 
   
    
    
    if flag == True:
        if len(companies_without_dates) >1:
            company_list = ','.join(map(str,companies_without_dates))
            highlight.append(f"No starting date and ending date of employment found for these companies - {company_list} in government documents")
        else:
            highlight.append(f"No starting date and ending date of employment found for {companies_without_dates[0]} in government documents")
    
    first_name = await db_backend.execute(
        text('SELECT firstName '
             'FROM `form` '
             'WHERE appid = :id'
        ),
        {"id": person_id}
    )        
    firstname = first_name.fetchone()
    name = firstname[0]
    if average_duration <24:
        remark = "short"
    elif 24<= average_duration<=60:
        remark = "average"
    else:
        remark = "Long"                    
    tenure_remarks = f"{name}'s tenure with companies seem to be {remark}. This could be linked to his personal performance or market opportunity."
    
    exp_summary=ExperienceSummary(total_experience = total_duration,
    median_tenure=median_duration,
    median_tenure_text=risk_duration,
    dual_employment=len(overlapping_durations),
    dual_employment_text="Bad" if len(overlapping_durations)>0 else "Good",
    overlapping_contract=business_count,
    overlapping_contract_text="Bad" if business_count>0 else "Good",
    tenure_highlights= tenure_remarks,
    exp_highlights=highlight)
    ###
    xx = await db_backend.execute(
        text('SELECT compid '
             'FROM `applicationlist` '
             'WHERE id = :id'
        ),
        {"id": person_id}
    )        
    yy = xx.fetchone()
    #print(yy)
    ##Extracting currentctc, offeredctc from compcanlist
    result = await db_backend.execute(
        text('SELECT currentctc, rolebudget, offeredctc '
             'FROM `compcanlist` '
             'WHERE id = :id'
        ),
        {"id": yy[0]}
    )

    ctc_info = result.fetchone()
    #print(ctc_info)
    if ctc_info is None:
        raise HTTPException(status_code=404, detail=f"Personal information not found for id {person_id}")

    currentctc = round(float(ctc_info[0]),0)
    offeredctc = round(float(ctc_info[2]),0)

    offered_ctc_percentange = round(float((offeredctc/4000000)*100),0)
    if offered_ctc_percentange < 50:
        output = "LOW"
    elif 50<= offered_ctc_percentange<75:
        output = "Optimal"
    elif 75<= offered_ctc_percentange<90:
        output="High"
    else:
        output= "Very High"

    monthly_income_query = text("""
        SELECT 
            strftime('%Y-%m', formatted_date) as month_year,
            (CASE WHEN "A2(section_1)" LIKE '192%' THEN CAST("A7(paid_credited_amt)" AS FLOAT) ELSE 0 END) as salary_amount
        FROM (
            SELECT 
                CASE
                    WHEN substr("A3(transaction_dt)", 4, 3) = 'Jan' THEN substr("A3(transaction_dt)", 8, 4) || '-01-' || substr("A3(transaction_dt)", 1, 2)
                    WHEN substr("A3(transaction_dt)", 4, 3) = 'Feb' THEN substr("A3(transaction_dt)", 8, 4) || '-02-' || substr("A3(transaction_dt)", 1, 2)
                    WHEN substr("A3(transaction_dt)", 4, 3) = 'Mar' THEN substr("A3(transaction_dt)", 8, 4) || '-03-' || substr("A3(transaction_dt)", 1, 2)
                    WHEN substr("A3(transaction_dt)", 4, 3) = 'Apr' THEN substr("A3(transaction_dt)", 8, 4) || '-04-' || substr("A3(transaction_dt)", 1, 2)
                    WHEN substr("A3(transaction_dt)", 4, 3) = 'May' THEN substr("A3(transaction_dt)", 8, 4) || '-05-' || substr("A3(transaction_dt)", 1, 2)
                    WHEN substr("A3(transaction_dt)", 4, 3) = 'Jun' THEN substr("A3(transaction_dt)", 8, 4) || '-06-' || substr("A3(transaction_dt)", 1, 2)
                    WHEN substr("A3(transaction_dt)", 4, 3) = 'Jul' THEN substr("A3(transaction_dt)", 8, 4) || '-07-' || substr("A3(transaction_dt)", 1, 2)
                    WHEN substr("A3(transaction_dt)", 4, 3) = 'Aug' THEN substr("A3(transaction_dt)", 8, 4) || '-08-' || substr("A3(transaction_dt)", 1, 2)
                    WHEN substr("A3(transaction_dt)", 4, 3) = 'Sep' THEN substr("A3(transaction_dt)", 8, 4) || '-09-' || substr("A3(transaction_dt)", 1, 2)
                    WHEN substr("A3(transaction_dt)", 4, 3) = 'Oct' THEN substr("A3(transaction_dt)", 8, 4) || '-10-' || substr("A3(transaction_dt)", 1, 2)
                    WHEN substr("A3(transaction_dt)", 4, 3) = 'Nov' THEN substr("A3(transaction_dt)", 8, 4) || '-11-' || substr("A3(transaction_dt)", 1, 2)
                    WHEN substr("A3(transaction_dt)", 4, 3) = 'Dec' THEN substr("A3(transaction_dt)", 8, 4) || '-12-' || substr("A3(transaction_dt)", 1, 2)
                END as formatted_date,
                "A2(section_1)",
                "A7(paid_credited_amt)"
            FROM "26as_details"
            WHERE person_id = :person_id 
            AND strftime('%Y-%m-%d', formatted_date) >= strftime('%Y-%m-%d', 'now', '-12 months')
        ) 
        GROUP BY strftime('%Y-%m', formatted_date)
    """)
    monthly_income_result = await db.execute(monthly_income_query, {"person_id":person_id})
    monthly_income_raw_data = monthly_income_result.fetchall()
    
    
    pf_result = await db.execute(
        text('SELECT "employer_total" '
             'FROM "get_passbook_details" '
             'WHERE "person_id" = :id'
        ),
        {"id": person_id}
    )
    pf_summary = pf_result.fetchone()
    pf = 0
    if pf_summary:
        pf = pf_summary[0] if pf_summary[0] is not None else 0
    differences = []

    for i in range(1, len(monthly_income_raw_data)):
        date, value = monthly_income_raw_data[i]
        previous_value = monthly_income_raw_data[i - 1][1]
        difference = abs(value - previous_value)
        differences.append(difference)

    max_difference_value = int(max(differences))
    #print(differences)
    monthly_income_dict = dict(monthly_income_raw_data)
    salary_list = list(monthly_income_dict.values())
    #print(salary_list)
    if len(salary_list) != 12:
        total_salary = int(((sum(salary_list)-max_difference_value)/len(salary_list))*12)
    else:
        total_salary = int((sum(salary_list))- max_difference_value)   

    net_ctc = total_salary + max_difference_value + pf
    possible_ctc_variation = int(net_ctc*15/100)
    estimated_ctc_range = f"{net_ctc}-{net_ctc+possible_ctc_variation}"
    most_likely_past_ctc = int((net_ctc+possible_ctc_variation/2))
    gap = int(currentctc-most_likely_past_ctc)      
    ctc_accuracy = min(int((most_likely_past_ctc/currentctc)*100),100)

    if ctc_accuracy < 80:
        remark = "Incorrect"
    elif 80<= ctc_accuracy < 90:
        remark = "Concern"
    elif 90<= ctc_accuracy < 95:
        remark = "Close"
    else:
        remark = "Exact"

    if ctc_accuracy<90:
        highlite = " Past CTC declared by the candidate does not seem to be close to the actual. Candidate is most probably inflating it to negotiate a better offer."
    elif 90<= ctc_accuracy<95:
        highlite = " Past CTC declared by the candidate seems to be close to the actual "
    else:
        highlite = " Past CTC declared by the candidate seems to be exact to the actual "            
    
    #expense
    query_2 = text("""
    SELECT DISTINCT person_id, AccountNumber, AccountType, LastPayment, AccountStatus
    FROM "RetailAccountDetails"
    WHERE person_id = :person_id AND AccountStatus = "Current Account"
    """)


    result_2 = await db.execute(query_2, {"person_id": person_id})
    summary_2 = result_2.fetchall()
    if not summary_2:
        emi = 0
    else:
        emi = sum(float(row[3]) for row in summary_2 if row[3] is not None and row[3] != "")
            
    #        raise HTTPException(status_code=404, detail=f"No records found for person_id {person_id}")

    
    factor=0.3
    new_exp = ((offeredctc)*0.4)+emi
    pre_exp = ((currentctc)*0.4)+emi
    most_likely_expense = round(float((pre_exp+new_exp)/2),0)
    income_summary_ratio = float((most_likely_expense/currentctc)*100)
    if income_summary_ratio<50:
        income_summary_highlight = "Household income is very stable with a very high potential of savings."
    elif 50<=income_summary_ratio< 80:
        income_summary_highlight= "Household income is stable with a low potential of savings."
    else:
        income_summary_highlight = "Household income is not stable."       
    
    #response
    idealctc= Ideal_ctc(
        lower=800000,
        upper=4000000
    )
    offered_ctc_summary= offered_past_ctc_summary(
        declared_past_ctc=currentctc,
        declared_past_ctc_remark= remark,
        most_likely_past_ctc= net_ctc,
        highlight_1=highlite,
        offered_ctc= offeredctc,
        offered_ctc_remark= output,
        ideal_ctc_band=idealctc,
        highlight_2=f"Offered CTC will be {output} Cost to the Company"
        )
    declared_household_income = declared_household_income_summary(
        candidate_ctc= offeredctc,
        spouse_ctc=0,
        household_ctc=offeredctc,
        mostlikely_expense=most_likely_expense,
        highlight=income_summary_highlight
    )
    ###contact
    result_1 = await db_backend.execute(
    text('SELECT firstName, lastName, phone, email, city '
         'FROM `form` WHERE appid = :id'),
    {"id": person_id}
    )

    contact_info_1 = result_1.fetchone()

    if contact_info_1 is None:
        raise HTTPException(status_code=404, detail=f"Personal information not found for id : {person_id}")

    result_3 = await db.execute(
        text('SELECT "pan_name","contact_primary_mobile","contact_primary_email","address_post_office","address_city","address_state","address_pin_code"'
             'FROM "download_profile" WHERE person_id = :id'),
        {"id": person_id}
    )
    contact_info_3 = result_3.fetchone()

    if contact_info_3 is None:
        raise HTTPException(status_code=404, detail=f"Personal information not found for id {person_id}")

    name_flag, pan_match, aadhar_match, tax_match, name_remarks = await check_discrepancy_1(
        f"{contact_info_1[0]} {contact_info_1[1]}", contact_info_3[0], "N/A", contact_info_3[0], "Name")

    mobile_flag, pan_match_mobile, aadhar_match_mobile, government_match_mobile, mobile_remarks = await check_discrepancy(
        contact_info_1[2], contact_info_3[1], "N/A", contact_info_3[1], "Mobile")

    email_flag, pan_match_email, aadhar_match_email, government_match_email, email_remarks = await check_discrepancy(
        contact_info_1[3], contact_info_3[2], "N/A", contact_info_3[2], "Email")

    address_flag, pan_match_address, aadhar_match_address, government_match_address, address_remarks = await check_discrepancy_address(
        contact_info_1[4] if contact_info_1[4] is not None else "N/A", f"{contact_info_3[3]},{contact_info_3[4]},{contact_info_3[5]},{contact_info_3[6]}", "N/A", f"{contact_info_3[3]},{contact_info_3[4]},{contact_info_3[5]},{contact_info_3[6]}", "Address")

    name_response = Name(
        provided=f"{contact_info_1[0]} {contact_info_1[1]}",
        Pan=contact_info_3[0],
        Aadhar="N/A",
        Tax=contact_info_3[0],
        flag=name_flag,
        pan_match=pan_match,
        aadhar_match=aadhar_match,
        tax_match=tax_match,
        remarks=name_remarks
    )

    mobile_response = Mobile(
        provided=contact_info_1[2],
        Pan=contact_info_3[1],
        Aadhar="N/A",
        Government= contact_info_3[1],
        flag=mobile_flag,
        pan_match=pan_match_mobile,
        aadhar_match=aadhar_match_mobile,
        government_match=government_match_mobile,
        remarks=mobile_remarks
    )

    email_response = Email(
        provided=contact_info_1[3],
        Pan=contact_info_3[2],
        Aadhar="N/A",
        Government=contact_info_3[2],
        flag=email_flag,
        pan_match=pan_match_email,
        aadhar_match=aadhar_match_email,
        government_match=government_match_email,
        remarks=email_remarks
    )

    address_response = Address(
        provided=contact_info_1[4] if contact_info_1[4] is not None else "N/A",
        Pan=f"{contact_info_3[3]},{contact_info_3[4]},{contact_info_3[5]},{contact_info_3[6]}",
        Aadhar="N/A",
        Government=f"{contact_info_3[3]},{contact_info_3[4]},{contact_info_3[5]},{contact_info_3[6]}",
        flag=address_flag,
        pan_match=pan_match_address,
        aadhar_match=aadhar_match_address,
        government_match=government_match_address,
        remarks=address_remarks
    )
    consistency_name = 1 if name_response.provided == name_response.Pan==name_response.Aadhar == name_response.Tax else 0
    consistency_phone = 1 if mobile_response.provided == mobile_response.Pan == mobile_response.Aadhar == mobile_response.Government else 0
    consistency_email = 1 if email_response.provided == email_response.Pan == email_response.Aadhar == email_response.Government else 0
    consistency_address = 1 if address_response.provided == address_response.Pan ==address_response.Aadhar == address_response.Government else 0

    # consistency_name = 1 if name_response.provided == name_response.Pan == name_response.Tax else 0
    # consistency_phone = 1 if mobile_response.provided == mobile_response.Pan == mobile_response.Government else 0
    # consistency_email = 1 if email_response.provided == email_response.Pan ==  email_response.Government else 0
    # consistency_address = 1 if address_response.provided  ==address_response.Aadhar == address_response.Government else 0

    discrepancy_name = 1 - consistency_name
    discrepancy_phone = 1 - consistency_phone
    discrepancy_email = 1 - consistency_email
    discrepancy_address = 1 - consistency_address

    consistency= []
    discrepancy=[]
    
    
    if consistency_name == 1:
        consistency.append("Name")
    else:
        discrepancy.append("Name")

    
    if consistency_phone == 1:
        consistency.append("Mobile")
    else:
        discrepancy.append("Mobile")        
    
    
    if consistency_email == 1:
        consistency.append("Email")
    else:
        discrepancy.append("Email")

    
    if consistency_address == 1:
        consistency.append("Address")
    else:
        discrepancy.append("Address")
    
    if consistency:
        note_1= f"{', '.join(consistency)} are Consistent."
    else:
        note_1 =""
    if discrepancy:
        note_2= f"{', '.join(discrepancy)} have Discrepancies."
    else:
        note_2 =""
    
    
    name_issue = 0
    mobile_issue =0
    email_issue = 0
    address_issue = 0
    if name_response.pan_match == True:
        name_issue+=0
    else:
        name_issue+=1    
    if name_response.aadhar_match == True:
        name_issue+=0
    else:
        name_issue+=1
    if name_response.tax_match == True:
        name_issue+=0
    else:
        name_issue+=1
    
    if mobile_response.pan_match == True:
        mobile_issue+=0
    else:
        mobile_issue+=1    
    if mobile_response.aadhar_match == True:
        mobile_issue+=0
    else:
        mobile_issue+=1
    if mobile_response.government_match == True:
        mobile_issue+=0
    else:
        mobile_issue+=1

    if email_response.pan_match == True:
        email_issue+=0
    else:
        email_issue+=1    
    if email_response.aadhar_match == True:
        email_issue+=0
    else:
        email_issue+=1
    if email_response.government_match == True:
        email_issue+=0
    else:
        email_issue+=1

    if address_response.pan_match == True:
        address_issue+=0
    else:
        address_issue+=1    
    if address_response.aadhar_match == True:
        address_issue+=0
    else:
        address_issue+=1
    if address_response.government_match == True:
        address_issue+=0
    else:
        address_issue+=1   
    
    if name_issue == 0:
        name_text_1 = ""
        name_text_2 = "No issue"
    elif name_issue == 1:
        name_text_1 = "Concern"
        name_text_2 = "1 issue"
    else:
        name_text_1 = "Concern"
        name_text_2 =f"{name_issue} issues"
    
    if address_issue == 0:
        address_text_1 = ""
        address_text_2 = "No issue"
    elif address_issue == 1:
        address_text_1 = "Concern"
        address_text_2 = "1 issue"
    else:
        address_text_1 = "Concern"
        address_text_2 =f"{address_issue} issues"            
    
    if mobile_issue == 0:
        mobile_text_1 = ""
        mobile_text_2 = "No issue"
    elif name_issue == 1:
        mobile_text_1 = "Concern"
        mobile_text_2 = "1 issue"
    else:
        mobile_text_1 = "Concern"
        mobile_text_2 =f"{mobile_issue} issues"
        
    if email_issue == 0:
        email_text_1 = ""
        email_text_2 = "No issue"
    elif email_issue == 1:
        email_text_1 = "Concern"
        email_text_2 = "1 issue"
    else:
        email_text_1 = "Concern"
        email_text_2 =f"{email_issue} issues"
    
    
    mobile_ = Mobile_(
        remark=mobile_text_1,
        issue = mobile_text_2
    )
    name_ = Name_(
        remark = name_text_1,
        issue = name_text_2
    )
    email_ = Email_(
        remark=email_text_1,
        issue = email_text_2
    )
    address_ = Address_(
        remark = address_text_1,
        issue = address_text_2
    )
    contact_=contact_information(
        name=name_,
        mobile=mobile_,
        email= email_,
        address= address_,
        highlight_1 = note_1,
        highlight_2 = note_2
    )
    # edited by samiran 1046-1069
    #aadhar_issue=0
    #pan_issue=0
    #pan_text = None
    #aadhar_text = None
    #temp = await iden_info(int(person_id))
    #highlight=temp["Remarks"]
    #if temp["Aadhar_Status"] == 'Concern':
    #    aadhar_text = "Concern"
    #    if temp["Extracted_Aadhar_Number_flag"]==False:
    #        aadhar_issue+=1
    #    if temp["Aadhar_Number_flag"]==False:
    #        aadhar_issue+=1
    #    if temp["govt_aadhaar_number_flag"]==False:
    #        aadhar_issue+=1
    #        aadhar_text = "Bad"
    #if temp["Pan_Status"] == 'Concern':
    #    pan_text = "Concern"
    #    if temp["govt_pan_number_flag"]==False:
    #        pan_issue+=1
    #        pan_text = "Bad"
    #    if temp["Extracted_Pan_Number_flag"]==False:
    #        pan_issue+=1
    #    if temp["Pan_Number_flag"]==False:
    #        pan_issue+=1
    aadhar_issue = 0
    pan_issue = 0
    aadhar_text = None
    pan_text = None

    temp = await iden_info(int(person_id),session)
    highlight = temp["Remarks"]

# Check for Aadhar status
    if temp["Aadhar_Status"] in ['Concern', 'Bad']:
        aadhar_text = temp["Aadhar_Status"]
        aadhar_flags = [
            temp["Extracted_Aadhar_Number_flag"],
            temp["Aadhar_Number_flag"],
            temp["govt_aadhaar_number_flag"]
        ]
        aadhar_issue = aadhar_flags.count(False)

# Check for PAN status
    if temp["Pan_Status"] in ['Concern', 'Bad']:
        pan_text = temp["Pan_Status"]
        pan_flags = [
            temp["govt_pan_number_flag"],
            temp["Extracted_Pan_Number_flag"],
            temp["Pan_Number_flag"]
        ]
        pan_issue = pan_flags.count(False)




    iden=identity_info(
        pan_issue=pan_issue,
        aadhar_issue=aadhar_issue,
        highlight=highlight,
        pan_text=pan_text,
        aadhar_text=aadhar_text
    ) 
    return Summary(income_position=income_position,
                   experience_summary=exp_summary,
                   ctc_summary=offered_ctc_summary,
                   household_income_summary=declared_household_income,
                   contact =contact_,
                   identity=iden
                   )