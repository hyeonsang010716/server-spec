from fastapi import APIRouter, Depends, HTTPException, Query, status
from dependency_injector.wiring import inject, Provide

from app.container import Container
from app.service.user import UserService
from app.database.session import UnitOfWork
from app.schema.user import (
    UserCreateRequest, 
    UserUpdateRequest, 
    UserResponse, 
    UserListResponse,
    SuccessResponse
)
from app.dto.user import UserCreateDTO, UserUpdateDTO

router = APIRouter(prefix="/test", tags=["User-Test"])


@router.post(
    "", 
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="사용자 생성",
    description="새로운 사용자를 생성"
)
@inject
async def create_user(
    user_request: UserCreateRequest,
    user_service: UserService = Depends(Provide[Container.user_service])
) -> UserResponse:
    """사용자 생성"""
    try:
        user_dto = UserCreateDTO(
            email=user_request.email,
            name=user_request.name
        )
        created_user = await user_service.create_user(user_dto)
        return UserResponse(
            email=created_user.email,
            name=created_user.name,
            created_at=created_user.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/controller", 
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="사용자 생성 (컨트롤러 레벨 트랜잭션)",
    description="컨트롤러에서 트랜잭션을 관리하는 새로운 사용자 생성 예시"
)
@inject
async def create_user_controller_transaction(
    user_request: UserCreateRequest,
    user_service: UserService = Depends(Provide[Container.user_service_session]),
    uow: UnitOfWork = Depends(Provide[Container.uow])
) -> UserResponse:
    """사용자 생성 - 컨트롤러 레벨 트랜잭션 관리"""
    try:
        async with uow as session:
            user_dto = UserCreateDTO(
                email=user_request.email,
                name=user_request.name
            )
            
            created_user = await user_service.create_user_with_session(session, user_dto)
            
            return UserResponse(
                email=created_user.email,
                name=created_user.name,
                created_at=created_user.created_at
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/search",
    response_model=UserListResponse,
    summary="사용자 목록 조회",
    description="모든 사용자 목록을 조회합니다. (페이징)"
)
@inject
async def get_users(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 레코드 수"),
    user_service: UserService = Depends(Provide[Container.user_service])
) -> UserListResponse:
    """사용자 목록 조회"""
    try:
        users, total = await user_service.get_all_users(skip=skip, limit=limit)
        user_responses = [
            UserResponse(
                email=user.email,
                name=user.name,
                created_at=user.created_at
            ) for user in users
        ]
        return UserListResponse(users=user_responses, total=total)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/{email}",
    response_model=UserResponse,
    summary="사용자 조회",
    description="이메일로 특정 사용자를 조회"
)
@inject
async def get_user(
    email: str,
    user_service: UserService = Depends(Provide[Container.user_service])
) -> UserResponse:
    """사용자 조회"""
    try:
        user = await user_service.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email} not found"
            )
        return UserResponse(
            email=user.email,
            name=user.name,
            created_at=user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put(
    "/{email}",
    response_model=UserResponse,
    summary="사용자 정보 수정",
    description="특정 사용자의 정보를 수정합니다."
)
@inject
async def update_user(
    email: str,
    user_request: UserUpdateRequest,
    user_service: UserService = Depends(Provide[Container.user_service])
) -> UserResponse:
    """사용자 정보 수정"""
    try:
        user_dto = UserUpdateDTO(name=user_request.name)
        updated_user = await user_service.update_user(email, user_dto)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email} not found"
            )
        return UserResponse(
            email=updated_user.email,
            name=updated_user.name,
            created_at=updated_user.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete(
    "/{email}",
    response_model=SuccessResponse,
    summary="사용자 삭제",
    description="특정 사용자를 삭제합니다."
)
@inject
async def delete_user(
    email: str,
    user_service: UserService = Depends(Provide[Container.user_service])
) -> SuccessResponse:
    """사용자 삭제"""
    try:
        deleted = await user_service.delete_user(email)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email} not found"
            )
        return SuccessResponse(message=f"User with email {email} has been deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )