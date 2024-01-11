from collections import defaultdict
import datetime
import statistics
from fastapi import APIRouter, Depends, HTTPException
from async_sessions.sessions import get_db, get_db_backend
from starlette.status import HTTP_404_NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from tools.benchmark_tools import get_indicator, convert_to_datetime,get_ratio_indicator
from models.Benchmark import ChangeResponse,IdealCtcBand, CtcResponse, ExpenseIncomeAnalysis, NewResponse, PayAnalysis, PreviousResponse, Response, TenureAnalysis

benchmark_router = APIRouter()

@benchmark_router.get("/benchmark/{id}", response_model=Response, tags=['Benchmarking'])
async def get_ctc_info(id: int,  db_1: AsyncSession = Depends(get_db_backend), db_2: AsyncSession = Depends(get_db)):
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
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"Personal information not found for id : {id}")

    currentctc = float(ctc_info[0])
    offeredctc = float(ctc_info[2])

    difference = offeredctc - currentctc
    change_in_ctc = difference
    change_percent = round((float(difference / currentctc) * 100),0) if currentctc != 0 else 0
    
    if change_percent < 5:
        ctc_growth = [change_percent,"Low"]
    elif 5<=change_percent<20:
        ctc_growth = [change_percent,"Optimal"]
    elif 20<= change_percent<40:
        ctc_growth = [change_percent,"High"]
    else:
        ctc_growth = [change_percent,"Very High"]            
    highlight = f"CTC change reflects {ctc_growth[1]} CTC growth"    
        

    offered_ctc_percentange = round(float((offeredctc/2800000)*100),0)
    if offered_ctc_percentange < 50:
        output = [offered_ctc_percentange,"LOW"]
    elif 50<= offered_ctc_percentange<75:
        output = [offered_ctc_percentange,"Optimal"]
    elif 75<= offered_ctc_percentange<90:
        output=[offered_ctc_percentange,"High"]
    else:
        output= [offered_ctc_percentange,"Very High"]
        


    currentctc_indicator = await get_indicator(currentctc)
    offeredctc_indicator = await get_indicator(offeredctc)
    risk_ = f"{offeredctc_indicator[0]} Cost to the Company"

    ##extracting name 
    first_name = await db_1.execute(
        text('SELECT firstName '
             'FROM form '
             'WHERE appid = :id'
        ),
        {"id": id}
    )        
    firstname = first_name.fetchone()
    name = firstname[0]

    ##payanalysis
    current_percentile =((currentctc-1200000)/(2800000-1200000))*100
    offered_percentile =((offeredctc-1200000)/(2800000-1200000))*100
## to do-0-20= minor
#20-30= moderate
#30-50= major
#else- very high
    change_in_pay = ((offeredctc - currentctc)/currentctc)*100
    if change_in_pay <20:
        pay_analysis_remark = "Minor"
    elif 20<=change_in_pay<30:
        pay_analysis_remark = "Moderate"
    elif 30<= change_in_pay<50:
        pay_analysis_remark = "Major"        
    else:
        pay_analysis_remark = "Very High" 
    pay_analysis_final_remark = f"Based on {name}'s Education, location, Industry, role and experience, he will be moving from {current_percentile} percentile to {offered_percentile} percentile level. This will be considered as a {pay_analysis_remark} change in Pay."       
##Expense/Income ratio:
    query_1 = text("""
        SELECT
            SUM(case when "A2(section_1)" LIKE '194%' then CAST("A7(paid_credited_amt)" AS FLOAT) end) as total_other_income
        FROM "26as_details"
        WHERE person_id = :person_id
    """)

    result_1 = await db_2.execute(query_1, {"person_id": id})
    summary_1 = result_1.fetchone()
    total_other_income = summary_1[0] if summary_1[0] is not None else 0.0

    query_2 = text("""
    SELECT DISTINCT person_id, AccountNumber, AccountType, LastPayment, AccountStatus
    FROM "RetailAccountDetails"
    WHERE person_id = :person_id AND AccountStatus = "Current Account"
    """)


    result_2 = await db_2.execute(query_2, {"person_id": id})
    summary_2 = result_2.fetchall()
    if not summary_2:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=f"No records found for person_id : {id}")

    emi = sum(float(row[3]) for row in summary_2 if row[3] is not None and row[3] != "")

    factor=0.3
    new_exp = ((offeredctc)*0.4)+emi
    new_increase =round(float(new_exp + (new_exp * factor)),0) 
    new_decrease =round(float(new_exp - (new_exp * factor)),0)
    new_income =(float(offeredctc)+float(total_other_income))
    pre_exp = ((currentctc)*0.4)+emi
    pre_income =(float(currentctc)+float(total_other_income))
    ctc_change =(offeredctc - currentctc)
    income_change = (new_income- pre_income)
    exp_change = (new_exp - pre_exp)
    new_ratio =round(float((new_exp/new_income)*100),0)
    pre_ratio = round(float((pre_exp/pre_income)*100),0)
    most_likely_expense = round(float((pre_exp+new_exp)/2),0)

    if new_ratio > pre_ratio:
        ratio_change = new_ratio - pre_ratio
    else:
        ratio_change = pre_ratio - new_ratio

