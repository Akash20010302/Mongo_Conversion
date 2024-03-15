from collections import defaultdict
import datetime
import math
import random
import statistics
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel import Session
from db.db import get_db_analytics, get_db_backend
from starlette.status import HTTP_404_NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from email_response import send_email
from tools.benchmark_tools import (
    get_indicator,
    convert_to_datetime,
    get_ratio_indicator,
)
from models.Benchmark import (
    ChangeResponse,
    IdealCtcBand,
    CtcResponse,
    estimatedExpense,
    ExpenseIncomeAnalysis,
    NewResponse,
    PayAnalysis,
    PreviousResponse,
    Response,
    TenureAnalysis,
)

benchmark_router = APIRouter()


@benchmark_router.get("/benchmark/{id}", response_model=Response, tags=["Benchmarking"])
async def get_ctc_info(
    id: int,
    db_1: Session = Depends(get_db_backend),
    db_2: Session = Depends(get_db_analytics),
):
    try:
        ##appid to compid mapping:
        compid_result = db_1.exec(
            text('SELECT compid '
                'FROM `applicationlist` '
                'WHERE id = :id'
            ).params(id = id)
        )        
        compid = compid_result.fetchone()
        if compid is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Comp_id is not found for id : {id}")
        else:
            comp_id = compid[0]


        result = db_1.exec(
        text('SELECT currentctc, rolebudget, offeredctc '
            'FROM `compcanlist` '
            'WHERE id = :id').params(id = comp_id)
        )
        ctc_info = result.fetchone()
        if ctc_info:
            currentctc = round(float(ctc_info[0]),0)
            offeredctc = round(float(ctc_info[2]),0)
        else:
            currentctc = 0
            offeredctc = 0
        lower_limit = random.randint(offeredctc*(0.6),offeredctc*(0.7))
        upper_limit = random.randint(offeredctc*(1.2),offeredctc*(1.5))
        
        difference = offeredctc - currentctc
        change_in_ctc = difference
        change_percent = round((float(difference / currentctc) * 100),0) if currentctc != 0 else 0
        

        if change_percent < 5:
            ctc_growth = [change_percent, "Low"]
        elif 5 <= change_percent < 20:
            ctc_growth = [change_percent, "Optimal"]
        elif 20 <= change_percent < 40:
            ctc_growth = [change_percent, "High"]
        else:
            ctc_growth = [change_percent, "Very High"]
        highlight = f"CTC change reflects {ctc_growth[1]} CTC growth"

        offered_ctc_percentange = min(round(float((offeredctc / upper_limit) * 100), 0),100) if upper_limit != 0 else 0
        if offered_ctc_percentange < 50:
            output = [offered_ctc_percentange, "LOW"]
        elif 50 <= offered_ctc_percentange < 75:
            output = [offered_ctc_percentange, "Optimal"]
        elif 75 <= offered_ctc_percentange < 90:
            output = [offered_ctc_percentange, "High"]
        else:
            output = [offered_ctc_percentange, "Very High"]

        currentctc_indicator = await get_indicator(currentctc,lower_limit,upper_limit)
        offeredctc_indicator = await get_indicator(offeredctc,lower_limit,upper_limit)
        risk_ = f"{offeredctc_indicator[0]} Cost to the Company"

        ##extracting name
        first_name = db_1.exec(
            text("SELECT firstName " "FROM form " "WHERE appid = :id").params(id=id)
        )
        firstname = first_name.fetchone()
        name = firstname[0]
        # logger.debug("PASSED FIRST NAME")
        ##payanalysis
        current_percentile = round(((currentctc - lower_limit) / (upper_limit - lower_limit)) * 100,2) if (upper_limit-lower_limit) != 0 else 0
        offered_percentile = round(((offeredctc - lower_limit) / (upper_limit - lower_limit)) * 100,2) if (upper_limit-lower_limit) != 0 else 0
        ## to do-0-20= minor
        # 20-30= moderate
        # 30-50= major
        # else- very high
        change_in_pay = ((offeredctc - currentctc) / currentctc) * 100
        if change_in_pay < 20:
            pay_analysis_remark = "Minor"
        elif 20 <= change_in_pay < 30:
            pay_analysis_remark = "Moderate"
        elif 30 <= change_in_pay < 50:
            pay_analysis_remark = "Major"
        else:
            pay_analysis_remark = "Very High"
        pay_analysis_final_remark = f"Based on {name}'s Education, location, Industry, role and experience, he will be moving from {current_percentile} percentile to {offered_percentile} percentile level. This will be considered as a {pay_analysis_remark} change in Pay."

        query_1 = text(
            """
            SELECT
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
                END) AS total_other_income
            FROM itr_26as_details
            WHERE application_id = :application_id
                AND transaction_dt >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        """
        )

        result_1 = db_2.exec(query_1.params(application_id=id))
        summary_1 = result_1.fetchone()
        if summary_1:
            total_other_income = summary_1[0]
        else:
            total_other_income = 0.0

        query_2 = text(
            """
        SELECT DISTINCT AccountNumber, AccountType, LastPayment, AccountStatus
        FROM credits_retailaccountdetails
        WHERE application_id = :application_id AND AccountStatus = 'Current Account'
    """
        )

        result_2 = db_2.exec(query_2.params(application_id=id))
        summary_2 = result_2.fetchall()
        if not summary_2:
            emi = 0
        else:
            emi = sum(
                float(row[2])
                for row in summary_2
                if row[2] is not None and row[2] != ""
            )


        total_other_income = float(total_other_income) if total_other_income is not None else 0.0
        factor = 0.3
        new_exp = ((offeredctc) * 0.4) + emi
        new_increase = round(float(new_exp + (new_exp * factor)), 0)
        new_decrease = round(float(new_exp - (new_exp * factor)), 0)
        new_income = float(offeredctc) + float(total_other_income)
        pre_exp = ((currentctc) * 0.4) + emi
        pre_income = float(currentctc) + float(total_other_income)
        ctc_change = offeredctc - currentctc
        income_change = new_income - pre_income
        exp_change = new_exp - pre_exp

        most_likely_expense = round(float((pre_exp + new_exp) / 2), 0)
        new_ratio = round(float((most_likely_expense / new_income) * 100), 0) if new_income != 0 else 0
        pre_ratio = round(float((most_likely_expense / pre_income) * 100), 0) if pre_income != 0 else 0
        # print(new_ratio,pre_ratio)

        if new_ratio > pre_ratio:
            ratio_change = new_ratio - pre_ratio
        else:
            ratio_change = pre_ratio - new_ratio

        # Determine risk
        change_ratio = pre_ratio - new_ratio
        if 25 < change_ratio:
            risk = "Vey Low Financial Instability"
        elif 3 < change_ratio <= 25:
            risk = "Low Financial Instability"
        elif -3 <= change_ratio <= 3:
            risk = "No change in Financial Instability"
        elif 3 < change_ratio <= 15:
            risk = "Vey Low Financial Instability"
        else:
            risk = "Vey Low Financial Instability"

        pre_ratio_indicator = await get_ratio_indicator(pre_ratio)
        new_ratio_indicator = await get_ratio_indicator(new_ratio)

        if pre_ratio_indicator[0] == new_ratio_indicator[0]:
            expense_remark = "Minor"
        else:
            expense_remark = "Major"

        if pre_ratio_indicator[0] == new_ratio_indicator[0]:
            expense_income_remark = f"{name}’s Expense to Income ratio is changing from {pre_ratio}%({pre_ratio_indicator[0]}) to {new_ratio}%({new_ratio_indicator[0]}). This will be considered as a {expense_remark} change in Family’s Financial position."
        else:
            expense_income_remark = f"{name}’s Expense to Income ratio is changing from {pre_ratio}%({pre_ratio_indicator[0]}) to {new_ratio}%({new_ratio_indicator[0]}). This will be considered as a {expense_remark} change in Family’s Financial position."

        idealctcband = IdealCtcBand(lower=lower_limit, upper=upper_limit)
        estimated_range = estimatedExpense(lower=new_decrease, upper=new_increase)

        new_response = NewResponse(
            HouseholdTakeHome=offeredctc,
            OtherIncome=total_other_income,
            TotalTakeHome=new_income,
            EMI_CreditCard=emi,
            EstimatedExpense=estimated_range,
            MostLikelyExpense=most_likely_expense,
            E_IRatio=new_ratio,
        )

        pre_response = PreviousResponse(
            HouseholdTakeHome=currentctc,
            OtherIncome=total_other_income,
            TotalTakeHome=pre_income,
            EMI_CreditCard=emi,
            EstimatedExpense=estimated_range,
            MostLikelyExpense=most_likely_expense,
            E_IRatio=pre_ratio,
        )

        change_response = ChangeResponse(
            HouseholdTakeHome=ctc_change,
            OtherIncome=total_other_income,
            TotalTakeHome=income_change,
            EMI_CreditCard=0,
            EstimatedExpense="0",
            MostLikelyExpense=0,
            E_IRatio=ratio_change,
        )

        ctc = CtcResponse(
            ctc_benchmark_analysis=output,
            offeredctc=str(offeredctc),
            ideal_ctc_band=idealctcband,
            past_ctc=str(currentctc),
            change_in_ctc=change_in_ctc,
            ctc_growth=ctc_growth,
            highlight=highlight,
        )

        indicators = PayAnalysis(
            previous_pay=currentctc_indicator,
            current_offer=offeredctc_indicator,
            highlight_1=risk_,
            highlight_2=pay_analysis_final_remark,
        )

        E_i = ExpenseIncomeAnalysis(
            expense_income_ratio=new_ratio_indicator,
            total_household_income=int(new_income),
            most_likely_expense=most_likely_expense,
            highlights=expense_income_remark,
            prev=pre_response,
            new_=new_response,
            change_=change_response,
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
        if passbook_raw_data is not None:
            for exp in passbook_raw_data:
                company_name = exp[0]
                year = exp[1]
                month = exp[2]

                date = await convert_to_datetime(year, month)
                if date:
                    company_data[company_name].append(date)
                else:
                    company_data[company_name].append("N/A")

        result = []
        overlapping_durations = []
        gaps = []
        durations = []
        # count=0

        if company_data is not None:
            for company_name, dates in company_data.items():
                if dates != "N/A":
                    dates = [date for date in dates if isinstance(date, datetime.datetime)]
                    if dates:
                        start_date = min(dates)
                        end_date = max(dates)
                        duration = (end_date.year - start_date.year) * 12 + (
                            end_date.month - start_date.month
                        )

                        # row_value = 1 if count % 2 == 0 else 2
                        result.append(
                            {
                                # "row": row_value,
                                "company_name": company_name,
                                "startYear": start_date.strftime("%m-%d-%Y"),
                                "endYear": end_date.strftime("%m-%d-%Y"),
                                "duration": duration,
                            }
                        )
                        # count+=1
                        durations.append(duration)
                # else:
                #    result.append({"company_name": company_name, "start_date": "N/A","end_date": "N/A","duration":"N/A"})

        if result:
            result = sorted(result, key=lambda x: x.get("startYear", "N/A"))
            for i, item in enumerate(result):
                item["row"] = 1 if i % 2 == 0 else 2
            # result = sorted(result, key=lambda x: (x.get("start_date", "N/A"), x.get("row", 0)))
            ## for inserting type
            for i, job in enumerate(result):
                if i > 0:
                    prev_job = sorted(result, key=lambda x: x.get("startYear", "N/A"))[
                        i - 1
                    ]
                    if job["startYear"] < prev_job["endYear"]:
                        job["workType"] = "overlap"
                    else:
                        job["workType"] = "regular"
                else:
                    job["workType"] = "regular"

        if durations:
            total_duration = round(float(sum(durations)/12),2)
            total_duration = round(total_duration, 0)
            median_duration = int(statistics.median(durations))
            average_duration = int(statistics.mean(durations))
        else:
            total_duration = 0
            median_duration = 0
            average_duration = 0
        if result:
            total_jobs = len(result)
        else:
            total_jobs = 0    


        if average_duration < 15:
            risk_duration = "Very High"
        elif 15 <= average_duration < 35:
            risk_duration = "High"
        elif 35 <= average_duration < 60:
            risk_duration = "Optimal"
        else:
            risk_duration = "Low"

        if average_duration < 24:
            remark = "short"
        elif 24 <= average_duration <= 60:
            remark = "average"
        else:
            remark = "Long"
        tenure_remarks = f"{name}’s tenure with companies seem to be {remark}. This could be linked to his personal performance or market opportunity."

        # Calculate calculated_work_exp
        calculated_work_exp = 0
        logger.debug(total_jobs)
        if total_jobs == 1:
            # If there's only one job, use the duration of that job
            calculated_work_exp = result[0]["duration"]
            calculated_work_exp = round((calculated_work_exp / 12), 1)
        elif total_jobs > 1:
            # If there are multiple jobs, calculate the difference between the start date of the first job
            # and the end date of the last job
            first_job_start_dates = [datetime.datetime.strptime(job["startYear"], "%m-%d-%Y") for job in result]
            first_job_start_date = min(first_job_start_dates)
            #last_job_end_date = max(result, key=lambda x: x["endYear"])["endYear"]
            #last_job_end_date = max(job["endYear"] for job in result)
            # Assuming startYear and endYear are in the format "%m-%d-%Y", convert them to datetime objects
            #first_job_start_date = datetime.datetime.strptime(
            #    first_job_start_date, "%m-%d-%Y"
            #)
            #last_job_end_date = datetime.datetime.strptime(
            #    last_job_end_date, "%m-%d-%Y"
            #)
            last_job_end_dates = [datetime.datetime.strptime(job["endYear"], "%m-%d-%Y") for job in result]
            last_job_end_date = max(last_job_end_dates)
            
            # Calculate the difference in months
            calculated_work_exp = (
                last_job_end_date.year - first_job_start_date.year
            ) * 12 + (last_job_end_date.month - first_job_start_date.month)
            calculated_work_exp = round((calculated_work_exp / 12), 1)
            logger.debug(result)
            logger.debug(first_job_start_date)
            logger.debug(last_job_end_date)
        tenure = TenureAnalysis(
            work_exp=result,
            avg_tenure=average_duration,
            median_tenure=median_duration,
            Risk=risk_duration,
            remarks=tenure_remarks,
            total_exp=total_duration,
            num_of_jobs=total_jobs,
            calculated_work_exp=calculated_work_exp if calculated_work_exp is not None else 0.0,
        )

        return Response(
            ctc_offered=ctc,
            pay_analysis=indicators,
            Expense_income_analysis=E_i,
            Tenure_analysis=tenure,
        )
    except Exception as e:
        send_email(500, "Report_benchmark")
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(detail="Internal Server Error", status_code=500)
