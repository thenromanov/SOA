import pytest
from unittest.mock import patch, MagicMock
import grpc
import uuid
from datetime import datetime

from grpc_server.post_server import PostServicer
from proto import post_pb2


@pytest.fixture
def post_servicer():
    servicer = PostServicer()

    context = MagicMock()

    with patch("grpc_server.post_server.get_db") as db_mock:
        session_mock = MagicMock()
        db_mock.return_value = session_mock

        yield servicer, context, session_mock


@pytest.fixture
def kafka_mock():
    with patch("grpc_server.post_server.get_kafka_producer") as kafka_producer_mock:
        producer_mock = MagicMock()
        kafka_producer_mock.return_value = producer_mock
        producer_mock.send_message.return_value = True
        
        yield producer_mock


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

def test_view_post_success(post_servicer, kafka_mock):
    servicer, context, session_mock = post_servicer

    post_id = str(uuid.uuid4())
    user_id = "user1"
    
    post_mock = MagicMock()
    post_mock.id = post_id
    post_mock.creator_id = "creator1"
    post_mock.is_private = False
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = post_mock
    
    request = post_pb2.ViewPostRequest(
        post_id=post_id,
        user_id=user_id
    )

    response = servicer.ViewPost(request, context)
    
    session_mock.add.assert_called_once()
    
    session_mock.commit.assert_called_once()
    
    kafka_mock.send_message.assert_called_once()
    
    context.set_code.assert_not_called()


def test_view_post_not_found(post_servicer, kafka_mock):
    servicer, context, session_mock = post_servicer

    post_id = str(uuid.uuid4())
    user_id = "user1"
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = None
    
    request = post_pb2.ViewPostRequest(
        post_id=post_id,
        user_id=user_id
    )
    
    servicer.ViewPost(request, context)
    
    session_mock.add.assert_not_called()
    
    session_mock.commit.assert_not_called()
    
    kafka_mock.send_message.assert_not_called()
    
    context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)


def test_view_private_post_denied(post_servicer, kafka_mock):
    servicer, context, session_mock = post_servicer

    post_id = str(uuid.uuid4())
    user_id = "user1"
    
    post_mock = MagicMock()
    post_mock.id = post_id
    post_mock.creator_id = "creator1"  
    post_mock.is_private = True        
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = post_mock
    
    
    request = post_pb2.ViewPostRequest(
        post_id=post_id,
        user_id=user_id
    )
    
    servicer.ViewPost(request, context)
    
    session_mock.add.assert_not_called()
    
    session_mock.commit.assert_not_called()
    
    kafka_mock.send_message.assert_not_called()
    
    context.set_code.assert_called_with(grpc.StatusCode.PERMISSION_DENIED)


def test_like_post_success(post_servicer, kafka_mock):
    servicer, context, session_mock = post_servicer

    post_id = str(uuid.uuid4())
    user_id = "user1"
    
    post_mock = MagicMock()
    post_mock.id = post_id
    post_mock.creator_id = "creator1"
    post_mock.is_private = False
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    first_mock = MagicMock()
    
    session_mock.query.side_effect = [query_mock, query_mock]
    query_mock.filter.side_effect = [filter_mock, filter_mock]
    filter_mock.first.side_effect = [post_mock, None]  
    
    
    request = post_pb2.LikePostRequest(
        post_id=post_id,
        user_id=user_id
    )
    
    response = servicer.LikePost(request, context)
    
    
    session_mock.add.assert_called_once()
    
    session_mock.commit.assert_called_once()
    
    kafka_mock.send_message.assert_called_once()
    
    context.set_code.assert_not_called()