# Determine risk
    change_ratio = pre_ratio - new_ratio
    if 25 < change_ratio:
        risk = "Vey Low Financial Instability"
    elif 3 < change_ratio <=25:
        risk = "Low Financial Instability"
    elif -3 <= change_ratio <= 3:
        risk = "No change in Financial Instability"
    elif 3< change_ratio <=15:
        risk = "Vey Low Financial Instability"
    else:
        risk = "Vey Low Financial Instability"
#Creating Remarks:
#    if ratio_change < 15:
#        expense_remark = "Minor"
#    else:
#        expense_remark = "Major"
    pre_ratio_indicator = await get_ratio_indicator(pre_ratio)
    new_ratio_indicator = await get_ratio_indicator(new_ratio)
    
    if pre_ratio_indicator[0]==new_ratio_indicator[0]:
        expense_remark = "Minor"
    else:
        expense_remark = "Major"

    if pre_ratio_indicator[0] == new_ratio_indicator[0]:
        expense_income_remark = f"{name}’s Expense to Income ratio is changing from {pre_ratio}%({pre_ratio_indicator[0]}) to {new_ratio}%({new_ratio_indicator[0]}). This will be considered as a {expense_remark} change in Family’s Financial position."        
    else:
        expense_income_remark = f"{name}’s Expense to Income ratio is changing from {pre_ratio}%({pre_ratio_indicator[0]}) to {new_ratio}%({new_ratio_indicator[0]}). This will be considered as a {expense_remark} change in Family’s Financial position."        

    #print(f"----[DEBUG] PRE_RATIO: {pre_ratio} POST RATIO: {new_ratio}")
    #if currentctc_indicator == offeredctc_indicator:
    #    expense_income_remark = f"{name}’s Expense to Income ratio is changing from {pre_ratio}% to {new_ratio}%. This will be considered as a {expense_remark} change in Family’s Financial position."        
    #else:
    #    expense_income_remark = f"{name}’s Expense to Income ratio is changing from {pre_ratio}% ({currentctc_indicator[0]}) to {new_ratio}% ({offeredctc_indicator[0]}). This will be considered as a {expense_remark} change in Family’s Financial position."        




#    new_response = NewResponse(
#        HouseholdTakeHome=offeredctc,
#        OtherIncome=total_other_income,
#        TotalTakeHome=new_income,
#        EMI_CreditCard=emi,
#        EstimatedExpense=f"{new_decrease}-{new_increase}",
#        MostLikelyExpense=most_likely_income,
#        E_IRatio=new_ratio
#    )
#
#    pre_response = PreviousResponse(
#        HouseholdTakeHome=currentctc,
#        OtherIncome=total_other_income,
#        TotalTakeHome=pre_income,
#        EMI_CreditCard=emi,
#        EstimatedExpense=f"{new_decrease}-{new_increase}",
#        MostLikelyExpense=most_likely_income,
#        E_IRatio=pre_ratio
#    )

#    change_response = ChangeResponse(
#       HouseholdTakeHome=ctc_change,
#       OtherIncome=total_other_income,
#       TotalTakeHome=income_change,
#       EMI_CreditCard=0,
#       EstimatedExpense="0",
#       MostLikelyExpense=0,
#       E_IRatio=ratio_change
#    )

