import concurrent.futures
import grpc
import time
import logging
import os
import signal
import sys
from grpc_server.stats_server import StatsServicer
from proto import stats_pb2_grpc
from db.database import init_db
from broker.consumer import init_kafka_consumer, get_kafka_consumer, close_kafka_consumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    logger.info("Stopping")
    if server:
        server.stop(0)
    close_kafka_consumer()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def serve():
    global server
    
    logger.info("ClickHouse init")
    init_db()
    
    logger.info("Kafka consumer init")
    init_kafka_consumer()
    get_kafka_consumer().start()
    
    logger.info("gRPC starting")
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    stats_pb2_grpc.add_StatsServiceServicer_to_server(StatsServicer(), server)
    
    port = os.getenv("GRPC_PORT", "50053")
    
    server.add_insecure_port(f"[::]:{str(port)}")
    server.start()
    
    logger.info(f"gRPC stats server launched on port {str(port)}")
    
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
