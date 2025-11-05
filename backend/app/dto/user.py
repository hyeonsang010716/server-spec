from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserDTO(BaseModel):
    """User Data Transfer Object"""
    email: EmailStr = Field(..., description="사용자 이메일")
    name: str = Field(..., min_length=1, max_length=255, description="사용자 이름")
    created_at: Optional[datetime] = Field(None, description="등록 시간")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @classmethod
    def from_orm(cls, user_model):
        return cls(
            email=user_model.email,
            name=user_model.name,
            created_at=user_model.created_at
        )


class UserCreateDTO(BaseModel):
    """User Create DTO"""
    email: EmailStr = Field(..., description="사용자 이메일")
    name: str = Field(..., min_length=1, max_length=255, description="사용자 이름")

    class Config:
        from_attributes = True


class UserUpdateDTO(BaseModel):
    """User Update DTO"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="사용자 이름")

    class Config:
        from_attributes = True