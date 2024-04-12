from mongoengine import connect, Document, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField, StringField, EmailField, IntField, FloatField, ListField, DateTimeField, DictField, BooleanField, URLField, ReferenceField
import datetime
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")



class CompanyList(Document):
    id = IntField(required=True)
    legalname = StringField()
    displayname = StringField()
    pincode = StringField()
    state = StringField()
    city = StringField()
    address1 = StringField()
    address2 = StringField()
    numberofemployees = StringField()
    industryvertical = StringField()
    status = StringField(default='Active')
    createddate = DateTimeField(default=lambda: datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30))
    createdby = IntField()
    updateddate = DateTimeField()
    updatedby = IntField()
    lastlogin = DateTimeField()
    isDeleted = BooleanField(default=False)
    DeletedBy = IntField()

    meta = {
        'indexes': [
            {'fields': ['id'], 'name': 'idx_companylist_id'}
        ]
    }
