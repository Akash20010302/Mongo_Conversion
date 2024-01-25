from db.db import session
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, FastAPI
from sqlalchemy.sql import text
from sqlmodel import SQLModel
from async_sessions.sessions import get_db
from typing import List, Optional, Tuple
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from endpoints.summary_endpoints import summary_router
from endpoints.identification_endpoints import identification_router
from endpoints.contact_endpoints import contact_router
from endpoints.benchmark_endpoints import benchmark_router
from endpoints.about_endpoints import about_router
from endpoints.career_endpoints import career_router
from endpoints.share_endpoints import share_router
from endpoints.newhire_endpoints import new_hire_router

app = FastAPI()
logger.success("Report Server StartUp Successful")
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
app.include_router(benchmark_router)
app.include_router(about_router)
app.include_router(career_router)
app.include_router(share_router)
app.include_router(new_hire_router)

@app.get('/sessionrollback',tags=['App'])
async def rollback():
    session.rollback()
    return "Sucess"

class TwentySixAsDetails(SQLModel):
    person_id: str
    A1_section_1: str
    A7_paid_credited_amount: str

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


class RetailAccountDetails(SQLModel):
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

class A2_section_1(SQLModel):
    person_id: str
    A2: Optional[str]


class A2Section1Count(SQLModel):
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
class Enquiries(SQLModel):
    queries_last_1_month: int
    queries_last_3_months: int
    queries_last_6_months: int
    queries_last_12_months: int
    queries_last_24_months: int

class ResponseModel(SQLModel):
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

class CreditResponse(SQLModel):
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


class AccountSummaryResponse(SQLModel):
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
class Enquiries(SQLModel):
    queries_last_1_month: int
    queries_last_3_months: int
    queries_last_6_months: int
    queries_last_12_months: int
    queries_last_24_months: int

class tradeline(SQLModel):
    count: int
    balance: int
    high_credit: int
    credit_limit: int
    past_due: int

