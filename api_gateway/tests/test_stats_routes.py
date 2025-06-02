import grpc
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import status

from main import app
from routes.stats_routes import stats_client

client = TestClient(app)

@pytest.fixture
def auth_mock():
    from routes.stats_routes import get_current_user
    
    app.dependency_overrides[get_current_user] = lambda: {"user_id": "test-user"}
    yield
    app.dependency_overrides = {}

@pytest.fixture
def stats_client_mock():
    with patch("routes.stats_routes.stats_client") as mock:
        yield mock
    
class MockRpcError(grpc.RpcError):
    def __init__(self, code: grpc.StatusCode, details: str = ""):
        self._code = code
        self._details = details

    def code(self):
        return self._code

    def details(self):
        return self._details

def test_get_post_stats_success(auth_mock, stats_client_mock):
    grpc_response = MagicMock()
    grpc_response.views = 100
    grpc_response.likes = 50
    grpc_response.comments = 30
    stats_client_mock.get_post_stats.return_value = grpc_response

    response = client.get(
        "/stats/posts/post123",
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "post_id": "post123",
        "views": 100,
        "likes": 50,
        "comments": 30
    }
    stats_client_mock.get_post_stats.assert_called_once_with(post_id="post123")

def test_get_post_stats_not_found(auth_mock, stats_client_mock):
    stats_client_mock.get_post_stats.side_effect = MockRpcError(
        grpc.StatusCode.NOT_FOUND, 
        "Not found"
    )

    response = client.get(
        "/stats/posts/invalid_post",
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Stats for post ID invalid_post not found"

def test_get_views_timeline_success(auth_mock, stats_client_mock):
    grpc_response = MagicMock()
    grpc_response.entries = [
        MagicMock(date="2023-01-01", count=10),
        MagicMock(date="2023-01-02", count=20)
    ]
    stats_client_mock.get_post_views_timeline.return_value = grpc_response

    response = client.get(
        "/stats/posts/post123/views/timeline?days=7",
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "entries": [
            {"date": "2023-01-01", "count": 10},
            {"date": "2023-01-02", "count": 20}
        ]
    }
    stats_client_mock.get_post_views_timeline.assert_called_once_with(
        post_id="post123",
        days=7
    )

def test_get_likes_timeline_invalid_days(auth_mock, stats_client_mock):
    response = client.get(
        "/stats/posts/post123/likes/timeline?days=60",
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "ensure this value is less than or equal to 30" in response.text

def test_get_comments_timeline_error(auth_mock, stats_client_mock):
    stats_client_mock.get_post_comments_timeline.side_effect = MockRpcError(
        grpc.StatusCode.INTERNAL, 
        "Internal error"
    )

    response = client.get(
        "/stats/posts/post123/comments/timeline",
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Error getting comments timeline" in response.json()["detail"]

def test_get_top_posts_success(auth_mock, stats_client_mock):
    grpc_response = MagicMock()
    grpc_response.posts = [
        MagicMock(post_id="post1", title="Post 1", count=1000),
        MagicMock(post_id="post2", title="Post 2", count=900)
    ]
    stats_client_mock.get_top_posts.return_value = grpc_response

    response = client.get(
        "/stats/top/posts?metric=views&limit=2",
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "posts": [
            {"post_id": "post1", "title": "Post 1", "count": 1000},
            {"post_id": "post2", "title": "Post 2", "count": 900}
        ]
    }
    stats_client_mock.get_top_posts.assert_called_once_with(
        metric_type="views",
        limit=2
    )

def test_get_top_users_invalid_metric(auth_mock, stats_client_mock):
    stats_client_mock.get_top_users.side_effect = ValueError("Invalid metric type: invalid")
    
    response = client.get(
        "/stats/top/users?metric=invalid",
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid metric type: invalid" in response.json()["detail"]

def test_get_top_users_max_limit(auth_mock, stats_client_mock):
    grpc_response = MagicMock()
    grpc_response.users = [MagicMock(user_id=f"user{i}", username=f"User {i}", count=i*100) for i in range(1, 51)]
    stats_client_mock.get_top_users.return_value = grpc_response

    response = client.get(
        "/stats/top/users?limit=50",
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["users"]) == 50
    stats_client_mock.get_top_users.assert_called_once_with(
        metric_type="views",
        limit=50
    )

def test_unauthorized_access():
    response = client.get("/stats/posts/post123")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED