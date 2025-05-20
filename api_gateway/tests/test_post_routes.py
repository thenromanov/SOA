import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_mock():
    from routes.post_routes import get_current_user
    
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "test-user-id"}
    yield
    app.dependency_overrides = {}


@pytest.fixture
def post_client_mock():
    with patch("routes.post_routes.post_client") as mock:
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


def test_view_post(client, auth_mock, post_client_mock):
    post_client_mock.view_post.return_value = MagicMock()
    
    response = client.post(
        "/posts/post-id/view",
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Post viewed successfully"
    
    post_client_mock.view_post.assert_called_once_with(
        post_id="post-id", 
        user_id="test-user-id"
    )


def test_like_post(client, auth_mock, post_client_mock):
    post_client_mock.like_post.return_value = MagicMock()
    
    response = client.post(
        "/posts/post-id/like",
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Post liked successfully"
    
    post_client_mock.like_post.assert_called_once_with(
        post_id="post-id", 
        user_id="test-user-id"
    )


def test_add_comment(client, auth_mock, post_client_mock):
    comment_id = "comment-id"
    created_at = datetime.now().isoformat()
    
    mock_comment = MagicMock()
    mock_comment.id = comment_id
    mock_comment.post_id = "post-id"
    mock_comment.user_id = "test-user-id"
    mock_comment.text = "Test comment"
    mock_comment.created_at = created_at
    
    post_client_mock.add_comment.return_value = mock_comment
    
    response = client.post(
        "/posts/post-id/comment",
        json={"text": "Test comment"},
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == comment_id
    assert data["post_id"] == "post-id"
    assert data["user_id"] == "test-user-id"
    assert data["text"] == "Test comment"
    assert "created_at" in data
    
    post_client_mock.add_comment.assert_called_once_with(
        post_id="post-id", 
        user_id="test-user-id",
        text="Test comment"
    )


def test_get_comments(client, auth_mock, post_client_mock):
    comment1 = MagicMock()
    comment1.id = "comment-1"
    comment1.post_id = "post-id"
    comment1.user_id = "user-1"
    comment1.text = "First comment"
    comment1.created_at = datetime.now().isoformat()
    
    comment2 = MagicMock()
    comment2.id = "comment-2"
    comment2.post_id = "post-id"
    comment2.user_id = "user-2"
    comment2.text = "Second comment"
    comment2.created_at = datetime.now().isoformat()
    
    mock_response = MagicMock()
    mock_response.comments = [comment1, comment2]
    mock_response.total = 2
    mock_response.page = 1
    mock_response.page_size = 10
    
    post_client_mock.get_comments.return_value = mock_response
    
    response = client.get(
        "/posts/post-id/comments?page=1&page_size=10",
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["comments"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 10
    
    assert data["comments"][0]["id"] == "comment-1"
    assert data["comments"][0]["post_id"] == "post-id"
    assert data["comments"][0]["user_id"] == "user-1"
    assert data["comments"][0]["text"] == "First comment"
    
    post_client_mock.get_comments.assert_called_once_with(
        post_id="post-id",
        page=1,
        page_size=10
    )
