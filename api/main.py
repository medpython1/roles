from fastapi import FastAPI, Depends, HTTPException,Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
import jwt
from mongoengine import *
import json
from starlette.responses import JSONResponse
from fastapi import File, UploadFile, HTTPException
from typing import List
import base64
from fastapi.staticfiles import StaticFiles

app = FastAPI()
connect(db="Role", host="13.51.159.230", port=27017)
class User(Document):
    email=StringField()
    password=StringField()
    roles=StringField()
    department=StringField()
    Active_Status=StringField()
class UserCreate(BaseModel):
    email:str
    password:str
    roles:str
    department:str
class VideoClip(Document):
    sno=IntField()
    base64_data = StringField(required=True)
    isuue_type=StringField(required=True)
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.mount("/videos_clip", StaticFiles(directory="./api/videos_clip"), name="videos_clip")

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(email, password):
    try:
        user = User.objects(email=email).only('password', 'roles','department').first()
        if user:
            user_dict = json.loads(user.to_json())
            password_check = pwd_context.verify(password, user_dict.get('password'))
            if password_check:
                return user_dict['roles']
        return False
    except User.DoesNotExist:
        return False


def get_password(password):
    return pwd_context.hash(password)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid authentication token")
        token_data = User(email=email)
    except PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid authentication token")
    user = User.objects(email=email).first()
    if user is None:
        raise HTTPException(status_code=400, detail="User not found")
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.Active_Status == "Active":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

## if two or more manager having same access but different departments in that case we use this code##
def get_current_admin(current_user: User = Depends(get_current_user)):
    if  current_user.roles == "admin" and current_user.department not in ["It","Hr"]:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return current_user
def get_current_hr_access(current_user: User = Depends(get_current_user)):
    if not (current_user.Active_Status == "Active" and (current_user.department == "Hr" or current_user.department=="It") and current_user.roles == "Manager"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token")
async def login(from_data: OAuth2PasswordRequestForm = Depends()):
    email = from_data.username
    password = from_data.password
    try:
        roles = authenticate_user(email, password)
        if not roles:
            raise ValueError("Invalid email or password")
        access_token = create_access_token(data={"sub": email, "roles": roles})
        data = {"Error": "False", "Message": "Login successful", "access_token": access_token, "token_type": "bearer"}
        return data
    except ValueError as e:
        data = {
            "Error": "True",
            "Message": str(e)
        }
        return JSONResponse(content=data, status_code=401)


@app.post("/signup")
async def signup(me: UserCreate):
    # , current_user: User = Depends(get_current_admin)
    password = get_password(me.password)
    user = User(email=me.email, password=password, roles=me.roles, department=me.department,Active_Status="Active")
    user.save()
    return {"message": "User created successfully"}
@app.get("/get_data")
def getting_data(current_user: User = Depends(get_current_hr_access)):
    gett_user=User.objects().to_json()
    bey=json.loads(gett_user)
    if bey:
        data=[{"Email":data["email"],"Department":data["department"]} for data in bey]
    return data

class VideoClipResponse(BaseModel):
    base64_data: str
@app.post("/upload/")
async def upload_video_clip(file: UploadFile = File(...),issue_type:str=File(...)):
    content = await file.read()
    base64_data = base64.b64encode(content).decode('utf-8')
    video_clip = VideoClip(sno=VideoClip.objects.count()+1,base64_data=base64_data,isuue_type=issue_type)
    video_clip.save()
    return {"message": "Video clip uploaded successfully."}
import os

VIDEO_CLIPS_FOLDER = "video_clips"

@app.get("/video_clips/")
async def get_video_clips(sno:int,request: Request):
    video_clips = VideoClip.objects(sno=sno)
    if video_clips:
        saved_clips = []
        # Create the folder if it doesn't exist
        for clip in video_clips:
            # Decode Base64 data and save it as a video file
            video_data = base64.b64decode(clip.base64_data)
            pdf_filename = f"{sno}.mp4"
            file_path = os.path.join("api/videos_clip/",pdf_filename)
            base_url = request.base_url
            pdf_return_path = f"{base_url.scheme}://{base_url.netloc}/{file_path}"

            # Save the video file
            with open(file_path, "wb") as video_file:
                video_file.write(video_data)

            # Append the saved file path to the response data
            saved_clips.append({"file_path": pdf_return_path})

        return saved_clips
