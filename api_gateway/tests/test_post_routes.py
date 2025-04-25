import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient

from api_gateway.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_mock():
    with patch("api_gateway.routes.post_routes.get_current_user") as mock:
        mock.return_value = {"user_id": "test-user-id"}
        yield mock


@pytest.fixture
def post_client_mock():
    with patch("api_gateway.routes.post_routes.post_client") as mock:
        yield mock


def test_create_post(client, auth_mock, post_client_mock):
    mock_response = MagicMock()
    mock_response.id = "post-id"
    mock_response.title = "Test Post"
    mock_response.description = "Test Description"
    mock_response.creator_id = "test-user-id"
    mock_response.created_at = datetime.now().isoformat()
    mock_response.updated_at = datetime.now().isoformat()
    mock_response.is_private = False
    mock_response.tags = ["test", "api"]

    post_client_mock.create_post.return_value = mock_response

    response = client.post(
        "/posts/",
        json={
            "title": "Test Post",
            "description": "Test Description",
            "is_private": False,
            "tags": ["test", "api"],
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "post-id"
    assert data["title"] == "Test Post"
    assert data["is_private"] == False
    post_client_mock.create_post.assert_called_once()


def test_update_post(client, auth_mock, post_client_mock):
    mock_response = MagicMock()
    mock_response.id = "post-id"
    mock_response.title = "Updated Post"
    mock_response.description = "Updated Description"
    mock_response.creator_id = "test-user-id"
    mock_response.created_at = datetime.now().isoformat()
    mock_response.updated_at = datetime.now().isoformat()
    mock_response.is_private = True
    mock_response.tags = ["updated", "api"]

    post_client_mock.update_post.return_value = mock_response

    response = client.put(
        "/posts/post-id",
        json={
            "title": "Updated Post",
            "description": "Updated Description",
            "is_private": True,
            "tags": ["updated", "api"],
        },
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "post-id"
    assert data["title"] == "Updated Post"
    assert data["is_private"] == True
    post_client_mock.update_post.assert_called_once()


def test_get_post(client, auth_mock, post_client_mock):
    mock_response = MagicMock()
    mock_response.id = "post-id"
    mock_response.title = "Test Post"
    mock_response.description = "Test Description"
    mock_response.creator_id = "test-user-id"
    mock_response.created_at = datetime.now().isoformat()
    mock_response.updated_at = datetime.now().isoformat()
    mock_response.is_private = False
    mock_response.tags = ["test", "api"]

    post_client_mock.get_post.return_value = mock_response

    response = client.get("/posts/post-id", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "post-id"
    assert data["title"] == "Test Post"
    post_client_mock.get_post.assert_called_once()


def test_delete_post(client, auth_mock, post_client_mock):
    mock_response = MagicMock()
    mock_response.success = True

    post_client_mock.delete_post.return_value = mock_response

    response = client.delete("/posts/post-id", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 204
    post_client_mock.delete_post.assert_called_once()


def test_list_posts(client, auth_mock, post_client_mock):
    mock_post = MagicMock()
    mock_post.id = "post-id"
    mock_post.title = "Test Post"
    mock_post.description = "Test Description"
    mock_post.creator_id = "test-user-id"
    mock_post.created_at = datetime.now().isoformat()
    mock_post.updated_at = datetime.now().isoformat()
    mock_post.is_private = False
    mock_post.tags = ["test", "api"]

    mock_response = MagicMock()
    mock_response.posts = [mock_post]
    mock_response.total = 1
    mock_response.page = 1
    mock_response.page_size = 10

    post_client_mock.list_posts.return_value = mock_response

    response = client.get(
        "/posts/?page=1&page_size=10", headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["posts"]) == 1
    assert data["posts"][0]["id"] == "post-id"
    assert data["page"] == 1
    assert data["page_size"] == 10
    post_client_mock.list_posts.assert_called_once()
