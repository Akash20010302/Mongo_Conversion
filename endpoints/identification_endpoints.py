from fastapi import APIRouter, HTTPException
from loguru import logger
from starlette.status import HTTP_404_NOT_FOUND
from auth.auth import AuthHandler
from repos.form_repos import get_identification
from tools.file_manager import download_file_from_s3, encode_file_to_base64, parse_s3_url

identification_router = APIRouter()
auth_handler = AuthHandler()

@identification_router.get("/identification/{id}", tags=['Identification'])
async def iden_info(id:int):
    pancon = aadharcon = aadhardis = pandis =0
    meter = 1
    iden = await get_identification(id)
    if iden["govt_aadhaar_number"] is not None:
        iden["govt_Aadhar_Number_flag"] = True
        if (iden["govt_aadhaar_number"]!=iden["Aadhar_Number"]):
            iden["Aadhar_Number_flag"] = False
            aadhardis+=1
        else:
            iden["Aadhar_Number_flag"] = True
            aadharcon+=1
            meter+=1
        if (iden["govt_aadhaar_number"]!=iden["Extracted_Aadhar_Number"]):
            iden["Extracted_Aadhar_Number_flag"] = False
            aadhardis+=1
        else:
            iden["Extracted_Aadhar_Number_flag"] = True
            aadharcon+=1
            meter+=1
    else:
        iden["govt_aadhaar_number"] = "N/A"
        iden["govt_Aadhar_Number_flag"] = False
        if(iden["Aadhar_Number"]!=iden["Extracted_Aadhar_Number"]):
                iden["Extracted_Aadhar_Number_flag"] = False
                aadhardis+=1
        else:
            iden["Extracted_Aadhar_Number_flag"] = True
            aadharcon+=1
            meter+=1
    if iden["govt_pan_number"] is not None:
        iden["govt_pan_Number_flag"] = True
        if (iden["govt_pan_number"]!=iden["Pan_Number"]):
            iden["Pan_Number_flag"] = False
            pandis+=1
        else:
            iden["Pan_Number_flag"] = True
            pancon+=1
            meter+=1
        if (iden["govt_pan_number"]!=iden["Extracted_Pan_Number"]):
            iden["Extracted_Pan_Number_flag"] = False
            pandis+=1
        else:
            iden["Extracted_Pan_Number_flag"] = True
            pancon+=1
            meter+=1
    else:
        iden["govt_pan_Number"] = "N/A"
        iden["govt_pan_Number_flag"] = False
        if(iden["Pan_Number"]!=iden["Extracted_Pan_Number"]):
            iden["Extracted_Pan_Number_flag"] = False
            pandis+=1
        else:
            iden["Extracted_Pan_Number_flag"] = True
            pancon+=1
            meter+=1
    iden["consistency"] = aadharcon + pancon
    iden["discrepancy"] = aadhardis + pandis
    if aadhardis > 0:
        iden["Aadhar_Status"] = "Concern"
    else:
        iden["Aadhar_Status"] = "Verified"
    if pandis > 0:
        iden["Pan_Status"] = "Concern"
    else:
        iden["Pan_Status"] = "Verified"
    iden["meter"] = min(5,meter)
    if iden["consistency"] == 0:
        iden["consistency_meter"]= "Very Low"
    elif iden["consistency"] == 1:
        iden["consistency_meter"] = "Low"
    elif iden["consistency"] == 2:
        iden["consistency_meter"] = "Medium"      
    elif iden["consistency"] == 3:
        iden["consistency_meter"]= "High"
    else:
        iden["consistency_meter"]= "Very High"
    if iden["Aadhar_Status"] == "Verified" and iden["Pan_Status"] == "Verified":
        iden["Remarks"] = "Both PAN and AADHAAR are Consistent."
    elif iden["Aadhar_Status"] == "Concern" and iden["Pan_Status"] == "Concern":
        iden["Remarks"] = "Both PAN and AADHAAR have discrepancies."
    elif iden["Aadhar_Status"] == "Verified" and iden["Pan_Status"] == "Concern":
        iden["Remarks"] = "AADHAAR is Consistent while PAN has Discrepancies."
    else:
        iden["Remarks"] = "PAN is Consistent while AADHAAR has Discrepancies."
    if iden is not None:
        for file_key in ['aadharurl', 'panurl']:
            if file_key in iden and iden.get(file_key):
                try:
                    file_buffer = await download_file_from_s3(iden[file_key])
                    encoded_file = await encode_file_to_base64(file_buffer)
                    iden[f"{file_key}_data"] = encoded_file
                except Exception as e:
                    iden[f"{file_key}_data"] = f"File Not Found{e}"
                iden[file_key]= (await parse_s3_url(iden[file_key]))[1].split('/')[-1]
        iden.pop("aadharurl",None)
        iden.pop("panurl",None)
        for key in iden.keys():
            if iden[key]==None:
                iden[key]='N/A'
        return iden
    else:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Page info not found")