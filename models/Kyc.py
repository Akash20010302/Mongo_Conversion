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