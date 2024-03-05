import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")

class epfo_get_kyc_details(SQLModel, table=True):
    application_id : int = Field(primary_key=True) 
    client_id : str 
    pf_uan : Optional[str]   
    kyc_details_pan_number : Optional[str]  
    kyc_details_aadhaar_number : Optional[str]  
    kyc_details_mobile_number : Optional[str]  
    kyc_details_email : Optional[str]  
    kyc_details_full_name : Optional[str]  
    kyc_details_relation_name : Optional[str]  
    kyc_details_relation_type : Optional[str]  
    kyc_details_dob : Optional[datetime.date] 
    kyc_details_doj_epf : Optional[datetime.date] 
    kyc_details_doj_eps : Optional[datetime.date] 
    kyc_details_account_number : Optional[str]  
    kyc_details_ifsc : Optional[str]  
    kyc_details_details : Optional[str] 
    
    class Config:
        from_attributes = True
        
class itr_download_profile(SQLModel,table=True):
    application_id: int = Field(primary_key=True)
    client_id : str 
    activity_datetime : datetime.datetime
    status_code: Optional[int] 
    success : Optional[bool] 
    message : Optional[str]
    message_code : Optional[str] 
    address_country : Optional[str] 
    address_door_number : Optional[str] 
    address_street : Optional[str] 
    address_pin_code : int
    address_zip_code : Optional[str] 
    address_locality : Optional[str] 
    address_post_office : Optional[str] 
    address_city : Optional[str] 
    address_state : Optional[str] 
    pan_pan : Optional[str] 
    pan_name : Optional[str] 
    pan_dob_date : Optional[datetime.date] 
    pan_gender : Optional[str] 
    pan_category : Optional[str] 
    pan_address : Optional[str] 
    pan_status : Optional[str] 
    pan_indian_citizen : Optional[str] 
    contact_resident : Optional[bool]
    contact_non_resident : Optional[bool] 
    contact_primary_mobile : Optional[str] 
    contact_primary_mobile_belongs_to : Optional[str] 
    contact_primary_email : Optional[str] 
    contact_primary_email_belongs_to : Optional[str] 
    contact_secondary_mobile : Optional[str] 
    contact_secondary_mobile_belongs_to : Optional[str]  
    contact_secondary_email : Optional[str]  
    contact_secondary_email_belongs_to : Optional[str]  
    jurisdiction_area_code : Optional[str] 
    jurisdiction_ao_type : Optional[str] 
    jurisdiction_range_code : Optional[int] 
    jurisdiction_ao_number : Optional[int] 
    jurisdiction_jurisdiction : Optional[str] 
    jurisdiction_building_name : Optional[str] 
    jurisdiction_email_id : Optional[str] 
    jurisdiction_ao_building_id : Optional[str] 
    aadhaar_aadhaar_number : Optional[str] 
    aadhaar_aadhaar_status : Optional[str]
    
    class Config:
        from_attributes = True