from collections import defaultdict
from typing import DefaultDict
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from db.db import get_db_analytics, get_db_backend
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from email_response import send_email
from models.About import HouseholdIncome, Info
from starlette.status import HTTP_404_NOT_FOUND
from tools.benchmark_tools import convert_to_datetime
from starlette import status
from loguru import logger

about_router = APIRouter()

mandatory_fields = ["firstName", "lastName", "phone", "email", "dob", "age", "gender", "marital_status", "education", "experience", "city", "salary"]
@about_router.get("/about_user/{id}", response_model=Info, tags=["About"])
async def about_user(
    id: int,
    db_1: Session = Depends(get_db_backend),
    db_2: Session = Depends(get_db_analytics),
):
    try:
        # Fetch data from the first database
        result_1 = db_1.exec(
            text(
                "SELECT firstName, middleName, lastName, phone, email, dob, age, gender, marital_status, "
                "education, experience, city, salary, home, homeLoan, car, carLoan, twoWheeler, twoWheelerLoan, "
                "creditCard, personalLoan, stocks, realEstate,spouseExperience, totalkids, "
                "totaladults FROM `form` WHERE appid = :id"
            ).params(id=id)
        )

        personal_info_1 = result_1.fetchone()

        #if personal_info_1 is None:
        #    raise HTTPException(
        #        status_code=HTTP_404_NOT_FOUND,
        #        detail=f"Personal information not found for id : {id}",
        #    )
        missing_fields = [field for field, index in zip(mandatory_fields, range(len(mandatory_fields))) if personal_info_1[index] is None]       
        if missing_fields:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The following mandatory fields are missing: {', '.join(missing_fields)}")
        
        
        salary_response = HouseholdIncome(
            candidate_monthly_take=personal_info_1[12],
            spouse_monthly_take=0,
            total_family_income=personal_info_1[12],
        )
        query = text(
            """
            SELECT company_name,
                passbook_year,
                passbook_month
            FROM
                epfo_get_passbook_details
            WHERE application_id = :application_id
            GROUP BY
                company_name, passbook_year, passbook_month
        """
        )

        result = db_2.exec(query.params(application_id=id))
        passbook_raw_data = result.fetchall()

        company_data = defaultdict(list)
        if len(passbook_raw_data):
            for exp in passbook_raw_data:
                company_name = exp[0]
                year = exp[1]
                month = exp[2]

                date = await convert_to_datetime(year, month)
                if date:
                    company_data[company_name].append(date)
                else:
                    company_data[company_name].append("N/A")

        work_exp = []
        durations = []

        if len(company_data):
            for company_name, date_list in company_data.items():
                dates = [date for date in date_list if date != "N/A"]
                if len(dates):
                    start_date = min(dates)
                    end_date = max(dates)
                    start_date_formatted = start_date.strftime("%m-%d-%Y")
                    end_date_formatted = end_date.strftime("%m-%d-%Y")

                    total_months = (end_date.year - start_date.year) * 12 + (
                        end_date.month - start_date.month
                    )

                    work_exp.append(
                        {
                            "company_name": company_name,
                            "start_date": start_date_formatted,
                            "end_date": end_date_formatted,
                            "totalMonth": total_months,
                            "type": "work_exp",
                        }
                    )
                    durations.append(total_months)
                else:
                    work_exp.append(
                        {
                            "company_name": company_name,
                            "start_date": "N/A",
                            "end_date": "N/A",
                            "totalMonth": 0,
                            "type": "work_exp",
                        }
                    )
                    durations.append(0)
        if durations:
            total_duration = float(sum(durations) / 12)
            total_duration = round(total_duration, 2)
        else:
            total_duration = 0

        if work_exp:
            logger.debug(work_exp)
            work_exp = [exp for exp in work_exp if exp.get("start_date") != "N/A" or exp.get("end_date") != "N/A" ]
            work_exp = sorted(work_exp, key=lambda x: x.get("start_date"))
            if work_exp:
                last_job = work_exp[-1]
                last_job_duration = last_job["totalMonth"]
            else:
                last_job_duration = -1
        else:
            last_job_duration = -1



        ##extracting role from tenure

        result_role = db_1.exec(
            text('SELECT "role" ' "FROM `tenure` WHERE formid = :id").params(id=id)
        )
        role = result_role.fetchone()

        

        # logger.debug(f"PERSONAL INFO: {personal_info_1}")

        # Combine data from both databases into the Info response
        return Info(
            firstName=personal_info_1[0],
            middleName=personal_info_1[1],
            lastName=personal_info_1[2],
            phone=personal_info_1[3],
            email=personal_info_1[4],
            city=personal_info_1[11] if personal_info_1[11] is not None else "N/A",
            gender=personal_info_1[7],
            dob=personal_info_1[5],
            age=personal_info_1[6],
            marital_status=personal_info_1[8],
            spouse_work_status="N/A",
            spouse_employer="N/A",
            kidsnum=personal_info_1[24] if personal_info_1[24] is not None else 0,
            adultdependents=personal_info_1[25],
            home=personal_info_1[13],
            car=personal_info_1[15],
            twoWheeler=personal_info_1[17],
            creditCard=personal_info_1[19],
            Loan=any(
                [
                    personal_info_1[14],
                    personal_info_1[16],
                    personal_info_1[18],
                    personal_info_1[20],
                ]
            ),
            Investment=any([personal_info_1[21], personal_info_1[22]]),
            education=personal_info_1[9],
            education_institute="N/A",
            location=personal_info_1[11],
            total_experience=personal_info_1[10],
            work_industry="N/A",
            skillset="N/A",
            current_role=role[0] if role is not None else "N/A",
            tenure_last_job=last_job_duration,
            household_income=salary_response,
        )
    except Exception as e:
        send_email(500, "Report_about_user")
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(detail="Internal Server Error", status_code=500)
