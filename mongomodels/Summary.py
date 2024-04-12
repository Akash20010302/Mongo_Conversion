from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField, StringField, EmailField, IntField, FloatField, ListField, DateTimeField, DictField, BooleanField, URLField, ReferenceField
import datetime
from db.db import get_db_analytics, get_db_backend
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")


class SummaryBasicInfo(Document):
    firstName = StringField(default='N/A')
    middleName = StringField(default='N/A')
    lastName = StringField(default='N/A')
    phone = StringField(default='N/A')
    email = EmailField(default='N/A')
    age = IntField(default='N/A')
    gender = StringField(default='N/A')
    marital_status = StringField(default='N/A')
    city = StringField(default='N/A')
    role = StringField(default='N/A')
    company = StringField(default='N/A')
    legalname = StringField(default='N/A')
    report_date = DateTimeField(default=lambda: datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30))

    class Config:
        from_attributes = True

class Ideal_ctc(EmbeddedDocument):
    lower = IntField()
    upper = IntField()

class offered_past_ctc_summary(EmbeddedDocument):
    declared_past_ctc = IntField()
    declared_past_ctc_remark = StringField()
    most_likely_past_ctc = IntField()
    highlight_1 = StringField()
    offered_ctc = IntField()
    offered_ctc_remark = StringField()
    ideal_ctc_band = EmbeddedDocumentField(Ideal_ctc)
    highlight_2 = StringField()

class declared_household_income_summary(EmbeddedDocument):
    candidate_ctc = IntField()
    spouse_ctc = IntField()
    household_ctc = IntField()
    mostlikely_expense = IntField()
    highlight = StringField()

class Mobile_(EmbeddedDocument):
    remark = StringField()
    issue = StringField()

class Email_(EmbeddedDocument):
    remark = StringField()
    issue = StringField()

class Address_(EmbeddedDocument):
    remark = StringField()
    issue = StringField()

class Name_(EmbeddedDocument):
    remark = StringField()
    issue = StringField()

class contact_information(EmbeddedDocument):
    name = EmbeddedDocumentField(Name_)
    mobile = EmbeddedDocumentField(Mobile_)
    email = EmbeddedDocumentField(Email_)
    address = EmbeddedDocumentField(Address_)
    highlight_1 = StringField()
    highlight_2 = StringField()
        
class identity_info(EmbeddedDocument):
    pan_issue = IntField()
    aadhar_issue = IntField()
    highlight = StringField()
    pan_text = StringField()
    aadhar_text = StringField()
        
class IncomePosition(EmbeddedDocument):
    total_income = IntField()
    salary_income = IntField()
    salary_text = StringField()
    salary_percentage = IntField()
    business_income = IntField()
    business_percentage = IntField()
    overseas_income = IntField()
    overseas_percentage = IntField()
    personal_income = IntField()
    personal_income_percentage = IntField()
    other_income = IntField()
    other_income_percentage = IntField()
    highlights = ListField(StringField())
    
class ExperienceSummary(EmbeddedDocument):
    total_experience = IntField()
    median_tenure = FloatField()
    median_tenure_text = StringField()
    dual_employment = IntField()
    dual_employment_text = StringField()
    overlapping_contract = IntField()
    overlapping_contract_text = StringField()
    tenure_highlights = StringField()
    exp_highlights = ListField(StringField())
        
class Summary(Document):
    application_id = StringField(required=True)
    page_id = IntField(required=True, default=1)
    income_position = EmbeddedDocumentField(IncomePosition)
    experience_summary = EmbeddedDocumentField(ExperienceSummary)
    ctc_summary = EmbeddedDocumentField(offered_past_ctc_summary)
    household_income_summary = EmbeddedDocumentField(declared_household_income_summary)
    contact = EmbeddedDocumentField(contact_information)
    identity = EmbeddedDocumentField(identity_info)
    meta = {
        'indexes':[
            {'fields':['application_id', 'page_id'], 'unique': True}
        ]
    }

class AsyncGenerator:
    def __init__(self):
        self.backend = get_db_backend()
        self.analytics = get_db_analytics()
