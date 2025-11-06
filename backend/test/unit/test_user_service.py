import pytest
from unittest.mock import AsyncMock

from app.dto.user import UserUpdateDTO, UserDTO


@pytest.mark.unit
class TestUserServiceDI:
    """UserService DI 기반 단위 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self, user_service_with_di, sample_user_create_dto, sample_user_dto, sample_user_update_dto):
        """각 테스트 메서드 실행 전 설정"""
        self.user_service, repo_mapping = user_service_with_di
        
        self.mock_repository = repo_mapping["UserRepository"]
        
        self.sample_user_create_dto = sample_user_create_dto
        self.sample_user_dto = sample_user_dto
        self.sample_user_update_dto = sample_user_update_dto

    async def test_create_user_success(self):
        """사용자 생성 성공 테스트 - DI 패턴"""
        # Given
        self.mock_repository.get_by_email.return_value = None  # 기존 사용자 없음
        self.mock_repository.create.return_value = self.sample_user_dto
        
        # When
        result = await self.user_service.create_user(self.sample_user_create_dto)
        
        # Then
        assert result == self.sample_user_dto
        self.mock_repository.get_by_email.assert_called_once_with(self.sample_user_create_dto.email)
        self.mock_repository.create.assert_called_once_with(self.sample_user_create_dto)

    async def test_create_user_already_exists(self):
        """사용자 생성 실패 - 이미 존재하는 이메일"""
        # Given
        self.mock_repository.get_by_email.return_value = self.sample_user_dto  # 이미 존재
        
        # When & Then
        with pytest.raises(ValueError, match="already exists"):
            await self.user_service.create_user(self.sample_user_create_dto)
        
        self.mock_repository.get_by_email.assert_called_once_with(self.sample_user_create_dto.email)
        self.mock_repository.create.assert_not_called()

    async def test_create_user_with_session_success(self):
        """세션을 사용한 사용자 생성 성공 테스트"""
        # Given
        mock_session = AsyncMock()
        self.mock_repository.get_by_email.return_value = None
        self.mock_repository.create.return_value = self.sample_user_dto
        
        # When
        result = await self.user_service.create_user_with_session(
            mock_session, self.sample_user_create_dto
        )
        
        # Then
        assert result == self.sample_user_dto
        self.mock_repository.get_by_email.assert_called_once_with(self.sample_user_create_dto.email)
        self.mock_repository.create.assert_called_once_with(self.sample_user_create_dto)

    async def test_get_user_by_email_found(self):
        """이메일로 사용자 조회 성공 테스트"""
        # Given
        email = "test@example.com"
        self.mock_repository.get_by_email.return_value = self.sample_user_dto
        
        # When
        result = await self.user_service.get_user_by_email(email)
        
        # Then
        assert result == self.sample_user_dto
        self.mock_repository.get_by_email.assert_called_once_with(email)

    async def test_get_user_by_email_not_found(self):
        """이메일로 사용자 조회 실패 - 사용자 없음"""
        # Given
        email = "nonexistent@example.com"
        self.mock_repository.get_by_email.return_value = None
        
        # When
        result = await self.user_service.get_user_by_email(email)
        
        # Then
        assert result is None
        self.mock_repository.get_by_email.assert_called_once_with(email)

    async def test_get_all_users_success(self, sample_user_list):
        """모든 사용자 조회 성공 테스트"""
        # Given
        skip, limit = 0, 10
        total_count = 2
        self.mock_repository.get_all.return_value = sample_user_list
        self.mock_repository.count_all.return_value = total_count
        
        # When
        users, total = await self.user_service.get_all_users(skip=skip, limit=limit)
        
        # Then
        assert users == sample_user_list
        assert total == total_count
        self.mock_repository.get_all.assert_called_once_with(skip=skip, limit=limit)
        self.mock_repository.count_all.assert_called_once()

    async def test_get_all_users_default_params(self, sample_user_list):
        """모든 사용자 조회 - 기본 파라미터 테스트"""
        # Given
        self.mock_repository.get_all.return_value = sample_user_list
        self.mock_repository.count_all.return_value = 2
        
        # When
        users, total = await self.user_service.get_all_users()
        
        # Then
        self.mock_repository.get_all.assert_called_once_with(skip=0, limit=100)

    async def test_update_user_success(self):
        """사용자 업데이트 성공 테스트"""
        # Given
        email = "test@example.com"
        updated_user = UserDTO(
            email=email,
            name="Updated User",
            created_at=self.sample_user_dto.created_at
        )
        
        self.mock_repository.get_by_email.return_value = self.sample_user_dto
        self.mock_repository.update.return_value = updated_user
        
        # When
        result = await self.user_service.update_user(email, self.sample_user_update_dto)
        
        # Then
        assert result == updated_user
        self.mock_repository.get_by_email.assert_called_once_with(email)
        self.mock_repository.update.assert_called_once_with(email, self.sample_user_update_dto)

    async def test_update_user_not_found(self):
        """사용자 업데이트 실패 - 사용자 없음"""
        # Given
        email = "nonexistent@example.com"
        self.mock_repository.get_by_email.return_value = None
        
        # When & Then
        with pytest.raises(ValueError, match="not found"):
            await self.user_service.update_user(email, self.sample_user_update_dto)
        
        self.mock_repository.get_by_email.assert_called_once_with(email)
        self.mock_repository.update.assert_not_called()

    async def test_update_user_no_data(self):
        """사용자 업데이트 실패 - 업데이트할 데이터 없음"""
        # Given
        email = "test@example.com"
        empty_update_dto = UserUpdateDTO()
        
        self.mock_repository.get_by_email.return_value = self.sample_user_dto
        
        # When & Then
        with pytest.raises(ValueError, match="No data provided"):
            await self.user_service.update_user(email, empty_update_dto)
        
        self.mock_repository.get_by_email.assert_called_once_with(email)
        self.mock_repository.update.assert_not_called()

    async def test_delete_user_success(self):
        """사용자 삭제 성공 테스트"""
        # Given
        email = "test@example.com"
        self.mock_repository.get_by_email.return_value = self.sample_user_dto
        self.mock_repository.delete.return_value = True
        
        # When
        result = await self.user_service.delete_user(email)
        
        # Then
        assert result is True
        self.mock_repository.get_by_email.assert_called_once_with(email)
        self.mock_repository.delete.assert_called_once_with(email)

    async def test_delete_user_not_found(self):
        """사용자 삭제 실패 - 사용자 없음"""
        # Given
        email = "nonexistent@example.com"
        self.mock_repository.get_by_email.return_value = None
        
        # When & Then
        with pytest.raises(ValueError, match="not found"):
            await self.user_service.delete_user(email)
        
        self.mock_repository.get_by_email.assert_called_once_with(email)
        self.mock_repository.delete.assert_not_called()