from mongoengine import Document, ListField, StringField, FloatField, IntField, DictField, EmbeddedDocumentField, EmbeddedDocumentListField, EmbeddedDocument
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")




class MonthlyIncome(EmbeddedDocument):
    month = StringField(required=True)
    salary_amount = FloatField(required=True)
    other_income_amount = FloatField(required=True)
    overseas_income_amount = FloatField(required=True)
    business_income_amount = FloatField(required=True)
    personal_income_amount = FloatField(required=True)
    total_income_amount = FloatField(required=True)

class IncomeSources(EmbeddedDocument):
    salary_sources = ListField(StringField())
    other_income_sources = ListField(StringField())
    business_income_sources = ListField(StringField())
    personal_income_sources = ListField(StringField())
    overseas_income_sources = ListField(StringField())


class IncomeSummaryResponse(Document):
    application_id = StringField(required=True)
    page_id = IntField(required=True, default=True)
    number_of_salary_accounts = IntField(required=True)
    number_of_other_income_accounts = IntField(required=True)
    number_of_personal_savings_account = IntField(required=True)
    number_of_business_income_accounts = IntField(required=True)
    number_of_overseas_acount = IntField(required=True)
    red_flag = IntField(required=True)
    total_number_of_income_sources = IntField(required=True)
    total_salary_received = FloatField(required=True)
    total_other_income = FloatField(required=True)
    total_personal_savings = FloatField(required=True)
    total_overseas_income = FloatField(required=True)
    total_business_income = FloatField(required=True)
    total_income = FloatField(required=True)
    monthly_income_details = EmbeddedDocumentListField(MonthlyIncome)
    income_sources = EmbeddedDocumentField(IncomeSources)
    income_percentage = DictField()
    income_score_percentage = IntField(required=True)
    income_score_text = StringField(required=True)
    highlights = ListField(StringField())
    income_highlights = ListField(StringField())
    distribution_highlights = ListField(StringField())
    meta = {
        'indexes':[
            {'fields':['application_id', 'page_id'], 'unique': True}
        ]
    }
