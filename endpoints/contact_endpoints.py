from fastapi import APIRouter, Depends, HTTPException
from models.Contact_Information import Address, Email, Index, Mobile, Name, contact_info
from sqlalchemy.sql import text
from async_sessions.sessions import get_db, get_db_backend
from sqlalchemy.ext.asyncio import AsyncSession
from tools.contact_tools import check_discrepancy, check_discrepancy_1, check_discrepancy_address

contact_router = APIRouter()

@contact_router.get("/contact_information/{id}", response_model=contact_info,tags=['Contact Information'])
async def get_combined_info(id: int, db_1: AsyncSession = Depends(get_db_backend), db_2: AsyncSession = Depends(get_db)):
    # Fetch data from the first database
    result_1 = await db_1.execute(
        text('SELECT firstName, lastName,phone,email,city '
             'FROM "form" WHERE appid = :id'),  # changed id to appid
        {"id": id}
    )
    contact_info_1 = result_1.fetchone()

    if contact_info_1 is None:
        raise HTTPException(status_code=404, detail=f"Personal information not found for id : {id}")

    result_3 = await db_2.execute(
        text('SELECT "pan_name","contact_primary_mobile","contact_primary_email","address_post_office","address_city","address_state","address_pin_code"'
             'FROM "download_profile" WHERE person_id = :id'),
        {"id": id}
    )
    contact_info_3 = result_3.fetchone()

    if contact_info_3 is None:
        raise HTTPException(status_code=404, detail=f"Personal information not found for id {id}")

    name_flag, pan_match, aadhar_match, tax_match, name_remarks = await check_discrepancy_1(
        f"{contact_info_1[0]} {contact_info_1[1]}", contact_info_3[0], "N/A", contact_info_3[0], "Name")

    mobile_flag, pan_match_mobile, aadhar_match_mobile, government_match_mobile, mobile_remarks = await check_discrepancy(
        contact_info_1[2], contact_info_3[1], "N/A", contact_info_3[1], "Mobile")

    email_flag, pan_match_email, aadhar_match_email, government_match_email, email_remarks = await check_discrepancy(
        contact_info_1[3], contact_info_3[2], "N/A", contact_info_3[2], "Email")

    address_flag, pan_match_address, aadhar_match_address, government_match_address, address_remarks = await check_discrepancy_address(
        contact_info_1[4] if contact_info_1[4] is not None else "N/A", contact_info_3[3], "N/A", contact_info_3[3], "Address")

    name_response = Name(
        provided=f"{contact_info_1[0]} {contact_info_1[1]}",
        Pan=contact_info_3[0],
        Aadhar="N/A",
        Tax=contact_info_3[0],
        flag=name_flag,
        pan_match=pan_match,
        aadhar_match=aadhar_match,
        tax_match=tax_match,
        remarks=name_remarks
    )

    mobile_response = Mobile(
        provided=contact_info_1[2],
        Pan=contact_info_3[1],
        Aadhar="N/A",
        Government= contact_info_3[1],
        flag=mobile_flag,
        pan_match=pan_match_mobile,
        aadhar_match=aadhar_match_mobile,
        government_match=government_match_mobile,
        remarks=mobile_remarks
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
        remarks=email_remarks
    )

    address_response = Address(
        provided=contact_info_1[4] if contact_info_1[4] is not None else "N/A",
        Pan=contact_info_3[3],
        Aadhar="N/A",
        Government=contact_info_3[3],
        flag=address_flag,
        pan_match=pan_match_address,
        aadhar_match=aadhar_match_address,
        government_match=government_match_address,
        remarks=address_remarks
    )

    consistency_name = 1 if name_response.provided == name_response.Pan==name_response.Aadhar == name_response.Tax else 0
    consistency_phone = 1 if mobile_response.provided == mobile_response.Pan == mobile_response.Aadhar == mobile_response.Government else 0
    consistency_email = 1 if email_response.provided == email_response.Pan == email_response.Aadhar == email_response.Government else 0
    consistency_address = 1 if address_response.provided == address_response.Pan ==address_response.Aadhar == address_response.Government else 0

    discrepancy_name = 1 - consistency_name
    discrepancy_phone = 1 - consistency_phone
    discrepancy_email = 1 - consistency_email
    discrepancy_address = 1 - consistency_address

    consistency= []
    discrepancy=[]
    
    
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
        note= f"{', '.join(consistency)} are Consistent while {', '.join(discrepancy)} have Discrepancies."
    else:
        note =f"{', '.join(discrepancy)} have Discrepancies."
    
        
    # Calculate total consistency and discrepancy counts
    total_consistency = consistency_name + consistency_phone + consistency_email + consistency_address
    total_discrepancy = discrepancy_name + discrepancy_phone + discrepancy_email + discrepancy_address

    if total_consistency == 0:
        meter= "Very Low"
    elif total_consistency == 1:
        meter= "Low"
    elif total_consistency == 2:
        meter= "Medium"      
    elif total_consistency == 3:
        meter= "High"
    else:
        meter= "Very High"

    index_response = Index(
        consistency=total_consistency,
        discrepancy=total_discrepancy,
        meter = total_consistency, 
        meter_text = meter,
        remarks=note
    )
    
    return contact_info(
        name=name_response,
        mobile= mobile_response,
        email=email_response,
        address=address_response,
        index=index_response)