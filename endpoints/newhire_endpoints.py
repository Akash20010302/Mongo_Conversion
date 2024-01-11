
from fastapi import APIRouter, Depends, HTTPException
from async_sessions.sessions import get_db, get_db_backend
from starlette.status import HTTP_404_NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from models.new_hire import Response,Info,Graph,CtcRange

new_hire_router = APIRouter()

@new_hire_router.get("/new_hire/{id}", response_model=Response, tags=['New Hire'])
async def get_past_ctc_accuracy(id: int,  db_1: AsyncSession = Depends(get_db_backend), db_2: AsyncSession = Depends(get_db)):
    ##appid to compid mapping:
    xx = await db_1.execute(
        text('SELECT compid '
             'FROM applicationlist '
             'WHERE id = :id'
        ),
        {"id": id}
    )        
    yy = xx.fetchone()
    #print(yy)
    ##Extracting currentctc, offeredctc from compcanlist
    result = await db_1.execute(
        text('SELECT currentctc, rolebudget, offeredctc '
             'FROM compcanlist '
             'WHERE "id" = :id'
        ),
        {"id": yy[0]}
    )

    ctc_info = result.fetchone()

    if ctc_info is None:
        raise HTTPException(status_code=404, detail=f"Personal information not found for id {id}")

    currentctc = round(float(ctc_info[0]),0)
    offeredctc = round(float(ctc_info[2]),0)
    #gross salary
    #query = text("""
    #    SELECT
    #        COUNT(DISTINCT case when "A2(section_1)" LIKE '192%' then deductor_tan_no end) as salary_accounts,
    #        COUNT(DISTINCT case when "A2(section_1)" LIKE '194%' then deductor_tan_no end) as other_income_accounts,
    #        SUM(case when "A2(section_1)" LIKE '192%' then CAST("A7(paid_credited_amt)" AS FLOAT) end) as total_salary,
    #        SUM(case when "A2(section_1)" LIKE '194%' then CAST("A7(paid_credited_amt)" AS FLOAT) end) as total_other_income
    #    FROM "26as_details"
    #    WHERE person_id = :person_id
    #    AND strftime('%Y-%m-%d', 
    #        substr("A3(transaction_dt)", 8, 4) || '-' || 
    #        case substr("A3(transaction_dt)", 4, 3)
    #            when 'Jan' then '01'
    #            when 'Feb' then '02'
    #            when 'Mar' then '03'
    #            when 'Apr' then '04'
    #            when 'May' then '05'
    #            when 'Jun' then '06'
    #            when 'Jul' then '07'
    #            when 'Aug' then '08'
    #            when 'Sep' then '09'
    #            when 'Oct' then '10'
    #            when 'Nov' then '11'
    #            when 'Dec' then '12'
    #        end || '-' ||
    #        substr("A3(transaction_dt)", 1, 2)
    #    ) >= strftime('%Y-%m-%d', 'now', '-12 months')
    #""")

    
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
    monthly_income_result = await db_2.execute(monthly_income_query, {"person_id":id})
    monthly_income_raw_data = monthly_income_result.fetchall()
    #result = await db_2.execute(query, {"person_id":id})
    #summary = result.fetchone()
    #total_salary = summary[2] if summary[2] is not None else 0.0
    
    pf_result = await db_2.execute(
        text('SELECT "employer_total" '
             'FROM "get_passbook_details" '
             'WHERE "person_id" = :id'
        ),
        {"id": id}
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
    #print("Maximum absolute difference:", max_difference_value)
    
    monthly_income_dict = dict(monthly_income_raw_data)
    salary_list = list(monthly_income_dict.values())
    print(salary_list)
    if len(salary_list) != 12:
        total_salary = int(((sum(salary_list)-max_difference_value)/len(salary_list))*12)
    else:
        total_salary = int((sum(salary_list))- max_difference_value)   


    net_ctc = total_salary + max_difference_value + pf
    possible_ctc_variation = int(net_ctc*15/100)
    estimated_ctc_range = CtcRange(
        lower=net_ctc,
        upper=net_ctc+possible_ctc_variation
        )
    most_likely_past_ctc = int(((2*net_ctc)+possible_ctc_variation)/2)
    gap = int(currentctc-most_likely_past_ctc)      
    ctc_accuracy = min(int((most_likely_past_ctc/currentctc)*100),100)
    gap_percentage = int((gap/currentctc)*100)
    
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

    info_response=Info(
        declared_ctc_accuracy=ctc_accuracy,
        remark= remark,
        declared_past_ctc=currentctc,
        estimated_ctc_range=estimated_ctc_range,
        most_likely_past_ctc=most_likely_past_ctc,
        gap=gap,
        highlight=highlite
    )
    graph_response=Graph(
        gross_salary=total_salary,
        bonus=max_difference_value,
        provident_fund=pf,
        possible_ctc_variation=possible_ctc_variation,
        most_likely_ctc=most_likely_past_ctc,
        declared_ctc=currentctc,
        gap=gap,
        gap_percentage= gap_percentage
    )

    return Response(
        info=info_response,
        graph=graph_response  
    )    