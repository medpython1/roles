import os
from fastapi import FastAPI,Request
from mongoengine import *
from qrcode import make as make_qr
from pydantic import BaseModel

app = FastAPI()

# Connect to MongoDB
connect(db="bill_generate", host="13.53.47.2", port=27017)

# Define a MongoDB model
class Item(Document):
    sno=IntField()
    name = StringField(required=True, max_length=100)
    description = StringField(max_length=200)
    path_data=StringField()
    Qr_code=StringField()
class item_create(BaseModel):
    name:str
    description:str


# Directory to store QR codes
QR_CODE_DIR = "./apis/static/qrcodes/"
# Ensure the directory exists
os.makedirs(QR_CODE_DIR, exist_ok=True)

# Route to create an item and generate a QR code
@app.post("/items/")
async def create_item(me:item_create,request: Request):
    # Generate QR code
    qr_code="QR23045{:002d}".format(Item.objects.count() + 1)
    qr_data = f"{qr_code}"
    qr = make_qr(qr_data)
    sno1=Item.objects.count() + 1
    # Save the QR code in the specified directory
    qr_filename = f"{sno1}.png"
    qr_filepath = os.path.join("apis/static/qrcodes/",qr_filename)
    qr.save(qr_filepath)
    if os.path.exists(qr_filepath):
                # Construct the URL to the saved PDF
                base_url = request.base_url
                pdf_return_path = f"{base_url.scheme}://{base_url.netloc}/{qr_filepath}"
    
    create_table=Item(sno=sno1,name=me.name,description=me.description,Qr_code=qr_code,path_data=pdf_return_path).save()
    return {"message": "QR code created successfully", "Path": pdf_return_path}

# Route to get a QR code for a specific item


