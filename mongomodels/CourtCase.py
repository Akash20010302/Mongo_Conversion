from mongoengine import Document, EmbeddedDocument, StringField, IntField, ListField, EmbeddedDocumentField
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")




class CourtCase(EmbeddedDocument):
    # court_case_type = StringField(required=True)
    court_case_type = StringField()
    address = StringField(default="Not Available")
    name = StringField()
    case_year = StringField(default="Not Available")
    court_address = StringField(default="Not Available")
    case_no = StringField(default="Not Available")
    filing_no = StringField(default="Not Available")
    registration_no = StringField(default="Not Available")
    status = StringField(default="Not Available")
    order_summary = StringField(default="Not Available")
    first_hearing = StringField(default="Not Available")
    next_hearing = StringField(default="Not Available")
    decision = StringField(default="Not Available")
    police_station = StringField(default="Not Available")
    case_type = StringField(default="Not Available")
    under_act = StringField(default="Not Available")
    fir_no = StringField(default="Not Available")
    under_section = StringField(default="Not Available")
    case_category = StringField(default="Not Available")

class Index(EmbeddedDocument):
    legal_position = IntField()
    legal_position_text = StringField()
    civil = IntField()
    criminal = IntField()
    highlight = ListField(StringField())

class CourtCaseResponse(Document):
    application_id = IntField(required=True)
    page_id = IntField(required=True, default=1)
    index = EmbeddedDocumentField(Index)
    cases = ListField(EmbeddedDocumentField(CourtCase))
    meta = {
        'indexes':[
            {'fields':['application_id', 'page_id'], 'unique': True}
        ]
    }
