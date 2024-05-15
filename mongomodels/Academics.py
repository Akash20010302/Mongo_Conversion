from mongoengine import Document, ListField, IntField, StringField
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")




class AcademicDetailsResponse(Document):
    application_id = IntField(required=True)
    candidate_type = StringField(required=True)   # Required = true added
    page_id = IntField(required=True, default=1)
    all_academic_govt_docs = ListField()
    all_academic_tenure = ListField()
    red_flag = IntField()
    discrepancies = IntField()
    highlight = ListField()
    academic_score = IntField()
    academic_score_text = StringField()
    meta = {
        'indexes':[
            {'fields':['application_id', 'page_id'], 'unique': True}
        ]
    }


