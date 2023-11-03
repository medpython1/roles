from pydantic import BaseModel
from typing import Optional
class user(BaseModel):
    email:str
    password:str
    roles:str
    department:str
class TokenData(BaseModel):
    email: Optional[str] = None