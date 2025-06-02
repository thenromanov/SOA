import os
import time
import json
import logging
import threading
from datetime import datetime
from kafka import KafkaConsumer
from dotenv import load_dotenv
from models.stats_model import StatsView, StatsLike, StatsComment
from db.database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

POST_VIEW_TOPIC = "post_views"
POST_LIKE_TOPIC = "post_likes"
POST_COMMENT_TOPIC = "post_comments"

_kafka_consumer_instance = None

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "stats-service")


class KafkaMessageConsumer:
    def __init__(self, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id=KAFKA_GROUP_ID, max_retries=10, retry_delay=5):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = [POST_VIEW_TOPIC, POST_LIKE_TOPIC, POST_COMMENT_TOPIC]
        self.consumer = None
        self.running = False
        self.thread = None
        self.connect_with_retry(max_retries, retry_delay)
    
    def connect_with_retry(self, max_retries=10, retry_delay=5):
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting Kafka Consumer {attempt+1}")
                self.consumer = KafkaConsumer(
                    *self.topics,
                    bootstrap_servers=self.bootstrap_servers,
                    auto_offset_reset='earliest',
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                    group_id=self.group_id,
                    api_version=(0, 10, 1)
                )
                topics = self.consumer.subscription()
                logger.info(f"Topics: {', '.join(topics)}")
                if topics != set(self.topics):
                    raise ValueError("Mismatch topics connection")
                logger.info(f"Kafka Consumer connected to {self.bootstrap_servers}")
                return
                
            except Exception as e:
                logger.warning(f"Kafka Consumer error {attempt+1}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retry in {retry_delay} sec")
                    time.sleep(retry_delay)
                else:
                    logger.error("Kafka Consumer connection failed")
                    raise
    
    def process_message(self, message):
        try:
            topic = message.topic
            data = message.value
            db = get_db()
            
            if topic == POST_VIEW_TOPIC:
                viewed_at = datetime.fromisoformat(data["viewed_at"])
                
                view = StatsView(
                    view_id=data["view_id"],
                    post_id=data["post_id"],
                    user_id=data["user_id"],
                    viewed_at=viewed_at
                )
                
                db.execute(
                    "INSERT INTO post_views (view_id, post_id, user_id, viewed_at) VALUES",
                    [view.to_dict()]
                )
                logger.info(f"Processed view event for post {data['post_id']}")
                
            elif topic == POST_LIKE_TOPIC:
                liked_at = datetime.fromisoformat(data["liked_at"])
                
                like = StatsLike(
                    like_id=data["like_id"],
                    post_id=data["post_id"],
                    user_id=data["user_id"],
                    liked_at=liked_at
                )
                
                db.execute(
                    "INSERT INTO post_likes (like_id, post_id, user_id, liked_at) VALUES",
                    [like.to_dict()]
                )
                logger.info(f"Processed like event for post {data['post_id']}")
                
            elif topic == POST_COMMENT_TOPIC:
                created_at = datetime.fromisoformat(data["created_at"])
                
                comment = StatsComment(
                    comment_id=data["comment_id"],
                    post_id=data["post_id"],
                    user_id=data["user_id"],
                    text=data["text"],
                    created_at=created_at
                )
                
                db.execute(
                    "INSERT INTO post_comments (comment_id, post_id, user_id, text, created_at) VALUES",
                    [comment.to_dict()]
                )
                logger.info(f"Processed comment event for post {data['post_id']}")
                
            else:
                logger.warning(f"Unknown topic: {topic}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def consume_messages(self):
        if not self.consumer:
            logger.error("Kafka consumer not initialized")
            return
            
        try:
            logger.info(f"Starting to consume from topics: {self.topics}")
            
            for message in self.consumer:
                if not self.running:
                    break
                self.process_message(message)
                
        except Exception as e:
            logger.error(f"Error consuming messages from Kafka: {str(e)}")
        finally:
            if self.consumer:
                self.consumer.close()
                logger.info("Kafka consumer closed")
    
    def start(self):
        if self.thread and self.thread.is_alive():
            logger.warning("Consumer is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self.consume_messages)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Kafka consumer started in background thread")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            logger.info("Kafka consumer thread stopped")
        
        if self.consumer:
            self.consumer.close()
            self.consumer = None
            logger.info("Kafka consumer closed")


def init_kafka_consumer():
    global _kafka_consumer_instance
    _kafka_consumer_instance = KafkaMessageConsumer()


def get_kafka_consumer():
    global _kafka_consumer_instance
    if not _kafka_consumer_instance:
        init_kafka_consumer()
    return _kafka_consumer_instance


def close_kafka_consumer():
    global _kafka_consumer_instance
    if _kafka_consumer_instance:
        _kafka_consumer_instance.stop()
        _kafka_consumer_instance = None
