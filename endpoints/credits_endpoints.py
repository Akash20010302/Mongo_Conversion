from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import text
from sqlmodel import Session
from db.db import get_db_analytics
from email_response import send_email
# from models.credits import CombinedResponseModel, Enquiries, tradeline
from mongomodels.Credits import CombinedResponseModel, Enquiries, tradeline, DatePhoneTuple, DateEmailTuple, DateAddressTuple
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from mongoengine import connect
from typing import List, Tuple

credits_router = APIRouter()

connect(db='trace_about', host="mongodb://localhost:27017/")




def compute_score_factors(
    enquiries_data, summary_data, active_account_count, credit_score
):
    score_factors = []

    # Assuming the order of summary_data is as follows:
    # 0: number_of_closed_accounts, 1: total_balance, 2: total_credit_limit, 3: total_past_due
    total_credit_limit = float(summary_data[2]) if summary_data[2] is not None else 0.0

    # Rule 1: Insufficient payment activity over the last year
    if active_account_count < 3:
        score_factors.append("Insufficient payment activity over the last year")
    else:
        score_factors.append("Sufficient payment activity over the last year")

    # Rule 2: Not enough available credit
    if total_credit_limit < 10000000:
        score_factors.append("Not enough available credit")
    else:
        score_factors.append("Enough available credit")

    # Assuming the order of enquiries_data is as follows:
    # 0: queries_last_1_month, 1: queries_last_3_months, 2: queries_last_6_months, 3: queries_last_12_months, 4: queries_last_24_months
    queries_last_12_months = enquiries_data[3] if enquiries_data[3] else 0

    # Rule 3: Too many inquiries
    if queries_last_12_months > 2:
        score_factors.append("Too many inquiries")
    else:
        score_factors.append("Limited inquiries")

    # Rule 4: Not enough balance decreases on active non-mortgage accounts

    if credit_score < 600:
        score_factors.append(
            "Not enough balance decreases on active non-mortgage accounts"
        )
    else:
        score_factors.append("Enough balance decreases on active non-mortgage accounts")

    return score_factors


