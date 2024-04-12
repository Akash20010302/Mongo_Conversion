from mongoengine import connect, Document, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField, StringField, EmailField, IntField, FloatField, ListField, DateTimeField, DictField, BooleanField, URLField, ReferenceField
import datetime
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")



class CompCanList(Document):
    id = IntField(required=True)
    firstName = StringField()
    lastName = StringField()
    role = StringField(default="Candidate")
    email = StringField()
    phone = StringField(min_length=10, max_length=10)
    company = ReferenceField('CompanyList')
    companyid = IntField()
    verified = BooleanField(default=False)
    appactive = BooleanField(default=False)
    createddate = DateTimeField(default=lambda: datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30))
    createdby = IntField()
    updateddate = DateTimeField()
    updatedby = IntField()
    lastlogin = DateTimeField()
    isDeleted = BooleanField(default=False)
    DeletedBy = IntField()
    CanId = IntField()
    candidate = ReferenceField('CandidateUser')
    currentctc = StringField()
    rolebudget = StringField()
    offeredctc = StringField()

    meta = {
        'indexes': [
            {'fields': ['companyid'], 'name': 'idx_comcanlist_companyid'},
            {'fields': ['CanId'], 'name': 'idx_comcanlist_CanId'},
            {'fields': ['id'], 'name': 'idx_comcanlist_id'}
        ]
    }
