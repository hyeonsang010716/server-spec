from fastapi import APIRouter

from app.api.v1.user import register

router = APIRouter(prefix="/user")

router.include_router(register.router)