@credits_router.get(
    "/credit_standing/{application_id}",
    tags=["Credit Details"],
)
async def get_career_summary(
    application_id: str, db: Session = Depends(get_db_analytics)
):
    try:
        validation_query = text("""
                                SELECT count(*) FROM epfo_status_uan WHERE application_id = :application_id
                                """)
        
        valid_count = db.exec(validation_query.params(application_id=application_id))
        count_raw_data = valid_count.fetchone()
        if count_raw_data[0] == 0:
            raise HTTPException(detail="Application not found", status_code=404)
        
        query_accounts = text(
            """
            SELECT DISTINCT AccountNumber
            FROM credits_retailaccountdetails
            WHERE application_id = :application_id
            AND AccountStatus = 'Current Account'
            AND OwnershipType = 'Individual'
            AND CAST(Balance AS DECIMAL) > :balance
        """
        )

        query_summary = text(
            """
            SELECT 
                (SELECT DISTINCT COUNT(DISTINCT AccountNumber) FROM credits_retailaccountdetails WHERE AccountStatus = 'Closed Account' AND application_id = :application_id) as number_of_closed_accounts,
                SUM(DISTINCT CAST(Balance AS DECIMAL)) as total_balance,
                SUM(DISTINCT  CAST(CreditLimit AS DECIMAL)) as total_credit_limit,
                SUM(DISTINCT  CAST(PastDueAmount AS DECIMAL)) as total_past_due,
                AccountNumber
            FROM credits_retailaccountdetails
            WHERE application_id = :application_id    
            
        """
        )

        query_enquiries = text(
            """
            SELECT 
                SUM(CASE WHEN DATE(Date) >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH) THEN 1 ELSE 0 END) as queries_last_1_month,
                SUM(CASE WHEN DATE(Date) >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH) THEN 1 ELSE 0 END) as queries_last_3_months,
                SUM(CASE WHEN DATE(Date) >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) THEN 1 ELSE 0 END) as queries_last_6_months,
                SUM(CASE WHEN DATE(Date) >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH) THEN 1 ELSE 0 END) as queries_last_12_months,
                SUM(CASE WHEN DATE(Date) >= DATE_SUB(CURDATE(), INTERVAL 24 MONTH) THEN 1 ELSE 0 END) as queries_last_24_months
            FROM credits_enquiries
            WHERE application_id = :application_id
        """
        )

        query_credit_score = text(
            """
            SELECT 
                credit_score
            FROM credits_creditdata_master
            WHERE application_id = :application_id
        """
        )

        query_phone = text(
            """
            SELECT ReportedDate, Number
            FROM credits_phoneinfo
            WHERE application_id = :application_id
        """
        )

        query_email = text(
            """
            SELECT ReportedDate, EmailAddress
            FROM credits_emailinfo
            WHERE application_id = :application_id
        """
        )
        query_address = text(
            """
            SELECT ReportedDate, Address
            FROM credits_addressinfo
            WHERE application_id = :application_id
        """
        )

        tradeline_summary_installment_query = text(
            """
                                    SELECT 
                                        COUNT(DISTINCT Balance) as distinct_balance_count,
                                        SUM(DISTINCT Balance) as distinct_balance_sum,
                                        SUM(DISTINCT PastDueAmount) as distinct_past_due_sum,
                                        SUM(DISTINCT HighCredit) as distinct_high_credit_sum,
                                        SUM(DISTINCT CreditLimit) as distinct_high_credit_limit
                                    FROM credits_retailaccountdetails
                                    WHERE AccountType != "Credit Card" 
                                        AND AccountStatus = "Current Account" 
                                        AND DATE(LastPaymentDate) >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                                        AND application_id = :application_id
                                    """
        )
        tradeline_summary_open_query = text(
            """
                                    SELECT 
                                        COUNT(DISTINCT Balance) as distinct_balance_count,
                                        SUM(DISTINCT Balance) as distinct_balance_sum,
                                        SUM(DISTINCT PastDueAmount) as distinct_past_due_sum,
                                        SUM(DISTINCT HighCredit) as distinct_high_credit_sum,
                                        SUM(DISTINCT CreditLimit) as distinct_high_credit_limit
                                    FROM credits_retailaccountdetails
                                    WHERE AccountStatus = "Current Account" 
                                        AND DATE(LastPaymentDate) >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                                        AND application_id = :application_id
                                    """
        )
        tradeline_summary_close_query = text(
            """
                                    SELECT 
                                        COUNT(DISTINCT Balance) as distinct_balance_count,
                                        SUM(DISTINCT Balance) as distinct_balance_sum,
                                        SUM(DISTINCT PastDueAmount) as distinct_past_due_sum,
                                        SUM(DISTINCT HighCredit) as distinct_high_credit_sum,
                                        SUM(DISTINCT CreditLimit) as distinct_high_credit_limit
                                    FROM credits_retailaccountdetails
                                    WHERE AccountStatus = "Closed Account" 
                                        AND DATE(LastPaymentDate) >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                                        AND application_id = :application_id
                                    """
        )

        # Execute queries
        result_accounts = db.exec(
            query_accounts.params(application_id=application_id, balance=99)
        )
        result_summary = db.exec(query_summary.params(application_id=application_id))
        result_enquiries = db.exec(
            query_enquiries.params(application_id=application_id)
        )
        result_credit_score = db.exec(
            query_credit_score.params(application_id=application_id)
        )
        result_installment = db.exec(
            tradeline_summary_installment_query.params(application_id=application_id)
        )
        result_open = db.exec(
            tradeline_summary_open_query.params(application_id=application_id)
        )
        result_close = db.exec(
            tradeline_summary_close_query.params(application_id=application_id)
        )

        # Fetch results
        active_accounts_data = result_accounts.fetchall()
        logger.debug(active_accounts_data)
        summary_data = result_summary.fetchone()
        logger.debug(summary_data)
        enquiries_data = result_enquiries.fetchone()
        logger.debug(enquiries_data)
        credit_score = result_credit_score.fetchone()
        logger.debug(credit_score)
        installment_data = result_installment.fetchone()
        logger.debug(installment_data)
        open_data = result_open.fetchone()
        logger.debug(open_data)
        close_data = result_close.fetchone()
        logger.debug(close_data)
        # Extract information
        active_accounts = [row[0] for row in active_accounts_data]
        active_account_count = len(active_accounts)

        result_phone = db.exec(query_phone.params(application_id=application_id))
        phone_data = [(row[0], row[1]) for row in result_phone.fetchall()]

        # Execute email query
        result_email = db.exec(query_email.params(application_id=application_id))
        email_data = [(row[0], row[1]) for row in result_email.fetchall()]

        # Execute address query
        result_address = db.exec(query_address.params(application_id=application_id))
        address_data = [(row[0], row[1]) for row in result_address.fetchall()]

        # Score Summary
        active_accounts = [row[0] for row in active_accounts_data]
        active_account_count = len(active_accounts)
        # summary_data = summary_data
        enquiries_data = enquiries_data
        credit_score = int(credit_score[0]) if credit_score else 0

        score_factors = compute_score_factors(
            enquiries_data, summary_data, active_account_count, credit_score
        )

        # # Fetch data from SQL database
        # query_result = db.exec(query_params)
        # result_data = query_result.fetchone()

        # # Transform tuple result into a dictionary
        # data_dict = dict(result_data)
    
        
        # Handling Old data and Current data
        existing_document = CombinedResponseModel.objects(application_id=application_id, page_id=1).first()
        if existing_document:
            existing_document.delete()

        # response = CombinedResponseModel(**data_dict)

        # Build the response
        response = CombinedResponseModel(
            application_id=application_id,
            page_id = 1,
            active_accounts=active_accounts,
            enquiries=Enquiries(
                queries_last_1_month=enquiries_data[0]
                if enquiries_data[0] is not None
                else 0,
                queries_last_3_months=enquiries_data[1]
                if enquiries_data[1] is not None
                else 0,
                queries_last_6_months=enquiries_data[2]
                if enquiries_data[2] is not None
                else 0,
                queries_last_12_months=enquiries_data[3]
                if enquiries_data[3] is not None
                else 0,
                queries_last_24_months=enquiries_data[4]
                if enquiries_data[4] is not None
                else 0,
            ),
            active_account_count=active_account_count,
            number_of_closed_accounts=summary_data[0],
            total_balance=float(summary_data[1])
            if summary_data[1] is not None
            else 0.0,
            total_credit_limit=float(summary_data[2])
            if summary_data[2] is not None
            else 0.0,
            total_past_due=float(summary_data[3])
            if summary_data[3] is not None
            else 0.0,
            credit_score=credit_score if credit_score else 0.0,
            tradeline_summary_installment=tradeline(
                count=installment_data[0] if installment_data[0] else 0,
                balance=installment_data[1] if installment_data[1] else 0,
                past_due=installment_data[2] if installment_data[2] else 0,
                high_credit=installment_data[3] if installment_data[3] else 0,
                credit_limit=installment_data[4] if installment_data[4] else 0,
            ),
            tradeline_summary_open=tradeline(
                count=open_data[0] if open_data[0] else 0,
                balance=open_data[1] if open_data[1] else 0,
                past_due=open_data[2] if open_data[2] else 0,
                high_credit=open_data[3] if open_data[3] else 0,
                credit_limit=open_data[4] if open_data[4] else 0,
            ),
            tradeline_summary_close=tradeline(
                count=close_data[0] if close_data[0] else 0,
                balance=close_data[1] if close_data[1] else 0,
                past_due=close_data[2] if close_data[2] else 0,
                high_credit=close_data[3] if close_data[3] else 0,
                credit_limit=close_data[4] if close_data[4] else 0,
            ),
            tradeline_summary_total=tradeline(
                count=open_data[0] if open_data[0] else 0,
                balance=open_data[1] if open_data[1] else 0,
                past_due=open_data[2] if open_data[2] else 0,
                high_credit=open_data[3] if open_data[3] else 0,
                credit_limit=open_data[4] if open_data[4] else 0,
            ),
            # phone_numbers=phone_data,
            # email_addresses=email_data,
            # addresses=address_data,
            phone_numbers=[DatePhoneTuple(date=date, phone=number) for date, number in phone_data],
            addresses=[DateAddressTuple(date=date, address=address) for date, address in address_data],
            email_addresses=[DateEmailTuple(date=date, email=email) for date, email in email_data],
            score_factors=score_factors if score_factors else [],
        )
        logger.debug(response)
        # print(response.to_mongo())
        # info_result1 = response
        # response.save()
        response.save()

    except HTTPException as ht:
        raise ht
    except Exception as e:
        send_email(500, "Report_credit_standing")
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(detail="Internal Server Error", status_code=500)
