from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, IntField, BooleanField, StringField
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")




class Name(EmbeddedDocument):
    provided = StringField()
    Pan = StringField()
    Aadhar = StringField()
    Tax = StringField()
    flag = BooleanField()
    pan_match = BooleanField()
    aadhar_match = BooleanField()
    tax_match = BooleanField()
    remarks = StringField()

class Mobile(EmbeddedDocument):
    provided = StringField()
    Pan = StringField()
    Aadhar = StringField()
    Government = StringField()
    flag = BooleanField()
    pan_match = BooleanField()
    aadhar_match = BooleanField()
    government_match = BooleanField()
    remarks = StringField()

class Email(EmbeddedDocument):
    provided = StringField()
    Pan = StringField()
    Aadhar = StringField()
    Government = StringField()
    flag = BooleanField()
    pan_match = BooleanField()
    aadhar_match = BooleanField()
    government_match = BooleanField()
    remarks = StringField()

class Address(EmbeddedDocument):
    provided = StringField()
    Pan = StringField()
    Aadhar = StringField()
    Government = StringField()
    flag = BooleanField()
    pan_match = BooleanField()
    aadhar_match = BooleanField()
    government_match = BooleanField()
    remarks = StringField()

class Index(EmbeddedDocument):
    contact_consistency = IntField()
    consistency = IntField()
    discrepancy = IntField()
    meter = StringField()
    remarks = StringField()

class contact_info(Document):
    application_id = IntField(required=True)
    page_id = IntField(required=True, default=1)
    name = EmbeddedDocumentField(Name)
    mobile = EmbeddedDocumentField(Mobile)
    email = EmbeddedDocumentField(Email)
    address = EmbeddedDocumentField(Address)
    index = EmbeddedDocumentField(Index)
    meta = {
        'indexes':[
            {'fields':['application_id', 'page_id'], 'unique': True}
        ]
    }
