from datetime import datetime
from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, ListField, StringField, IntField, FloatField, DateTimeField, DictField
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")


class DateEmailTuple(EmbeddedDocument):
    date = DateTimeField(default=datetime.date)
    email = StringField(required=True)
    # a1 = DictField(field=(DateTimeField(), StringField()))

class DatePhoneTuple(EmbeddedDocument):
    date = DateTimeField(default=datetime.date)    
    phone = StringField(required=True)
    # a2 = DictField(field=(DateTimeField(), StringField()))

class DateAddressTuple(EmbeddedDocument):
    date = DateTimeField(default=datetime.date)
    address = StringField(required=True)
    # a3 = DictField(field=(DateTimeField(), StringField()))



class Enquiries(EmbeddedDocument):
    queries_last_1_month = IntField()
    queries_last_3_months = IntField()
    queries_last_6_months = IntField()
    queries_last_12_months = IntField()
    queries_last_24_months = IntField()

class tradeline(EmbeddedDocument):
    count = IntField()
    balance = IntField()
    high_credit = IntField()
    credit_limit = IntField()
    past_due = IntField()

class CombinedResponseModel(Document):
    application_id = StringField(required=True)
    page_id = IntField(required=True, default=1)
    active_accounts = ListField(StringField())
    enquiries = EmbeddedDocumentField(Enquiries)
    active_account_count = IntField()
    number_of_closed_accounts = IntField()
    total_balance = FloatField()
    total_credit_limit = FloatField()
    total_past_due = FloatField()
    credit_score = IntField()
    tradeline_summary_installment = EmbeddedDocumentField(tradeline)
    tradeline_summary_open = EmbeddedDocumentField(tradeline)
    tradeline_summary_close = EmbeddedDocumentField(tradeline)
    tradeline_summary_total = EmbeddedDocumentField(tradeline)    
    phone_numbers = ListField(EmbeddedDocumentField(DatePhoneTuple))
    addresses = ListField(EmbeddedDocumentField(DateAddressTuple))
    email_addresses = ListField(EmbeddedDocumentField(DateEmailTuple))
    # phone_numbers = ListField()
    # addresses = ListField()
    # email_addresses = ListField()
    # phone_numbers = ListField(ListField(DateTimeField(), StringField()))
    # addresses = ListField(ListField(DateTimeField(), StringField()))
    # email_addresses = ListField(ListField(DateTimeField(), StringField()))
    
    # phone_numbers = ListField(DictField(required=True), default=list)
    # addresses = ListField(DictField(required=True), default=list)
    # email_addresses = ListField(DictField(required=True), default=list)
    score_factors = ListField(StringField())
    meta = {
        'indexes':[
            {'fields':['application_id', 'page_id'], 'unique': True}
        ]
    }

