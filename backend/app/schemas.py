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


class CompanyCreateInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(pattern="^[a-z0-9-]{3,80}$")
    mode: str = Field(pattern="^(ip|location)$")
    allowed_cidr: str | None = Field(default=None, max_length=64)
    latitude: str | None = None
    longitude: str | None = None
    radius_meters: int | None = Field(default=None, ge=10, le=100000)
