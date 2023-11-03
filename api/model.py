from mongoengine import Document, StringField, ListField

class User(Document):
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    roles = StringField()
    Active_Status=StringField()
    department=StringField()