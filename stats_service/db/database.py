import os
import time
import logging
from clickhouse_driver import Client
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_PORT", "9000")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "default")

clickhouse_client = None

def create_tables(client):
    try:
        client.execute('''
            CREATE TABLE IF NOT EXISTS post_views (
                view_id String,
                post_id String,
                user_id String,
                viewed_at DateTime,
                event_date Date DEFAULT toDate(viewed_at)
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(event_date)
            ORDER BY (event_date, post_id, user_id)
        ''')
        
        client.execute('''
            CREATE TABLE IF NOT EXISTS post_likes (
                like_id String,
                post_id String,
                user_id String,
                liked_at DateTime,
                event_date Date DEFAULT toDate(liked_at)
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(event_date)
            ORDER BY (event_date, post_id, user_id)
        ''')
        
        client.execute('''
            CREATE TABLE IF NOT EXISTS post_comments (
                comment_id String,
                post_id String,
                user_id String,
                text String,
                created_at DateTime,
                event_date Date DEFAULT toDate(created_at)
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(event_date)
            ORDER BY (event_date, post_id, user_id)
        ''')
        
        logger.info("ClickHouse tables created or already exist")
    except Exception as e:
        logger.error(f"Error creating ClickHouse tables: {e}")
        raise

def init_db(max_retries=5, retry_delay=2):
    global clickhouse_client
    for attempt in range(max_retries):
        try:
            logger.info(f"Connecting to ClickHouse {attempt+1}")
            client = Client(
                host=CLICKHOUSE_HOST,
                port=CLICKHOUSE_PORT,
                user=CLICKHOUSE_USER,
                password=CLICKHOUSE_PASSWORD,
                database=CLICKHOUSE_DB
            )
            
            client.execute("SELECT 1")
            
            create_tables(client)
            
            clickhouse_client = client
            logger.info("ClickHouse connected")
            return
        except Exception as e:
            logger.warning(f"ClickHouse error {attempt+1}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retry in {retry_delay} sec")
                time.sleep(retry_delay)
            else:
                logger.error("ClickHouse connection failed")
                raise

def get_db():
    global clickhouse_client
    if not clickhouse_client:
        init_db()
    return clickhouse_client

def execute_query(query, params=None, with_column_types=False):
    client = get_db()
    try:
        return client.execute(query, params or {}, with_column_types=with_column_types)
    except Exception as e:
        logger.error(f"ClickHouse query error: {str(e)}, Query: {query}")
        raise
