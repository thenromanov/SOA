import os
import time
import json
import logging
from kafka import KafkaProducer
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

POST_VIEW_TOPIC = "post_views"
POST_LIKE_TOPIC = "post_likes"
POST_COMMENT_TOPIC = "post_comments"
CLIENT_REGISTRATION_TOPIC = "client_registrations"

_kafka_producer_instance = None

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")


class KafkaMessageProducer:    
    def __init__(self, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, max_retries=5, retry_delay=2):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.connect_with_retry(max_retries, retry_delay)
    
    def connect_with_retry(self, max_retries=5, retry_delay=2):
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting Kafka {attempt+1}")
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    api_version=(0, 10, 1)
                )
                self.producer.bootstrap_connected()
                logger.info(f"Kafka connected to {self.bootstrap_servers}")
                return
                
            except Exception as e:
                logger.warning(f"Kafka error {attempt+1}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retry in {retry_delay} sec")
                    time.sleep(retry_delay)
                else:
                    logger.error("Kafka connection failed")
                    raise
    
    def send_message(self, topic, message):
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
            
        try:
            future = self.producer.send(topic, message)
            self.producer.flush()
            record_metadata = future.get(timeout=10)
            logger.info(f"Message sent to topic {topic}")
            logger.debug(f"Message metadata: {record_metadata}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {str(e)}")
            return False
    
    def close(self):
        if self.producer:
            self.producer.close()
            self.producer = None
            logger.info("Kafka producer closed")


def init_kafka_producer():
    global _kafka_producer_instance
    _kafka_producer_instance = KafkaMessageProducer()


def get_kafka_producer():
    global _kafka_producer_instance
    if not _kafka_producer_instance:
        init_kafka_producer()
    return _kafka_producer_instance


def close_kafka_producer():
    global _kafka_producer_instance
    if _kafka_producer_instance:
        _kafka_producer_instance.close()
        _kafka_producer_instance = None
