from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, FastAPI
from sqlalchemy.sql import text
from async_sessions.sessions import get_db, get_db_backend
from typing import List, Optional, Tuple, DefaultDict
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import statistics
from endpoints.summary_endpoints import summary_router
from endpoints.identification_endpoints import identification_router
from endpoints.contact_endpoints import contact_router

class TwentySixAsDetails(BaseModel):
    person_id: str
    A1_section_1: str
    A7_paid_credited_amount: str


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(summary_router)
app.include_router(identification_router)
app.include_router(contact_router)


## 1. about Pinaki
class PersonalInfo(BaseModel):
    id: int
    Name: str
    gender: str
    marital_status: str
    age: int
    email: str
    phone: str
    city: Optional[str]

class HouseholdIncome(BaseModel):
    candidate_monthly_take: float
    spouse_monthly_take: float
    total_family_income: float

class Info(BaseModel):
    firstName: str
    middleName: Optional[str]
    lastName: str
    phone: str
    email: str
    city: Optional[str]
    gender: str
    dob: str
    age: int
    marital_status: str
    spouse_work_status: Optional[str]
    spouse_employer: Optional[str]
    kidsnum: int
    adultdependents: int
    home: bool
    car: bool
    twoWheeler: bool
    creditCard: bool
    Loan: bool
    Investment: bool
    education: str
    education_institute: Optional[str]
    location: Optional[str]
    total_experience: float
    work_industry: str
    skillset: str
    current_role: str
    tenure_last_job: int
    household_income: HouseholdIncome
    
def convert_to_datetime(year, month):
    if year or month:
        return datetime(int(year), int(month), 1)
    return None    

def convert_to_datetime_gap(date_str):
    return datetime.strptime(date_str, "%m-%Y")

