from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from sqlalchemy.sql import text
from fuzzywuzzy import fuzz
from loguru import logger
from db.db import get_db_analytics, get_db_backend
from email_response import send_email

# from models.Career import CareerDetailsResponse
from mongomodels.Career import CareerDetailsResponse
from tools.benchmark_tools import convert_to_datetime_format
from tools.career_tools import convert_to_datetime, overlap
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK,
)
from mongoengine import connect

career_router = APIRouter()

connect(db='trace_about', host="mongodb://localhost:27017/")



@career_router.get(
    "/career_details/{application_id}",
    tags=["Career Details"],
)
async def get_career_summary(
    application_id: str,
    db: Session = Depends(get_db_analytics),
    db_backend: Session = Depends(get_db_backend),
):
    try:
        validation_query = text("""
                                SELECT count(*) FROM epfo_status_uan WHERE application_id = :application_id
                                """)
        
        valid_count = db.exec(validation_query.params(application_id=application_id))
        count_raw_data = valid_count.fetchone()
        if count_raw_data[0] == 0:
            raise HTTPException(detail="Application not found", status_code=404)
        
        flag = False
        companies_without_dates = []
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
        logger.debug(result)

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

        if len(company_data):
            for company_name, date_list in company_data.items():
                logger.debug(date_list)
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

            for i, entry1 in enumerate(work_exp):
                if entry1["end_date"] != "N/A":
                    end_date1 = await convert_to_datetime_format(
                        entry1["end_date"].split("-")[2],
                        entry1["end_date"].split("-")[1],
                        entry1["end_date"].split("-")[0]
                    )

                    for entry2 in work_exp[i + 1 :]:
                        if entry2["start_date"] != "N/A":
                            start_date2 = await convert_to_datetime_format(
                                entry2["start_date"].split("-")[2],
                                entry2["start_date"].split("-")[1],
                                entry2["start_date"].split("-")[0],
                            )

                            # overlapping

                            if end_date1 > start_date2:
                                start_date_dt = datetime.strptime(
                                    entry2["start_date"], "%m-%d-%Y"
                                )
                                end_date_dt = datetime.strptime(
                                    entry1["end_date"], "%m-%d-%Y"
                                )
                                total_months = (
                                    end_date_dt.year - start_date_dt.year
                                ) * 12 + (end_date_dt.month - start_date_dt.month)

                                overlapping_durations.append(
                                    {
                                        "start_date": entry2["start_date"],
                                        "end_date": entry1["end_date"],
                                        "totalMonth": total_months,
                                        "type": "overlap",
                                    }
                                )

                            # gaps

                            if end_date1 < start_date2:
                                gap_start_date = (
                                    end_date1 + timedelta(days=1)
                                ).strftime("%m-%d-%Y")
                                gap_end_date = (
                                    start_date2 - timedelta(days=1)
                                ).strftime("%m-%d-%Y")
                                gaps.append(
                                    {
                                        "start_date": gap_start_date,
                                        "end_date": gap_end_date,
                                        "type": "gaps",
                                    }
                                )

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
        for exp in resume_raw_data:
            company = exp[0]
            from_date = datetime.strptime(exp[1], "%Y-%m-%d")
            if exp[2].lower() == "current":
                to_date = datetime.now()
                to_date = datetime.date(to_date)
                logger.debug(to_date)
            else:
                to_date = datetime.strptime(exp[2], "%Y-%m-%d")
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
        company_data = sorted(company_data, key=lambda x: datetime.strptime(x['start_date'],"%m-%d-%Y"))
        logger.debug(company_data)
        overlapping_durations_tenure = []
        gaps_tenure = []

        for i in range(len(company_data)-1):
            entry1 = company_data[i]
            end_date1 = datetime.strptime(entry1["end_date"], "%m-%d-%Y")
            entry2= company_data[i+1]
            start_date2 = datetime.strptime(entry2["start_date"], "%m-%d-%Y")
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
                #end_date1_datetime = datetime.strptime(end_date1, "%m-%d-%Y")
                gap_start_date = (end_date1 + timedelta(days=1)).strftime(
                        "%m-%d-%Y"
                    )

                #start_date2_datetime = datetime.strptime(start_date2, "%m-%d-%Y")
                gap_end_date = (start_date2 - timedelta(days=1)).strftime(
                        "%m-%d-%Y"
                    )

                gaps_tenure.append({"company_name": "","start_date": gap_start_date, "end_date": gap_end_date,"type":"gaps"})
        
        # discrepancies
        gaps_tenure = [entry for entry in gaps_tenure if entry['start_date'][:2] != entry['end_date'][:2] and entry['start_date'][6:] != entry['end_date'][6:]]
        overlapping_durations_tenure = [entry for entry in overlapping_durations_tenure if entry['start_date'][:2] != entry['end_date'][:2] and entry['start_date'][6:] != entry['end_date'][6:]]

        overlapping_gaps = []

        for gap in gaps:
            gap_start = gap["start_date"]
            gap_end = gap["end_date"]

            for exp in company_data:
                exp_start = exp["start_date"]
                exp_end = exp["end_date"]

                if await overlap(gap_start, gap_end, exp_start, exp_end):
                    overlapping_gaps.append(gap)
                    break

        logger.debug(f"Work_Exp : {work_exp}")
        logger.debug(f"Overlap : {overlapping_durations}")
        logger.debug(f"Gaps : {gaps}")
        
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
                                from_date = datetime.strptime(govt.get("start_date"), "%m-%d-%Y")
                                logger.debug(from_date)
                                to_date = datetime.strptime(resume.get("start_date"), "%m-%d-%Y")
                                logger.debug(to_date)
                                total_months_start = abs(to_date.year - from_date.year) * 12 + abs(
                                from_date.month - to_date.month
                                )
                                from_date = datetime.strptime(govt.get("end_date"), "%m-%d-%Y")
                                to_date = datetime.strptime(resume.get("end_date"), "%m-%d-%Y")
                                total_months_end = abs(to_date.year - from_date.year) * 12 + abs(
                                from_date.month - to_date.month
                                )
                                if total_months_start >1 or total_months_end >1: 
                                    date_mismatch.append(govt.get('company_name'))

        logger.debug(date_mismatch)
        
        all_experiences_sorted_tenure = sorted(
            all_exp_tenure, key=lambda x: datetime.strptime(x.get("start_date", "N/A"), "%m-%d-%Y")
        )


        business_income_query = text(
            """
                                    SELECT COUNT(distinct deductor_tan_no) AS NO_OF_SOURCE from itr_26as_details WHERE section_1 IN("194C", '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O') AND application_id = :application_id  AND transaction_dt >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                                    """
        )

        overseas_income_query = text(
            """
                                    SELECT COUNT(distinct deductor_tan_no) AS NO_OF_SOURCE FROM itr_26as_details WHERE section_1 IN('206CQ','206CO') AND application_id = :application_id  AND transaction_dt >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
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
            + len(overlapping_durations_tenure)
            + business_count
            + overseas_count
        )
        discrepancies = len(overlapping_gaps) + len(date_mismatch)
        good_to_know = len(gaps_tenure)

        meter = max(0, int(100 - discrepancies * 2 - red_flag * 10))

        if meter >= 95:
            meter_text = "Excellent"
        elif meter >= 90 and meter < 95:
            meter_text = "Good"
        elif meter >= 80 and meter < 90:
            meter_text = "Concern"
        else:
            meter_text = "Bad"

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
        if len(all_exp_govt_docs):
            for i in all_exp_govt_docs:
                if i["start_date"] != "N/A" or i["end_date"] != "N/A":
                    final_exp_govt_docs.append(i)
                else:
                    flag = True

        highlight = []
        if good_to_know == 0:
            highlight.append(
                f"No GAPs are identified in the resume"
            )
        elif good_to_know == 1:
            highlight.append(
                f"{good_to_know} GAP is identified in the resume"
            )
        else:
            highlight.append(
                f"{good_to_know} GAPs are identified in the resume"
            )

        if len(overlapping_durations) == 0 and len(overlapping_durations_tenure)==0:
            highlight.append(f"No situation of dual employment found (Red Flag)")
        else:
            highlight.append(
                f"{len(overlapping_durations)+len(overlapping_durations_tenure)} situation of dual employment found (Red Flag)"
            )

        if business_count == 0:
            business_count = "No"
        if overseas_count == 0:
            overseas_count = "No"

        highlight.append(
            f"{business_count} situations of Business and {overseas_count} situations of overseas Income identified that could be related to moonlighting (Red Flag)"
        )
        
        if len(date_mismatch) == 1:
            highlight.append(f"For {date_mismatch[0]}, a mismatch is found between the joining date or exit date in the government document and the resume (Discrepancy)")
        elif len(date_mismatch) >1:
            companies = ', '.join(date_mismatch[:-1]) + ' and ' + date_mismatch[-1]
           
            highlight.append(f"For {companies} mismatches are found between the joining date or exit date in the government document and the resume (Discrepancy)")

        if len(overlapping_gaps) >0:
            highlight.append(f"There are gaps in the goverment documents but not in the resume (Discrepancy)")

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
        # Handling existing & Current Document
        existing_document = CareerDetailsResponse.objects(application_id=application_id, page_id=1).first()
        if existing_document:
            existing_document.delete()

        info_document2 =  CareerDetailsResponse(
            application_id= application_id,
            page_id= 1,
            all_experiences_govt_docs=final_exp_govt_docs,
            all_experiences_tenure=all_experiences_sorted_tenure,
            good_to_know=good_to_know,
            red_flag=red_flag,
            discrepancies=discrepancies,
            highlight=highlight,
            career_score=meter,
            career_score_text=meter_text,
        )
        info_document2.save()
    except HTTPException as ht:
        raise ht
    except Exception as e:
        send_email(500, "Report_career_details")
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(detail="Internal Server Error", status_code=500)
