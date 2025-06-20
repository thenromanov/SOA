import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_client_mock():
    with patch("routes.user_routes.user_client") as mock:
        yield mock


def test_register_user_success(client, user_client_mock):
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.message = "Success"
    
    user_client_mock.register.return_value = mock_response
    
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Success"
    
    user_client_mock.register.assert_called_once_with(
        "testuser",
        "test@example.com",
        "SecurePass123!"
    )


def test_register_user_already_exists(client, user_client_mock):
    mock_response = MagicMock()
    mock_response.success = False
    mock_response.message = "Already exists"
    
    user_client_mock.register.return_value = mock_response
    
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "existing@example.com",
            "password": "SecurePass123!"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Already exists"
    
    user_client_mock.register.assert_called_once()


def test_register_user_missing_fields(client, user_client_mock):
    mock_response = MagicMock()
    mock_response.success = False
    mock_response.message = "Fields required"
    
    user_client_mock.register.return_value = mock_response
    
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": ""
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Fields required"


def test_login_user_success(client, user_client_mock):
    mock_user_info = MagicMock()
    mock_user_info.id = "user-123"
    mock_user_info.username = "testuser"
    mock_user_info.email = "test@example.com"
    
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.message = "Success"
    mock_response.token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.jwt.token"
    mock_response.user = mock_user_info
    
    user_client_mock.login.return_value = mock_response
    
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Success"
    assert data["token"] == "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.jwt.token"
    assert data["user"]["id"] == "user-123"
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "test@example.com"
    
    user_client_mock.login.assert_called_once_with(
        "test@example.com",
        "SecurePass123!"
    )


def test_login_user_invalid_credentials(client, user_client_mock):
    mock_response = MagicMock()
    mock_response.success = False
    mock_response.message = "Invalid credentials"
    
    user_client_mock.login.return_value = mock_response
    
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword"
        }
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid credentials"
    
    user_client_mock.login.assert_called_once()


def test_login_user_not_found(client, user_client_mock):
    mock_response = MagicMock()
    mock_response.success = False
    mock_response.message = "Invalid credentials"
    
    user_client_mock.login.return_value = mock_response
    
    response = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
    )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid credentials"
