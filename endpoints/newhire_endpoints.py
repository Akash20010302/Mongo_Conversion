from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel import Session
from db.db import get_db_analytics, get_db_backend
from starlette.status import HTTP_404_NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from email_response import send_email

from models.new_hire import Response, Info, Graph, CtcRange

new_hire_router = APIRouter()


@new_hire_router.get("/new_hire/{id}", response_model=Response, tags=["New Hire"])
async def get_past_ctc_accuracy(
    id: int,
    db_1: Session = Depends(get_db_backend),
    db_2: Session = Depends(get_db_analytics),
):
    try:
        ##appid to compid mapping:
        xx = db_1.exec(
            text("SELECT compid " "FROM applicationlist " "WHERE id = :id").params(
                id=id
            )
        )
        yy = xx.fetchone()
        # print(yy)
        ##Extracting currentctc, offeredctc from compcanlist
        result = db_1.exec(
            text(
                "SELECT currentctc, rolebudget, offeredctc "
                "FROM compcanlist "
                "WHERE id = :id"
            ).params(id=yy[0])
        )

        ctc_info = result.fetchone()

        if ctc_info is None:
            raise HTTPException(
                status_code=404, detail=f"Personal information not found for id {id}"
            )

        currentctc = round(float(ctc_info[0]), 0)
        offeredctc = round(float(ctc_info[2]), 0)

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

        monthly_income_result = db_2.exec(
            monthly_income_query.params(application_id=id)
        )
        monthly_income_raw_data = monthly_income_result.fetchall()
        # result = await db_2.execute(query, {"person_id":id})
        # summary = result.fetchone()
        # total_salary = summary[2] if summary[2] is not None else 0.0

        pf_result = db_2.exec(
            text(
                "SELECT employer_total "
                "FROM epfo_get_passbook_details "
                "WHERE application_id = :id"
            ).params(id=id)
        )
        pf_summary = pf_result.fetchone()
        pf = pf_summary[0] if pf_summary[0] is not None else 0

        differences = []

        for i in range(1, len(monthly_income_raw_data)):
            date, value = monthly_income_raw_data[i]
            previous_value = monthly_income_raw_data[i - 1][1]
            difference = abs(value - previous_value)
            differences.append(difference)

        max_difference_value = int(max(differences))
        # print("Maximum absolute difference:", max_difference_value)

        monthly_income_dict = dict(monthly_income_raw_data)
        salary_list = list(monthly_income_dict.values())
        # print(salary_list)
        if len(salary_list) != 12:
            total_salary = int(
                ((sum(salary_list) - max_difference_value) / len(salary_list)) * 12
            )
        else:
            total_salary = int((sum(salary_list)) - max_difference_value)

        net_ctc = total_salary + max_difference_value + pf
        possible_ctc_variation = int(net_ctc * 15 / 100)
        estimated_ctc_range = CtcRange(
            lower=net_ctc, upper=net_ctc + possible_ctc_variation
        )
        most_likely_past_ctc = int(((2 * net_ctc) + possible_ctc_variation) / 2)
        gap = int(currentctc - most_likely_past_ctc)
        ctc_accuracy = min(int((most_likely_past_ctc / currentctc) * 100), 100)
        gap_percentage = int((gap / currentctc) * 100)

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

        info_response = Info(
            declared_ctc_accuracy=ctc_accuracy,
            remark=remark,
            declared_past_ctc=currentctc,
            estimated_ctc_range=estimated_ctc_range,
            most_likely_past_ctc=most_likely_past_ctc,
            gap=gap,
            highlight=highlite,
        )
        graph_response = Graph(
            gross_salary=total_salary,
            bonus=max_difference_value,
            provident_fund=pf,
            possible_ctc_variation=possible_ctc_variation,
            most_likely_ctc=most_likely_past_ctc,
            declared_ctc=currentctc,
            gap=gap,
            gap_percentage=gap_percentage,
        )

        return Response(info=info_response, graph=graph_response)
    except Exception as e:
        send_email(500, "Report_new_hire")
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(detail="Internal Server Error", status_code=500)
