from pydantic import BaseModel, EmailStr, Field


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class OtpRequestInput(BaseModel):
    email: EmailStr
    purpose: str = Field(pattern="^(verify_email|reset_password)$")


class OtpVerifyInput(OtpRequestInput):
    code: str = Field(pattern="^\\d{6}$")
    new_password: str | None = Field(default=None, min_length=12, max_length=128)
