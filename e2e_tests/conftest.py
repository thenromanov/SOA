import pytest
import requests
import time
import random
import string
import os
import psycopg2
from clickhouse_driver import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BASE_URL", "http://api-gateway:3000")

POSTGRES_DSN = "postgresql://postgres:postgres@postgres:5432/"
CLICKHOUSE_HOST = "clickhouse"

@pytest.fixture(scope="session")
def wait_for_services():
    timeout = 120
    start_time = time.time()
    
    api_gateway_ready = False
    postgres_ready = False
    clickhouse_ready = False
    
    while time.time() - start_time < timeout:
        if not api_gateway_ready:
            try:
                response = requests.get(f"{BASE_URL}/", timeout=2)
                if response.status_code == 200:
                    api_gateway_ready = True
            except Exception as e:
                logger.debug(f"API Gateway not ready: {str(e)}")
        
        if not postgres_ready:
            try:
                conn = psycopg2.connect(POSTGRES_DSN + "userservice")
                conn.close()
                postgres_ready = True
            except Exception as e:
                logger.debug(f"PostgreSQL not ready: {str(e)}")
        
        if not clickhouse_ready:
            try:
                client = Client(host=CLICKHOUSE_HOST)
                client.execute("SELECT 1")
                clickhouse_ready = True
            except Exception as e:
                logger.debug(f"ClickHouse not ready: {str(e)}")
        
        time.sleep(2)
    
    errors = []
    if not api_gateway_ready:
        errors.append("API Gateway")
    if not postgres_ready:
        errors.append("PostgreSQL")
    if not clickhouse_ready:
        errors.append("ClickHouse")
    
    pytest.fail(f"Services not ready: {', '.join(errors)}")

@pytest.fixture(scope="session")
def clickhouse_client():
    return Client(host=CLICKHOUSE_HOST)

@pytest.fixture(scope="session")
def postgres_conn():
    conn = psycopg2.connect(POSTGRES_DSN + "userservice")
    return conn

@pytest.fixture
def generate_random_string():
    def _generate(length=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return _generate

@pytest.fixture
def test_user_data(generate_random_string):
    username = f"test_user_{generate_random_string(8)}"
    email = f"test_{generate_random_string(5)}@example.com"
    password = "strongpassword123"
    
    return {
        "username": username,
        "email": email,
        "password": password
    }

@pytest.fixture
def test_user(wait_for_services, test_user_data):
    url = f"{BASE_URL}/auth/register"

    try:
        response = requests.post(url, json=test_user_data)
        
        if response.status_code == 201:
            response_data = response.json()
            
            return {
                "username": test_user_data["username"],
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        else:
            pytest.fail(f"User registration failed: {response.status_code}")
    except Exception as e:
        pytest.fail(f"Exception during user registration: {str(e)}")

@pytest.fixture
def auth_headers(test_user):
    url = f"{BASE_URL}/auth/login"
    login_data = {
        "email": test_user['email'],
        "password": test_user['password']
    }
    
    try:
        response = requests.post(url, json=login_data)
        
        if response.status_code == 200:
            token = response.json().get("token")
            assert token, "Token not found in login response"
            headers = {"Authorization": f"Bearer {token}"}
            return headers
        else:
            pytest.fail(f"User login failed: {response.status_code}")
    except Exception as e:
        pytest.fail(f"Exception during user login: {str(e)}")