def test_like_post_already_liked(post_servicer, kafka_mock):
    servicer, context, session_mock = post_servicer

    post_id = str(uuid.uuid4())
    user_id = "user1"
    
    post_mock = MagicMock()
    post_mock.id = post_id
    post_mock.creator_id = "creator1"
    post_mock.is_private = False
    
    like_mock = MagicMock()
    
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    
    session_mock.query.side_effect = [query_mock, query_mock]
    query_mock.filter.side_effect = [filter_mock, filter_mock]
    filter_mock.first.side_effect = [post_mock, like_mock]  
    
    
    request = post_pb2.LikePostRequest(
        post_id=post_id,
        user_id=user_id
    )
    
    servicer.LikePost(request, context)
    
    session_mock.add.assert_not_called()
    
    session_mock.commit.assert_not_called()
    
    kafka_mock.send_message.assert_not_called()
    
    context.set_code.assert_called_with(grpc.StatusCode.ALREADY_EXISTS)


def test_add_comment_success(post_servicer, kafka_mock):
    servicer, context, session_mock = post_servicer

    post_id = str(uuid.uuid4())
    user_id = "user1"
    comment_text = "This is a test comment"
    
    post_mock = MagicMock()
    post_mock.id = post_id
    post_mock.creator_id = "creator1"
    post_mock.is_private = False
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = post_mock
    
    request = post_pb2.AddCommentRequest(
        post_id=post_id,
        user_id=user_id,
        text=comment_text
    )
    
    response = servicer.AddComment(request, context)
    
    assert response.post_id == post_id
    assert response.user_id == user_id
    assert response.text == comment_text
    assert response.id is not None
    assert response.created_at is not None
    
    session_mock.add.assert_called_once()
    
    session_mock.commit.assert_called_once()
    
    kafka_mock.send_message.assert_called_once()
    
    context.set_code.assert_not_called()


def test_get_comments_success(post_servicer):
    servicer, context, session_mock = post_servicer

    post_id = str(uuid.uuid4())
    user_id = "user1"

    post_mock = MagicMock()
    post_mock.id = post_id
    post_mock.creator_id = "creator1"
    post_mock.is_private = False

    comment1 = MagicMock()
    comment1.id = str(uuid.uuid4())
    comment1.post_id = post_id
    comment1.user_id = "user1"
    comment1.text = "Comment 1"
    comment1.created_at = datetime.now()

    comment2 = MagicMock()
    comment2.id = str(uuid.uuid4())
    comment2.post_id = post_id
    comment2.user_id = "user2"
    comment2.text = "Comment 2"
    comment2.created_at = datetime.now()

    post_query_mock = MagicMock()
    count_query_mock = MagicMock()
    comments_query_mock = MagicMock()
    
    post_filter_mock = MagicMock()
    count_filter_mock = MagicMock()
    comments_filter_mock = MagicMock()
    
    post_query_mock.filter.return_value = post_filter_mock
    post_filter_mock.first.return_value = post_mock
    
    count_query_mock.filter.return_value = count_filter_mock
    count_filter_mock.count.return_value = 2
    
    comments_query_mock.filter.return_value = comments_filter_mock
    
    order_mock = MagicMock()
    offset_mock = MagicMock()
    limit_mock = MagicMock()
    
    comments_filter_mock.order_by.return_value = order_mock
    order_mock.offset.return_value = offset_mock
    offset_mock.limit.return_value = limit_mock
    limit_mock.all.return_value = [comment1, comment2]
    
    session_mock.query.side_effect = [post_query_mock, count_query_mock, comments_query_mock]

    request = post_pb2.GetCommentsRequest(
        post_id=post_id,
        page=1,
        page_size=10
    )

    response = servicer.GetComments(request, context)

    assert response.total == 2
    assert response.page == 1
    assert response.page_size == 10
    assert len(response.comments) == 2
    
    assert response.comments[0].id == comment1.id
    assert response.comments[0].post_id == post_id
    assert response.comments[0].user_id == "user1"
    assert response.comments[0].text == "Comment 1"
    
    context.set_code.assert_not_called()


def test_get_comments_post_not_found(post_servicer):
    servicer, context, session_mock = post_servicer

    post_id = str(uuid.uuid4())
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = None
    
    request = post_pb2.GetCommentsRequest(
        post_id=post_id,
        page=1,
        page_size=10
    )
    
    servicer.GetComments(request, context)
    
    context.set_code.assert_called_with(grpc.StatusCode.NOT_FOUND)
