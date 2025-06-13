from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    id: int
    email: EmailStr
    user_name: str

class UserDTO(BaseModel):
    class Config:
        from_attributes = True
    id: int
    user_name: str
    email: str



class UserCreate(BaseModel):
    email: EmailStr 
    user_name: str 
    password: str 
    phone_number: str  



class UserLogin(BaseModel):
    email: EmailStr 
    password: str 