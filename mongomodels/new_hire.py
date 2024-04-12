from mongoengine import Document, EmbeddedDocument, IntField, StringField, EmbeddedDocumentField
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")



class CtcRange(EmbeddedDocument):
    lower = IntField()
    upper = IntField()


class Info(EmbeddedDocument):
    declared_ctc_accuracy = IntField()
    remark = StringField()
    declared_past_ctc = IntField()
    estimated_ctc_range = EmbeddedDocumentField(CtcRange)
    most_likely_past_ctc = IntField()
    gap = IntField()
    highlight = StringField()


class Graph(EmbeddedDocument):
    gross_salary = IntField()
    bonus = IntField()
    provident_fund = IntField()
    possible_ctc_variation = IntField()
    most_likely_ctc = IntField()
    declared_ctc = IntField()
    gap = IntField()
    gap_percentage = IntField()


class Response(Document):
    application_id = IntField(required=True)
    page_id = IntField(required=True, default=1)
    info = EmbeddedDocumentField(Info)
    graph = EmbeddedDocumentField(Graph)
    meta = {
        'indexes':[
            {'fields':['application_id', 'page_id'], 'unique': True}
        ]
    }