class CombinedResponseModel(SQLModel):
    active_accounts: List[str]
    enquiries: Enquiries
    active_account_count: int
    number_of_closed_accounts: int
    total_balance: float
    total_credit_limit: float
    total_past_due: float
    credit_score: int
    tradeline_summary_installment: tradeline
    tradeline_summary_open: tradeline
    tradeline_summary_close: tradeline
    tradeline_summary_total: tradeline
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
        score_factors.append("Not enough balance decreases on active non-mortgage accounts")
    else:
        score_factors.append("Enough balance decreases on active non-mortgage accounts")
        
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
    
    tradeline_summary_installment_query = text('''
                                   SELECT COUNT(distinct Balance),SUM(distinct Balance),SUM(distinct PastDueAmount),SUM(distinct HighCredit), SUM(distinct CreditLimit) FROM RetailAccountDetails WHERE AccountType !="Credit Card" AND open = "Yes" AND date(LastPaymentDate) >= date("now","-12 months")
                                   AND person_id = :person_id
                                   ''')
    tradeline_summary_open_query = text('''
                                   SELECT COUNT(distinct Balance),SUM(distinct Balance),SUM(distinct PastDueAmount),SUM(distinct HighCredit), SUM(distinct CreditLimit) FROM RetailAccountDetails WHERE open = "Yes" AND date(LastPaymentDate) >= date("now","-12 months")
                                   AND person_id = :person_id
                                   ''')
    tradeline_summary_close_query = text('''
                                   SELECT COUNT(distinct Balance),SUM(distinct Balance),SUM(distinct PastDueAmount),SUM(distinct HighCredit), SUM(distinct CreditLimit) FROM RetailAccountDetails WHERE open = "No" AND date(LastPaymentDate) >= date("now","-12 months")
                                   AND person_id = :person_id
                                   ''')

    # Execute queries
    result_accounts = await db.execute(query_accounts, {"person_id": person_id, "balance": 99})
    result_summary = await db.execute(query_summary, {"person_id": person_id})
    result_enquiries = await db.execute(query_enquiries, {"person_id": person_id})
    result_credit_score = await db.execute(query_credit_score, {"person_id": person_id})
    result_installment = await db.execute(tradeline_summary_installment_query, {"person_id": person_id})
    result_open = await db.execute(tradeline_summary_open_query, {"person_id": person_id})
    result_close = await db.execute(tradeline_summary_close_query, {"person_id": person_id})
    
    # Fetch results
    active_accounts_data = result_accounts.fetchall()
    summary_data = result_summary.fetchone()
    enquiries_data = result_enquiries.fetchone()
    credit_score = result_credit_score.fetchone()
    installment_data = result_installment.fetchone()
    open_data = result_open.fetchone()
    close_data = result_close.fetchone()
    
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
            queries_last_1_month=enquiries_data[0] if enquiries_data[0] is not None else 0,
            queries_last_3_months=enquiries_data[1] if enquiries_data[1] is not None else 0,
            queries_last_6_months=enquiries_data[2] if enquiries_data[2] is not None else 0,
            queries_last_12_months=enquiries_data[3] if enquiries_data[3] is not None else 0,
            queries_last_24_months=enquiries_data[4] if enquiries_data[4] is not None else 0
        ),
        active_account_count=active_account_count,
        number_of_closed_accounts=summary_data[0],
        total_balance=float(summary_data[1]) if summary_data[1] is not None else 0.0,
        total_credit_limit=float(summary_data[2]) if summary_data[2] is not None else 0.0,
        total_past_due=float(summary_data[3]) if summary_data[3] is not None else 0.0,
        credit_score=credit_score if credit_score else 0.0,
        tradeline_summary_installment=tradeline(
            count=installment_data[0] if installment_data[0] else 0,
            balance=installment_data[1] if installment_data[1] else 0,
            past_due=installment_data[2] if installment_data[2] else 0,
            high_credit=installment_data[3] if installment_data[3] else 0,
            credit_limit=installment_data[4] if installment_data[4] else 0
        ),
        tradeline_summary_open=tradeline(
            count=open_data[0] if open_data[0] else 0,
            balance=open_data[1] if open_data[1] else 0,
            past_due=open_data[2] if open_data[2] else 0,
            high_credit=open_data[3] if open_data[3] else 0,
            credit_limit=open_data[4] if open_data[4] else 0
        ),
        tradeline_summary_close=tradeline(
            count=close_data[0] if close_data[0] else 0,
            balance=close_data[1] if close_data[1] else 0,
            past_due=close_data[2] if close_data[2] else 0,
            high_credit=close_data[3] if close_data[3] else 0,
            credit_limit=close_data[4] if close_data[4] else 0
        ),
        tradeline_summary_total=tradeline(
            count=close_data[0] if close_data[0] else 0 + open_data[0] if open_data[0] else 0,
            balance=close_data[1] if close_data[1] else 0 + open_data[1] if open_data[1] else 0,
            past_due=close_data[2] if close_data[2] else 0 + open_data[2] if open_data[2] else 0,
            high_credit=close_data[3] if close_data[3] else 0 + open_data[3] if open_data[3] else 0,
            credit_limit=close_data[4] if close_data[4] else 0 + open_data[4] if open_data[4] else 0
        ),
        phone_numbers=phone_data,
        email_addresses=email_data,
        addresses=address_data,
        score_factors=score_factors if score_factors else []

    )

    return response    






class MonthlyIncome(SQLModel):
    month: str
    salary_amount: float
    other_income_amount: float
    overseas_income_amount: float  # New field
    business_income_amount: float  # New field
    personal_income_amount: float  # New field
    total_income_amount: float

class IncomeSources(SQLModel):
    salary_sources: List[str]
    other_income_sources: List[str]
    overseas_income_sources: List[str]  # New field

