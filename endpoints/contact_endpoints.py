from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlmodel import Session
from email_response import send_email
# from models.Contact_Information import Address, Email, Index, Mobile, Name, contact_info
from mongomodels.Contact import Address, Email, Index, Mobile, Name, contact_info
from sqlalchemy.sql import text
from db.db import get_db_analytics, get_db_backend
from sqlalchemy.ext.asyncio import AsyncSession
from tools.contact_tools import (
    check_discrepancy,
    check_discrepancy_1,
    check_discrepancy_address,
)
from mongoengine import connect

contact_router = APIRouter()

connect(db='trace_about', host="mongodb://localhost:27017/")




@contact_router.get(
    "/contact_information/{id}",
    tags=["Contact Information"],
)
async def get_combined_info(
    id: int,
    db_1: Session = Depends(get_db_backend),
    db_2: Session = Depends(get_db_analytics),
):
    try:
        result_1 = db_1.exec(
            text(
                "SELECT firstName, lastName, phone, email, city "
                "FROM `form` WHERE appid = :id"
            ).params(id=id)
        )

        contact_info_1 = result_1.fetchone()
        # should we keep it?
        if contact_info_1 is None:
            raise HTTPException(
                status_code=404, detail=f"Personal information not found for id : {id}"
            )

        result_3 = db_2.exec(
            text(
                "SELECT pan_name, contact_primary_mobile, contact_primary_email, "
                "address_post_office, address_city, address_state, address_pin_code "
                "FROM itr_download_profile WHERE application_id = :id"
            ).params(id=id)
        )
        contact_info_3 = result_3.fetchone()
        logger.debug(contact_info_3)
        #if contact_info_3 is None:
        #    raise HTTPException(
        #        status_code=404, detail=f"Personal information not found for id {id}"
        #    )

        if contact_info_3 is None or all(value is None for value in contact_info_3):
            # Assign "N/A" to each column
            contact_info_3 = ["N/A"] * len(result_3.keys())
        else:
            contact_info_3 = [value if value is not None and value != "" else "N/A" for value in contact_info_3]
            # Check and replace None values or empty strings with "N/A"
            #contact_info_3 = [getattr(contact_info_3, column_name, "N/A") for column_name in result_3.keys()]
        logger.debug(contact_info_3)
        (
            name_flag,
            pan_match,
            aadhar_match,
            tax_match,
            name_remarks,
        ) = await check_discrepancy_1(
            f"{contact_info_1[0]} {contact_info_1[1]}",
            contact_info_3[0],
            "N/A",
            contact_info_3[0],
            "Name",
        )

        (
            mobile_flag,
            pan_match_mobile,
            aadhar_match_mobile,
            government_match_mobile,
            mobile_remarks,
        ) = await check_discrepancy(
            contact_info_1[2], contact_info_3[1], "N/A", contact_info_3[1], "Mobile"
        )

        (
            email_flag,
            pan_match_email,
            aadhar_match_email,
            government_match_email,
            email_remarks,
        ) = await check_discrepancy(
            contact_info_1[3], contact_info_3[2], "N/A", contact_info_3[2], "Email"
        )

        (
            address_flag,
            pan_match_address,
            aadhar_match_address,
            government_match_address,
            address_remarks,
        ) = await check_discrepancy_address(
            contact_info_1[4] if contact_info_1[4] is not None else "N/A",
            f"{contact_info_3[3]},{contact_info_3[4]},{contact_info_3[5]},{contact_info_3[6]}",
            "N/A",
            f"{contact_info_3[3]},{contact_info_3[4]},{contact_info_3[5]},{contact_info_3[6]}",
            "Address",
        )

        name_response = Name(
            provided=f"{contact_info_1[0]} {contact_info_1[1]}",
            Pan=contact_info_3[0],
            Aadhar="N/A",
            Tax=contact_info_3[0],
            flag=name_flag,
            pan_match=pan_match,
            aadhar_match=aadhar_match,
            tax_match=tax_match,
            remarks=name_remarks,
        )

        mobile_response = Mobile(
            provided=contact_info_1[2],
            Pan=contact_info_3[1],
            Aadhar="N/A",
            Government=contact_info_3[1],
            flag=mobile_flag,
            pan_match=pan_match_mobile,
            aadhar_match=aadhar_match_mobile,
            government_match=government_match_mobile,
            remarks=mobile_remarks,
        )

        email_response = Email(
            provided=contact_info_1[3],
            Pan=contact_info_3[2],
            Aadhar="N/A",
            Government=contact_info_3[2],
            flag=email_flag,
            pan_match=pan_match_email,
            aadhar_match=aadhar_match_email,
            government_match=government_match_email,
            remarks=email_remarks,
        )

        address_response = Address(
            provided=contact_info_1[4] if contact_info_1[4] is not None else "N/A",
            Pan=f"{contact_info_3[3]},{contact_info_3[4]},{contact_info_3[5]},{contact_info_3[6]}",
            Aadhar="N/A",
            Government=f"{contact_info_3[3]},{contact_info_3[4]},{contact_info_3[5]},{contact_info_3[6]}",
            flag=address_flag,
            pan_match=pan_match_address,
            aadhar_match=aadhar_match_address,
            government_match=government_match_address,
            remarks=address_remarks,
        )

        consistency_name = (
            1
            if name_response.provided
            == name_response.Pan
            == name_response.Aadhar
            == name_response.Tax
            else 0
        )
        consistency_phone = (
            1
            if mobile_response.provided
            == mobile_response.Pan
            == mobile_response.Aadhar
            == mobile_response.Government
            else 0
        )
        consistency_email = (
            1
            if email_response.provided
            == email_response.Pan
            == email_response.Aadhar
            == email_response.Government
            else 0
        )
        consistency_address = (
            1
            if address_response.provided
            == address_response.Pan
            == address_response.Aadhar
            == address_response.Government
            else 0
        )

        discrepancy_name = 1 - consistency_name
        discrepancy_phone = 1 - consistency_phone
        discrepancy_email = 1 - consistency_email
        discrepancy_address = 1 - consistency_address

        consistency = []
        discrepancy = []

        if consistency_name == 1:
            consistency.append("Name")
        else:
            discrepancy.append("Name")

        if consistency_phone == 1:
            consistency.append("Mobile")
        else:
            discrepancy.append("Mobile")

        if consistency_email == 1:
            consistency.append("Email")
        else:
            discrepancy.append("Email")

        if consistency_address == 1:
            consistency.append("Address")
        else:
            discrepancy.append("Address")

        if consistency:
            note = f"{', '.join(consistency)} are Consistent while {', '.join(discrepancy)} have Discrepancies."
        else:
            note = f"{', '.join(discrepancy)} have Discrepancies."

        total_consistency = 4
        total_discrepancy = 0
        if name_response.pan_match == True:
            total_consistency += 1
        else:
            total_discrepancy += 1
        if name_response.aadhar_match == True:
            total_consistency += 1
        else:
            total_discrepancy += 1
        if name_response.tax_match == True:
            total_consistency += 1
        else:
            total_discrepancy += 1

        if mobile_response.pan_match == True:
            total_consistency += 1
        else:
            total_discrepancy += 1
        if mobile_response.aadhar_match == True:
            total_consistency += 1
        else:
            total_discrepancy += 1
        if mobile_response.government_match == True:
            total_consistency += 1
        else:
            total_discrepancy += 1

        if email_response.pan_match == True:
            total_consistency += 1
        else:
            total_discrepancy += 1
        if email_response.aadhar_match == True:
            total_consistency += 1
        else:
            total_discrepancy += 1
        if email_response.government_match == True:
            total_consistency += 1
        else:
            total_discrepancy += 1

        if address_response.pan_match == True:
            total_consistency += 1
        else:
            total_discrepancy += 1
        if address_response.aadhar_match == True:
            total_consistency += 1
        else:
            total_discrepancy += 1
        if address_response.government_match == True:
            total_consistency += 1
        else:
            total_discrepancy += 1
        contact_consistency = round(float((total_consistency / 16) * 100), 0)
        if contact_consistency < 75:
            meter = "Bad"
        elif 75 <= contact_consistency < 85:
            meter = "Concern"
        elif 85 <= contact_consistency < 95:
            meter = "Good"
        else:
            meter = "Excellent"

        index_response = Index(
            contact_consistency=contact_consistency,
            consistency=total_consistency,
            discrepancy=total_discrepancy,
            meter=meter,
            remarks=note,
        )
        # Handling existing & Current Document
        existing_document = contact_info.objects(application_id=id, page_id=1).first()
        if existing_document:
            existing_document.delete()

        info_document = contact_info(
            application_id = id,
            page_id = 1,
            name=name_response,
            mobile=mobile_response,
            email=email_response,
            address=address_response,
            index=index_response,
        )
        info_document.save()

    except Exception as e:
        send_email(500, "Report_contact_information")
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(detail="Internal Server Error", status_code=500)
