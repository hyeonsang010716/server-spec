from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError

from app.database.model.user import User
from app.dto.user import UserCreateDTO, UserUpdateDTO, UserDTO


class UserRepository:
    """User Repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: UserCreateDTO) -> UserDTO:
        """사용자 생성"""
        try:
            user = User(
                email=user_data.email,
                name=user_data.name
            )
            self.session.add(user)
            await self.session.flush()
            await self.session.refresh(user)
            return UserDTO.from_orm(user)
        except IntegrityError:
            await self.session.rollback()
            raise ValueError(f"User with email {user_data.email} already exists")

    async def get_by_email(self, email: str) -> Optional[UserDTO]:
        """이메일로 사용자 조회"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        return UserDTO.from_orm(user) if user else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UserDTO]:
        """모든 사용자 조회 (페이징)"""
        result = await self.session.execute(
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        return [UserDTO.from_orm(user) for user in users]

    async def update(self, email: str, user_data: UserUpdateDTO) -> Optional[UserDTO]:
        """사용자 정보 업데이트"""
        
        update_data = {k: v for k, v in user_data.model_dump().items() if v is not None}
        
        if not update_data:
            return await self.get_by_email(email)

        result = await self.session.execute(
            update(User)
            .where(User.email == email)
            .values(**update_data)
            .returning(User)
        )
        user = result.scalar_one_or_none()
        return UserDTO.from_orm(user) if user else None

    async def delete(self, email: str) -> bool:
        """사용자 삭제"""
        result = await self.session.execute(
            delete(User).where(User.email == email)
        )
        return result.rowcount > 0

    async def exists(self, email: str) -> bool:
        """사용자 존재 여부 확인"""
        result = await self.session.execute(
            select(func.count(User.email)).where(User.email == email)
        )
        count = result.scalar()
        return count > 0

    async def count_all(self) -> int:
        """전체 사용자 수 조회"""
        result = await self.session.execute(select(func.count(User.email)))
        return result.scalar()