from collections import defaultdict
import datetime
import random
import statistics
import traceback
from sqlmodel import Session
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from sqlalchemy.sql import text
from auth.auth import AuthHandler
from db.db import get_db_analytics, get_db_backend
from email_response import send_email
from endpoints.identification_endpoints import iden_info
from models.Form import Form
from sqlalchemy.exc import PendingRollbackError
from models.Contact_Information import Address, Email, Mobile, Name
from models.Summary import (
    ExperienceSummary,
    Name_,
    Mobile_,
    Email_,
    Address_,
    contact_information,
    IncomePosition,
    Ideal_ctc,
    Summary,
    SummaryBasicInfo,
    offered_past_ctc_summary,
    declared_household_income_summary,
    identity_info,
)
from repos.application_repos import find_application
from repos.form_repos import get_basic_info
from tools.benchmark_tools import convert_to_datetime
from tools.career_tools import overlap
from fuzzywuzzy import fuzz
from tools.contact_tools import (
    check_discrepancy,
    check_discrepancy_1,
    check_discrepancy_address,
)


summary_router = APIRouter()
auth_handler = AuthHandler()


@summary_router.get(
    "/basic-info/{id}", response_model=SummaryBasicInfo, tags=["Summary"]
)
async def basic_info(id: int, session: Session = Depends(get_db_backend)):
    try:
        basic = get_basic_info(id, session)
        # logger.debug(basic)
        basic = SummaryBasicInfo(**basic)
        return basic
    except Exception as ex:
        logger.error(ex)
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="No Records Found."
        )


@summary_router.get("/application-journey/{id}", tags=["Summary"])
async def journey_info(id: int, session: Session = Depends(get_db_backend)):
    try:
        form = session.get(Form, id)
        if form is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND,detail="Form Not Found")
        appl = find_application(id, session)
        if form.report is None and appl is not None:
            return {
                "application_initiated": appl.createddate,
                "application_completed": form.formcompletiondate,
                "report_generated": "Under Progress",
                "form_initiation_to_complete": (
                    form.formcompletiondate.date() - appl.createddate.date()
                ).days,
            }
        return {
            "application_initiated": appl.createddate,
            "application_completed": form.formcompletiondate,
            "report_generated": form.report,
            "form_initiation_to_complete": (
                form.formcompletiondate.date() - appl.createddate.date()
            ).days,
            "form_complete_to_report": (form.report.date() - form.formcompletiondate.date()).days
        }
    except PendingRollbackError as pre:
        logger.error(pre)
        session.rollback()
        await journey_info(id,session)
    except HTTPException as ht:
        raise ht
    except Exception as ex:
        logger.error(ex)
        logger.debug("------DEBUG--------")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,detail="Unknown Error Occured.Please try after sometime.")