@app.get("/about_user/{id}", response_model=Info, tags=['About'])
async def about_user(id: int, db_1: AsyncSession = Depends(get_db_backend), db_2: AsyncSession = Depends(get_db)):
    # Fetch data from the first database
    result_1 = await db_1.execute(
        text('SELECT "firstName", "middleName", "lastName", phone, email, dob, age, gender, marital_status, '
        'education, experience, city, salary, home, "homeLoan", car, "carLoan", "twoWheeler", "twoWheelerLoan", '
        '"creditCard", "personlLoan", stocks, "realEstate","spouseExperience", totalkids, '
        'totaladults FROM "form" WHERE appid = :id'),# changed id to appid
        {"id": id}
    )

    personal_info_1 = result_1.fetchone()

    if personal_info_1 is None:
        raise HTTPException(status_code=404, detail=f"Personal information not found for id {id}")

    # Fetch data from the second database
    #salary_result = await db_2.execute(
    #    text('SELECT "A2(section_1)", "A7(paid_credited_amt)" FROM "26as_details" WHERE person_id = :person_id AND "A2(section_1)" LIKE "192%"'),
    #    {"person_id": id}
    #)
    #salary_data = salary_result.fetchall()

    #if not salary_data:
    #    raise HTTPException(status_code=404, detail=f"No records found for person_id {id}")

    #sum_of_values = sum(float(row[1]) for row in salary_data if row[1] is not None and row[1] != "")
    #city = personal_info_1[24] if personal_info_1[24] is not None and personal_info_1[24] != "null" else "N/A"
    salary_response = HouseholdIncome(
        candidate_monthly_take=personal_info_1[12],
        spouse_monthly_take=0,
        total_family_income=personal_info_1[12]
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
    
    company_data = DefaultDict(list)
    for exp in passbook_raw_data:
        company_name = exp[0]
        year = exp[1]
        month = exp[2]

        date = convert_to_datetime(year,month) 
        if date:
            company_data[company_name].append(date)
        else:
            company_data[company_name].append("N/A")
            
    result = []
    durations = []
    
    for company_name, dates in company_data.items():
        if dates!= ["N/A"]:
            start_date = min(dates)
            end_date = max(dates)
            duration = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            result.append({"company_name": company_name, "start_date": start_date.strftime("%m-%Y"), "end_date": end_date.strftime("%m-%Y"), "duration":duration})
            
            durations.append(duration)
    total_duration = float(sum(durations)/12)
    total_duration = round(total_duration, 2)

    ##extracting role from tenure

    result_role = await db_1.execute(
        text('SELECT "role" '
        'FROM "tenure" WHERE formid = :id'),# changed id to appid
        {"id": id}
    )
    role = result_role.fetchone()


    # Combine data from both databases into the Info response
    return Info(
        firstName=personal_info_1[0],
        middleName=personal_info_1[1],
        lastName=personal_info_1[2],
        phone=personal_info_1[3],
        email=personal_info_1[4],
        city = personal_info_1[11] if personal_info_1[11] is not None else "N/A",
        gender=personal_info_1[7],
        dob=personal_info_1[5],
        age=personal_info_1[6],
        marital_status=personal_info_1[8],
        spouse_work_status= "N/A",
        spouse_employer="N/A",
        kidsnum=personal_info_1[24] if personal_info_1[24] is not None else 0,
        adultdependents=personal_info_1[25],
        home=personal_info_1[13],
        car=personal_info_1[15],
        twoWheeler=personal_info_1[17],
        creditCard=personal_info_1[19],
        Loan=any([personal_info_1[14], personal_info_1[16], personal_info_1[18], personal_info_1[20]]),
        Investment=any([personal_info_1[21], personal_info_1[22]]),
        education=personal_info_1[9],
        education_institute="N/A",
        location=personal_info_1[11],
        total_experience=total_duration,
        work_industry= "N/A",
        skillset="N/A",
        current_role=role[0],
        tenure_last_job=personal_info_1[10],
        household_income= salary_response
        )
 

## 2. benchmarking
class CtcResponse(BaseModel):
    offeredctc: str
    currentctc: str
    difference: Optional[float]
    change_in_ctc: float
    change_percent: float

class NewResponse(BaseModel):
    HouseholdTakeHome: float
    OtherIncome: float
    TotalTakeHome: float
    EMI_CreditCard: float
    EstimatedExpense: str
    MostLikelyExpense: int
    E_IRatio: float

class PreviousResponse(BaseModel):
    HouseholdTakeHome: float
    OtherIncome: float
    TotalTakeHome: float
    EMI_CreditCard: float
    EstimatedExpense: str
    MostLikelyExpense: int
    E_IRatio: float

class ChangeResponse(BaseModel):
    HouseholdTakeHome: float
    OtherIncome: float
    TotalTakeHome: float
    EMI_CreditCard: float
    EstimatedExpense: str
    MostLikelyExpense: int
    E_IRatio: float

class ExpenseIncomeAnalysis(BaseModel):
    prev: PreviousResponse
    new_: NewResponse
    change_: ChangeResponse
    Risk: str
    remarks: str

class PayAnalysis(BaseModel):
    previous_pay: tuple
    current_offer: tuple
    Risk: str
    remarks: str


class TenureAnalysis(BaseModel):
    work_exp : list
    overlapping_durations: list
    gaps: list
    avg_tenure: float
    median_tenure: float
    Risk: str
    remarks: str


class Response(BaseModel):
    ctc_offered: CtcResponse
    pay_analysis: PayAnalysis
    Expense_income_analysis: ExpenseIncomeAnalysis
    Tenure_analysis: TenureAnalysis

def get_indicator(value: float) -> str:
    """Determine the indicator for the given value."""
    x =((value-1200000)/(2800000-1200000))*100
    
    if x < 20:
        if x<=0:
            return ("Very Low",0)
        else:
            return("Very Low",{x})
    elif 20 <= x < 40:
        return ("Low",{x})
    elif 40 <= x < 60:
        return ("Medium",{x})
    elif 60 <= x < 80:
        return ("High",{x})
    elif 80 <= x:
        if x <= 100:
            return("Very High",{x})
        else:
            return("Very High",100)
    else:
        return ""
    


    
def convert_to_datetime(year, month):
    if year or month:
        return datetime(int(year), int(month), 1)
    return None    

def convert_to_datetime_gap(date_str):
    return datetime.strptime(date_str, "%m-%Y")



@app.get("/benchmark/{id}", response_model=Response, tags=['Benchmarking'])
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
        raise HTTPException(status_code=404, detail=f"Personal information not found for id {id}")

    currentctc = float(ctc_info[0])
    offeredctc = float(ctc_info[2])

    difference = offeredctc - currentctc
    change_in_ctc = difference
    change_percent = round((float(difference / currentctc) * 100),0) if currentctc != 0 else 0

    currentctc_indicator = get_indicator(currentctc)
    offeredctc_indicator = get_indicator(offeredctc)
    risk_ = f"{offeredctc_indicator[0]} Cost to the Compamy"

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

    change_in_pay = (offeredctc - currentctc)/currentctc
    if change_in_pay > 0.5:
        pay_analysis_remark = "Major"
    else:
        pay_analysis_remark = "Minor" 
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
            raise HTTPException(status_code=404, detail=f"No records found for person_id {id}")

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
    most_likely_income = round(float((pre_exp+new_exp)/2),0)

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
    if ratio_change < 15:
        expense_remark = "Minor"
    else:
        expense_remark = "Major"

    if currentctc_indicator == offeredctc_indicator:
        expense_income_remark = f"{name}’s Expense to Income ratio is changing from {pre_ratio}% to {new_ratio}%. This will be considered as a {expense_remark} change in Family’s Financial position."        
    else:
        expense_income_remark = f"{name}’s Expense to Income ratio is changing from {pre_ratio}% {currentctc_indicator} to {new_ratio}% {offeredctc_indicator}. This will be considered as a {expense_remark} change in Family’s Financial position."        




    new_response = NewResponse(
        HouseholdTakeHome=offeredctc,
        OtherIncome=total_other_income,
        TotalTakeHome=new_income,
        EMI_CreditCard=emi,
        EstimatedExpense=f"{new_decrease}-{new_increase}",
        MostLikelyExpense=most_likely_income,
        E_IRatio=new_ratio
    )

    pre_response = PreviousResponse(
        HouseholdTakeHome=currentctc,
        OtherIncome=total_other_income,
        TotalTakeHome=pre_income,
        EMI_CreditCard=emi,
        EstimatedExpense=f"{new_decrease}-{new_increase}",
        MostLikelyExpense=most_likely_income,
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
        offeredctc=str(offeredctc),
        currentctc=str(currentctc),
        difference=difference,
        change_in_ctc=change_in_ctc,
        change_percent=change_percent
    )

    indicators = PayAnalysis(
        previous_pay=currentctc_indicator,
        current_offer=offeredctc_indicator,
        Risk = risk_,
        remarks=pay_analysis_final_remark
    )

    E_i = ExpenseIncomeAnalysis(
        prev = pre_response,
        new_ = new_response,
        change_ = change_response,
        Risk = risk,
        remarks=expense_income_remark
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

        date = convert_to_datetime(year,month) 
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
            result.append({"company_name": company_name, "start_date": start_date.strftime("%m-%Y"), "end_date": end_date.strftime("%m-%Y"), "duration":duration})
            
            durations.append(duration)
        else:
            result.append({"company_name": company_name, "start_date": "N/A","end_date": "N/A","duration":"N/A"})

    median_duration = statistics.median(durations)
    average_duration = statistics.mean(durations)
    if median_duration < 24:
        risk_duration = "High chance of Attrition"
    elif 24 <= median_duration <= 60:
        risk_duration = "Average chance of Attrition"
    else:
        risk_duration = "Low chance of Attrition"
    if median_duration <24:
        remark = "short"
    elif 24<= median_duration<=60:
        remark = "average"
    else:
        remark = "Long"                    
    tenure_remarks = f"{name}’s tenure with companies seem to be {remark}. This could be linked to his personal performance or market opportunity."
    #print(result)
    #overlapping
    
    for i, entry1 in enumerate(result):
        if entry1["end_date"]!="N/A":
            end_date1 = convert_to_datetime(entry1["end_date"].split("-")[1], entry1["end_date"].split("-")[0])

            for entry2 in result[i+1:]:
                if entry2["start_date"]!="N/A":
                    start_date2 = convert_to_datetime(entry2["start_date"].split("-")[1], entry2["start_date"].split("-")[0])

                    if end_date1 > start_date2:
                        overlapping_durations.append({
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
        remarks= tenure_remarks
    )        


    return Response(
        ctc_offered=ctc,
        pay_analysis=indicators,
        Expense_income_analysis=E_i,
        Tenure_analysis=tenure    
    )    
    


@app.get("/total_other_income/{person_id}")
async def get_a7_for_person_id(person_id: str, db: AsyncSession = Depends(get_db)):
    async with db as session:
        a7_result = await session.execute(
            text('SELECT person_id,"A2(section_1)", "A7(paid_credited_amt)" FROM "26as_details" WHERE person_id = :person_id AND "A2(section_1)" NOT LIKE "192%"'),
            {"person_id": person_id}
        )
        a7_data = a7_result.fetchall()

        if not a7_data:
            raise HTTPException(status_code=404, detail=f"No records found for person_id {person_id}")

        a7_response = [
            TwentySixAsDetails(person_id=row[0],A1_section_1=row[1], A7_paid_credited_amount=row[2])
            for row in a7_data
            if row[2] is not None and row[2] != ""
        ]


        sum_of_values = sum(float(row[2]) for row in a7_data if row[1] is not None and row[2] != "")

        return sum_of_values


class RetailAccountDetails(BaseModel):
    person_id: str
    AccountNumber: str
    AccountType: str
    LastPayment: Optional[str]
    AccountStatus: str

@app.get("/get_retail_account/{person_id}", response_model=List[RetailAccountDetails])
async def get_retail_account_details_for_person_id(person_id: str, db: AsyncSession = Depends(get_db)):
    async with db as session:
        retail_account_result = await session.execute(
            text('SELECT DISTINCT person_id,AccountNumber, AccountType,LastPayment, AccountStatus FROM "RetailAccountDetails" WHERE person_id = :person_id AND AccountStatus ="Current Account"'),
            {"person_id": person_id}
        )
        retail_account_data = retail_account_result.fetchall()
        #print("Retail Account Data:", retail_account_data)
        
        
        
        if not retail_account_data:
            raise HTTPException(status_code=404, detail=f"No records found for person_id {person_id}")

        retail_account_response = [RetailAccountDetails(
            person_id=row[0],
            AccountNumber= row[1],
            AccountType = row[2],
            LastPayment = row[3],
            AccountStatus = row[4]
            ) 
            for row in retail_account_data
            if row[3] is not None and row[3] != ""
        ]
        sum_of_values = sum(float(row[3]) for row in retail_account_data if row[3] is not None and row[3] != "")
        
        return retail_account_response

class A2_section_1(BaseModel):
    person_id: str
    A2: Optional[str]


class A2Section1Count(BaseModel):
    person_id: str
    Salary: int
    other_income: int


@app.get("/get_salary_and_other_income/{person_id}",response_model=A2Section1Count)
async def get_a2_for_person_id(person_id: str, db: AsyncSession = Depends(get_db)):
    async with db as session:
        a2_result = await session.execute(
            text('SELECT DISTINCT person_id,"A2(section_1)" FROM "26as_details" WHERE person_id = :person_id'),
            {"person_id": person_id}
        )
        a2_data = a2_result.fetchall()

        if not a2_data:
            raise HTTPException(status_code=404, detail=f"No records found for person_id {person_id}")

        a2_response = [
            A2_section_1(person_id=row[0],A2=row[1])
            for row in a2_data
            if row[1] is not None and row[1] != ""
        ]
        a2_192_count = sum(1 for a2_entry in a2_response if a2_entry.A2 and a2_entry.A2.startswith("192"))
        other_a2_count = len(a2_response) - a2_192_count

        count_response = A2Section1Count(
            person_id=person_id,
            Salary=a2_192_count,
            other_income=other_a2_count
        )

        return count_response
        
# Define the response model
class Enquiries(BaseModel):
    queries_last_1_month: int
    queries_last_3_months: int
    queries_last_6_months: int
    queries_last_12_months: int
    queries_last_24_months: int

class ResponseModel(BaseModel):
    active_accounts: List[str]
    enquiries: Enquiries
    active_account_count: int
        
@app.get("/get_active_account_and_credit_queries/{person_id}", response_model=ResponseModel)
async def get_active_account_credit_queries(person_id: str, db: AsyncSession = Depends(get_db)):
    # Query for active accounts
    result_accounts = await db.execute(
        text('SELECT DISTINCT AccountNumber '
              'FROM RetailAccountDetails '
              'WHERE person_id = :person_id '
              'AND AccountStatus = :account_status '
              'AND OwnershipType = :ownership_type '
              'AND CAST(Balance AS DECIMAL) > :balance'),
        {
            "person_id": person_id,
            "account_status": "Current Account",
            "ownership_type": "Individual",
            "balance": 99
        }
    )
    
    # Query for credit enquiries
    result_queries = await db.execute(
        text(
            'SELECT '
            'SUM(CASE WHEN date(Date) >= date("now", "-1 month") THEN 1 ELSE 0 END) as queries_last_1_month, '
            'SUM(CASE WHEN date(Date) >= date("now", "-3 months") THEN 1 ELSE 0 END) as queries_last_3_months, '
            'SUM(CASE WHEN date(Date) >= date("now", "-6 months") THEN 1 ELSE 0 END) as queries_last_6_months, '
            'SUM(CASE WHEN date(Date) >= date("now", "-12 months") THEN 1 ELSE 0 END) as queries_last_12_months, '
            'SUM(CASE WHEN date(Date) >= date("now", "-24 months") THEN 1 ELSE 0 END) as queries_last_24_months '
            'FROM Enquiries '
            'WHERE person_id = :person_id'
        ),
        {"person_id": person_id}
    )
    
    # Fetch the results
    active_accounts_data = result_accounts.fetchall()
    enquiries_data = result_queries.fetchone()

    # Extract the account numbers
    active_accounts = [row[0] for row in active_accounts_data]

    # Build the response
    response = ResponseModel(
        active_accounts=active_accounts,
        enquiries=Enquiries(
            queries_last_1_month=enquiries_data[0],
            queries_last_3_months=enquiries_data[1],
            queries_last_6_months=enquiries_data[2],
            queries_last_12_months=enquiries_data[3],
            queries_last_24_months=enquiries_data[4]
        ),
        active_account_count = len(active_accounts) if active_accounts else 0
    )

    return response

class CreditResponse(BaseModel):
    person_id: str
    CreditLimit: Optional[str]
    Balance: Optional[str]
    PastDueAmount:Optional[str]
    Open: str
@app.get("/get_credit_standing_tradeline_summary/{person_id}",response_model=List[CreditResponse])
async def credit_standing(person_id: str, db: AsyncSession = Depends(get_db)):
    async with db as session:
        result = await session.execute(
            text('SELECT person_id,CreditLimit, Balance, PastDueAmount, Open FROM "RetailAccountDetails" WHERE person_id = :person_id AND AccountStatus ="Current Account"'),
            {"person_id": person_id}
        )
        data = result.fetchall()
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No records found for person_id {person_id}")

        response = [CreditResponse(
            person_id=row[0],
            CreditLimit= row[1],
            Balance = row[2],
            PastDueAmount = row[3],
            Open = row[4]
            ) 
            for row in data
        ]
        return response


class AccountSummaryResponse(BaseModel):
    number_of_closed_accounts: int
    total_balance: float
    total_credit_limit: float
    total_past_due: float
    
@app.get("/account_summary/{person_id}", response_model=AccountSummaryResponse)
async def get_account_summary(person_id: str, db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT 
            COUNT(*) FILTER (WHERE AccountStatus = 'Closed Account') as number_of_closed_accounts,
            SUM(Balance) as total_balance,
            SUM(CreditLimit) as total_credit_limit,
            SUM(PastDueAmount) as total_past_due
        FROM (
            SELECT AccountNumber, AccountStatus,
                   CAST(Balance AS DECIMAL) as Balance,
                   CAST(CreditLimit AS DECIMAL) as CreditLimit,
                   CAST(PastDueAmount AS DECIMAL) as PastDueAmount,
                   ROW_NUMBER() OVER(PARTITION BY AccountNumber ORDER BY DateReported DESC) as rn
            FROM RetailAccountDetails
            WHERE person_id = :person_id
        ) as subquery
        WHERE rn = 1
    """)

    result = await db.execute(query, {"person_id": person_id})
    summary = result.fetchone()
    print(f"-----[debug] SUMMARY: {summary}")
    return AccountSummaryResponse(
        number_of_closed_accounts=summary[0],
        total_balance=float(summary[1]) if summary[1] is not None else 0.0,
        total_credit_limit=float(summary[2]) if summary[2] is not None else 0.0,
        total_past_due=float(summary[3]) if summary[3] is not None else 0.0,
    )    


DateEmailTuple = Tuple[str, str]  # (date, email)
DatePhoneTuple = Tuple[str, str]  # (date, phone)
DateAddressTuple = Tuple[str, str]  # (date, address)

# Existing Models
class Enquiries(BaseModel):
    queries_last_1_month: int
    queries_last_3_months: int
    queries_last_6_months: int
    queries_last_12_months: int
    queries_last_24_months: int
    
class CombinedResponseModel(BaseModel):
    active_accounts: List[str]
    enquiries: Enquiries
    active_account_count: int
    number_of_closed_accounts: int
    total_balance: float
    total_credit_limit: float
    total_past_due: float
    credit_score: int
    phone_numbers: List[DatePhoneTuple]
    addresses: List[DateAddressTuple]
    email_addresses: List[DateEmailTuple]
    score_factors: List[str]
    
def compute_score_factors(enquiries_data, summary_data, active_account_count, credit_score):
    score_factors = []

    # Assuming the order of summary_data is as follows:
    # 0: number_of_closed_accounts, 1: total_balance, 2: total_credit_limit, 3: total_past_due
    total_credit_limit = float(summary_data[2]) if summary_data[2] is not None else 0.0

    # Rule 1: Insufficient payment activity over the last year
    if active_account_count < 3:  
        score_factors.append("Insufficient payment activity over the last year")

    # Rule 2: Not enough available credit
    if total_credit_limit < 10000000:  
        score_factors.append("Not enough available credit")

    # Assuming the order of enquiries_data is as follows:
    # 0: queries_last_1_month, 1: queries_last_3_months, 2: queries_last_6_months, 3: queries_last_12_months, 4: queries_last_24_months
    queries_last_12_months = enquiries_data[3] if enquiries_data[3] else 0

    # Rule 3: Too many inquiries
    if queries_last_12_months > 2: 
        score_factors.append("Too many inquiries")

    # Rule 4: Not enough balance decreases on active non-mortgage accounts
    print(f"CREDIT: {credit_score}")
    if credit_score < 600:  
        score_factors.append("Not enough balance decreases on active non-mortgage accounts")

    return score_factors

    
@app.get("/credit_standing/{person_id}", response_model=CombinedResponseModel)
async def get_combined_account_info(person_id: str, db: AsyncSession = Depends(get_db)):
    # Query for active accounts and account summary
    query_accounts = text('''
        SELECT DISTINCT AccountNumber
        FROM RetailAccountDetails
        WHERE person_id = :person_id
        AND AccountStatus = 'Current Account'
        AND OwnershipType = 'Individual'
        AND CAST(Balance AS DECIMAL) > :balance
    ''')

    query_summary = text('''
        SELECT 
            COUNT(*) FILTER (WHERE AccountStatus = 'Closed Account') as number_of_closed_accounts,
            SUM(CAST(Balance AS DECIMAL)) as total_balance,
            SUM(CAST(CreditLimit AS DECIMAL)) as total_credit_limit,
            SUM(CAST(PastDueAmount AS DECIMAL)) as total_past_due
        FROM RetailAccountDetails
        WHERE person_id = :person_id
    ''')

    # Query for credit enquiries
    query_enquiries = text('''
        SELECT 
            SUM(CASE WHEN date(Date) >= date("now", "-1 month") THEN 1 ELSE 0 END) as queries_last_1_month,
            SUM(CASE WHEN date(Date) >= date("now", "-3 months") THEN 1 ELSE 0 END) as queries_last_3_months,
            SUM(CASE WHEN date(Date) >= date("now", "-6 months") THEN 1 ELSE 0 END) as queries_last_6_months,
            SUM(CASE WHEN date(Date) >= date("now", "-12 months") THEN 1 ELSE 0 END) as queries_last_12_months,
            SUM(CASE WHEN date(Date) >= date("now", "-24 months") THEN 1 ELSE 0 END) as queries_last_24_months
        FROM Enquiries
        WHERE person_id = :person_id
    ''')

    query_credit_score = text('''
        SELECT 
            credit_score
        FROM creditdata_master
        WHERE person_id = :person_id
    ''')
    
    query_phone = text('''
        SELECT "ReportedDate", "Number"
        FROM phoneInfo
        WHERE person_id = :person_id
    ''')
    query_email = text('''
        SELECT "ReportedDate", "EmailAddress"
        FROM emailInfo
        WHERE person_id = :person_id
    ''')
    query_address = text('''
        SELECT "ReportedDate", "Address"
        FROM addressInfo
        WHERE person_id = :person_id
    ''')

    # Execute queries
    result_accounts = await db.execute(query_accounts, {"person_id": person_id, "balance": 99})
    result_summary = await db.execute(query_summary, {"person_id": person_id})
    result_enquiries = await db.execute(query_enquiries, {"person_id": person_id})
    result_credit_score = await db.execute(query_credit_score, {"person_id": person_id})

    # Fetch results
    active_accounts_data = result_accounts.fetchall()
    summary_data = result_summary.fetchone()
    enquiries_data = result_enquiries.fetchone()
    credit_score = result_credit_score.fetchone()

    # Extract information
    active_accounts = [row[0] for row in active_accounts_data]
    active_account_count = len(active_accounts)

    result_phone = await db.execute(query_phone, {"person_id": person_id})
    phone_data = [(row[0], row[1]) for row in result_phone.fetchall()]

    # Execute email query
    result_email = await db.execute(query_email, {"person_id": person_id})
    email_data = [(row[0], row[1]) for row in result_email.fetchall()]

    # Execute address query
    result_address = await db.execute(query_address, {"person_id": person_id})
    address_data = [(row[0], row[1]) for row in result_address.fetchall()]
    
    #Score Summary
    active_accounts = [row[0] for row in active_accounts_data]
    active_account_count = len(active_accounts)
    summary_data = summary_data
    enquiries_data = enquiries_data
    credit_score = int(credit_score[0]) if credit_score else 0

    score_factors = compute_score_factors(enquiries_data, summary_data, active_account_count, credit_score)
    
    
    # Build the response
    response = CombinedResponseModel(
        active_accounts=active_accounts,
        enquiries=Enquiries(
            queries_last_1_month=enquiries_data[0],
            queries_last_3_months=enquiries_data[1],
            queries_last_6_months=enquiries_data[2],
            queries_last_12_months=enquiries_data[3],
            queries_last_24_months=enquiries_data[4]
        ),
        active_account_count=active_account_count,
        number_of_closed_accounts=summary_data[0],
        total_balance=float(summary_data[1]) if summary_data[1] is not None else 0.0,
        total_credit_limit=float(summary_data[2]) if summary_data[2] is not None else 0.0,
        total_past_due=float(summary_data[3]) if summary_data[3] is not None else 0.0,
        credit_score=credit_score if credit_score else 0.0,
        phone_numbers=phone_data,
        email_addresses=email_data,
        addresses=address_data,
        score_factors=score_factors if score_factors else []

    )

    return response    






class MonthlyIncome(BaseModel):
    month: str
    salary_amount: float
    other_income_amount: float
    overseas_income_amount: float  # New field
    business_income_amount: float  # New field
    personal_income_amount: float  # New field
    total_income_amount: float

class IncomeSources(BaseModel):
    salary_sources: List[str]
    other_income_sources: List[str]
    overseas_income_sources: List[str]  # New field

class IncomeSummaryResponse(BaseModel):
    number_of_salary_accounts: int
    number_of_other_income_accounts: int
    number_of_personal_savings_account: int
    number_of_business_income_accounts: int
    number_of_overseas_acount: int
    
    total_number_of_income_sources: int
    total_salary_received: float
    total_other_income: float
    total_personal_savings: float
    total_overseas_income: float
    total_business_income: float
    total_income: float
    risk_indicator: int
    monthly_income_details: List[MonthlyIncome]
    income_sources: IncomeSources
    #ADDED
    # overseas_income_sources: int  # New field
    # overseas_income_amount: float  # New field
    income_percentage: dict
    
def convert_date_format(date_str):
    month_mapping = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
        "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }
    parts = date_str.split('-')
    if len(parts) == 3:
        day, month_abbr, year = parts
        month = month_mapping.get(month_abbr, "00")
        return f"{year}-{month}"
    return "Unknown"    
        
@app.get("/financial_position/{person_id}", response_model=IncomeSummaryResponse)
async def get_income_summary(person_id: str, db: AsyncSession = Depends(get_db)):

    query = text("""
        SELECT
            COUNT(DISTINCT case when "A2(section_1)" LIKE '192%' then deductor_tan_no end) as salary_accounts,
            COUNT(DISTINCT case when "A2(section_1)" LIKE '194%' then deductor_tan_no end) as other_income_accounts,
            SUM(case when "A2(section_1)" LIKE '192%' then CAST("A7(paid_credited_amt)" AS FLOAT) end) as total_salary,
            SUM(case when "A2(section_1)" LIKE '194%' then CAST("A7(paid_credited_amt)" AS FLOAT) end) as total_other_income
        FROM "26as_details"
        WHERE person_id = :person_id
        AND strftime('%Y-%m-%d', 
            substr("A3(transaction_dt)", 8, 4) || '-' || 
            case substr("A3(transaction_dt)", 4, 3)
                when 'Jan' then '01'
                when 'Feb' then '02'
                when 'Mar' then '03'
                when 'Apr' then '04'
                when 'May' then '05'
                when 'Jun' then '06'
                when 'Jul' then '07'
                when 'Aug' then '08'
                when 'Sep' then '09'
                when 'Oct' then '10'
                when 'Nov' then '11'
                when 'Dec' then '12'
            end || '-' ||
            substr("A3(transaction_dt)", 1, 2)
        ) >= strftime('%Y-%m-%d', 'now', '-12 months')
    """)

    
    monthly_income_query = text("""
        SELECT 
            strftime('%Y-%m', formatted_date) as month_year,
            SUM(CASE WHEN "A2(section_1)" LIKE '192%' THEN CAST("A7(paid_credited_amt)" AS FLOAT) ELSE 0 END) as salary_amount,
            SUM(CASE WHEN "A2(section_1)" LIKE '194%' THEN CAST("A7(paid_credited_amt)" AS FLOAT) ELSE 0 END) as other_income_amount
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
    
    detA_query = text("""
                      SELECT distinct TA,"3A" FROM "26as_details" WHERE deductor_tan_no like "det%" AND person_id = :person_id
                      """)
    
    detA_result = await db.execute(detA_query, {"person_id": person_id})
    detA_raw_data = detA_result.fetchall()

    detA={}
    for element in detA_raw_data:
        detA[element[0]]=element[1]
    
    print(detA)
    
    overseas_income_query = text("""
    SELECT 
        strftime('%Y-%m', formatted_date) as month_year,
        SUM(CASE 
            WHEN B2 = '206CQ' OR B2 = '206CO' THEN 
                CASE 
                    WHEN CAST(B7 AS FLOAT) / 0.05 <= 700000 THEN CAST(B7 AS FLOAT) / 0.05
                    ELSE CAST(B7 AS FLOAT) / 0.05
                END
            ELSE 0 END) as overseas_income_amount,
        deductor_tan_no
    FROM (
        SELECT 
            CASE
                WHEN substr(B3, 4, 3) = 'Jan' THEN substr(B3, 8, 4) || '-01-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Feb' THEN substr(B3, 8, 4) || '-02-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Mar' THEN substr(B3, 8, 4) || '-03-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Apr' THEN substr(B3, 8, 4) || '-04-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'May' THEN substr(B3, 8, 4) || '-05-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Jun' THEN substr(B3, 8, 4) || '-06-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Jul' THEN substr(B3, 8, 4) || '-07-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Aug' THEN substr(B3, 8, 4) || '-08-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Sep' THEN substr(B3, 8, 4) || '-09-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Oct' THEN substr(B3, 8, 4) || '-10-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Nov' THEN substr(B3, 8, 4) || '-11-' || substr(B3, 1, 2)
                WHEN substr(B3, 4, 3) = 'Dec' THEN substr(B3, 8, 4) || '-12-' || substr(B3, 1, 2)
            END as formatted_date,
            B2,
            B7,
            deductor_tan_no
        FROM "26as_details"
        WHERE person_id = :person_id AND B2 = '206CQ'
    ) 
    GROUP BY strftime('%Y-%m', formatted_date)
    """)


    
    overseas_income_result = await db.execute(overseas_income_query, {"person_id": person_id, "source": "206CQ"})
    overseas_income_raw_data = overseas_income_result.fetchall()

    print(f"-----[DEBUG] Overseas income source: {list(overseas_income_raw_data)}")
    
    # Process overseas income data
    overseas_income_sources = []
    monthly_overseas_income = {}
    for row in overseas_income_raw_data:
        month_year, amount, source = row
        if detA.get(source[4:]) is not None:
            overseas_income_sources.append(detA.get(source[4:])+" {"+source[4:]+"}")
        else:
            overseas_income_sources.append("NONAME COMPANY {"+source[4:]+"}")
        monthly_overseas_income.setdefault(month_year, 0)
        monthly_overseas_income[month_year] += amount    
    
    overseas_income_sources=list(set(overseas_income_sources))
    
    # Query for distinct income sources
    income_sources_query = text("""
        SELECT DISTINCT 
            CASE WHEN "A2(section_1)" LIKE '192%' THEN deductor_tan_no END as salary_source,
            CASE WHEN "A2(section_1)" LIKE '194%' THEN deductor_tan_no END as other_income_source
        FROM "26as_details"
        WHERE person_id = :person_id
    """)

    

    # Execute queries
    monthly_income_result = await db.execute(monthly_income_query, {"person_id": person_id})
    income_sources_result = await db.execute(income_sources_query, {"person_id": person_id})

    # Fetch and process monthly income results
    monthly_income_raw_data = monthly_income_result.fetchall()
    print(f"DEBUG---- {monthly_income_raw_data}")

    print(row[1])
    monthly_income_details = [
    MonthlyIncome(
        month=row[0],
        salary_amount=row[1],
        other_income_amount=0.0,
        overseas_income_amount=0.0,
        business_income_amount=row[2],
        personal_income_amount=0.0,
        total_income_amount=0.0
        
        
    )
    for row in monthly_income_raw_data if row[0]
    ]
    print(monthly_income_details)
    #Added for overseas
    total_overseas_income = 0.0
    for income_detail in monthly_income_details:
        income_detail.overseas_income_amount = monthly_overseas_income.get(income_detail.month, 0.0)
        total_overseas_income += monthly_overseas_income.get(income_detail.month, 0.0)
        income_detail.total_income_amount = income_detail.salary_amount + income_detail.other_income_amount + income_detail.overseas_income_amount + income_detail.business_income_amount + income_detail.personal_income_amount

    salary_sources = []
    other_income_sources = []
    for row in income_sources_result.fetchall():
        if row[0] is not None:
            salary_sources.append(detA.get(row[0][4:])+" {"+row[0][4:]+"}")
        if row[1] is not None:
            other_income_sources.append(detA.get(row[1][4:])+" {"+row[1][4:]+"}")

    income_sources = IncomeSources(
        salary_sources=salary_sources, 
        other_income_sources=other_income_sources,
        overseas_income_sources=overseas_income_sources
        )
    # income_sources.overseas_income_sources = overseas_income_sources




    result = await db.execute(query, {"person_id": person_id})
    summary = result.fetchone()
    print(f"SUMMMARY: {summary}")
    salary_accounts = summary[0]
    other_income_accounts = summary[1]
    total_salary = summary[2] if summary[2] is not None else 0.0
    total_other_income = summary[3] if summary[3] is not None else 0.0
    
    risk_indicator = 1
    if other_income_accounts > 2 * salary_accounts:
        if total_other_income < 3 * total_salary:
            risk_indicator = 5
        elif total_other_income < 2 * total_salary:
            risk_indicator = 4
        elif total_other_income <  total_salary:
            risk_indicator = 3
    elif other_income_accounts >  salary_accounts:
        if total_other_income < 3 * total_salary:
            risk_indicator = 4
        elif total_other_income < 2 * total_salary:
            risk_indicator = 3
        elif total_other_income <  total_salary:
            risk_indicator = 2
    elif other_income_accounts <  salary_accounts:
        if total_other_income < 3 * total_salary:
            risk_indicator = 3
        elif total_other_income < 2 * total_salary:
            risk_indicator = 2
        elif total_other_income <  total_salary:
            risk_indicator = 1            

    total_income = total_salary + total_other_income + total_overseas_income

    # Calculate the percentage share of each income type
    salary_percentage = (total_salary / total_income * 100) if total_income > 0 else 0
    other_income_percentage = (total_other_income / total_income * 100) if total_income > 0 else 0
    overseas_income_percentage = (total_overseas_income / total_income * 100) if total_income > 0 else 0

    income_percentage = {
        "salary_percentage": salary_percentage,
        "other_income_percentage": 0.0,
        "overseas_income_percentage": overseas_income_percentage,
        "business_income_percentage": other_income_percentage,
        "personal_income_percentage": 0.0
    }

            
    return IncomeSummaryResponse(
        number_of_salary_accounts=salary_accounts,
        number_of_other_income_accounts=0,
        number_of_business_income_accounts=other_income_accounts,
        number_of_personal_savings_account=0,
        number_of_overseas_acount = len(overseas_income_sources),
        total_number_of_income_sources=salary_accounts + other_income_accounts,
        total_salary_received=total_salary,
        total_other_income=0.0,
        total_business_income=total_other_income,
        total_personal_savings=0.0,
        total_overseas_income=total_overseas_income,
        total_income=total_salary + total_other_income + total_overseas_income,
        risk_indicator=risk_indicator,
        monthly_income_details=monthly_income_details,
        income_sources=income_sources,
        # overseas_income_sources=len(overseas_income_sources),
        # overseas_income_amount=sum(monthly_overseas_income.values()),
        income_percentage=income_percentage
    )

class CareerDetailsResponse(BaseModel):
    all_experiences_govt_docs : list
    all_experiences_tenure: list
    good_to_know: int
    red_flag: int
    discrepancies: int
    lack_of_trust: int
    
def convert_to_datetime(year, month):
    if year or month:
        return datetime(int(year), int(month), 1)
    return None    

def convert_to_datetime_gap(date_str):
    return datetime.strptime(date_str, "%m-%Y")

def overlap(start1, end1, start2, end2):
    return convert_to_datetime_gap(start1) <= convert_to_datetime_gap(end2) and convert_to_datetime_gap(start2) <= convert_to_datetime_gap(end1)

@app.get("/career_details/{person_id}", response_model=CareerDetailsResponse)
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

        date = convert_to_datetime(year,month) 
        if date:
            company_data[company_name].append(date)
        else:
            company_data[company_name].append("N/A")
            
    work_exp = []
    overlapping_durations=[]
    gaps=[]
    
    for company_name, dates in company_data.items():
        if dates!= ["N/A"]:
            start_date = min(dates).strftime("%m-%Y")
            end_date = max(dates).strftime("%m-%Y")
            work_exp.append({"company_name": company_name, "start_date": start_date, "end_date": end_date,"type":"work_exp"})
        else:
            work_exp.append({"company_name": company_name, "start_date": "N/A","end_date": "N/A","type":"work_exp"})

    for i, entry1 in enumerate(work_exp):
        if entry1["end_date"]!="N/A":
            end_date1 = convert_to_datetime(entry1["end_date"].split("-")[1], entry1["end_date"].split("-")[0])

            for entry2 in work_exp[i+1:]:
                if entry2["start_date"]!="N/A":
                    start_date2 = convert_to_datetime(entry2["start_date"].split("-")[1], entry2["start_date"].split("-")[0])
                    
                    #overlapping
                    
                    if end_date1 > start_date2:
                        overlapping_durations.append({
                        "start_date": entry2["start_date"],
                        "end_date": entry1["end_date"],
                        "type":"overlap"
                        })

                    #gaps
                    
                    if end_date1 < start_date2:
                        gap_start_date = (end_date1 + timedelta(days=1)).strftime("%m-%Y")
                        gap_end_date = (start_date2 - timedelta(days=1)).strftime("%m-%Y")
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
        from_date = from_date.strftime("%m-%Y")
        to_date = to_date.strftime("%m-%Y")
        
        company_data.append({"company_name":company,"start_date":from_date,"end_date":to_date,"type":"work_exp"})
        
    overlapping_durations_tenure=[]
    gaps_tenure = []
    
    for i, entry1 in enumerate(company_data):
        end_date1 = entry1["end_date"]
        for entry2 in company_data[i+1:]:
            start_date2 = entry2["start_date"]
            if end_date1 > start_date2:
                overlapping_durations_tenure.append({
                        "start_date": entry2["start_date"],
                        "end_date": entry1["end_date"],
                        "type":"overlap"
                        })
                
            if end_date1 < start_date2:
                gap_start_date = (end_date1 + timedelta(days=1)).strftime("%m-%Y")
                gap_end_date = (start_date2 - timedelta(days=1)).strftime("%m-%Y")
                gaps_tenure.append({"start_date": gap_start_date, "end_date": gap_end_date,"type":"gaps"})

    #discrepancies
    
    overlapping_gaps = []
    
    for gap in gaps:
        gap_start = gap["start_date"]
        gap_end = gap["end_date"]

        for exp in company_data:
            exp_start = exp["start_date"]
            exp_end = exp["end_date"]

            if overlap(gap_start, gap_end, exp_start, exp_end):
                overlapping_gaps.append(gap)
                break 
    
    all_exp_govt_docs = work_exp + overlapping_durations + gaps
    all_experiences_sorted_govt_docs = sorted(all_exp_govt_docs, key=lambda x: x.get("start_date", "N/A"))

    #print(all_experiences_sorted)
    all_exp_tenure = company_data + overlapping_durations_tenure + gaps_tenure
    all_experiences_sorted_tenure = sorted(all_exp_tenure, key=lambda x: x.get("start_date", "N/A"))
    
    return CareerDetailsResponse(
        all_experiences_govt_docs = all_experiences_sorted_govt_docs,
        all_experiences_tenure = all_experiences_sorted_tenure,
        good_to_know = len(gaps),
        red_flag = len(overlapping_durations),
        discrepancies = len(overlapping_gaps),
        lack_of_trust = min(5,(len(overlapping_durations)+len(overlapping_gaps)))
    )

 
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host='0.0.0.0', port=8080, reload=True)