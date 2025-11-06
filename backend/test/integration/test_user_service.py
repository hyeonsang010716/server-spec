import pytest
from sqlalchemy import text

from app.dto.user import UserCreateDTO, UserUpdateDTO, UserDTO


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserServiceIntegration:
    """UserService 통합 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self, user_service_integration, integration_user_create_dto, integration_user_update_dto):
        """각 테스트 메서드 실행 전 설정"""
        self.user_service = user_service_integration
        self.sample_user_create_dto = integration_user_create_dto
        self.sample_user_update_dto = integration_user_update_dto

    async def test_create_user_full_flow(self, test_session):
        """사용자 생성 전체 플로우 통합 테스트"""
        # When - 사용자 생성
        created_user = await self.user_service.create_user(self.sample_user_create_dto)
        
        # Then - 생성된 사용자 검증
        assert created_user.email == self.sample_user_create_dto.email
        assert created_user.name == self.sample_user_create_dto.name
        assert created_user.created_at is not None
        
        # Database에서 직접 확인
        result = await test_session.execute(
            text("SELECT email, name FROM user WHERE email = :email"),
            {"email": self.sample_user_create_dto.email}
        )
        db_user = result.fetchone()
        assert db_user is not None
        assert db_user.email == self.sample_user_create_dto.email
        assert db_user.name == self.sample_user_create_dto.name

    async def test_create_duplicate_user(self, sample_user_in_db):
        """중복 사용자 생성 시도 통합 테스트"""
        # Given - 이미 DB에 사용자 존재
        existing_email = sample_user_in_db.email
        duplicate_user_dto = UserCreateDTO(email=existing_email, name="Duplicate User")
        
        # When & Then - 중복 생성 시도 시 예외 발생
        with pytest.raises(ValueError, match="already exists"):
            await self.user_service.create_user(duplicate_user_dto)

    async def test_get_user_by_email_existing(self, sample_user_in_db):
        """기존 사용자 이메일로 조회 통합 테스트"""
        # When
        found_user = await self.user_service.get_user_by_email(sample_user_in_db.email)
        
        # Then
        assert found_user is not None
        assert found_user.email == sample_user_in_db.email
        assert found_user.name == sample_user_in_db.name

    async def test_get_user_by_email_not_found(self):
        """존재하지 않는 사용자 조회 통합 테스트"""
        # When
        found_user = await self.user_service.get_user_by_email("nonexistent@example.com")
        
        # Then
        assert found_user is None

    async def test_get_all_users_with_pagination(self, multiple_users_in_db):
        """사용자 목록 조회 및 페이징 통합 테스트"""
        # When - 첫 번째 페이지 (2개씩)
        users_page1, total_count = await self.user_service.get_all_users(skip=0, limit=2)
        
        # Then
        assert len(users_page1) == 2
        assert total_count == 3
        
        # When - 두 번째 페이지 (나머지 1개)
        users_page2, total_count = await self.user_service.get_all_users(skip=2, limit=2)
        
        # Then
        assert len(users_page2) == 1
        assert total_count == 3

    async def test_get_all_users_empty_database(self):
        """빈 데이터베이스에서 사용자 목록 조회 통합 테스트"""
        # When
        users, total_count = await self.user_service.get_all_users()
        
        # Then
        assert len(users) == 0
        assert total_count == 0

    async def test_update_user_full_flow(self, sample_user_in_db, test_session):
        """사용자 업데이트 전체 플로우 통합 테스트"""
        # Given
        original_email = sample_user_in_db.email
        update_dto = UserUpdateDTO(name="Updated Integration Name")
        
        # When
        updated_user = await self.user_service.update_user(original_email, update_dto)
        
        # Then
        assert updated_user is not None
        assert updated_user.email == original_email
        assert updated_user.name == "Updated Integration Name"
        
        # Database에서 직접 확인
        result = await test_session.execute(
            text("SELECT name FROM user WHERE email = :email"),
            {"email": original_email}
        )
        db_user = result.fetchone()
        assert db_user.name == "Updated Integration Name"

    async def test_update_nonexistent_user(self):
        """존재하지 않는 사용자 업데이트 시도 통합 테스트"""
        # Given
        nonexistent_email = "nonexistent@example.com"
        update_dto = UserUpdateDTO(name="Should Not Work")
        
        # When & Then
        with pytest.raises(ValueError, match="not found"):
            await self.user_service.update_user(nonexistent_email, update_dto)

    async def test_update_user_with_empty_data(self, sample_user_in_db):
        """빈 데이터로 사용자 업데이트 시도 통합 테스트"""
        # Given
        empty_update_dto = UserUpdateDTO()
        
        # When & Then
        with pytest.raises(ValueError, match="No data provided"):
            await self.user_service.update_user(sample_user_in_db.email, empty_update_dto)

    async def test_delete_user_full_flow(self, sample_user_in_db, test_session):
        """사용자 삭제 전체 플로우 통합 테스트"""
        # Given
        user_email = sample_user_in_db.email
        
        # When
        deletion_result = await self.user_service.delete_user(user_email)
        
        # Then
        assert deletion_result is True
        
        # Database에서 직접 확인 - 사용자가 삭제되었는지
        result = await test_session.execute(
            text("SELECT COUNT(*) FROM user WHERE email = :email"),
            {"email": user_email}
        )
        count = result.scalar()
        assert count == 0

    async def test_delete_nonexistent_user(self):
        """존재하지 않는 사용자 삭제 시도 통합 테스트"""
        # Given
        nonexistent_email = "nonexistent@example.com"
        
        # When & Then
        with pytest.raises(ValueError, match="not found"):
            await self.user_service.delete_user(nonexistent_email)

    async def test_create_user_with_session_full_flow(self, test_session):
        """세션 기반 사용자 생성 전체 플로우 통합 테스트"""
        # Given
        create_dto = UserCreateDTO(email="session@example.com", name="Session User")
        
        # When
        created_user = await self.user_service.create_user_with_session(test_session, create_dto)
        await test_session.commit()
        
        # Then
        assert created_user.email == create_dto.email
        assert created_user.name == create_dto.name
        
        # Database에서 직접 확인
        result = await test_session.execute(
            text("SELECT email, name FROM user WHERE email = :email"),
            {"email": create_dto.email}
        )
        db_user = result.fetchone()
        assert db_user is not None

    async def test_multiple_user_creation(self):
        """여러 사용자 생성 시나리오 통합 테스트"""
        # Given
        user1_dto = UserCreateDTO(email="concurrent1@example.com", name="Concurrent User 1")
        user2_dto = UserCreateDTO(email="concurrent2@example.com", name="Concurrent User 2")
        
        # When - 여러 사용자 생성
        user1 = await self.user_service.create_user(user1_dto)
        user2 = await self.user_service.create_user(user2_dto)
        results = [
            user1,
            user2,
        ]
        
        # Then - 두 사용자 모두 성공적으로 생성
        assert len(results) == 2
        assert all(isinstance(result, UserDTO) for result in results)
        assert results[0].email == user1_dto.email
        assert results[1].email == user2_dto.email


@pytest.mark.integration
@pytest.mark.slow
class TestUserServiceIntegrationComplexScenarios:
    """복잡한 시나리오의 UserService 통합 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self, user_service_integration):
        self.user_service = user_service_integration

    async def test_bulk_operations_scenario(self, test_session):
        """대량 작업 시나리오 통합 테스트"""
        # Given - 여러 사용자 생성
        user_emails = [f"bulk{i}@example.com" for i in range(10)]
        created_users = []
        
        # When - 대량 사용자 생성
        for i, email in enumerate(user_emails):
            user_dto = UserCreateDTO(email=email, name=f"Bulk User {i}")
            created_user = await self.user_service.create_user(user_dto)
            created_users.append(created_user)
        
        # Then - 모든 사용자가 생성되었는지 확인
        all_users, total_count = await self.user_service.get_all_users(limit=20)
        assert total_count == 10
        assert len(all_users) == 10
        
        # When - 일부 사용자 업데이트
        for i in range(0, 5):
            update_dto = UserUpdateDTO(name=f"Updated Bulk User {i}")
            await self.user_service.update_user(user_emails[i], update_dto)
        
        # When - 일부 사용자 삭제
        for i in range(5, 10):
            await self.user_service.delete_user(user_emails[i])
        
        # Then - 최종 상태 확인
        final_users, final_count = await self.user_service.get_all_users()
        assert final_count == 5
        
        # 업데이트된 사용자들의 이름 확인
        updated_users = {user.email: user for user in final_users}
        for i in range(0, 5):
            user = updated_users[user_emails[i]]
            assert user.name == f"Updated Bulk User {i}"