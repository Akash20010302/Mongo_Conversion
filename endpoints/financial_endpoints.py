from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import text
from sqlmodel import Session
from email_response import send_email
# from models.financial import IncomeSources, IncomeSummaryResponse, MonthlyIncome
from mongomodels.Financial import IncomeSources, IncomeSummaryResponse, MonthlyIncome
from db.db import get_db_analytics
from mongoengine import connect


financial_router = APIRouter()

connect(db='trace_about', host="mongodb://localhost:27017/")


@financial_router.get(
    "/financial_position/{application_id}")
async def get_income_summary(
    application_id: str, db: Session = Depends(get_db_analytics)
):
    try:
        validation_query = text("""
                                SELECT count(*) FROM itr_status WHERE application_id = :application_id
                                """)
        
        valid_count = db.exec(validation_query.params(application_id=application_id))
        count_raw_data = valid_count.fetchone()
        if count_raw_data[0] == 0:
            raise HTTPException(detail="Application not found", status_code=404)
        query = text(
            """
            SELECT
                COUNT(DISTINCT CASE WHEN section_1 = '192' THEN deductor_tan_no END) AS salary_accounts,
                COUNT(DISTINCT CASE WHEN section_1 IN ('194DA', '194I(a)', '194I(b)', '194I', '194LA', '194S', '194M', '194N', '194P', '194Q', '196DA', '206CA', '206CB', '206CC', '206CD', '206CE', '206CF', '206CG', '206CH', '206CI', '206CJ', '206CK', '206CL', '206CM', '206CP', '206CR') THEN deductor_tan_no END) AS other_income_accounts,
                COUNT(DISTINCT CASE WHEN section_1 IN ('194C', '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O') THEN deductor_tan_no END) AS business_income_accounts,
                COUNT(DISTINCT CASE WHEN section_1 IN ('192A','193', '194', '194A', '194B', '194BB', '194EE', '194F', '194G', '194IA', '194IB', '194K', '194LB', '194LBB', '194LBC', '194LD') THEN deductor_tan_no END) AS personal_income_accounts,
                SUM(CASE WHEN section_1 LIKE '192%' THEN paid_credited_amt END) AS total_salary,
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
                END) AS total_other_income,
                SUM(CASE WHEN section_1 IN ('194C', '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O') THEN 
                        CASE
                            WHEN section_1 = '206CN' THEN paid_credited_amt / 0.01
                            ELSE paid_credited_amt
                        END
                END) AS total_business_income,
                SUM(CASE WHEN section_1 IN ('192A','193', '194', '194A', '194B', '194BB', '194EE', '194F', '194G', '194IA', '194IB', '194K', '194LB', '194LBB', '194LBC', '194LD') THEN 
                        CASE
                            WHEN section_1 = '192A' THEN paid_credited_amt / 0.1
                            ELSE paid_credited_amt
                        END
                END) AS total_personal_income
            FROM itr_26as_details
            WHERE application_id = :application_id
                AND transaction_dt >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        """
        )

        monthly_income_query = text(
            """SELECT
                                            DATE_FORMAT(formatted_date, '%Y-%m') AS month_year,
                                            SUM(CASE WHEN section_1 LIKE '192%' THEN paid_credited_amt ELSE 0 END) AS total_salary_amount,
                                            SUM(CASE WHEN section_1 IN ('194DA', '194I(a)', '194I(b)', '194I', '194LA', '194S', '194M', '194N', '194P', '194Q', '196DA', '206CA', '206CB', '206CC', '206CD', '206CE', '206CF', '206CG', '206CH', '206CI', '206CJ', '206CK', '206CL', '206CM', '206CP', '206CR') THEN paid_credited_amt ELSE 0 END) AS total_other_income_amount,
                                            SUM(CASE WHEN section_1 IN ('194C', '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O') THEN paid_credited_amt ELSE 0 END) AS total_business_income_amount,
                                            SUM(CASE WHEN section_1 IN ('192A','193', '194', '194A', '194B', '194BB', '194EE', '194F', '194G', '194IA', '194IB', '194K', '194LB', '194LBB', '194LBC', '194LD') THEN paid_credited_amt ELSE 0 END) AS total_personal_income_amount
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

        overseas_income_query = text(
            """
                                    SELECT 
                                        DATE_FORMAT(transaction_dt, '%Y-%m') AS month_year,
                                        SUM(CASE 
                                            WHEN section_1 IN ('206CQ', '206CO') THEN 
                                                CASE 
                                                WHEN paid_credited_amt / 0.05 <= 700000 THEN paid_credited_amt / 0.05
                                                ELSE paid_credited_amt / 0.10
                                                END
                                            ELSE 0 
                                        END) AS overseas_income_amount,
                                        deductor_tan_no
                                    FROM itr_26as_details
                                    WHERE application_id = :application_id AND section_1 IN ('206CQ', '206CO') AND transaction_dt >= CURDATE() - INTERVAL 12 MONTH
                                            AND transaction_dt < CURDATE()
                                    GROUP BY month_year
            """
        )

        overseas_income_result = db.exec(
            overseas_income_query.params(application_id=application_id)
        )
        overseas_income_raw_data = overseas_income_result.fetchall()
        logger.debug(f"OVERSEAR INCOME: {overseas_income_raw_data}")

        deductor_name_query = text(
            """
                                    SELECT DISTINCT deductor_tan_no,deductor_name FROM itr_26as_details WHERE application_id = :application_id
                                """
        )

        deductor_name_result = db.exec(
            deductor_name_query.params(application_id=application_id)
        )
        deductor_name_data = deductor_name_result.fetchall()

        tan_map = {}
        for row in deductor_name_data:
            tan_map[row[0]] = row[1]

        # Process overseas income data
        overseas_income_sources = []
        monthly_overseas_income = {}
        first_flag = True
        for row in overseas_income_raw_data:
            month_year, amount, source = row
            if first_flag:
                amount += 700000
                first_flag = False
            if tan_map.get(source) is not None:
                overseas_income_sources.append(
                    tan_map.get(source) + " {" + source + "}"
                )
            else:
                overseas_income_sources.append("NONAME COMPANY {" + source + "}")
            monthly_overseas_income.setdefault(month_year, 0)
            monthly_overseas_income[month_year] += amount

        overseas_income_sources = list(set(overseas_income_sources))
        logger.debug(overseas_income_sources)
        overseas_income_sources_count = len(overseas_income_sources)
        # Query for distinct income sources
        income_sources_query = text(
            """
                                SELECT 
                                    DISTINCT salary_source,
                                    other_source,
                                    business_source,
                                    personal_income
                                FROM (
                                    SELECT 
                                        DISTINCT CASE WHEN section_1 = '192' THEN deductor_tan_no END as salary_source,
                                        CASE WHEN section_1 IN ('194DA', '194I(a)', '194I(b)', '194I', '194LA', '194S', '194M', '194N', '194P', '194Q', '196DA', '206CA', '206CB', '206CC', '206CD', '206CE', '206CF', '206CG', '206CH', '206CI', '206CJ', '206CK', '206CL', '206CM', '206CP', '206CR') THEN deductor_tan_no END as other_source,
                                        CASE WHEN section_1 IN ('194C', '194D', '194E', '194H', '194J(a)', '194J(b)', '194J', '194JA', '194JB', '194LC', '194LBA', '194R', '194O', '206CN', '17(2)', '17(3)', '10(5)', '194O') THEN deductor_tan_no END as business_source,
                                        CASE WHEN section_1 IN ('192A','193', '194', '194A', '194B', '194BB', '194EE', '194F', '194G', '194IA', '194IB', '194K', '194LB', '194LBB', '194LBC', '194LD') THEN deductor_tan_no END as personal_income
                                    FROM itr_26as_details
                                    WHERE application_id = :application_id
                                        AND transaction_dt >= CURDATE() - INTERVAL 12 MONTH
                                        AND transaction_dt < CURDATE()
                                ) AS categorized_incomes
                                WHERE salary_source IS NOT NULL
                                    OR other_source IS NOT NULL
                                    OR business_source IS NOT NULL
                                    OR personal_income IS NOT NULL
        """
        )

        # Execute queries
        monthly_income_result = db.exec(
            monthly_income_query.params(application_id=application_id)
        )
        income_sources_result = db.exec(
            income_sources_query.params(application_id=application_id)
        )

        # Fetch and process monthly income results
        monthly_income_raw_data = monthly_income_result.fetchall()
        logger.debug(f"Monthly income: {monthly_income_raw_data}")
        monthly_income_details = [
            MonthlyIncome(
                month=row[0],
                salary_amount=row[1],
                other_income_amount=float(row[2]) if row[2] is not None else 0.0,
                overseas_income_amount=0.0,
                business_income_amount=float(row[3]) if row[3] is not None else 0.0,
                personal_income_amount=float(row[4]) if row[4] is not None else 0.0,
                total_income_amount=0.0,
            )
            for row in monthly_income_raw_data
            if row[0]
        ]
        monthly_income_details.reverse()
        # Added for overseas
        total_overseas_income = 0.0
        first_flag = True
        for income_detail in monthly_income_details:
            if first_flag and monthly_overseas_income.get(income_detail.month, 0.0):
                income_detail.overseas_income_amount = (
                    monthly_overseas_income.get(income_detail.month, 0.0) + 700000
                )
                first_flag = False
            else:
                income_detail.overseas_income_amount = monthly_overseas_income.get(
                    income_detail.month, 0.0
                )
            total_overseas_income += monthly_overseas_income.get(
                income_detail.month, 0.0
            )
            income_detail.total_income_amount = (
                income_detail.salary_amount
                + income_detail.other_income_amount
                + income_detail.overseas_income_amount
                + income_detail.business_income_amount
                + income_detail.personal_income_amount
            )

        salary_sources = []
        other_income_sources = []
        business_income_sources = []
        personal_income_sources = []

        for row in income_sources_result.fetchall():
            if row[0] is not None:
                salary_sources.append(tan_map.get(row[0]) + " {" + row[0] + "}")
            if row[1] is not None:
                other_income_sources.append(tan_map.get(row[1]) + " {" + row[1] + "}")
            if row[2] is not None:
                business_income_sources.append(
                    tan_map.get(row[2]) + " {" + row[2] + "}"
                )
            if row[3] is not None:
                personal_income_sources.append(
                    tan_map.get(row[3]) + " {" + row[3] + "}"
                )

        if len(salary_sources) == 0:
            salary_sources.append("N/A")
        if len(other_income_sources) == 0:
            other_income_sources.append("N/A")
        if len(business_income_sources) == 0:
            business_income_sources.append("N/A")
        if len(personal_income_sources) == 0:
            personal_income_sources.append("N/A")
        if len(overseas_income_sources) == 0:
            overseas_income_sources.append("N/A")

        income_sources = IncomeSources(
            salary_sources=salary_sources,
            other_income_sources=other_income_sources,
            business_income_sources=business_income_sources,
            personal_income_sources=personal_income_sources,
            overseas_income_sources=overseas_income_sources,
        )
        # income_sources.overseas_income_sources = overseas_income_sources

        result = db.exec(query.params(application_id=application_id))
        summary = result.fetchone()
        logger.debug(f"SUMMARY: {summary}")
        salary_accounts = summary[0]
        other_income_accounts = summary[1]
        business_income_accounts = summary[2]
        personal_income_accounts = summary[3]

        total_salary = summary[4] if summary[4] is not None else 0.0
        total_other_income = summary[5] if summary[5] is not None else 0.0
        total_business_income = summary[6] if summary[6] is not None else 0.0
        total_personal_income = summary[7] if summary[7] is not None else 0.0

        total_income = (
            total_salary
            + total_other_income
            + total_business_income
            + total_overseas_income
            + total_personal_income
        )

        # Calculate the percentage share of each income type
        salary_percentage = (
            (total_salary / total_income * 100) if total_income > 0 else 0
        )
        other_income_percentage = (
            (total_other_income / total_income * 100) if total_income > 0 else 0
        )
        business_income_percentage = (
            (total_business_income / total_income * 100) if total_income > 0 else 0
        )
        overseas_income_percentage = (
            (total_overseas_income / total_income * 100) if total_income > 0 else 0
        )
        personal_income_percentage = (
            (total_personal_income / total_income * 100) if total_income > 0 else 0
        )

        income_percentage = {
            "salary_percentage": round(salary_percentage),
            "other_income_percentage": round(other_income_percentage),
            "overseas_income_percentage": round(overseas_income_percentage),
            "business_income_percentage": round(business_income_percentage),
            "personal_income_percentage": round(personal_income_percentage),
        }

        income_score_percentage = max(0, 100 - 2 * (other_income_accounts + personal_income_accounts)) - 10 * (
            overseas_income_sources_count + business_income_accounts
        )
        if income_score_percentage >= 95:
            income_score_text = "Excellent"
        elif income_score_percentage >= 90 and income_score_percentage < 95:
            income_score_text = "Good"
        elif income_score_percentage >= 80 and income_score_percentage < 90:
            income_score_text = "Concern"
        else:
            income_score_text = "Bad"

        total_number_of_income_sources = (
            salary_accounts
            + other_income_accounts
            + business_income_accounts
            + overseas_income_sources_count
            + personal_income_accounts
        )

        highlights = []

        highlights.append(
            f"Total {total_number_of_income_sources} income sources were identified in tht last 12 months"
        )

        if business_income_accounts > 0:
            highlights.append(
                f"{business_income_accounts} Business income sources contributing {round(business_income_percentage)}% of the total income (Red Flag)"
            )
        if other_income_accounts > 0:
            highlights.append(
                f"{other_income_accounts} Other income sources contributing {round(other_income_percentage)}% of the total income (Discrepancy)"
            )
        if personal_income_accounts > 0:
            highlights.append(
                f"{personal_income_accounts} Personal income sources contributing {round(personal_income_percentage)}% of the total income (Discrepancy)"
            )
        if overseas_income_sources_count > 0:
            highlights.append(
                f"{overseas_income_sources_count} Overseas income sources contributing {round(overseas_income_percentage)}% of the total income (Red Flag)"
            )

        income_highlights = []
        if business_income_percentage + personal_income_percentage + other_income_percentage + overseas_income_percentage > 5:
            income_highlights.append(
                f"Additional income is available from other sources. Since this income is more than 5% of the overall income, it should be declared."
            )
        elif (
            business_income_percentage > 0 or overseas_income_percentage > 0
        ) and business_income_percentage + personal_income_percentage + other_income_percentage + overseas_income_percentage <= 5:
            income_highlights.append(
                f"Additional income is available from other sources. But this income is less than or equal to 5% of the overall income."
            )
        elif business_income_percentage <= 0 and overseas_income_percentage <= 0 and personal_income_percentage<=0 and other_income_percentage<=0:
            income_highlights.append(
                f"No additional income is available from other sources."
            )

        if business_income_percentage > salary_percentage:
            income_highlights.append(
                f"Business income is more than the Salary. This could lead to the candidate paying more attention to the additional income sources."
            )
        else:
            income_highlights.append(
                f"Salary income is more than the Business income. This has lesser chances of the candidate paying attention to the additional income sources."
            )
        if salary_percentage < 50:
            income_highlights.append(
                f"Salary seems to be less than 50% of the candidate's income. Financial needs from Salary income does not sufficiently met. This could be a reason for future attrition."
            )
        else:
            income_highlights.append(
                f"Salary seems to be more than 50% of the candidate's income. Financial needs from Salary income sufficiently met."
            )

        summary_messages = []
        business_growth_percentage = 0
        personal_growth_percentage = 0
        other_growth_percentage = 0
        overseas_growth_percentage = 0
        
        for i in range(1, len(monthly_income_raw_data)):
            (
                current_month,
                current_salary_income,
                current_other_income,
                current_business_income,
                current_personal_income,
            ) = monthly_income_raw_data[i]
            current_overseas_income = monthly_overseas_income.get(current_month, 0.0)
            (
                previous_month,
                previous_salary_income,
                previous_other_income,
                previous_business_income,
                previous_personal_income,
            ) = monthly_income_raw_data[i - 1]
            previous_overseas_income = monthly_overseas_income.get(previous_month, 0.0)
            previous_business_income = (
                previous_business_income if previous_business_income is not None else 0
            )
            previous_other_income = (
                previous_other_income if previous_other_income is not None else 0
            )
            previous_personal_income = (
                previous_personal_income if previous_personal_income is not None else 0
            )
            previous_overseas_income = (
                previous_overseas_income if previous_overseas_income is not None else 0
            )
            current_business_income = (
                current_business_income if current_business_income is not None else 0
            )
            current_other_income = (
                current_other_income if current_other_income is not None else 0
            )
            current_overseas_income = (
                current_overseas_income if current_overseas_income is not None else 0
            )
            current_personal_income = (
                current_personal_income if current_personal_income is not None else 0
            )
            previous_income, current_income = (
                previous_business_income
                + previous_other_income
                + previous_personal_income
                + previous_overseas_income,
                current_business_income
                + current_other_income
                + current_overseas_income
                + current_personal_income,
            )

            if previous_income == 0:
                growth_percentage = float("inf")
            else:
                growth_percentage = (
                    (current_income - previous_income) / previous_income
                ) * 100

            if growth_percentage > 200:
                summary_messages.append(
                    f"{current_month} saw more than {growth_percentage:.2f}% growth"
                )

            if previous_business_income == 0:
                business_growth_percentage = 0
            else:
                business_growth_percentage = (
                    (current_business_income - previous_business_income)
                    / previous_business_income
                ) * 100

            if previous_personal_income == 0:
                personal_growth_percentage = 0
            else:
                personal_growth_percentage = (
                    (current_personal_income - previous_personal_income)
                    / previous_personal_income
                ) * 100

            if previous_other_income == 0:
                other_growth_percentage = 0
            else:
                other_growth_percentage = (
                    (current_other_income - previous_other_income)
                    / previous_other_income
                ) * 100

            if previous_overseas_income == 0:
                overseas_growth_percentage = 0
            else:
                overseas_growth_percentage = (
                    (current_overseas_income - previous_overseas_income)
                    / previous_overseas_income
                ) * 100

        summary_line = ", ".join(summary_messages) if len(summary_messages) > 0 else ""

        distribution_highlights = []

        if salary_accounts == 1:
            if len(summary_line) > 0:
                distribution_highlights.append(
                    f"Salary came from {salary_accounts} source (TBD). Month over month, salary payments are consistent.{summary_line}  compared to the respective previous month"
                )
            else:
                distribution_highlights.append(
                    f"Salary came from {salary_accounts} source (TBD). Month over month, salary payments are consistent."
                )
        elif salary_accounts > 1:
            if len(summary_line) > 0:
                distribution_highlights.append(
                    f"Salary came from {salary_accounts} sources (TBD). Month over month, salary payments are consistent.{summary_line} compared to the respective previous month"
                )
            else:
                distribution_highlights.append(
                    f"Salary came from {salary_accounts} sources (TBD). Month over month, salary payments are consistent."
                )

        if business_growth_percentage > 0:
            distribution_highlights.append(
                "Business income has a growing trend month-over-month. This could lead to drop in performance"
            )
        if overseas_growth_percentage > 0:
            distribution_highlights.append(
                "Overseas income has a growing trend month-over-month. This could lead to drop in performance"
            )
        if personal_growth_percentage > 0:
            distribution_highlights.append(
                "Personal income has a growing trend month-over-month. This could lead to drop in performance"
            )
        if other_growth_percentage > 0:
            distribution_highlights.append(
                "Other income has a growing trend month-over-month. This could lead to drop in performance"
            )

        if len(distribution_highlights) == 0:
            distribution_highlights.append("No month-over-month income trend found ")

        # Handling existing & Current Document
        existing_document = IncomeSummaryResponse.objects(application_id=application_id, page_id=1).first()
        if existing_document:
            existing_document.delete()

        info_document = IncomeSummaryResponse(
            application_id = application_id,
            page_id = 1,
            number_of_salary_accounts=salary_accounts,
            number_of_other_income_accounts=other_income_accounts,
            number_of_business_income_accounts=business_income_accounts,
            number_of_personal_savings_account=personal_income_accounts,
            number_of_overseas_acount=overseas_income_sources_count,
            total_number_of_income_sources=total_number_of_income_sources,
            red_flag=business_income_accounts
            + overseas_income_sources_count,
            total_salary_received=round(total_salary),
            total_other_income=round(total_other_income),
            total_business_income=round(total_business_income),
            total_personal_savings=round(total_personal_income),
            total_overseas_income=round(total_overseas_income),
            total_income=round(total_salary
            + total_other_income
            + total_overseas_income
            + total_personal_income
            + total_business_income),
            monthly_income_details=monthly_income_details,
            income_sources=income_sources,
            income_percentage=income_percentage,
            income_score_percentage=income_score_percentage,
            income_score_text=income_score_text,
            highlights=highlights,
            income_highlights=income_highlights,
            distribution_highlights=distribution_highlights,
        )
        info_document.save()
    except HTTPException as ht:
        raise ht
    except Exception as e:
        send_email(500, "Report_financial_position")
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(detail="Internal Server Error", status_code=500)
