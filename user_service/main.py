import concurrent.futures
import grpc
import time
import logging
import signal
import sys
from grpc_server.user_server import UserServicer
from proto import user_pb2_grpc
from db.database import init_db
from broker.producer import init_kafka_producer, close_kafka_producer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    logger.info("Stopping")
    if "server" in globals():
        server.stop(0)
        close_kafka_producer() 
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def serve():
    global server

    logger.info("DB init")
    init_db()

    logger.info("Kafka init")
    init_kafka_producer()

    logger.info("gRPC starting")
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServicer(), server)

    port = 50051

    server.add_insecure_port(f"[::]:{str(port)}")
    server.start()

    logger.info(f"gRPC user server launched on port {str(port)}")

    server.wait_for_termination()


if __name__ == "__main__":
    serve()
