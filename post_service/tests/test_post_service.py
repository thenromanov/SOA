import pytest
from unittest.mock import patch, MagicMock
import grpc
import uuid
from datetime import datetime

from post_service.grpc_server.post_server import PostServicer
from post_service.proto import post_pb2


@pytest.fixture
def post_servicer():
    servicer = PostServicer()

    context = MagicMock()

    with patch("post_service.grpc_server.post_server.SessionLocal") as db_mock:
        session_mock = MagicMock()
        db_mock.return_value = session_mock

        yield servicer, context, session_mock


def test_create_post(post_servicer):
    servicer, context, session_mock = post_servicer

    request = post_pb2.CreatePostRequest(
        title="Test Post",
        description="Test Description",
        creator_id="user1",
        is_private=False,
        tags=["tag1", "tag2"],
    )

    response = servicer.CreatePost(request, context)

    assert response.id is not None
    assert response.title == "Test Post"
    assert response.description == "Test Description"
    assert response.creator_id == "user1"
    assert response.is_private == False
    assert list(response.tags) == ["tag1", "tag2"]

    session_mock.add.assert_called_once()
    session_mock.commit.assert_called_once()


def test_update_post(post_servicer):
    servicer, context, session_mock = post_servicer

    post_id = str(uuid.uuid4())
    post_mock = MagicMock()
    post_mock.id = post_id
    post_mock.creator_id = "user1"
    post_mock.created_at = datetime.utcnow()

    query_mock = MagicMock()
    filter_mock = MagicMock()

    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = post_mock

    request = post_pb2.UpdatePostRequest(
        id=post_id,
        title="Updated Post",
        description="Updated Description",
        creator_id="user1",
        is_private=True,
        tags=["tag3", "tag4"],
    )

    response = servicer.UpdatePost(request, context)

    assert response.id == post_id
    assert post_mock.title == "Updated Post"
    assert post_mock.description == "Updated Description"
    assert post_mock.is_private == True
    assert post_mock.tags == ["tag3", "tag4"]

    session_mock.commit.assert_called_once()


def test_update_post_not_found(post_servicer):
    servicer, context, session_mock = post_servicer

    query_mock = MagicMock()
    filter_mock = MagicMock()

    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = None

    post_id = str(uuid.uuid4())
    request = post_pb2.UpdatePostRequest(
        id=post_id,
        title="Updated Post",
        description="Updated Description",
        creator_id="user1",
        is_private=True,
        tags=["tag3", "tag4"],
    )

    servicer.UpdatePost(request, context)

    context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)


def test_delete_post(post_servicer):
    servicer, context, session_mock = post_servicer

    post_id = str(uuid.uuid4())
    post_mock = MagicMock()
    post_mock.id = post_id
    post_mock.creator_id = "user1"

    query_mock = MagicMock()
    filter_mock = MagicMock()

    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = post_mock

    request = post_pb2.DeletePostRequest(id=post_id, creator_id="user1")

    response = servicer.DeletePost(request, context)

    assert response.success == True

    session_mock.delete.assert_called_once_with(post_mock)
    session_mock.commit.assert_called_once()


def test_get_post(post_servicer):
    servicer, context, session_mock = post_servicer

    post_id = str(uuid.uuid4())
    post_mock = MagicMock()
    post_mock.id = post_id
    post_mock.title = "Test Post"
    post_mock.description = "Test Description"
    post_mock.creator_id = "user1"
    post_mock.created_at = datetime.utcnow()
    post_mock.updated_at = datetime.utcnow()
    post_mock.is_private = False
    post_mock.tags = ["tag1", "tag2"]

    query_mock = MagicMock()
    filter_mock = MagicMock()

    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = post_mock

    request = post_pb2.GetPostRequest(id=post_id, user_id="user1")

    response = servicer.GetPost(request, context)

    assert response.id == post_id
    assert response.title == "Test Post"
    assert response.description == "Test Description"
    assert response.creator_id == "user1"
