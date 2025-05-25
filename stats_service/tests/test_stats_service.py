import pytest
from unittest.mock import patch, MagicMock
import grpc
from datetime import datetime, timedelta
import uuid

from proto import stats_pb2
from grpc_server.stats_server import StatsServicer

@pytest.fixture
def stats_servicer():
    servicer = StatsServicer()
    context = MagicMock()

    with patch("grpc_server.stats_server.get_db") as db_mock:
        db_instance_mock = MagicMock()
        db_mock.return_value = db_instance_mock

        yield servicer, context, db_instance_mock

def test_get_post_stats_success(stats_servicer):
    servicer, context, db_mock = stats_servicer
    post_id = str(uuid.uuid4())

    db_mock.execute.side_effect = [
        [(100,)],
        [(50,)],
        [(30,)],
    ]

    request = stats_pb2.PostStatsRequest(post_id=post_id)
    response = servicer.GetPostStats(request, context)

    assert response.views == 100
    assert response.likes == 50
    assert response.comments == 30
    context.set_code.assert_not_called()

def test_get_post_stats_database_error(stats_servicer):
    servicer, context, db_mock = stats_servicer
    post_id = str(uuid.uuid4())

    db_mock.execute.side_effect = Exception("Database error")

    request = stats_pb2.PostStatsRequest(post_id=post_id)
    response = servicer.GetPostStats(request, context)

    context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)
    context.set_details.assert_called_with("Internal error: Database error")

def test_get_post_views_timeline_success(stats_servicer):
    servicer, context, db_mock = stats_servicer
    post_id = str(uuid.uuid4())
    test_data = [
        (datetime.now().date() - timedelta(days=2), 10),
        (datetime.now().date() - timedelta(days=1), 20),
        (datetime.now().date(), 30),
    ]

    db_mock.execute.return_value = test_data

    request = stats_pb2.PostTimelineRequest(post_id=post_id)
    response = servicer.GetPostViewsTimeline(request, context)

    assert len(response.entries) == 3
    for entry, (day, count) in zip(response.entries, test_data):
        assert entry.date == day.strftime('%Y-%m-%d')
        assert entry.count == count
    context.set_code.assert_not_called()

def test_get_post_views_timeline_with_dates(stats_servicer):
    servicer, context, db_mock = stats_servicer
    post_id = str(uuid.uuid4())
    
    request = stats_pb2.PostTimelineRequest(
        post_id=post_id,
        start_date="2025-01-01",
        end_date="2025-12-31"
    )
    
    servicer.GetPostViewsTimeline(request, context)
    
    executed_query = db_mock.execute.call_args[0][0]
    assert "AND toDate(viewed_at) >= %(start_date)s" in executed_query
    assert "AND toDate(viewed_at) <= %(end_date)s" in executed_query

def test_get_post_likes_timeline_success(stats_servicer):
    servicer, context, db_mock = stats_servicer
    post_id = str(uuid.uuid4())
    test_data = [
        (datetime.now().date() - timedelta(days=1), 5),
        (datetime.now().date(), 15),
    ]

    db_mock.execute.return_value = test_data

    request = stats_pb2.PostTimelineRequest(post_id=post_id)
    response = servicer.GetPostLikesTimeline(request, context)

    assert len(response.entries) == 2
    context.set_code.assert_not_called()

def test_get_post_comments_timeline_invalid_date(stats_servicer):
    servicer, context, db_mock = stats_servicer
    post_id = str(uuid.uuid4())
    
    request = stats_pb2.PostTimelineRequest(
        post_id=post_id,
        start_date="invalid-date"
    )
    
    response = servicer.GetPostCommentsTimeline(request, context)
    
    assert len(response.entries) == 0
    context.set_code.assert_not_called()

def test_get_top_posts_by_views(stats_servicer):
    servicer, context, db_mock = stats_servicer
    test_data = [
        ("post1", 1000),
        ("post2", 900),
        ("post3", 800),
    ]
    
    db_mock.execute.return_value = test_data

    request = stats_pb2.TopRequest(
        metric_type=stats_pb2.TopRequest.MetricType.VIEWS,
        limit=3
    )
    response = servicer.GetTopPosts(request, context)

    assert len(response.posts) == 3
    for post, (post_id, count) in zip(response.posts, test_data):
        assert post.post_id == post_id
        assert post.count == count

def test_get_top_users_by_likes(stats_servicer):
    servicer, context, db_mock = stats_servicer
    test_data = [
        ("user1", 500),
        ("user2", 400),
        ("user3", 300),
    ]
    
    db_mock.execute.return_value = test_data

    request = stats_pb2.TopRequest(
        metric_type=stats_pb2.TopRequest.MetricType.LIKES,
        limit=3
    )
    response = servicer.GetTopUsers(request, context)

    assert len(response.users) == 3
    for user, (user_id, count) in zip(response.users, test_data):
        assert user.user_id == user_id
        assert user.count == count

def test_get_top_posts_default_limit(stats_servicer):
    servicer, context, db_mock = stats_servicer
    test_data = [(f"post{i}", i*100) for i in range(1, 11)]
    
    db_mock.execute.return_value = test_data

    request = stats_pb2.TopRequest(
        metric_type=stats_pb2.TopRequest.MetricType.VIEWS,
        limit=0  # should default to 10
    )
    response = servicer.GetTopPosts(request, context)

    assert len(response.posts) == 10

def test_get_top_users_database_error(stats_servicer):
    servicer, context, db_mock = stats_servicer
    
    db_mock.execute.side_effect = Exception("Query failed")

    request = stats_pb2.TopRequest(
        metric_type=stats_pb2.TopRequest.MetricType.COMMENTS
    )
    response = servicer.GetTopUsers(request, context)

    context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)
    context.set_details.assert_called_with("Internal error: Query failed")