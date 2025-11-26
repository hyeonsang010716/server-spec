from typing import Callable
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config.setting import settings
from app.core.logger import get_logger


class BearerTokenAuthMiddleware(BaseHTTPMiddleware):
    """Bearer 토큰 인증 미들웨어"""
    
    EXCLUDED_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/favicon.ico"
    ]
    
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.logger = get_logger("middleware.bearer_auth")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # PROD 환경이 아니거나 ACCESS_TOKEN이 설정되지 않았으면 인증 스킵
        if settings.ENVIRONMENT != "PROD" or not settings.ACCESS_TOKEN:
            return await call_next(request)
        
        # 제외 경로는 인증 스킵
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # Authorization 헤더 확인
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            self.logger.bind(
                request_id=getattr(request.state, "request_id", "unknown"),
                path=request.url.path
            ).warning("Authorization 헤더가 없음")
            return Response(
                content='{"detail":"Authorization header required"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json"
            )
        
        # Bearer 토큰 확인
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
        except ValueError:
            self.logger.bind(
                request_id=getattr(request.state, "request_id", "unknown"),
                path=request.url.path
            ).warning("잘못된 Authorization 헤더 형식")
            return Response(
                content='{"detail":"Invalid authorization header format"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json"
            )
        
        # 토큰 검증
        if token != settings.ACCESS_TOKEN:
            self.logger.bind(
                request_id=getattr(request.state, "request_id", "unknown"),
                path=request.url.path
            ).warning("유효하지 않은 액세스 토큰")
            return Response(
                content='{"detail":"Invalid access token"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json"
            )
        
        return await call_next(request)