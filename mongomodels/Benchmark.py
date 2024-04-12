from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, ListField, FloatField, StringField, IntField, BooleanField
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")




class estimatedExpense(EmbeddedDocument):
    lower = IntField()
    upper = IntField()

class IdealCtcBand(EmbeddedDocument):
    lower = IntField()
    upper = IntField()

class CtcResponse(EmbeddedDocument):
    ctc_benchmark_analysis = ListField()
    offeredctc = StringField()
    ideal_ctc_band = EmbeddedDocumentField(IdealCtcBand)
    past_ctc = StringField()
    change_in_ctc = FloatField()
    ctc_growth = ListField()
    highlight = StringField()

class NewResponse(EmbeddedDocument):
    HouseholdTakeHome = FloatField()
    OtherIncome = FloatField()
    TotalTakeHome = FloatField()
    EMI_CreditCard = FloatField()
    EstimatedExpense = EmbeddedDocumentField(estimatedExpense)
    MostLikelyExpense = IntField()
    E_IRatio = FloatField()

class PreviousResponse(EmbeddedDocument):
    HouseholdTakeHome = FloatField()
    OtherIncome = FloatField()
    TotalTakeHome = FloatField()
    EMI_CreditCard = FloatField()
    EstimatedExpense = EmbeddedDocumentField(estimatedExpense)
    MostLikelyExpense = IntField()
    E_IRatio = FloatField()

class ChangeResponse(EmbeddedDocument):
    HouseholdTakeHome = FloatField()
    OtherIncome = FloatField()
    TotalTakeHome = FloatField()
    EMI_CreditCard = FloatField()
    EstimatedExpense = StringField()
    MostLikelyExpense = IntField()
    E_IRatio = FloatField()

class ExpenseIncomeAnalysis(EmbeddedDocument):
    expense_income_ratio = ListField()
    total_household_income = IntField()
    most_likely_expense = IntField()
    highlights = StringField()
    prev = EmbeddedDocumentField(PreviousResponse)
    new_ = EmbeddedDocumentField(NewResponse)
    change_ = EmbeddedDocumentField(ChangeResponse)

class PayAnalysis(EmbeddedDocument):
    previous_pay = ListField()
    current_offer = ListField()
    highlight_1 = StringField()
    highlight_2 = StringField()

class TenureAnalysis(EmbeddedDocument):
    work_exp = ListField()
    avg_tenure = IntField()
    median_tenure = IntField()
    Risk = StringField()
    remarks = StringField()
    total_exp = FloatField()
    num_of_jobs = IntField()
    calculated_work_exp = FloatField(default=0.0)

class Benchmark(Document):
    application_id = IntField(required=True)
    page_id = IntField(required=True, default=1)
    ctc_offered = EmbeddedDocumentField(CtcResponse)
    pay_analysis = EmbeddedDocumentField(PayAnalysis)
    Expense_income_analysis = EmbeddedDocumentField(ExpenseIncomeAnalysis)
    Tenure_analysis = EmbeddedDocumentField(TenureAnalysis)
    meta = {
        'indexes':[
            {'fields':['application_id', 'page_id'], 'unique': True}
        ]
    }