class IncomeSummaryResponse(SQLModel):
    number_of_salary_accounts: int
    number_of_other_income_accounts: int
    number_of_personal_savings_account: int
    number_of_business_income_accounts: int
    number_of_overseas_acount: int
    red_flag: int
    total_number_of_income_sources: int
    total_salary_received: float
    total_other_income: float
    total_personal_savings: float
    total_overseas_income: float
    total_business_income: float
    total_income: float
    monthly_income_details: List[MonthlyIncome]
    income_sources: IncomeSources
    #ADDED
    # overseas_income_sources: int  # New field
    # overseas_income_amount: float  # New field
    income_percentage: dict
    income_score_percentage: int
    income_score_text: str
    highlights: List[str]
    income_highlights: List[str]
    distribution_highlights: List[str]
    
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
            COUNT(DISTINCT CASE WHEN "A2(section_1)" = "192" THEN deductor_tan_no END) AS salary_accounts,
            COUNT(DISTINCT CASE 
                WHEN "A2(section_1)" IN ('194DA', '194I(a)', '194I(b)', '194I', '194LA', '194S', '194M', '194N', '194P', '194Q', '196DA', '206CA', '206CB', '206CC', '206CD', '206CE', '206CF', '206CG', '206CH', '206CI', '206CJ', '206CK', '206CL', '206CM', '206CP', '206CR') 
                THEN deductor_tan_no 
            END) AS other_income_accounts,
            COUNT(DISTINCT CASE 
                WHEN "A2(section_1)" IN ('194C', '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O') 
                THEN deductor_tan_no 
            END) AS business_income_accounts,
			COUNT(DISTINCT CASE 
                WHEN "A2(section_1)" IN ('192A','193', '194', '194A', '194B', '194BB', '194EE', '194F', '194G', '194IA', '194IB', '194K', '194LB', '194LBB', '194LBC', '194S', '194LD') 
                THEN deductor_tan_no 
            END) AS personal_income_accounts,
            SUM(CASE WHEN "A2(section_1)" LIKE '192%' THEN CAST("A7(paid_credited_amt)" AS FLOAT) END) AS total_salary,
            SUM(CASE 
                WHEN "A2(section_1)" IN ('194DA', '194I(a)', '194I(b)', '194I', '194LA', '194S', '194M', '194N', '194P', '194Q', '196DA', '206CA', '206CB', '206CC', '206CD', '206CE', '206CF', '206CG', '206CH', '206CI', '206CJ', '206CK', '206CL', '206CM', '206CP', '206CR') 
                THEN 
                    CASE 
                        WHEN "A2(section_1)" IN ('206CA', '206CE', '206CJ', '206CL', '206CN') THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.01
                        WHEN "A2(section_1)" IN ('206CK', '206CM') AND CAST("A7(paid_credited_amt)" AS FLOAT) / 0.01 > 200000 THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.01
                        WHEN "A2(section_1)" IN ('206CB', '206CC','206CD') THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.025
                        WHEN "A2(section_1)" IN ('206CF', '206CG','206CH') THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.02
                        WHEN "A2(section_1)" = '206CI' THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.05
                        WHEN "A2(section_1)" = '206CR' AND CAST("A7(paid_credited_amt)" AS FLOAT) / 0.001 > 5000000 THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.001
                        ELSE CAST("A7(paid_credited_amt)" AS FLOAT)
                    END
            END) AS total_other_income,
            SUM(CASE 
                WHEN "A2(section_1)" IN ('194C', '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O')
                THEN
                    CASE
                        WHEN "A2(section_1)" = '206CN' THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.01
                        ELSE CAST("A7(paid_credited_amt)" AS FLOAT)
                    END
            END) AS total_business_income,
			SUM(CASE 
                WHEN "A2(section_1)" IN ('192A','193', '194', '194A', '194B', '194BB', '194EE', '194F', '194G', '194IA', '194IB', '194K', '194LB', '194LBB', '194LBC', '194S', '194LD')
                THEN
                    CASE
                        WHEN "A2(section_1)" = '192A' THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.1
                        ELSE CAST("A7(paid_credited_amt)" AS FLOAT)
                    END
            END) AS total_personal_income
        FROM "26as_details"
        WHERE person_id = :person_id
            AND strftime('%Y-%m-%d', 
                substr("A3(transaction_dt)", 8, 4) || '-' || 
                CASE substr("A3(transaction_dt)", 4, 3)
                    WHEN 'Jan' THEN '01'
                    WHEN 'Feb' THEN '02'
                    WHEN 'Mar' THEN '03'
                    WHEN 'Apr' THEN '04'
                    WHEN 'May' THEN '05'
                    WHEN 'Jun' THEN '06'
                    WHEN 'Jul' THEN '07'
                    WHEN 'Aug' THEN '08'
                    WHEN 'Sep' THEN '09'
                    WHEN 'Oct' THEN '10'
                    WHEN 'Nov' THEN '11'
                    WHEN 'Dec' THEN '12'
                    END || '-' ||
                    substr("A3(transaction_dt)", 1, 2)
            ) >= strftime('%Y-%m-%d', 'now', '-12 months')

    """)

    
    monthly_income_query = text("""
        SELECT 
            strftime('%Y-%m', formatted_date) as month_year,
            (CASE WHEN "A2(section_1)" LIKE '192%' THEN CAST("A7(paid_credited_amt)" AS FLOAT) ELSE 0 END) as salary_amount,
            (SUM(CASE 
                WHEN "A2(section_1)" IN ('194DA', '194I(a)', '194I(b)', '194I', '194LA', '194S', '194M', '194N', '194P', '194Q', '196DA', '206CA', '206CB', '206CC', '206CD', '206CE', '206CF', '206CG', '206CH', '206CI', '206CJ', '206CK', '206CL', '206CM', '206CP', '206CR') 
                THEN 
                    CASE 
                        WHEN "A2(section_1)" IN ('206CA', '206CE', '206CJ', '206CL', '206CN') THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.01
                        WHEN "A2(section_1)" IN ('206CK', '206CM') AND CAST("A7(paid_credited_amt)" AS FLOAT) / 0.01 > 200000 THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.01
                        WHEN "A2(section_1)" IN ('206CB', '206CC','206CD') THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.025
                        WHEN "A2(section_1)" IN ('206CF', '206CG','206CH') THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.02
                        WHEN "A2(section_1)" = '206CI' THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.05
                        WHEN "A2(section_1)" = '206CR' AND CAST("A7(paid_credited_amt)" AS FLOAT) / 0.001 > 5000000 THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.001
                        ELSE CAST("A7(paid_credited_amt)" AS FLOAT)
                    END
            END))as other_income_amount,
            (SUM(CASE 
                WHEN "A2(section_1)" IN ('194C', '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O')
                THEN
                    CASE
                        WHEN "A2(section_1)" = '206CN' THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.01
                        ELSE CAST("A7(paid_credited_amt)" AS FLOAT)
                    END
            END)) as business_income_amount,
			(SUM(CASE 
                WHEN "A2(section_1)" IN ('192A','193', '194', '194A', '194B', '194BB', '194EE', '194F', '194G', '194IA', '194IB', '194K', '194LB', '194LBB', '194LBC', '194S', '194LD')
                THEN
                    CASE
                        WHEN "A2(section_1)" = '192A' THEN CAST("A7(paid_credited_amt)" AS FLOAT) / 0.1
                        ELSE CAST("A7(paid_credited_amt)" AS FLOAT)
                    END
            END)) AS total_personal_income
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
    
    
    
    overseas_income_query = text("""
    SELECT 
        strftime('%Y-%m', formatted_date) as month_year,
        SUM(CASE 
            WHEN B2 = '206CQ' OR B2 = '206CO' THEN 
                CASE 
                    WHEN CAST(B7 AS FLOAT) / 0.05 <= 700000 THEN CAST(B7 AS FLOAT) / 0.05
                    ELSE CAST(B7 AS FLOAT) / 0.20
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
        WHERE person_id = :person_id AND B2 = '206CQ' OR B2 = '206CO'
    ) 
    GROUP BY strftime('%Y-%m', formatted_date)
    """)


    
    overseas_income_result = await db.execute(overseas_income_query, {"person_id": person_id, "source": "206CQ"})
    overseas_income_raw_data = overseas_income_result.fetchall()

    
    
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

    monthly_income_details = [
    MonthlyIncome(
        month=row[0],
        salary_amount=row[1],
        other_income_amount=float(row[2]) if row[2] is not None else 0.0,
        overseas_income_amount=0.0,
        business_income_amount=float(row[3]) if row[3] is not None else 0.0,
        personal_income_amount=float(row[4]) if row[4] is not None else 0.0,
        total_income_amount=0.0
        
        
    )
    for row in monthly_income_raw_data if row[0]
    ]
    monthly_income_details.reverse()
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
    
    salary_accounts = summary[0]
    other_income_accounts = summary[1]
    business_income_accounts = summary[2]
    personal_income_accounts = summary[3]
    
    total_salary = summary[4] if summary[4] is not None else 0.0
    total_other_income = summary[5] if summary[5] is not None else 0.0
    total_business_income = summary[6] if summary[6] is not None else 0.0
    total_personal_income = summary[7] if summary[7] is not None else 0.0
    
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

    finance_meter_map = {
        1: "Very Low",
        2: "Low",
        3: "Medium",
        4: "High",
        5: "Very High"
    }
    
    total_income = total_salary + total_other_income + total_business_income + total_overseas_income + total_personal_income

    # Calculate the percentage share of each income type
    salary_percentage = (total_salary / total_income * 100) if total_income > 0 else 0
    other_income_percentage = (total_other_income / total_income * 100) if total_income > 0 else 0
    business_income_percentage = (total_business_income / total_income * 100) if total_income > 0 else 0
    overseas_income_percentage = (total_overseas_income / total_income * 100) if total_income > 0 else 0
    personal_income_percentage = (total_personal_income / total_income * 100) if total_income > 0 else 0

    income_percentage = {
        "salary_percentage": round(salary_percentage),
        "other_income_percentage": round(other_income_percentage),
        "overseas_income_percentage": round(overseas_income_percentage),
        "business_income_percentage": round(business_income_percentage),
        "personal_income_percentage": round(personal_income_percentage)
    }

    income_score_percentage=max(0,100- 2*(other_income_accounts))-10*(len(overseas_income_sources)+business_income_accounts)
    if income_score_percentage >= 95:
        income_score_text="Excellent"
    elif income_score_percentage >= 90  and income_score_percentage < 95:
        income_score_text="Good"
    elif income_score_percentage >= 80  and income_score_percentage < 90:
        income_score_text="Concern"
    else:
        income_score_text="Bad"
    
    total_number_of_income_sources=salary_accounts + other_income_accounts + business_income_accounts +len(overseas_income_sources)+personal_income_accounts
    
    highlights =[]
    
    highlights.append(f"Total {total_number_of_income_sources} income sources were identified in tht last 12 months")
    
    if business_income_accounts > 0:
        highlights.append(f"{business_income_accounts} Business income sources contributing {round(business_income_percentage)}% of the total income (Red Flag)")
    if other_income_accounts > 0:
        highlights.append(f"{other_income_accounts} Other income sources contributing {round(other_income_percentage)}% of the total income (Red Flag)")
    if personal_income_accounts > 0:
        highlights.append(f"{personal_income_accounts} Personal income sources contributing {round(personal_income_percentage)}% of the total income (Red Flag)")
    if len(overseas_income_sources) > 0:
        highlights.append(f"{len(overseas_income_sources)} Overseas income sources contributing {round(overseas_income_percentage)}% of the total income (Red Flag)")
    
    income_highlights = []
    if business_income_percentage + overseas_income_percentage >5:
        income_highlights.append(f"Additional income is available from other businesses. Since this income is more than 5% of the overall income, it should be declared.")
    elif (business_income_percentage>0 or overseas_income_percentage>0) and business_income_percentage + overseas_income_percentage <=5:
        income_highlights.append(f"Additional income is available from other businesses. But this income is less than or equal to 5% of the overall income.")
    elif  business_income_percentage<=0 and overseas_income_percentage<=0:
        income_highlights.append(f"No additional income is available from other businesses.")
        
    if business_income_percentage>salary_percentage:
        income_highlights.append(f"Business income is more than the Salary. This could lead to the candidate paying more attention to the additional income sources.")
    else:
        income_highlights.append(f"Salary income is more than the Business income. This has lesser chances of the candidate paying attention to the additional income sources.")
    if salary_percentage<50:
        income_highlights.append(f"Salary seems to be less than 50% of the candidate's income. Financial needs from Salary income does not sufficiently met. This could be a reason for future attrition.")
    else:
        income_highlights.append(f"Salary seems to be more than 50% of the candidate's income. Financial needs from Salary income sufficiently met.")
    
    summary_messages = []
    
    for i in range(1, len(monthly_income_raw_data)):
        current_month, current_salary_income, current_other_income, current_business_income, current_personal_income = monthly_income_raw_data[i]
        current_overseas_income = monthly_overseas_income.get(current_month, 0.0)
        previous_month,previous_salary_income, previous_other_income, previous_business_income,previous_personal_income= monthly_income_raw_data[i - 1]
        previous_overseas_income = monthly_overseas_income.get(previous_month, 0.0)
        previous_business_income = previous_business_income if previous_business_income is not None else 0
        previous_other_income = previous_other_income if previous_other_income is not None else 0 
        previous_personal_income = previous_personal_income if previous_personal_income is not None else 0
        previous_overseas_income = previous_overseas_income if previous_overseas_income is not None else 0
        current_business_income = current_business_income if current_business_income is not None else 0
        current_other_income = current_other_income if current_other_income is not None else 0
        current_overseas_income = current_overseas_income if current_overseas_income is not None else 0
        current_personal_income = current_personal_income if current_personal_income is not None else 0
        previous_income, current_income = previous_business_income + previous_other_income +previous_personal_income +previous_overseas_income , current_business_income+current_other_income+current_overseas_income+current_personal_income 
    
        if previous_income == 0:
            growth_percentage = float('inf')  
        else:
            growth_percentage = ((current_income - previous_income) / previous_income) * 100

        if growth_percentage > 200:
            summary_messages.append(f"{current_month} saw more than {growth_percentage:.2f}% growth")
            
        if previous_business_income == 0:
            business_growth_percentage = 0 
        else:
            business_growth_percentage = ((current_business_income - previous_business_income) / previous_business_income) * 100

        if previous_personal_income == 0:
            personal_growth_percentage = 0
        else:
            personal_growth_percentage = ((current_personal_income - previous_personal_income) / previous_personal_income) * 100

        if previous_other_income == 0:
            other_growth_percentage = 0  
        else:
            other_growth_percentage = ((current_other_income - previous_other_income) / previous_other_income) * 100

        if previous_overseas_income == 0:
            overseas_growth_percentage = 0
        else:
            overseas_growth_percentage = ((current_overseas_income - previous_overseas_income) / previous_overseas_income) * 100



    summary_line = ", ".join(summary_messages) if len(summary_messages)>0 else "" 
    
    distribution_highlights = []
    
    if salary_accounts == 1 :
        if len(summary_line) > 0:
            distribution_highlights.append(f"Salary came from {salary_accounts} source (TBD). Month over month, salary payments are consistent.{summary_line}  compared to the respective previous month")
        else:
            distribution_highlights.append(f"Salary came from {salary_accounts} source (TBD). Month over month, salary payments are consistent.")
    elif salary_accounts >1:
        if len(summary_line) > 0:
            distribution_highlights.append(f"Salary came from {salary_accounts} sources (TBD). Month over month, salary payments are consistent.{summary_line} compared to the respective previous month")
        else:
            distribution_highlights.append(f"Salary came from {salary_accounts} sources (TBD). Month over month, salary payments are consistent.")
    
    if business_growth_percentage > 0:
        distribution_highlights.append("Business income has a growing trend month-over-month. This could lead to drop in performance")
    if overseas_growth_percentage > 0:
        distribution_highlights.append("Overseas income has a growing trend month-over-month. This could lead to drop in performance")
    if personal_growth_percentage > 0:
        distribution_highlights.append("Personal income has a growing trend month-over-month. This could lead to drop in performance")
    if other_growth_percentage > 0:
        distribution_highlights.append("Other income has a growing trend month-over-month. This could lead to drop in performance")
      
    
    return IncomeSummaryResponse(
        number_of_salary_accounts=salary_accounts,
        #number_of_salary_accounts=len(salary_sources),
        number_of_other_income_accounts=other_income_accounts,
        # number_of_business_income_accounts=other_income_accounts,
        #number_of_business_income_accounts=len(other_income_sources),
        number_of_business_income_accounts=business_income_accounts,
        number_of_personal_savings_account=personal_income_accounts,
        number_of_overseas_acount = len(overseas_income_sources),
        total_number_of_income_sources=total_number_of_income_sources,
        red_flag = other_income_accounts + business_income_accounts + personal_income_accounts + len(overseas_income_sources),
        total_salary_received=total_salary,
        total_other_income=total_other_income,
        total_business_income=total_business_income,
        total_personal_savings=total_personal_income,
        total_overseas_income=total_overseas_income,
        total_income=total_salary + total_other_income + total_overseas_income+total_personal_income+total_business_income,
        monthly_income_details=monthly_income_details,
        income_sources=income_sources,
        # overseas_income_sources=len(overseas_income_sources),
        # overseas_income_amount=sum(monthly_overseas_income.values()),
        income_percentage=income_percentage,
        income_score_percentage=income_score_percentage,
        income_score_text=income_score_text,
        highlights = highlights,
        income_highlights = income_highlights,
        distribution_highlights = distribution_highlights
    )

 
# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run('app:app', host='0.0.0.0', port=8080, reload=True)