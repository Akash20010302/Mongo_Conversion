from mongoengine import connect, Document, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField, StringField, EmailField, IntField, FloatField, ListField, DateTimeField, DictField, BooleanField, URLField, ReferenceField
import datetime
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")




class ApplicationList(Document):
    id = IntField(required=True)
    compid = ReferenceField('CompCanList')
    candidatetype = StringField()
    applicationtype = StringField()
    expiry_date = DateTimeField()
    status = StringField(default="1 - Request Sent")
    createddate = DateTimeField(default=lambda: datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30))
    createdby = IntField()
    updateddate = DateTimeField()
    updatedby = IntField()
    isDeleted = BooleanField(default=False)
    DeletedBy = IntField()
    report = DateTimeField()

    meta = {
        'indexes': [
            {'fields': ['compid'], 'name': 'idx_applicationlist_comcanid'},
            {'fields': ['id'], 'name': 'idx_applicationlist_id'}
        ]
    }
