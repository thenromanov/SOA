import pytest
from unittest.mock import patch, MagicMock
import grpc
from datetime import datetime, timedelta
import uuid
from kafka import KafkaProducer
from db.database import get_db, init_db
from broker.consumer import KafkaMessageConsumer, close_kafka_consumer
import json
import time

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

def test_get_post_stats_zero_metrics(stats_servicer):
    servicer, context, db_mock = stats_servicer
    post_id = str(uuid.uuid4())

    db_mock.execute.side_effect = [
        [(0,)],
        [(0,)],
        [(0,)],
    ]

    request = stats_pb2.PostStatsRequest(post_id=post_id)
    response = servicer.GetPostStats(request, context)

    assert db_mock.execute.call_count == 3
    
    calls = db_mock.execute.call_args_list
    
    views_query = calls[0][0][0]
    views_params = calls[0][0][1]
    assert "SELECT COUNT(*) FROM post_views" in views_query
    assert views_params["post_id"] == post_id
    
    likes_query = calls[1][0][0]
    likes_params = calls[1][0][1]
    assert "SELECT COUNT(*) FROM post_likes" in likes_query
    assert likes_params["post_id"] == post_id
    
    comments_query = calls[2][0][0]
    comments_params = calls[2][0][1]
    assert "SELECT COUNT(*) FROM post_comments" in comments_query
    assert comments_params["post_id"] == post_id

    assert response.views == 0
    assert response.likes == 0
    assert response.comments == 0
    
    context.set_code.assert_not_called()


def test_get_post_views_timeline_large_dataset(stats_servicer):
    servicer, context, db_mock = stats_servicer
    post_id = str(uuid.uuid4())
    
    base_date = datetime.now().date()
    test_data = []
    for i in range(30):
        day = base_date - timedelta(days=i)
        count = (i + 1) * 10
        test_data.append((day, count))
    
    test_data.sort(key=lambda x: x[0])
    
    db_mock.execute.return_value = test_data

    start_date = (base_date - timedelta(days=29)).strftime('%Y-%m-%d')
    end_date = base_date.strftime('%Y-%m-%d')
    
    request = stats_pb2.PostTimelineRequest(
        post_id=post_id,
        start_date=start_date,
        end_date=end_date
    )
    
    response = servicer.GetPostViewsTimeline(request, context)

    assert db_mock.execute.called
    
    executed_query = db_mock.execute.call_args[0][0]
    executed_params = db_mock.execute.call_args[0][1]
    
    assert "SELECT" in executed_query
    assert "toDate(viewed_at) as day" in executed_query
    assert "COUNT(*) as count" in executed_query
    assert "FROM post_views" in executed_query
    assert "WHERE post_id = %(post_id)s" in executed_query
    assert "GROUP BY day ORDER BY day" in executed_query
    
    assert executed_params["post_id"] == post_id
    assert "start_date" in executed_params
    assert "end_date" in executed_params
    
    assert len(response.entries) == 30
    
    for i, (entry, (day, count)) in enumerate(zip(response.entries, test_data)):
        assert entry.date == day.strftime('%Y-%m-%d')
        assert entry.count == count
    
    context.set_code.assert_not_called()


def test_get_top_posts_by_comments_with_sql_injection_prevention(stats_servicer):
    servicer, context, db_mock = stats_servicer
    
    test_data = [
        ("post_popular_1", 250),
        ("post_popular_2", 200),
        ("post_popular_3", 180),
        ("post_popular_4", 150),
        ("post_popular_5", 120),
    ]
    
    db_mock.execute.return_value = test_data

    request = stats_pb2.TopRequest(
        metric_type=stats_pb2.TopRequest.MetricType.COMMENTS,
        limit=5
    )
    
    response = servicer.GetTopPosts(request, context)

    assert db_mock.execute.called
    
    executed_query = db_mock.execute.call_args[0][0]
    
    assert "FROM post_comments" in executed_query
    assert "SELECT" in executed_query
    assert "post_id" in executed_query
    assert "COUNT(*) as count" in executed_query
    assert "GROUP BY post_id" in executed_query
    assert "ORDER BY count DESC" in executed_query
    assert "LIMIT 5" in executed_query

    assert len(response.posts) == 5
    
    for i, (post, (post_id, count)) in enumerate(zip(response.posts, test_data)):
        assert post.post_id == post_id
        assert post.count == count
        
        if i > 0:
            assert response.posts[i-1].count >= post.count
    
    context.set_code.assert_not_called()


@pytest.fixture(scope="module")
def kafka_producer():
    producer = KafkaProducer(
        bootstrap_servers="kafka:29092",
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    yield producer
    producer.close()

@pytest.fixture()
def setup_teardown():
    init_db()
    consumer = KafkaMessageConsumer()
    consumer.start()
    yield
    consumer.stop()
    close_kafka_consumer()
    db = get_db()
    db.execute("TRUNCATE TABLE post_views")
    db.execute("TRUNCATE TABLE post_likes")
    db.execute("TRUNCATE TABLE post_comments")

def test_view_event_processing(kafka_producer, setup_teardown):
    view_event = {
        "view_id": "view_test_1",
        "post_id": "post_test_1",
        "user_id": "user_test_1",
        "viewed_at": "2025-01-01T12:00:00"
    }
    kafka_producer.send("post_views", value=view_event)
    kafka_producer.flush()
    
    time.sleep(3)
    
    db = get_db()
    result = db.execute("SELECT * FROM post_views WHERE view_id = 'view_test_1'")
    assert len(result) == 1
    assert result[0][1] == "post_test_1"
    assert result[0][2] == "user_test_1"

def test_like_event_processing(kafka_producer, setup_teardown):
    like_event = {
        "like_id": "like_test_1",
        "post_id": "post_test_1",
        "user_id": "user_test_1",
        "liked_at": "2025-01-01T12:00:00"
    }
    kafka_producer.send("post_likes", value=like_event)
    kafka_producer.flush()
    
    time.sleep(3)
    
    db = get_db()
    result = db.execute("SELECT * FROM post_likes WHERE like_id = 'like_test_1'")
    assert len(result) == 1
    assert result[0][1] == "post_test_1"
    assert result[0][2] == "user_test_1"