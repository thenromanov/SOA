import pytest
from unittest.mock import patch, MagicMock
import uuid
import bcrypt
from datetime import datetime

from proto import user_pb2
from models.user_model import User
from broker.producer import CLIENT_REGISTRATION_TOPIC

@pytest.fixture
def user_servicer():
    from grpc_server.user_server import UserServicer
    
    servicer = UserServicer()
    context = MagicMock()
    
    with patch("grpc_server.user_server.get_db") as db_mock:
        session_mock = MagicMock()
        db_mock.return_value = session_mock
        
        yield servicer, context, session_mock


@pytest.fixture
def kafka_mock():
    with patch("grpc_server.user_server.get_kafka_producer") as kafka_producer_mock:
        producer_mock = MagicMock()
        kafka_producer_mock.return_value = producer_mock
        producer_mock.send_message.return_value = True
        
        yield producer_mock


def test_register_success(user_servicer, kafka_mock):
    servicer, context, session_mock = user_servicer
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = None 
    
    user_id = uuid.uuid4()
    
    def side_effect_add(new_user):
        new_user.id = user_id
        return None
    
    session_mock.add.side_effect = side_effect_add
    
    request = user_pb2.RegisterRequest(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    
    with patch("uuid.uuid4", return_value=user_id):
        response = servicer.Register(request, context)
    
    assert response.success == True
    assert response.message == "Success"
    
    assert session_mock.add.called
    assert session_mock.commit.called
    assert session_mock.refresh.called
    
    kafka_mock.send_message.assert_called_once()
    args = kafka_mock.send_message.call_args[0]
    assert args[0] == CLIENT_REGISTRATION_TOPIC
    event = args[1]
    assert event["username"] == "testuser"
    assert event["email"] == "test@example.com"
    assert event["client_id"] == str(user_id)


def test_register_missing_fields(user_servicer):
    servicer, context, session_mock = user_servicer
    
    request = user_pb2.RegisterRequest(
        username="",
        email="test@example.com",
        password="password123"
    )
    
    response = servicer.Register(request, context)
    
    assert response.success == False
    assert response.message == "Fields required"
    
    session_mock.query.assert_not_called()


def test_register_user_exists(user_servicer):
    servicer, context, session_mock = user_servicer
    
    existing_user = MagicMock(spec=User)
    existing_user.email = "test@example.com"
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = existing_user
    
    request = user_pb2.RegisterRequest(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    
    response = servicer.Register(request, context)
    
    assert response.success == False
    assert response.message == "Already exists"
    
    session_mock.add.assert_not_called()


def test_login_success(user_servicer):
    servicer, context, session_mock = user_servicer
    
    password = "password123"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.password = hashed_password
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = user
    
    request = user_pb2.LoginRequest(
        email="test@example.com",
        password="password123"
    )
    
    with patch("grpc_server.user_server.jwt.encode", return_value="test-token"):
        response = servicer.Login(request, context)
    
    assert response.success == True
    assert response.message == "Success"
    assert response.token == "test-token"
    assert response.user.id == str(user.id)
    assert response.user.username == "testuser"
    assert response.user.email == "test@example.com"


def test_login_invalid_credentials(user_servicer):
    servicer, context, session_mock = user_servicer
    
    hashed_password = bcrypt.hashpw("different_password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.password = hashed_password
    
    query_mock = MagicMock()
    filter_mock = MagicMock()
    session_mock.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = user
    
    request = user_pb2.LoginRequest(
        email="test@example.com",
        password="wrong_password"
    )
    
    response = servicer.Login(request, context)
    
    assert response.success == False
    assert response.message == "Invalid credentials"
