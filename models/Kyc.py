from sqlmodel import Field, SQLModel
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")

class Get_Kyc_Details(SQLModel, table=True):
    person_id : str = Field(primary_key=True)
    client_id : str
    pf_uan : str 
    kyc_details_pan_number : str
    kyc_details_aadhaar_number : str 
    kyc_details_mobile_number : str
    kyc_details_email : str
    kyc_details_full_name : str
    kyc_details_relation_name : str
    kyc_details_relation_type : str
    kyc_details_dob : str
    kyc_details_doj_epf : str
    kyc_details_doj_eps : str
    kyc_details_account_number : str
    kyc_details_ifsc : str
    kyc_details_details : str
    
    class Config:
        from_attributes = True