import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime
from typing import Optional, List

from app.dto.user import UserDTO, UserCreateDTO, UserUpdateDTO
from app.service.user import UserService
from app.database.session import UnitOfWork
from app.repository.user import UserRepository


""" 
테스트 단위테스트 환경 셋업
"""


@pytest.fixture
def mock_uow():
    """Mock UnitOfWork fixture for unit tests"""
    uow = Mock(spec=UnitOfWork)
    mock_session = AsyncMock()
    
    uow.__aenter__ = AsyncMock(return_value=mock_session)
    uow.__aexit__ = AsyncMock(return_value=None)
    
    return uow


@pytest.fixture
def mock_repository_factory():
    """Factory for creating common mock objects for any Repository class"""
    def _factory(repo_cls, **default_returns):
        mock_repo = AsyncMock(spec=repo_cls)
        # 기본 동작 지정
        for method, value in default_returns.items():
            getattr(mock_repo, method).return_value = value
        return mock_repo
    return _factory


@pytest.fixture
def mock_user_repository(mock_repository_factory):
    """Mock UserRepository fixture for unit tests"""
    return mock_repository_factory(
        UserRepository,
        get_by_email=None,
        get_all=[],
        count_all=0,
        create=None,
        update=None,
        delete=False,
    )


@pytest.fixture
def service_di_factory(monkeypatch):
    """Service DI Factory — allows injecting one or more Repositories into any Service"""
    def _factory(service_cls, service_module_path: str, repo_mapping: dict):
        """
        repo_mapping 예시:
        {
            "UserRepository": mock_user_repository,
            "OrderRepository": mock_order_repository,
        }
        """
        # 여러 Repository 교체
        for repo_cls_name, mock_repo in repo_mapping.items():
            repository_path = f"{service_module_path}.{repo_cls_name}"
            monkeypatch.setattr(repository_path, lambda session, _mock=mock_repo: _mock)

        # transactional 무력화
        def mock_transactional(func):
            async def wrapper(self, *args, **kwargs):
                return await func(self, *args, **kwargs)
            return wrapper

        transactional_path = f"{service_module_path}.transactional"
        monkeypatch.setattr(transactional_path, mock_transactional)

        # UnitOfWork Mock 구성
        mock_uow = Mock()
        mock_session = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_session)
        mock_uow.__aexit__ = AsyncMock(return_value=None)

        # 서비스 인스턴스 생성
        service = service_cls(uow=mock_uow)
        return service, repo_mapping

    return _factory


""" 
테스트 목업 데이터 셋업
"""


@pytest.fixture
def user_service_with_di(mock_user_repository, service_di_factory):
    return service_di_factory(
        UserService,
        "app.service.user",
        {"UserRepository": mock_user_repository}
    )


@pytest.fixture
def sample_user_create_dto():
    """Sample UserCreateDTO for unit testing"""
    return UserCreateDTO(
        email="test@example.com",
        name="Test User"
    )


@pytest.fixture
def sample_user_update_dto():
    """Sample UserUpdateDTO for unit testing"""
    return UserUpdateDTO(
        name="Updated User"
    )


@pytest.fixture
def sample_user_dto():
    """Sample UserDTO for unit testing"""
    return UserDTO(
        email="test@example.com",
        name="Test User",
        created_at=datetime(2024, 1, 1, 12, 0, 0)
    )


@pytest.fixture
def sample_user_list():
    """Sample list of UserDTO for unit testing"""
    return [
        UserDTO(
            email="user1@example.com",
            name="User One",
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        ),
        UserDTO(
            email="user2@example.com",
            name="User Two",
            created_at=datetime(2024, 1, 2, 12, 0, 0)
        )
    ]