@summary_router.get(
    "/summary_details/{application_id}", response_model=Summary, tags=["Summary"]
)
async def summary(
    application_id: str,
    db: Session = Depends(get_db_analytics),
    db_backend: Session = Depends(get_db_backend),
):
    try:
        
        validation_query = text("""
                                SELECT count(*) FROM itr_status WHERE application_id = :application_id
                                """)
        
        valid_count = db.exec(validation_query.params(application_id=application_id))
        count_raw_data = valid_count.fetchone()
        if count_raw_data[0] == 0:
            raise HTTPException(detail="Application not found", status_code=404)
        
        query = text(
            """
            SELECT
                COUNT(DISTINCT CASE WHEN section_1 = '192' THEN deductor_tan_no END) AS salary_accounts,
                COUNT(DISTINCT CASE WHEN section_1 IN ('194DA', '194I(a)', '194I(b)', '194I', '194LA', '194S', '194M', '194N', '194P', '194Q', '196DA', '206CA', '206CB', '206CC', '206CD', '206CE', '206CF', '206CG', '206CH', '206CI', '206CJ', '206CK', '206CL', '206CM', '206CP', '206CR') THEN deductor_tan_no END) AS other_income_accounts,
                COUNT(DISTINCT CASE WHEN section_1 IN ('194C', '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O') THEN deductor_tan_no END) AS business_income_accounts,
                COUNT(DISTINCT CASE WHEN section_1 IN ('192A','193', '194', '194A', '194B', '194BB', '194EE', '194F', '194G', '194IA', '194IB', '194K', '194LB', '194LBB', '194LBC', '194LD') THEN deductor_tan_no END) AS personal_income_accounts,
                SUM(CASE WHEN section_1 LIKE '192%' THEN paid_credited_amt END) AS total_salary,
                SUM(CASE WHEN section_1 IN ('194DA', '194I(a)', '194I(b)', '194I', '194LA', '194S', '194M', '194N', '194P', '194Q', '196DA', '206CA', '206CB', '206CC', '206CD', '206CE', '206CF', '206CG', '206CH', '206CI', '206CJ', '206CK', '206CL', '206CM', '206CP', '206CR') THEN 
                        CASE 
                            WHEN section_1 IN ('206CA', '206CE', '206CJ', '206CL', '206CN') THEN paid_credited_amt / 0.01
                            WHEN section_1 IN ('206CK', '206CM') AND paid_credited_amt / 0.01 > 200000 THEN paid_credited_amt / 0.01
                            WHEN section_1 IN ('206CB', '206CC','206CD') THEN paid_credited_amt / 0.025
                            WHEN section_1 IN ('206CF', '206CG','206CH') THEN paid_credited_amt / 0.02
                            WHEN section_1 = '206CI' THEN paid_credited_amt / 0.05
                            WHEN section_1 = '206CR' AND paid_credited_amt / 0.001 > 5000000 THEN paid_credited_amt / 0.001
                            ELSE paid_credited_amt
                        END
                END) AS total_other_income,
                SUM(CASE WHEN section_1 IN ('194C', '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O') THEN 
                        CASE
                            WHEN section_1 = '206CN' THEN paid_credited_amt / 0.01
                            ELSE paid_credited_amt
                        END
                END) AS total_business_income,
                SUM(CASE WHEN section_1 IN ('192A','193', '194', '194A', '194B', '194BB', '194EE', '194F', '194G', '194IA', '194IB', '194K', '194LB', '194LBB', '194LBC', '194LD') THEN 
                        CASE
                            WHEN section_1 = '192A' THEN paid_credited_amt / 0.1
                            ELSE paid_credited_amt
                        END
                END) AS total_personal_income
            FROM itr_26as_details
            WHERE application_id = :application_id
                AND transaction_dt >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        """
        )
        result = db.exec(query.params(application_id=application_id))
        summary = result.fetchone()

        total_salary = summary[4] if summary[4] is not None else 0.0
        total_other_income = summary[5] if summary[5] is not None else 0.0
        total_business_income = summary[6] if summary[6] is not None else 0.0
        total_personal_income = summary[7] if summary[7] is not None else 0.0

        
        overseas_income_query = text(
            """
                                    SELECT 
                                        DATE_FORMAT(transaction_dt, '%Y-%m') AS month_year,
                                        SUM(CASE 
                                            WHEN section_1 IN ('206CQ', '206CO') THEN 
                                                CASE 
                                                WHEN paid_credited_amt / 0.05 <= 700000 THEN paid_credited_amt / 0.05
                                                ELSE paid_credited_amt / 0.10
                                                END
                                            ELSE 0 
                                        END) AS overseas_income_amount,
                                        deductor_tan_no
                                    FROM itr_26as_details
                                    WHERE application_id = :application_id AND section_1 IN ('206CQ', '206CO') AND transaction_dt >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                                    GROUP BY month_year  
        """
        )

        overseas_income_result = db.exec(
            overseas_income_query.params(application_id=application_id)
        )
        overseas_income_raw_data = overseas_income_result.fetchall()
        total_overseas_income = 0.0
        for row in overseas_income_raw_data:
            month_year, amount, source = row
            total_overseas_income += amount
        if len(overseas_income_raw_data) > 0:
            total_overseas_income += 700000
        total_income = (
            total_salary
            + total_other_income
            + total_business_income
            + total_overseas_income
            + total_personal_income
        )
        # Calculate the percentage share of each income type
        salary_percentage = (
            (total_salary / total_income * 100) if total_income > 0 else 0
        )
        other_income_percentage = (
            (total_other_income / total_income * 100) if total_income > 0 else 0
        )
        business_income_percentage = (
            (total_business_income / total_income * 100) if total_income > 0 else 0
        )
        overseas_income_percentage = (
            (total_overseas_income / total_income * 100) if total_income > 0 else 0
        )
        personal_income_percentage = (
            (total_personal_income / total_income * 100) if total_income > 0 else 0
        )

        
        highlights = []

        if business_income_percentage + personal_income_percentage + other_income_percentage + overseas_income_percentage > 5:
            highlights.append(
                f"Additional income is available from other sources. Since this income is more than 5% of the overall income, it should be declared."
            )
        elif (
            business_income_percentage > 0 or overseas_income_percentage > 0
        ) and business_income_percentage + personal_income_percentage + other_income_percentage + overseas_income_percentage <= 5:
            highlights.append(
                f"Additional income is available from other sources. But this income is less than or equal to 5% of the overall income."
            )
        elif business_income_percentage <= 0 and overseas_income_percentage <= 0 and personal_income_percentage<=0 and other_income_percentage<=0:
            highlights.append(
                f"No additional income is available from other sources."
            )
            
        if business_income_percentage > salary_percentage:
            highlights.append(
                f"Business income is more than the Salary. This could lead to the candidate paying more attention to the additional income sources."
            )
        else:
            highlights.append(
                f"Salary income is more than the Business income. This has lesser chances of the candidate paying attention to the additional income sources."
            )
        if salary_percentage < 50:
            highlights.append(
                f"Salary seems to be less than 50% of the candidate's income. Financial needs from Salary income does not sufficiently met. This could be a reason for future attrition."
            )
        else:
            highlights.append(
                f"Salary seems to be more than 50% of the candidate's income. Financial needs from Salary income sufficiently met."
            )

        if salary_percentage >= 95:
            salary_text = "Excellent"
        elif salary_percentage >= 90 and salary_percentage < 95:
            salary_text = "Good"
        elif salary_percentage >= 80 and salary_percentage < 90:
            salary_text = "Concern"
        else:
            salary_text = "Bad"

        income_position = IncomePosition(
            total_income=round(total_income),
            salary_income=round(total_salary),
            salary_text=salary_text,
            salary_percentage=round(salary_percentage),
            business_income=round(total_business_income),
            business_percentage=round(business_income_percentage),
            overseas_income=round(total_overseas_income),
            overseas_percentage=round(overseas_income_percentage),
            personal_income=round(total_personal_income),
            personal_income_percentage=round(personal_income_percentage),
            other_income=round(total_other_income),
            other_income_percentage=round(other_income_percentage),
            highlights=highlights,
        )

        logger.debug(income_position)

        # govt_docs
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

        result = db.exec(query.params(application_id=application_id))
        passbook_raw_data = result.fetchall()
        logger.debug(passbook_raw_data)
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
        overlapping_durations = []
        gaps = []
        duration = []
        flag = False
        companies_without_dates = []
        if len(company_data):
            for company_name, date_list in company_data.items():
                logger.debug(date_list)
                dates = [date for date in date_list if date != "N/A"]
                if len(dates):
                    # Parse the start and end dates into datetime objects
                    start_date = min(dates)
                    end_date = max(dates)
                    start_date_formatted = start_date.strftime("%m-%d-%Y")
                    end_date_formatted = end_date.strftime("%m-%d-%Y")

                    # Calculate the difference in months
                    total_months = (end_date.year - start_date.year) * 12 + (
                        end_date.month - start_date.month
                    )

                    # Append the data to work_exp with the new "totalMonth" key
                    work_exp.append(
                        {
                            "company_name": company_name,
                            "start_date": start_date_formatted,
                            "end_date": end_date_formatted,
                            "totalMonth": total_months,
                            "type": "work_exp",
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
                            "type": "work_exp",
                        }
                    )
                    flag = True
                    companies_without_dates.append(company_name)

        logger.debug(work_exp)
        logger.debug(duration)
        logger.debug(companies_without_dates)
        total_duration = float(sum(duration) / 12) if len(duration) else 0.0
        total_duration = round(total_duration, 0)
        logger.debug(total_duration)
        # median_duration = statistics.median(duration)
        # average_duration = statistics.mean(duration)
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
        elif 35 <= average_duration < 60:
            risk_duration = "Optimal"
        else:
            risk_duration = "Low"

        if len(work_exp):
            for i, entry1 in enumerate(work_exp):
                # if entry1["end_date"]!="N/A":
                #     end_date1 = convert_to_datetime(entry1["end_date"].split("-")[1], entry1["end_date"].split("-")[0])
                if entry1["end_date"] != "N/A":
                    end_date1 = await convert_to_datetime(
                        entry1["end_date"].split("-")[1],
                        entry1["end_date"].split("-")[0],
                    )

                    for entry2 in work_exp[i + 1 :]:
                        # if entry2["start_date"]!="N/A":
                        #     start_date2 = convert_to_datetime(entry2["start_date"].split("-")[1], entry2["start_date"].split("-")[0])
                        if entry2["start_date"] != "N/A":
                            start_date2 = await convert_to_datetime(
                                entry2["start_date"].split("-")[1],
                                entry2["start_date"].split("-")[0],
                            )

                            # overlapping

                            if end_date1 > start_date2:
                                start_date_dt = datetime.datetime.strptime(
                                    entry2["start_date"], "%m-%d-%Y"
                                )
                                end_date_dt = datetime.datetime.strptime(
                                    entry1["end_date"], "%m-%d-%Y"
                                )
                                total_months = (
                                    end_date_dt.year - start_date_dt.year
                                ) * 12 + (end_date_dt.month - start_date_dt.month)

                                overlapping_durations.append(
                                    {
                                        "company_name": entry2["company_name"],
                                        "start_date": entry2["start_date"],
                                        "end_date": entry1["end_date"],
                                        "totalMonth": total_months,
                                        "type": "overlap",
                                    }
                                )

                            # gaps

                            if end_date1 < start_date2:
                                end_date1_datetime = datetime.datetime.strptime(
                                    end_date1, "%m-%d-%Y"
                                )
                                gap_start_date = (
                                    end_date1_datetime + datetime.timedelta(days=1)
                                ).strftime("%m-%d-%Y")

                                start_date2_datetime = datetime.datetime.strptime(
                                    start_date2, "%m-%d-%Y"
                                )
                                gap_end_date = (
                                    start_date2_datetime - datetime.timedelta(days=1)
                                ).strftime("%m-%d-%Y")
                                gaps.append(
                                    {
                                        "start_date": gap_start_date,
                                        "end_date": gap_end_date,
                                        "type": "gaps",
                                    }
                                )

        logger.debug(overlapping_durations)
        logger.debug(gaps)
        # tenure

        resume_query = text(
            """
            SELECT company,
                from_date,
                to_date
            FROM
                tenure
            WHERE formid =:formid
        """
        )

        result = db_backend.exec(resume_query.params(formid=application_id))
        resume_raw_data = result.fetchall()
        company_data = []
        logger.debug(resume_raw_data)
        for exp in resume_raw_data:
            company = exp[0]
            from_date = datetime.datetime.strptime(exp[1], "%Y-%m-%d")
            if exp[2].lower() == "current":
                to_date = datetime.datetime.now()
                to_date = datetime.datetime.date(to_date)
                logger.debug(to_date)
            else:
                to_date = datetime.datetime.strptime(exp[2], "%Y-%m-%d")
            logger.debug(to_date)
            total_months = (to_date.year - from_date.year) * 12 + (
                from_date.month - to_date.month
            )

            from_date = from_date.strftime("%m-%d-%Y")
            to_date = to_date.strftime("%m-%d-%Y")

            company_data.append(
                {
                    "company_name": company,
                    "start_date": from_date,
                    "end_date": to_date,
                    "totalMonth": total_months,
                    "type": "work_exp",
                }
            )
        company_data = sorted(company_data, key=lambda x: datetime.datetime.strptime(x['start_date'],"%m-%d-%Y"))
        overlapping_durations_tenure = []
        gaps_tenure = []
        logger.debug(company_data)
        for i in range(len(company_data)-1):
            entry1 = company_data[i]
            end_date1 = datetime.datetime.strptime(entry1["end_date"], "%m-%d-%Y")
            entry2= company_data[i+1]
            start_date2 = datetime.datetime.strptime(entry2["start_date"], "%m-%d-%Y")
            logger.debug(end_date1)
            logger.debug(start_date2)
            if end_date1 > start_date2:
                overlapping_durations_tenure.append(
                        {
                            "company_name": entry2["company_name"],
                            "start_date": entry2["start_date"],
                            "end_date": entry1["end_date"],
                            "type": "overlap",
                        }
                    )

            if end_date1 < start_date2:
                #end_date1_datetime = datetime.datetime.strptime(end_date1, "%m-%d-%Y")
                gap_start_date = (end_date1 + datetime.timedelta(days=1)).strftime(
                        "%m-%d-%Y"
                    )

                #start_date2_datetime = datetime.datetime.strptime(start_date2, "%m-%d-%Y")
                gap_end_date = (start_date2 - datetime.timedelta(days=1)).strftime(
                        "%m-%d-%Y"
                    )

                gaps_tenure.append({"company_name": "","start_date": gap_start_date, "end_date": gap_end_date,"type":"gaps"})
                
        logger.debug(overlapping_durations_tenure)
        logger.debug(gaps_tenure)
        # discrepancies
        gaps_tenure = [entry for entry in gaps_tenure if entry['start_date'][:2] != entry['end_date'][:2] and entry['start_date'][6:] != entry['end_date'][6:]]
        overlapping_durations_tenure = [entry for entry in overlapping_durations_tenure if entry['start_date'][:2] != entry['end_date'][:2] and entry['start_date'][6:] != entry['end_date'][6:]]
        overlapping_gaps = []
        if len(gaps):
            for gap in gaps:
                gap_start = gap["start_date"]
                gap_end = gap["end_date"]

                for exp in company_data:
                    exp_start = exp["start_date"]
                    exp_end = exp["end_date"]

                    if await overlap(gap_start, gap_end, exp_start, exp_end):
                        overlapping_gaps.append(gap)
                        break

        # logger.debug(f"Work_Exp : {work_exp}")
        # logger.debug(f"Overlap : {overlapping_durations}")
        # logger.debug(f"Gaps : {gaps}")
        all_exp_govt_docs = []
        if work_exp:
            all_exp_govt_docs += work_exp
        if overlapping_durations:
            all_exp_govt_docs += overlapping_durations
        if gaps:
            all_exp_govt_docs += gaps
        all_exp_tenure=[]
        
        if company_data:
            all_exp_tenure += company_data 
        if overlapping_durations_tenure:
            all_exp_tenure += overlapping_durations_tenure
        # if gaps_tenure:
        #     all_exp_tenure += gaps_tenure

        date_mismatch = []
        
        if work_exp and company_data:
            
            for govt in work_exp:
                if govt.get("start_date") != "N/A" and govt.get("end_date") != "N/A":
                    for resume in company_data:
                        if resume.get("start_date") != "N/A" and resume.get("end_date") != "N/A":
                            logger.debug(f"{govt.get('company_name').lower()},{resume.get('company_name').lower()}:{fuzz.partial_ratio(govt.get('company_name').lower(),resume.get('company_name').lower())}")
                            if fuzz.partial_ratio(govt.get("company_name").lower(),resume.get("company_name").lower())>=80:
                                from_date = datetime.datetime.strptime(govt.get("start_date"), "%m-%d-%Y")
                                logger.debug(from_date)
                                to_date = datetime.datetime.strptime(resume.get("start_date"), "%m-%d-%Y")
                                logger.debug(to_date)
                                total_months_start = abs(to_date.year - from_date.year) * 12 + abs(
                                from_date.month - to_date.month
                                )
                                from_date = datetime.datetime.strptime(govt.get("end_date"), "%m-%d-%Y")
                                to_date = datetime.datetime.strptime(resume.get("end_date"), "%m-%d-%Y")
                                total_months_end = abs(to_date.year - from_date.year) * 12 + abs(
                                from_date.month - to_date.month
                                )
                                if total_months_start >1 or total_months_end >1: 
                                    date_mismatch.append(govt.get('company_name'))

        logger.debug(date_mismatch)
        

        business_income_query = text(
            """
                                    SELECT COUNT(distinct deductor_tan_no) AS NO_OF_SOURCE from itr_26as_details WHERE section_1 IN("194C", '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O') AND application_id = :application_id AND transaction_dt >= CURDATE() - INTERVAL 12 MONTH
                                        AND transaction_dt < CURDATE()
                                    """
        )

        overseas_income_query = text(
            """
                                    SELECT COUNT(distinct deductor_tan_no) AS NO_OF_SOURCE FROM itr_26as_details WHERE section_1 IN('206CQ','206CO') AND application_id = :application_id AND transaction_dt >= CURDATE() - INTERVAL 12 MONTH
                                        AND transaction_dt < CURDATE()
                                    """
        )


        
        business_income = db.exec(
            business_income_query.params(application_id=application_id)
        )
        overseas_income = db.exec(
            overseas_income_query.params(application_id=application_id)
        )

        no_of_business_sources = business_income.fetchall()
        no_of_overseas_sources = overseas_income.fetchall()

     
        for i in no_of_business_sources:
            business_count = i[0]

        for i in no_of_overseas_sources:
            overseas_count = i[0]

 

        red_flag = (
            len(overlapping_durations)
            +len(overlapping_durations_tenure)
            + business_count
            + overseas_count
        )
        discrepancies = len(overlapping_gaps) + len(date_mismatch)
        good_to_know = len(gaps_tenure)

        if len(all_exp_govt_docs):
            for i in all_exp_govt_docs:
                if i["start_date"] == "N/A" or i["end_date"] == "N/A":
                    for j in all_exp_tenure:
                        if (
                            fuzz.partial_ratio(i["company_name"], j["company_name"])
                            >= 80
                        ):
                            i["start_date"], i["end_date"], i["totalMonth"] = (
                                j["start_date"],
                                j["end_date"],
                                j["totalMonth"],
                            )
                            flag = False
                            if i["company_name"] in companies_without_dates:
                                companies_without_dates.remove(i["company_name"])

            # final_exp_govt_docs = list(filter(lambda i: i['start_date'] != 'N/A' and i['end_date'] != 'N/A', all_exp_govt_docs))

            # Removing elements with "N/A" dates and checking if still "N/A" exists in multiple "N/A" cases
            final_exp_govt_docs = []
            for i in all_exp_govt_docs:
                if i["start_date"] != "N/A" or i["end_date"] != "N/A":
                    final_exp_govt_docs.append(i)
                else:
                    flag = True

        highlight = []
        if good_to_know == 0:
            highlight.append(
                f"No GAPs are identified that is not reflected in the resume"
            )
        elif good_to_know == 1:
            highlight.append(
                f"{good_to_know} GAP is identified that is not reflected in the resume"
            )
        else:
            highlight.append(
                f"{good_to_know} GAPs are identified that is not reflected in the resume"
            )

        if len(overlapping_durations) == 0:
            highlight.append(f"No situation of dual employment found (Red Flag)")
        else:
            highlight.append(
                f"{len(overlapping_durations)} situation of dual employment found (Red Flag)"
            )
        dual_employment_text="Bad" if len(overlapping_durations) > 0 else "Good"
        overlapping_contract_text="Bad" if business_count > 0 else "Good"
        overlapping_contract=business_count
        # business_income=business_count+overseas_count+other_count

        if business_count == 0:
            business_count = "No"
        if overseas_count == 0:
            overseas_count = "No"
            
        highlight.append(
            f"{business_count} situations of Business and {overseas_count} situations of overseas Income identified that could be related to moonlighting (Red Flag)"
        )

        if flag == True:
            if len(companies_without_dates) > 1:
                company_list = ",".join(map(str, companies_without_dates))
                highlight.append(
                    f"No starting date and ending date of employment found for these companies - {company_list} in government documents"
                )
            else:
                highlight.append(
                    f"No starting date and ending date of employment found for {companies_without_dates[0]} in government documents"
                )
        if len(date_mismatch) == 1:
            highlight.append(f"For {date_mismatch[0]}, a mismatch is found between the joining date or exit date in the government document and the resume (Discrepancy)")
        elif len(date_mismatch) >1:
            companies = ', '.join(date_mismatch[:-1]) + ' and ' + date_mismatch[-1]
           
            highlight.append(f"For {companies} mismatches are found between the joining date or exit date in the government document and the resume (Discrepancy)")

        if len(overlapping_gaps) >0:
            highlight.append(f"There are gaps in the goverment documents but not in the resume (Discrepancy)")

        first_name = db_backend.exec(
            text("SELECT firstName,gender " "FROM `form` " "WHERE appid = :id").params(
                id=application_id
            )
        )
        firstname = first_name.fetchone()
        name = firstname[0]
        gender = firstname[1]
        if average_duration < 24:
            remark = "short"
        elif 24 <= average_duration <= 60:
            remark = "average"
        else:
            remark = "Long"

        if gender.lower() == "m" or gender.lower() == "male":
            tenure_remarks = f"{name}'s tenure with companies seem to be {remark}. This could be linked to his personal performance or market opportunity."
        elif gender.lower() == "f" or gender.lower() == "female":
            tenure_remarks = f"{name}'s tenure with companies seem to be {remark}. This could be linked to her personal performance or market opportunity."
        else:
            tenure_remarks = f"{name}'s tenure with companies seem to be {remark}. This could be linked to his/her personal performance or market opportunity."

        exp_summary = ExperienceSummary(
            total_experience=total_duration,
            median_tenure=median_duration,
            median_tenure_text=risk_duration,
            dual_employment=len(overlapping_durations),
            dual_employment_text=dual_employment_text,
            overlapping_contract=overlapping_contract,
            overlapping_contract_text=overlapping_contract_text,
            tenure_highlights=tenure_remarks,
            exp_highlights=highlight,
        )

        logger.debug(exp_summary)

        ###
        compid_result = db_backend.exec(
            text("SELECT compid " "FROM `applicationlist` " "WHERE id = :id").params(
                id=application_id
            )
        )
        compid = compid_result.fetchone()
        if compid is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Comp_id is not found for id : {id}")
        else:
            comp_id = compid[0]
        # print(yy)
        ##Extracting currentctc, offeredctc from compcanlist
        result = db_backend.exec(
            text(
                "SELECT currentctc, rolebudget, offeredctc "
                "FROM `compcanlist` "
                "WHERE id = :id"
            ).params(id=comp_id)
        )

        ctc_info = result.fetchone()
        # print(ctc_info)
        if ctc_info:
            currentctc = round(float(ctc_info[0]),0)
            offeredctc = round(float(ctc_info[2]),0)
        else:
            currentctc = 0
            offeredctc = 0
        random.seed(int(application_id))
        lower_limit = max(int(random.randint(offeredctc*2,offeredctc*6)/10),300000)
        upper_limit = min(int(random.randint(offeredctc*12,offeredctc*15)/10),5000000)
        
        offered_ctc_percentange = min(round(float((offeredctc / upper_limit) * 100), 0),100) if upper_limit != 0 else 0
        if offered_ctc_percentange < 50:
            output = "LOW"
        elif 50 <= offered_ctc_percentange < 75:
            output = "Optimal"
        elif 75 <= offered_ctc_percentange < 90:
            output = "High"
        else:
            output = "Very High"

        pf_result = db.exec(
            text(
                "SELECT employer_total "
                "FROM epfo_get_passbook_details "
                "WHERE application_id = :id"
            ).params(id=application_id)
        )
        pf_summary = pf_result.fetchone()
        if pf_summary:
            pf = pf_summary[0] if pf_summary[0] is not None else 0
        else:
            pf = -1



        monthly_income_query = text(
            """SELECT
                                            DATE_FORMAT(formatted_date, '%Y-%m') AS month_year,
                                            SUM(CASE WHEN section_1 LIKE '192%' THEN paid_credited_amt ELSE 0 END) AS total_salary_amount
                                        FROM (
                                            SELECT 
                                                transaction_dt AS formatted_date,
                                                section_1,
                                                paid_credited_amt
                                            FROM itr_26as_details
                                            WHERE application_id = :application_id
                                            AND transaction_dt >= CURDATE() - INTERVAL 12 MONTH
                                            AND transaction_dt < CURDATE()
                                        ) AS grouped_incomes
                                        GROUP BY month_year
                                        ORDER BY month_year"""
        )

        monthly_income_result = db.exec(
            monthly_income_query.params(application_id=application_id)
        )
        monthly_income_raw_data = monthly_income_result.fetchall()

        
        differences = []

        for i in range(1, len(monthly_income_raw_data)):
            date, value = monthly_income_raw_data[i]
            previous_value = monthly_income_raw_data[i - 1][1]
            if previous_value > value:
                difference = previous_value - value
                differences.append(difference)

        if differences:
            bonus = sum(differences)
        else:
            bonus = 0
            
        monthly_income_dict = dict(monthly_income_raw_data)
        salary_list = list(monthly_income_dict.values())
        if salary_list:
            if 0 < len(salary_list) <= 4:
                total_salary=int(sum(salary_list)-bonus)            
            elif 4<len(salary_list) < 12:
                total_salary = int(((sum(salary_list)-bonus)/len(salary_list))*12)
            elif len(salary_list)== 12:
                total_salary = int(sum(salary_list)-bonus)
            else:
                total_salary = int(((sum(salary_list)-bonus)/len(salary_list))*12)              
        else:
            total_salary = 0

        net_ctc = total_salary + bonus + pf
        possible_ctc_variation = int(net_ctc * 15 / 100)
        estimated_ctc_range = f"{net_ctc}-{net_ctc+possible_ctc_variation}"
        most_likely_past_ctc = int((net_ctc + possible_ctc_variation / 2))
        gap = int(currentctc - most_likely_past_ctc)
        ctc_accuracy = min(int((most_likely_past_ctc / currentctc) * 100), 100) if currentctc != 0 else 0

        if ctc_accuracy < 80:
            remark = "Incorrect"
        elif 80 <= ctc_accuracy < 90:
            remark = "Concern"
        elif 90 <= ctc_accuracy < 95:
            remark = "Close"
        else:
            remark = "Exact"

        if ctc_accuracy < 90:
            highlite = " Past CTC declared by the candidate does not seem to be close to the actual. Candidate is most probably inflating it to negotiate a better offer."
        elif 90 <= ctc_accuracy < 95:
            highlite = (
                " Past CTC declared by the candidate seems to be close to the actual "
            )
        else:
            highlite = (
                " Past CTC declared by the candidate seems to be exact to the actual "
            )

        # expense
        query_2 = text(
            """
        SELECT DISTINCT AccountNumber, AccountType, LastPayment, AccountStatus
        FROM credits_retailaccountdetails
        WHERE application_id = :application_id AND AccountStatus = 'Current Account'
    """
        )

        result_2 = db.exec(query_2.params(application_id=id))
        summary_2 = result_2.fetchall()
        if not summary_2:
            emi = 0
        else:
            emi = sum(
                float(row[3])
                for row in summary_2
                if row[3] is not None and row[3] != ""
            )

        #        raise HTTPException(status_code=404, detail=f"No records found for application_id {application_id}")

        factor = 0.3
        new_exp = ((offeredctc) * 0.4) + emi
        pre_exp = ((currentctc) * 0.4) + emi
        most_likely_expense = round(float((pre_exp + new_exp) / 2), 0)
        income_summary_ratio = float((most_likely_expense / currentctc) * 100) if currentctc != 0 else 0
        if income_summary_ratio < 50:
            income_summary_highlight = (
                "Household income is very stable with a very high potential of savings."
            )
        elif 50 <= income_summary_ratio < 80:
            income_summary_highlight = (
                "Household income is stable with a low potential of savings."
            )
        else:
            income_summary_highlight = "Household income is not stable."

        # response
        idealctc = Ideal_ctc(lower=lower_limit, upper=upper_limit)
        offered_ctc_summary = offered_past_ctc_summary(
            declared_past_ctc=currentctc,
            declared_past_ctc_remark=remark,
            most_likely_past_ctc=net_ctc,
            highlight_1=highlite,
            offered_ctc=offeredctc,
            offered_ctc_remark=output,
            ideal_ctc_band=idealctc,
            highlight_2=f"Offered CTC will be {output} Cost to the Company",
        )
        declared_household_income = declared_household_income_summary(
            candidate_ctc=offeredctc,
            spouse_ctc=0,
            household_ctc=offeredctc,
            mostlikely_expense=most_likely_expense,
            highlight=income_summary_highlight,
        )

        logger.debug(idealctc)
        logger.debug(offered_ctc_summary)
        logger.debug(declared_household_income)

        ###contact
        result_1 = db_backend.exec(
            text(
                "SELECT firstName, lastName, phone, email, city "
                "FROM `form` WHERE appid = :id"
            ).params(id=application_id)
        )

        contact_info_1 = result_1.fetchone()

        if contact_info_1 is None:
            raise HTTPException(
                status_code=404,
                detail=f"Personal information not found for id : {application_id}",
            )

        result_3 = db.exec(
            text(
                "SELECT pan_name, contact_primary_mobile, contact_primary_email, "
                "address_post_office, address_city, address_state, address_pin_code "
                "FROM itr_download_profile WHERE application_id = :id"
            ).params(id=application_id)
        )
        contact_info_3 = result_3.fetchone()

        if contact_info_3 is None or all(value is None for value in contact_info_3):
            # Assign "N/A" to each column
            contact_info_3 = ["N/A"] * len(result_3.keys())
        else:
            contact_info_3 = [value if value is not None and value != "" else "N/A" for value in contact_info_3]
            # Check and replace None values or empty strings with "N/A"
            #contact_info_3 = [getattr(contact_info_3, column_name, "N/A") for column_name in result_3.keys()]
        
        (
            name_flag,
            pan_match,
            aadhar_match,
            tax_match,
            name_remarks,
        ) = await check_discrepancy_1(
            f"{contact_info_1[0]} {contact_info_1[1]}",
            contact_info_3[0],
            "N/A",
            contact_info_3[0],
            "Name",
        )

        (
            mobile_flag,
            pan_match_mobile,
            aadhar_match_mobile,
            government_match_mobile,
            mobile_remarks,
        ) = await check_discrepancy(
            contact_info_1[2], contact_info_3[1], "N/A", contact_info_3[1], "Mobile"
        )

        (
            email_flag,
            pan_match_email,
            aadhar_match_email,
            government_match_email,
            email_remarks,
        ) = await check_discrepancy(
            contact_info_1[3], contact_info_3[2], "N/A", contact_info_3[2], "Email"
        )

        (
            address_flag,
            pan_match_address,
            aadhar_match_address,
            government_match_address,
            address_remarks,
        ) = await check_discrepancy_address(
            contact_info_1[4] if contact_info_1[4] is not None else "N/A",
            f"{contact_info_3[3]},{contact_info_3[4]},{contact_info_3[5]},{contact_info_3[6]}",
            "N/A",
            f"{contact_info_3[3]},{contact_info_3[4]},{contact_info_3[5]},{contact_info_3[6]}",
            "Address",
        )

        name_response = Name(
            provided=f"{contact_info_1[0]} {contact_info_1[1]}",
            Pan=contact_info_3[0],
            Aadhar="N/A",
            Tax=contact_info_3[0],
            flag=name_flag,
            pan_match=pan_match,
            aadhar_match=aadhar_match,
            tax_match=tax_match,
            remarks=name_remarks,
        )

        mobile_response = Mobile(
            provided=contact_info_1[2],
            Pan=contact_info_3[1],
            Aadhar="N/A",
            Government=contact_info_3[1],
            flag=mobile_flag,
            pan_match=pan_match_mobile,
            aadhar_match=aadhar_match_mobile,
            government_match=government_match_mobile,
            remarks=mobile_remarks,
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
            remarks=email_remarks,
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
            remarks=address_remarks,
        )

        logger.debug(name_response)
        logger.debug(mobile_response)
        logger.debug(email_remarks)
        logger.debug(address_response)

        consistency_name = (
            1
            if name_response.provided
            == name_response.Pan
            == name_response.Aadhar
            == name_response.Tax
            else 0
        )
        consistency_phone = (
            1
            if mobile_response.provided
            == mobile_response.Pan
            == mobile_response.Aadhar
            == mobile_response.Government
            else 0
        )
        consistency_email = (
            1
            if email_response.provided
            == email_response.Pan
            == email_response.Aadhar
            == email_response.Government
            else 0
        )
        consistency_address = (
            1
            if address_response.provided
            == address_response.Pan
            == address_response.Aadhar
            == address_response.Government
            else 0
        )

        # consistency_name = 1 if name_response.provided == name_response.Pan == name_response.Tax else 0
        # consistency_phone = 1 if mobile_response.provided == mobile_response.Pan == mobile_response.Government else 0
        # consistency_email = 1 if email_response.provided == email_response.Pan ==  email_response.Government else 0
        # consistency_address = 1 if address_response.provided  ==address_response.Aadhar == address_response.Government else 0

        discrepancy_name = 1 - consistency_name
        discrepancy_phone = 1 - consistency_phone
        discrepancy_email = 1 - consistency_email
        discrepancy_address = 1 - consistency_address

        consistency = []
        discrepancy = []

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
            note_1 = f"{', '.join(consistency)} are Consistent."
        else:
            note_1 = ""
        if discrepancy:
            note_2 = f"{', '.join(discrepancy)} have Discrepancies."
        else:
            note_2 = ""

        name_issue = 0
        mobile_issue = 0
        email_issue = 0
        address_issue = 0
        if name_response.pan_match == True:
            name_issue += 0
        else:
            name_issue += 1
        if name_response.aadhar_match == True:
            name_issue += 0
        else:
            name_issue += 1
        if name_response.tax_match == True:
            name_issue += 0
        else:
            name_issue += 1

        if mobile_response.pan_match == True:
            mobile_issue += 0
        else:
            mobile_issue += 1
        if mobile_response.aadhar_match == True:
            mobile_issue += 0
        else:
            mobile_issue += 1
        if mobile_response.government_match == True:
            mobile_issue += 0
        else:
            mobile_issue += 1

        if email_response.pan_match == True:
            email_issue += 0
        else:
            email_issue += 1
        if email_response.aadhar_match == True:
            email_issue += 0
        else:
            email_issue += 1
        if email_response.government_match == True:
            email_issue += 0
        else:
            email_issue += 1

        if address_response.pan_match == True:
            address_issue += 0
        else:
            address_issue += 1
        if address_response.aadhar_match == True:
            address_issue += 0
        else:
            address_issue += 1
        if address_response.government_match == True:
            address_issue += 0
        else:
            address_issue += 1

        if name_issue == 0:
            name_text_1 = ""
            name_text_2 = "No issue"
        elif name_issue == 1:
            name_text_1 = "Concern"
            name_text_2 = "1 issue"
        else:
            name_text_1 = "Concern"
            name_text_2 = f"{name_issue} issues"

        if address_issue == 0:
            address_text_1 = ""
            address_text_2 = "No issue"
        elif address_issue == 1:
            address_text_1 = "Concern"
            address_text_2 = "1 issue"
        else:
            address_text_1 = "Concern"
            address_text_2 = f"{address_issue} issues"

        if mobile_issue == 0:
            mobile_text_1 = ""
            mobile_text_2 = "No issue"
        elif name_issue == 1:
            mobile_text_1 = "Concern"
            mobile_text_2 = "1 issue"
        else:
            mobile_text_1 = "Concern"
            mobile_text_2 = f"{mobile_issue} issues"

        if email_issue == 0:
            email_text_1 = ""
            email_text_2 = "No issue"
        elif email_issue == 1:
            email_text_1 = "Concern"
            email_text_2 = "1 issue"
        else:
            email_text_1 = "Concern"
            email_text_2 = f"{email_issue} issues"

        mobile_ = Mobile_(remark=mobile_text_1, issue=mobile_text_2)
        name_ = Name_(remark=name_text_1, issue=name_text_2)
        email_ = Email_(remark=email_text_1, issue=email_text_2)
        address_ = Address_(remark=address_text_1, issue=address_text_2)
        contact_ = contact_information(
            name=name_,
            mobile=mobile_,
            email=email_,
            address=address_,
            highlight_1=note_1,
            highlight_2=note_2,
        )

        logger.debug(mobile_)
        logger.debug(name_)
        logger.debug(email_)
        logger.debug(address_)
        logger.debug(contact_)

        # edited by samiran 1046-1069
        # aadhar_issue=0
        # pan_issue=0
        # pan_text = None
        # aadhar_text = None
        # temp = await iden_info(int(application_id))
        # highlight=temp["Remarks"]
        # if temp["Aadhar_Status"] == 'Concern':
        #    aadhar_text = "Concern"
        #    if temp["Extracted_Aadhar_Number_flag"]==False:
        #        aadhar_issue+=1
        #    if temp["Aadhar_Number_flag"]==False:
        #        aadhar_issue+=1
        #    if temp["govt_aadhaar_number_flag"]==False:
        #        aadhar_issue+=1
        #        aadhar_text = "Bad"
        # if temp["Pan_Status"] == 'Concern':
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

        temp = await iden_info(int(application_id), db_backend)
        highlight = temp["Remarks"]

        # Check for Aadhar status
        if temp["Aadhar_Status"] in ["Concern", "Bad"]:
            aadhar_text = temp["Aadhar_Status"]
            aadhar_flags = [
                temp["Extracted_Aadhar_Number_flag"],
                temp["Aadhar_Number_flag"],
                temp["govt_aadhaar_number_flag"],
            ]
            aadhar_issue = aadhar_flags.count(False)

        # Check for PAN status
        if temp["Pan_Status"] in ["Concern", "Bad"]:
            pan_text = temp["Pan_Status"]
            pan_flags = [
                temp["govt_pan_number_flag"],
                temp["Extracted_Pan_Number_flag"],
                temp["Pan_Number_flag"],
            ]
            pan_issue = pan_flags.count(False)

        iden = identity_info(
            pan_issue=pan_issue,
            aadhar_issue=aadhar_issue,
            highlight=highlight,
            pan_text=pan_text,
            aadhar_text=aadhar_text,
        )
        return Summary(
            income_position=income_position,
            experience_summary=exp_summary,
            ctc_summary=offered_ctc_summary,
            household_income_summary=declared_household_income,
            contact=contact_,
            identity=iden,
        )
    except HTTPException as ht:
        raise ht
    except Exception as e:
        send_email(500, "Report_summary")
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(detail="Internal Server Error", status_code=500)
