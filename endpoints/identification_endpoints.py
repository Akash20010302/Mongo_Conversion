from fastapi import APIRouter, HTTPException
from loguru import logger
from starlette.status import HTTP_404_NOT_FOUND,HTTP_400_BAD_REQUEST
from auth.auth import AuthHandler
from repos.form_repos import get_identification
from tools.file_manager import download_file_from_s3, encode_file_to_base64, parse_s3_url

identification_router = APIRouter()
auth_handler = AuthHandler()

@identification_router.get("/identification/{id}", tags=['Identification'])
async def iden_info(id:int):
    aadhardis = pandis =0
    iden = await get_identification(id)
    if iden is None:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,detail="Identification Detail Not Found")
    if iden["Aadhar_Number"] is not None:
        iden["Aadhar_Number_flag"] = True
        if (iden["govt_aadhaar_number"]!=iden["Aadhar_Number"]):
            iden["govt_aadhaar_number_flag"] = False
            aadhardis+=1
        else:
            iden["govt_aadhaar_number_flag"] = True
        if (iden["Aadhar_Number"]!=iden["Extracted_Aadhar_Number"]):
            iden["Extracted_Aadhar_Number_flag"] = False
            aadhardis+=1
        else:
            iden["Extracted_Aadhar_Number_flag"] = True
    else:
        iden["Aadhar_Number"] = "N/A"
        iden["Aadhar_Number_flag"] = False
        aadhardis+=1
        if iden["govt_aadhaar_number"] is not None:
            iden["govt_aadhaar_number_flag"] = True
            if(iden["govt_aadhaar_number"]!=iden["Extracted_Aadhar_Number"]):
                    iden["Extracted_Aadhar_Number_flag"] = False
                    aadhardis+=1
            else:
                iden["Extracted_Aadhar_Number_flag"] = True
        else:
            iden["govt_aadhaar_number"] = "N/A"
            iden["govt_aadhaar_number_flag"] = False
            iden["Extracted_Aadhar_Number_flag"] = True if iden["Extracted_Aadhar_Number"] is not None else False
            if iden["Extracted_Aadhar_Number"] == False:
                aadhardis+=1
                iden["Extracted_Aadhar_Number"] = "N/A"
                
    if iden["Pan_Number"] is not None:
        iden["Pan_Number_flag"] = True
        if (iden["govt_pan_number"]!=iden["Pan_Number"]):
            iden["govt_pan_number_flag"] = False
            pandis+=1
        else:
            iden["govt_pan_number_flag"] = True
        if (iden["Pan_Number"]!=iden["Extracted_Pan_Number"]):
            iden["Extracted_Pan_Number_flag"] = False
            pandis+=1
        else:
            iden["Extracted_Pan_Number_flag"] = True
    else:
        iden["Pan_Number"] = "N/A"
        iden["Pan_Number_flag"] = False
        pandis+=1
        if iden["govt_pan_number"] is not None:
            iden["govt_pan_number_flag"] = True
            if(iden["govt_pan_number"]!=iden["Extracted_Pan_Number"]):
                    iden["Extracted_Pan_Number_flag"] = False
                    pandis+=1
            else:
                iden["Extracted_Pan_Number_flag"] = True
        else:
            iden["govt_pan_number"] = "N/A"
            iden["govt_pan_number_flag"] = False
            iden["Extracted_Pan_Number_flag"] = True if iden["Extracted_Pan_Number"] is not None else False
            if iden["Extracted_Pan_Number"] == False:
                pandis+=1
                iden["Extracted_Pan_Number"] = "N/A"
    iden["discrepancy"] = aadhardis + pandis
    iden["consistency"] = 6 - iden["discrepancy"]
    if aadhardis > 0:
        iden["Aadhar_Status"] = "Concern"
    else:
        iden["Aadhar_Status"] = "Verified"
    if pandis > 0:
        iden["Pan_Status"] = "Concern"
    else:
        iden["Pan_Status"] = "Verified"
    iden["meter"] = int(iden["consistency"]/6 *100)
    if iden["discrepancy"] == 0:
        iden["meter_text"]= "Good"
    elif (iden["govt_pan_number_flag"]== True and iden["govt_aadhaar_number_flag"]==True) and (iden["Extracted_Pan_Number_flag"]==False or iden["Extracted_Aadhar_Number_flag"]==False):
        iden["meter_text"]= "Concern"
    else:
        iden["meter_text"]= "Bad"
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