from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from async_sessions.sessions import get_db, get_db_backend
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from models.Career import CareerDetailsResponse
from tools.career_tools import convert_to_datetime, overlap

career_router =APIRouter()

@career_router.get("/career_details/{person_id}", response_model=CareerDetailsResponse, tags=['Career Details'])
async def get_career_summary(person_id: str, db: AsyncSession = Depends(get_db),db_backend: AsyncSession = Depends(get_db_backend)):

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
    
    company_data = defaultdict(list)
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
    
    # for company_name, dates in company_data.items():
    #     if dates!= ["N/A"]:
    #         start_date = min(dates).strftime("%m-%Y")
    #         end_date = max(dates).strftime("%m-%Y")
    #         # total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

    #         work_exp.append(
    #             {
    #                 "company_name": company_name, 
    #                 "start_date": start_date, 
    #                 "end_date": end_date,
    #                 "type":"work_exp"
    #                 }
    #             )
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
        else:
            work_exp.append(
                {
                    "company_name": company_name, 
                    "start_date": "",
                    "end_date": "",
                    "totalMonth": 0,
                    "type":"work_exp"
                    }
                )

    for i, entry1 in enumerate(work_exp):
        # if entry1["end_date"]!="N/A":
        #     end_date1 = convert_to_datetime(entry1["end_date"].split("-")[1], entry1["end_date"].split("-")[0])
        if entry1["end_date"]!="":
            end_date1 = await convert_to_datetime(entry1["end_date"].split("-")[1], entry1["end_date"].split("-")[0])        

            for entry2 in work_exp[i+1:]:
                # if entry2["start_date"]!="N/A":
                #     start_date2 = convert_to_datetime(entry2["start_date"].split("-")[1], entry2["start_date"].split("-")[0])
                if entry2["start_date"]!="":
                    start_date2 = await convert_to_datetime(entry2["start_date"].split("-")[1], entry2["start_date"].split("-")[0])
                    
                    #overlapping
                    
                    if end_date1 > start_date2:
                        start_date_dt = datetime.strptime(entry2["start_date"], "%m-%d-%Y")
                        end_date_dt = datetime.strptime(entry1["end_date"], "%m-%d-%Y")
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
                        gap_start_date = (end_date1 + timedelta(days=1)).strftime("%m-%d-%Y")
                        gap_end_date = (start_date2 - timedelta(days=1)).strftime("%m-%d-%Y")
                        gaps.append({"start_date": gap_start_date, "end_date": gap_end_date,"type":"gaps"})
    
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
    
    company_data = []
    for exp in resume_raw_data:
        company = exp[0]
        from_date = datetime.strptime(exp[1],"%Y-%m-%d")
        to_date = datetime.strptime(exp[2],"%Y-%m-%d")
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
                gap_start_date = (end_date1 + timedelta(days=1)).strftime("%m-%d-%Y")
                gap_end_date = (start_date2 - timedelta(days=1)).strftime("%m-%d-%Y")
                gaps_tenure.append({"start_date": gap_start_date, "end_date": gap_end_date,"type":"gaps"})

    #discrepancies
    
    overlapping_gaps = []
    
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
    all_experiences_sorted_govt_docs = sorted(all_exp_govt_docs, key=lambda x: x.get("start_date", "N/A"))

    #print(all_experiences_sorted)
    all_exp_tenure = company_data + overlapping_durations_tenure + gaps_tenure
    all_experiences_sorted_tenure = sorted(all_exp_tenure, key=lambda x: x.get("start_date", "N/A"))
    
    
    other_income_query = text("""
                                 SELECT COUNT(distinct "deductor_tan_no") AS NO_OF_SOURCE FROM "26as_details" WHERE "A2(section_1)" like "194%" AND person_id = :person_id
                                 """)
    
    business_income_query = text("""
                                 SELECT COUNT(distinct "deductor_tan_no") AS NO_OF_SOURCE FROM "26as_details" WHERE "B2"="206CQ" AND person_id = :person_id
                                 """)
    
    other_income = await db.execute(other_income_query,{"person_id":person_id})
    business_income = await db.execute(business_income_query, {"person_id": person_id})
    
    no_of_other_sources = other_income.fetchall()
    no_of_business_sources = business_income.fetchall()
    
    for i in no_of_other_sources:
        other_count = i[0]
    
    for i in no_of_business_sources:
        overseas_count = i[0]
    
    
    red_flag = len(overlapping_durations) + other_count + overseas_count
    discrepancies = len(overlapping_gaps)
    good_to_know = len(gaps)
    
    meter = max(0,int(100 - discrepancies * 2 - red_flag * 10))
    
    if meter >= 95:
        meter_text = "Excellent"
    elif meter >= 90 and meter < 95:
        meter_text = "Good"
    elif meter >= 80 and meter < 90:
        meter_text = "Concern"
    else:
        meter_text = "Bad"
        
    highlight = []
    if good_to_know == 0:
        highlight.append(f"No GAPs are identified that is not reflected in the resume")
    else:
        highlight.append(f"{good_to_know} GAPs are identified that is not reflected in the resume")
        
    if len(overlapping_durations) == 0:
        highlight.append(f"No situation of dual employment found (Red Flag)")
    else:
        highlight.append(f"{len(overlapping_durations)} situation of dual employment found (Red Flag)")
    if other_count + overseas_count == 0:
        highlight.append(f"No situations of Business Income identified that could be related to moonlighting (Red Flag)" ) 
    else:
        highlight.append(f"{other_count + overseas_count} situations of Business Income identified that could be related to moonlighting (Red Flag)")
    
    return CareerDetailsResponse(
        all_experiences_govt_docs = all_experiences_sorted_govt_docs,
        all_experiences_tenure = all_experiences_sorted_tenure,
        good_to_know = good_to_know,
        red_flag = red_flag,
        discrepancies = discrepancies,
        highlight = highlight,
        meter = meter,
        meter_text = meter_text
    )