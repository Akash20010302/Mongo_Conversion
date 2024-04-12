from mongoengine import Document, ListField, IntField, StringField
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")




class CareerDetailsResponse(Document):
    application_id = IntField(required=True)
    page_id = IntField(required=True, default=1)
    all_experiences_govt_docs = ListField()
    all_experiences_tenure = ListField()
    good_to_know = IntField()
    red_flag = IntField()
    discrepancies = IntField()
    highlight = ListField()
    career_score = IntField()
    career_score_text = StringField()
    meta = {
        'indexes':[
            {'fields':['application_id', 'page_id'], 'unique': True}
        ]
    }
