from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class RegisterInput(BaseModel):
    email: EmailStr
    username: str = Field(pattern="^[a-z0-9_]{3,32}$")
    phone: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class LoginInput(BaseModel):
    identifier: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordInput(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ProfileUpdateInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class PreferencesInput(BaseModel):
    locale: Literal["fa", "en"]
    theme: Literal["light", "dark", "system"]


class CompanyStatusInput(BaseModel):
    status: Literal["active", "pending_review", "suspended"]


class CompanyUpdateInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    name_en: str | None = Field(default=None, max_length=160)
    industry: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=32)


class OtpRequestInput(BaseModel):
    email: EmailStr
    purpose: Literal["verify_email", "reset_password", "login_2fa"]


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


class AttendancePolicyTestInput(BaseModel):
    ip: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    accuracy_meters: float | None = Field(default=None, ge=0)


class AttendancePolicyUpdateInput(BaseModel):
    mode: str = Field(pattern="^(ip|location)$")
    allowed_cidr: str | None = Field(default=None, max_length=64)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    radius_meters: int | None = Field(default=None, ge=10, le=100000)


class InvitationCreateInput(BaseModel):
    email: EmailStr
    role: str = Field(pattern="^(admin|manager|hr|employee)$")


class MembershipRoleUpdateInput(BaseModel):
    role: str = Field(pattern="^(admin|manager|hr|employee)$")


class BotConfigurationInput(BaseModel):
    mode: str = Field(pattern="^(shared|dedicated)$")
    username: str | None = Field(default=None, max_length=128)
    dedicated_token: str | None = Field(default=None, min_length=20, max_length=256)
