from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class UserCreateRequest(BaseModel):
    """User 생성 요청 스키마"""
    email: EmailStr = Field(..., description="사용자 이메일", example="user@example.com")
    name: str = Field(..., min_length=1, max_length=255, description="사용자 이름", example="홍길동")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "홍길동"
            }
        }


class UserUpdateRequest(BaseModel):
    """User 업데이트 요청 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="사용자 이름", example="김철수")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "김철수"
            }
        }


class UserResponse(BaseModel):
    """User 응답 스키마"""
    email: EmailStr = Field(..., description="사용자 이메일")
    name: str = Field(..., description="사용자 이름")
    created_at: datetime = Field(..., description="생성 일시")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "홍길동",
                "created_at": "2024-01-01T00:00:00"
            }
        }


class UserListResponse(BaseModel):
    """User 목록 응답 스키마"""
    users: List[UserResponse] = Field(..., description="사용자 목록")
    total: int = Field(..., description="전체 사용자 수")

    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "email": "user1@example.com",
                        "name": "홍길동",
                        "created_at": "2024-01-01T00:00:00"
                    },
                    {
                        "email": "user2@example.com", 
                        "name": "김철수",
                        "created_at": "2024-01-02T00:00:00"
                    }
                ],
                "total": 2
            }
        }


class SuccessResponse(BaseModel):
    """성공 응답 스키마"""
    message: str = Field(..., description="성공 메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "성공적으로 처리되었습니다."
            }
        }