#    ctc = CtcResponse(
#       offeredctc=str(offeredctc),
#       currentctc=str(currentctc),
#       difference=difference,
#       change_in_ctc=change_in_ctc,
#       change_percent=change_percent
#    )
#
#    indicators = PayAnalysis(
#        previous_pay=currentctc_indicator,
#        current_offer=offeredctc_indicator,
#        Risk = risk_,
#        remarks=pay_analysis_final_remark
#    )
#
#    E_i = ExpenseIncomeAnalysis(
#        prev = pre_response,
#        new_ = new_response,
#        change_ = change_response,
#       Risk = risk,
#        remarks=expense_income_remark
#    )
    idealctcband = IdealCtcBand(
        lower=1200000,
        upper=2800000
    )

    new_response = NewResponse(
        HouseholdTakeHome=offeredctc,
        OtherIncome=total_other_income,
        TotalTakeHome=new_income,
        EMI_CreditCard=emi,
        EstimatedExpense=f"{new_decrease}-{new_increase}",
        MostLikelyExpense=most_likely_expense,
        E_IRatio=new_ratio
    )

    pre_response = PreviousResponse(
        HouseholdTakeHome=currentctc,
        OtherIncome=total_other_income,
        TotalTakeHome=pre_income,
        EMI_CreditCard=emi,
        EstimatedExpense=f"{new_decrease}-{new_increase}",
        MostLikelyExpense=most_likely_expense,
        E_IRatio=pre_ratio
    )

    change_response = ChangeResponse(
        HouseholdTakeHome=ctc_change,
        OtherIncome=total_other_income,
        TotalTakeHome=income_change,
        EMI_CreditCard=0,
        EstimatedExpense="0",
        MostLikelyExpense=0,
        E_IRatio=ratio_change
    )

    ctc = CtcResponse(
        ctc_benchmark_analysis= output,
        offeredctc=str(offeredctc),
        ideal_ctc_band= idealctcband,
        past_ctc=str(currentctc),
        change_in_ctc=change_in_ctc,
        ctc_growth= ctc_growth,
        highlight=highlight
    )

    indicators = PayAnalysis(
        previous_pay=currentctc_indicator,
        current_offer=offeredctc_indicator,
        highlight_1= risk_,
        highlight_2=pay_analysis_final_remark
    )

    E_i = ExpenseIncomeAnalysis(
        expense_income_ratio= new_ratio_indicator,
        total_household_income= int(new_income),
        most_likely_expense= most_likely_expense,
        highlights= expense_income_remark,
        prev = pre_response,
        new_ = new_response,
        change_ = change_response
    )


    query = text("""
        SELECT company_name,
            passbook_year,
            passbook_month
        FROM
            get_passbook_details
        GROUP BY
            company_name, passbook_year, passbook_month
    """
    )
    
    result = await db_2.execute(query, {"person_id": id})
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
            
    result = []
    overlapping_durations=[]
    gaps=[]
    durations = []
    
    for company_name, dates in company_data.items():
        if dates!= ["N/A"]:
            start_date = min(dates)
            end_date = max(dates)
            duration = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            result.append(
                {
                    "company_name": company_name, 
                    "start_date": start_date.strftime("%m-%Y"), 
                    "end_date": end_date.strftime("%m-%Y"), 
                    "duration":duration
                    }
                )
            
            durations.append(duration)
        else:
            result.append({"company_name": company_name, "start_date": "N/A","end_date": "N/A","duration":"N/A"})

    total_duration = float(sum(durations)/12)
    total_duration = round(total_duration, 0)
    total_jobs = len(result)
    median_duration = statistics.median(durations)
    average_duration = statistics.mean(durations)
    if average_duration < 15:
        risk_duration = "Very High"
    elif 15 <= average_duration < 35:
        risk_duration = "High"
    elif 35 <= average_duration <60:
        risk_duration = "Optimal"    
    else:
        risk_duration = "Low"
        
        
    if average_duration <24:
        remark = "short"
    elif 24<= average_duration<=60:
        remark = "average"
    else:
        remark = "Long"                    
    tenure_remarks = f"{name}’s tenure with companies seem to be {remark}. This could be linked to his personal performance or market opportunity."
    #print(result)
    #overlapping
    
    for i, entry1 in enumerate(result):
        if entry1["end_date"]!="N/A":
            end_date1 = await convert_to_datetime(entry1["end_date"].split("-")[1], entry1["end_date"].split("-")[0])

            for entry2 in result[i+1:]:
                if entry2["start_date"]!="N/A":
                    start_date2 = await convert_to_datetime(entry2["start_date"].split("-")[1], entry2["start_date"].split("-")[0])

                    if end_date1 > start_date2:
                        overlapping_durations.append({
                        "company_name": entry2["company_name"],
                        "start_date": entry2["start_date"],
                        "end_date": entry1["end_date"]
                        })
                        #gaps
                    if end_date1 < start_date2:
                        gap_start_date = (end_date1 + datetime.timedelta(days=1)).strftime("%m-%Y")
                        gap_end_date = (start_date2 - datetime.timedelta(days=1)).strftime("%m-%Y")
                        gaps.append({"start_date": gap_start_date, "end_date": gap_end_date})

    tenure = TenureAnalysis(
        work_exp = result,
        overlapping_durations = overlapping_durations,
        gaps = gaps,
        avg_tenure= average_duration,
        median_tenure= median_duration,
        Risk= risk_duration,
        remarks= tenure_remarks,
        total_exp=total_duration,
        num_of_jobs= total_jobs
    )        
      


    return Response(
        ctc_offered=ctc,
        pay_analysis=indicators,
        Expense_income_analysis=E_i,
        Tenure_analysis=tenure    
    )