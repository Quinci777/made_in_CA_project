from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    username: str
    email: str

class UserInDB(User):
    hashed_password: str

class UserInResponse(User):
    pass

class UserLogin(BaseModel):
    username: str
    password: str
