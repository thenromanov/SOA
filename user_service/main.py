import concurrent.futures
import grpc
import time
import logging
import signal
import sys
from grpc_server.user_server import UserServicer
from proto import user_pb2_grpc
from db.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    logger.info("Stopping")
    if "server" in globals():
        server.stop(0)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def serve():
    global server
    logger.info("DB init")
    init_db()

    logger.info("gRPC starting")
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServicer(), server)

    server.add_insecure_port("[::]:50051")
    server.start()

    logger.info("gRPC running")

    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)
        logger.info("gRPC stopped")


if __name__ == "__main__":
    serve()
