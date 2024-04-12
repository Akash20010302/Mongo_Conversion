import traceback
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from db.db import get_db_analytics, get_db_backend
from sqlalchemy.sql import text
from email_response import send_email
from starlette.status import HTTP_404_NOT_FOUND
# from models.CourtCase import CourtCase, Index, Response
from mongomodels.CourtCase import CourtCase, Index, CourtCaseResponse
from starlette import status
from loguru import logger
from mongoengine import connect

courtcase_router = APIRouter()

connect(db='trace_about', host="mongodb://localhost:27017/")




@courtcase_router.get("/court_case/{application_id}", tags=["CourtCase"])
async def court_case(
    application_id: int,
    db_1: Session = Depends(get_db_backend),
    db_2: Session = Depends(get_db_analytics),
):
    try:
        validation_query = text("""
                                SELECT count(*) FROM court_cases WHERE application_id = :application_id
                                """)
        
        valid_count = db_2.exec(validation_query.params(application_id=application_id))
        count_raw_data = valid_count.fetchone()
        if count_raw_data[0] == 0:
            raise HTTPException(detail="No data found for the given application_id", status_code=404)
        result = db_2.exec(
            text(
                "SELECT name, case_year, court_name, case_number, filing_no, registration_number, address, "
                "status, order_summary, first_hearing_date, last_hearing_date, decision_date, police_station, "
                "fir_no, case_category, case_type, under_section, under_act, business_category "
                "FROM court_cases WHERE application_id = :application_id"
            ).params(application_id=application_id)
        )

        rows = result.fetchall()

        court_cases_list = []
        
        court_cases_list = []
        for row in rows:
            court_case_instance = CourtCase(
                name=row[0],
                case_year= row[1] if row[1] is not None and row[1] != "" else "Not Available",
                court_address= row[2] if row[2] is not None and row[2] != "" else "Not Available",
                case_no= row[3] if row[3] is not None and row[3] != "" else "Not Available",
                filing_no= row[4] if row[4] is not None and row[4] != "" else "Not Available",
                registration_no= row[5] if row[5] is not None and row[5] != "" else "Not Available",
                address= row[6] if row[6] is not None and row[6] != "" else "Not Available",
                status= row[7] if row[7] is not None and row[7] != "" else "Not Available",
                order_summary= row[8] if row[8] is not None and row[8] != "" else "Not Available",
                first_hearing= row[9] if row[9] is not None and row[9] != "" else "Not Available",
                next_hearing= row[10] if row[10] is not None and row[10] != "" else "Not Available",
                decision= row[11] if row[11] is not None and row[11] != "" else "Not Available",
                police_station= row[12] if row[12] is not None and row[12] != "" else "Not Available",
                fir_no= row[13] if row[13] is not None and row[13] != "" else "Not Available",
                court_case_type=row[14],
                case_type= row[15] if row[15] is not None and row[15] != "" else "Not Available",
                under_act= row[16] if row[16] is not None and row[16] != "" else "Not Available",
                under_section= row[17] if row[17] is not None and row[17] != "" else "Not Available",
                case_category=row[18] if row[18] is not None and row[18] != "" else "Not Available"
            )
            court_cases_list.append(court_case_instance)
    
        civil_count = sum(1 for case in court_cases_list if case.court_case_type.lower() == "civil")
        criminal_count = sum(1 for case in court_cases_list if case.court_case_type.lower() == "criminal")

        if len(court_cases_list) == 0:
            legal_position_text = "Good"
        elif civil_count == 1:
            legal_position_text = "Concern"
        elif civil_count > 2 or criminal_count >= 1:
            legal_position_text = "Bad"
        
        highlight = []
        if len(court_cases_list) == 0:
            score = 100
            highlight.append("There are no court cases associated with the candidate.")
        elif civil_count > 0 and criminal_count == 0:
            score = max((100 - 20 * civil_count), 0)
            civil_text = "case" if civil_count == 1 else "cases"
            verb = "has" if civil_count == 1 else "have"
            highlight.append(f"{civil_count} Civil {civil_text} {verb} been found for this candidate.")
        elif civil_count == 0 and criminal_count > 0:
            score = max((100 - 50 * criminal_count), 0)
            criminal_text = "case" if criminal_count == 1 else "cases"
            verb = "has" if criminal_count == 1 else "have"
            highlight.append(f"{criminal_count} Criminal {criminal_text} {verb} been found for this candidate.")
        else:
            score = max((100 - 20 * civil_count - 50 * criminal_count), 0)
            civil_text = "case" if civil_count == 1 else "cases"
            criminal_text = "case" if criminal_count == 1 else "cases"
            civil_verb = "has" if civil_count == 1 else "have"
            criminal_verb = "is" if criminal_count == 1 else "are"
            highlight.append(f"{civil_count} Civil {civil_text} {civil_verb} been found for this candidate.")
            highlight.append(f"{criminal_count} Criminal {criminal_text} {criminal_verb} also found for this candidate.")


        index_instance = Index(
            legal_position=score,  
            legal_position_text=legal_position_text,  
            civil=civil_count,
            criminal=criminal_count,
            highlight=highlight  
        )

        response_instance = CourtCaseResponse(application_id=application_id, page_id=1, index=index_instance, cases=court_cases_list)

        # return response_instance
        response_instance.save()

    except HTTPException as ht:
        return ht
    except Exception as e:
        traceback.format_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")