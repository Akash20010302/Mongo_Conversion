from mongoengine import connect, Document, BooleanField, StringField, IntField, EmbeddedDocumentField, EmbeddedDocumentListField, EmbeddedDocument
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")



class HouseholdIncomeDocument(EmbeddedDocument):
    candidate_monthly_take = IntField()
    spouse_monthly_take = IntField(default=0)
    total_family_income = IntField()

class InfoDocument(Document):
    application_id = IntField(required=True)
    page_id = IntField(required=True, default=1)
    firstName = StringField()
    middleName = StringField()
    lastName = StringField()
    phone = StringField()
    email = StringField()
    city = StringField(default="N/A")
    gender = StringField()
    dob = StringField()
    age = IntField()
    marital_status = StringField()
    spouse_work_status = StringField(default="N/A")
    spouse_employer = StringField(default="N/A")
    kidsnum = IntField(default=0)
    adultdependents = IntField()
    home = BooleanField()
    car = BooleanField()
    twoWheeler = BooleanField()
    creditCard = BooleanField()
    Loan = BooleanField()
    Investment = BooleanField()
    education = StringField()
    education_institute = StringField(default="N/A")
    location = StringField()
    total_experience = IntField()
    work_industry = StringField(default="N/A")
    skillset = StringField(default="N/A")
    current_role = StringField()
    tenure_last_job = BooleanField()
    household_income = EmbeddedDocumentField(HouseholdIncomeDocument)
    meta = {
        'indexes':[
            {'fields':['application_id', 'page_id'], 'unique': True}
        ]
    }
