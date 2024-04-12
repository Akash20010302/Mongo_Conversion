from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField, StringField, EmailField, IntField, FloatField, ListField, DateTimeField, DictField, BooleanField, URLField, ReferenceField
import datetime
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_bert")




class Form(Document):
    id = IntField(required=True)
    appid = IntField(ReferenceField('ApplicationList'))
    app = ReferenceField('ApplicationList', required=False)
    firstName = StringField(required=True)
    middleName = StringField()
    lastName = StringField(required=True)
    phone = StringField()
    email = EmailField()
    dob = StringField()
    age = IntField()
    gender = StringField()
    marital_status = StringField()
    education = StringField()
    experience = IntField()
    city = StringField()
    salary = StringField()
    home = BooleanField(default=False)
    homeLoan = BooleanField(default=False)
    car = BooleanField(default=False)
    carLoan = BooleanField(default=False)
    twoWheeler = BooleanField(default=False)
    twoWheelerLoan = BooleanField(default=False)
    creditCard = BooleanField(default=False)
    personalLoan = BooleanField(default=False)
    stocks = BooleanField(default=False)
    realEstate = BooleanField(default=False)
    spousefirstName = StringField()
    spousemiddleName = StringField()
    spouselastName = StringField()
    spousedob = StringField()
    spouseAge = IntField()
    spouseEducation = StringField()
    spouseExperience = IntField()
    kids = BooleanField(default=False)
    totalkids = IntField()
    adultsdependent = BooleanField(default=False)
    totaladults = IntField()
    panurl = URLField()
    aadharurl = URLField()
    resumeurl = URLField()
    itrusername = StringField()
    itrmessage = StringField()
    uannumber = StringField()
    uanmessage = StringField()
    last_page = IntField()
    formcompletion = BooleanField(default=False)
    isDeleted = BooleanField(default=False)
    DeletedBy = IntField()
    startdate = DateTimeField(default=lambda: datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30))
    agreement = BooleanField(default=False)
    Aadharnum = StringField()
    Pannum = StringField()
    formcompletiondate = DateTimeField()
    Aadhar_Number = StringField()
    Pan_Number = StringField()
    Extracted_Aadhar_Number = StringField()
    Extracted_Pan_Number = StringField()
    report = DateTimeField()
    reset = BooleanField(default=False)

    meta = {
        'indexes': [
            {'fields': ['appid'], 'name': 'idx_form_appid'},
            {'fields': ['id'], 'name': 'idx_form_id'}
        ]
    }
