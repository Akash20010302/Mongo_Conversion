from mongoengine import connect, Document, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField, StringField, EmailField, IntField, FloatField, ListField, DateTimeField, DictField, BooleanField, URLField, ReferenceField
import datetime
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")





class CandidateUser(Document):
    id = IntField(primary_key=True)
    firstName = StringField()
    lastName = StringField()
    role = StringField(default='Candidate')
    email = StringField(index=True)
    phone = StringField(min_length=10, max_length=10, index=True)
    password = StringField()
    createddate = DateTimeField(default=lambda: datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30))
    createdby = IntField()
    updateddate = DateTimeField()
    updatedby = IntField()
    lastlogin = DateTimeField()
    isDeleted = BooleanField(default=False)
    DeletedBy = IntField()

    meta = {
        'indexes': [
            {'fields': ['email'], 'name': 'idx_candidateuser_email'},
            {'fields': ['phone'], 'name': 'idx_candidateuser_phone'},
            {'fields': ['id'], 'name': 'idx_candidateuser_id'}
        ]
    }
