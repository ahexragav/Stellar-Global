
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional,Any

    
class RegisterUser(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    password: Optional[str] = None  # Optional for OAuth users
    is_staff: bool = False
    is_active: bool = True
    auth_provider: str
    phone_number: Optional[str] = None
    role: str = "user"

    @validator('password')
    def validate_password(cls, v):
        if v is None:  # Allow password to be None for OAuth users
            return v
        # Minimum 8 characters, should include at least one number and one special character
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char in '!@#$%^&*()_+{}:"<>?|[];\',./' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

    class Config:
        orm_mode = True  # Allows the model to be serialized from SQLAlchemy ORM objects
# class RegisterUser(BaseModel):
#     name: Optional[str]
#     email: Optional[EmailStr]
#     password:  Optional[str]
#     is_staff: Optional[bool] = False
#     is_active: Optional[bool]= True
#     auth_provider: Optional[str]
#     phone_number: Optional[str]
#     @validator('password')
#     def validate_password(cls, v):
#         # Minimum 8 characters, should include at least one number and one special character
#         if len(v) < 8:
#             raise ValueError('Password must be at least 8 characters long')
#         if not any(char.isdigit() for char in v):
#             raise ValueError('Password must contain at least one number')
#         if not any(char in '!@#$%^&*()' for char in v):
#             raise ValueError('Password must contain at least one special character')
#         return v

#     class Config:
#         orm_mode = True
class LoginSchema(BaseModel):
    email: str
    password: str
    remember_me: bool = False 






class ResponseSchema(BaseModel):
    data: Optional[Any] = None  # The data field can hold any type of data
    message: str  # A message to provide additional context

    class Config:
        orm_mode = True  # This allows compatibility with SQLAlchemy models


# Schema for requesting a password reset (sending OTP)
class ForgotPasswordRequest(BaseModel):
    email: EmailStr  # The email for password reset request

    class Config:
        orm_mode = True


# Schema for verifying password reset token and resetting password
class ResetPasswordRequest(BaseModel):
    token: str  # The reset token provided
    new_password: str  # New password to be set
    otp: str  # otp

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char in '!@#$%^&*()' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

    class Config:
        orm_mode = True

class PasswordResetResponse(BaseModel):
    message: str
    token: str


class VerifyOTPSchema(BaseModel):
    otp: str = Field(..., description="The OTP received by the user via email for password reset")

    class Config:
        schema_extra = {
            "example": {
                "otp": "123456"
            }
        }
#
class SetNewPasswordSchema(BaseModel):
    email: EmailStr = Field(..., description="The email of the user")
    new_password: str = Field(..., description="New password to be set")
    confirm_password: str = Field(..., description="Confirm the new password")

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char in '!@#$%^&*()' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

    class Config:
        orm_mode = True