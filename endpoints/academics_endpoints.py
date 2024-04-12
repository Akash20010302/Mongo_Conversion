from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from sqlalchemy.sql import text
from fuzzywuzzy import fuzz
from loguru import logger
from db.db import get_db_analytics, get_db_backend
from email_response import send_email

# from models.Academics import AcademicDetailsResponse
from mongomodels.Academics import AcademicDetailsResponse

from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK,
)
from mongoengine import connect



academics_router = APIRouter()

connect(db='trace_about', host="mongodb://localhost:27017/")




@academics_router.get(
    "/academic_details/{application_id}/{candidatetype}",
    tags=["Academic Details"],
)
async def get_academic_details(
    application_id: int,
    candidatetype: str,
    db: Session = Depends(get_db_analytics),
    db_backend: Session = Depends(get_db_backend),
):
    try:
        
        # govt_docs
        # query = text(
        #         """
        #         SELECT degree,
        #             institute,
        #             start_year,
        #             end_year
        #         FROM
        #             academics
        #         WHERE application_id = :application_id
        #     """
        #     )

        # result = db.exec(query.params(application_id=application_id))
        # govt_data_raw = result.fetchall()
        
        # logger.debug(result)

        # govt_data = []
        # if len(govt_data_raw):
        #     for edu in govt_data_raw:

        #         temp_dict = {
        #             "degree" : edu[0],
        #             "institute" : edu[1],
        #             "start_date" : edu[2],
        #             "end_date" : edu[3],
        #             "year": 4,
        #             "totalMonth":""}

        #         govt_data.append(temp_dict)
        
            #resume
        if candidatetype == "Employee":
            resume_query = text(
                    """
                    SELECT educationlevel,
                        institutename,
                        startyear,
                        endyear
                    FROM
                        employeeacademics
                    WHERE formid = :formid
                """
                )
        elif candidatetype == "New Hire":
            resume_query = text(
                    """
                    SELECT educationlevel,
                        institutename,
                        startyear,
                        endyear
                    FROM
                        newhireacademics
                    WHERE formid = :formid
                """
                )
        else:
            return HTTPException(status_code=400,detail="detail not found")
        result = db_backend.exec(resume_query.params(formid=application_id))
        resume_data_raw = result.fetchall()
        logger.debug(resume_data_raw)

        resume_data = []
        if len(resume_data_raw):
            for edu in resume_data_raw:
                if edu[2] != "" and edu[3] != "":
                    start_date = datetime.strptime(edu[2], '%Y-%m-%d')
                    end_date = datetime.strptime(edu[3], '%Y-%m-%d')
                    totalMonth = (end_date.year - start_date.year) * 12 + (
                    start_date.month - end_date.month
                )
                else:
                    totalMonth=""
                logger.debug(totalMonth)
                temp_dict = {
                    "degree" : edu[0],
                    "institute" : edu[1],
                    "start_year" : edu[2],
                    "end_year" : edu[3],
                    "totalMonth":totalMonth}

                resume_data.append(temp_dict) 

        govt_data = []
    
        red_flag = 0
        discrepancies = 0
        #TODO: red flag and discrepancy logic built

        highlight = []

        
        highlight.append("No situation of shifted timeline found") #Dummy response

        score= 100 - 2 * discrepancies - 10 * red_flag

        score = max(score,0)

        if score >= 95:
            score_text = "Good"

        elif score >=80 and score <95:
            score_text = "Concern"

        else:
            score_text = "Bad"
        info_document = AcademicDetailsResponse(
            application_id = application_id,
            candidate_type = candidatetype,
            page_id =1,
            all_academic_govt_docs=govt_data,
            all_academic_tenure=resume_data,
            red_flag=red_flag,
            discrepancies=discrepancies,
            highlight=highlight,
            academic_score=score,
            academic_score_text=score_text
        )
        info_document.save()       
    
    except HTTPException as ht:
        return ht
    except Exception as e:
        #send_email(500, "Report_academic_details")
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(detail="Internal Server Error", status_code=500)