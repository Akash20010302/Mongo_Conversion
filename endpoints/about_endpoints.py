from typing import DefaultDict
from fastapi import APIRouter, Depends, HTTPException
from async_sessions.sessions import get_db, get_db_backend
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from models.About import HouseholdIncome, Info
from starlette.status import HTTP_404_NOT_FOUND
from tools.benchmark_tools import convert_to_datetime
from loguru import logger

about_router = APIRouter()

@about_router.get("/about_user/{id}", response_model=Info, tags=['About'])
async def about_user(id: int, db_1: AsyncSession = Depends(get_db_backend), db_2: AsyncSession = Depends(get_db)):
    # Fetch data from the first database
    result_1 = await db_1.execute(
        text('SELECT firstName, middleName, lastName, phone, email, dob, age, gender, marital_status, '
        'education, experience, city, salary, home, homeLoan, car, carLoan, twoWheeler, twoWheelerLoan, '
        'creditCard, personalLoan, stocks, realEstate,spouseExperience, totalkids, '
        'totaladults FROM `form` WHERE appid = :id'),# changed id to appid
        {"id": id}
    )
#     result_1 = await db_1.execute(
#     text('SELECT `firstName`, `middleName`, `lastName`, phone, email, dob, age, gender, marital_status, '
#     'education, experience, city, salary, home, `homeLoan`, car, `carLoan`, `twoWheeler`, `twoWheelerLoan`, '
#     '`creditCard`, `personlLoan`, stocks, `realEstate`,`spouseExperience`, totalkids, '
#     'totaladults FROM `form` WHERE appid = :id'),
#     {"id": id}
# )


    personal_info_1 = result_1.fetchone()

    if personal_info_1 is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Personal information not found for id : {id}")

    salary_response = HouseholdIncome(
        candidate_monthly_take=personal_info_1[12],
        spouse_monthly_take=0,
        total_family_income=personal_info_1[12]
    )
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
    
    result = await db_2.execute(query, {"person_id": id})
    passbook_raw_data = result.fetchall()
    
    company_data = DefaultDict(list)
    for exp in passbook_raw_data:
        company_name = exp[0]
        year = exp[1]
        month = exp[2]

        date = await convert_to_datetime(year,month) 
        if date:
            company_data[company_name].append(date)
        else:
            company_data[company_name].append("N/A")
            
    result = []
    durations = []
    
    for company_name, date_list in company_data.items():
        logger.debug(date_list)
        dates = [date for date in date_list if date !="N/A"]
        if len(dates):
            start_date = min(dates)
            end_date = max(dates)
            duration = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            result.append({"company_name": company_name, "start_date": start_date.strftime("%m-%Y"), "end_date": end_date.strftime("%m-%Y"), "duration":duration})
            
            durations.append(duration)
    total_duration = float(sum(durations)/12)
    total_duration = round(total_duration, 2)

    ##extracting role from tenure

    result_role = await db_1.execute(
        text('SELECT "role" '
        'FROM `tenure` WHERE formid = :id'),# changed id to appid
        {"id": id}
    )
    role = result_role.fetchone()

    #logger.debug(f"PERSONAL INFO: {personal_info_1}")

    # Combine data from both databases into the Info response
    return Info(
        firstName=personal_info_1[0],
        middleName=personal_info_1[1],
        lastName=personal_info_1[2],
        phone=personal_info_1[3],
        email=personal_info_1[4],
        city = personal_info_1[11] if personal_info_1[11] is not None else "N/A",
        gender=personal_info_1[7],
        dob=personal_info_1[5],
        age=personal_info_1[6],
        marital_status=personal_info_1[8],
        spouse_work_status= "N/A",
        spouse_employer="N/A",
        kidsnum=personal_info_1[24] if personal_info_1[24] is not None else 0,
        adultdependents=personal_info_1[25],
        home=personal_info_1[13],
        car=personal_info_1[15],
        twoWheeler=personal_info_1[17],
        creditCard=personal_info_1[19],
        Loan=any([personal_info_1[14], personal_info_1[16], personal_info_1[18], personal_info_1[20]]),
        Investment=any([personal_info_1[21], personal_info_1[22]]),
        education=personal_info_1[9],
        education_institute="N/A",
        location=personal_info_1[11],
        total_experience=total_duration,
        work_industry= "N/A",
        skillset="N/A",
        current_role=role[0] if role is not None else "N/A",
        tenure_last_job=personal_info_1[10],
        household_income= salary_response
        )