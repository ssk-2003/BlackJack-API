from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["player1"])
    email: EmailStr = Field(..., examples=["player1@example.com"])
    password: str = Field(..., min_length=6, examples=["secretpassword"])

class UserLogin(BaseModel):
    username: str = Field(..., examples=["player1"])
    password: str = Field(..., examples=["secretpassword"])

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    chips_balance: int
