import os
import grpc
import logging
import time
from proto import user_pb2, user_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserClient:
    def __init__(self):
        self.server_address = os.getenv("USER_SERVICE_ADDRESS", "user-service:50051")
        self.channel = None
        self.stub = None
        self.connect_with_retry()

    def connect_with_retry(self, max_retries=5, retry_delay=2):
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting {self.server_address} {attempt+1}")
                self.channel = grpc.insecure_channel(self.server_address)
                self.stub = user_pb2_grpc.UserServiceStub(self.channel)
                grpc.channel_ready_future(self.channel).result(timeout=5)
                logger.info(f"Connected {self.server_address}")
                return
            except grpc.FutureTimeoutError:
                logger.warning(f"Timeout {attempt+1}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Connection failed")
                    raise Exception("Connection error")

    def register(self, username, email, password):
        try:
            request = user_pb2.RegisterRequest(username=username, email=email, password=password)
            logger.info(f"Register {email}")
            return self.stub.Register(request)
        except grpc.RpcError as e:
            logger.error(f"Register error {e}")
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                logger.info("Reconnect")
                self.connect_with_retry()
                request = user_pb2.RegisterRequest(
                    username=username, email=email, password=password
                )
                return self.stub.Register(request)
            raise

    def login(self, email, password):
        try:
            request = user_pb2.LoginRequest(email=email, password=password)
            logger.info(f"Login {email}")
            return self.stub.Login(request)
        except grpc.RpcError as e:
            logger.error(f"Login error {e}")
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                logger.info("Reconnect")
                self.connect_with_retry()
                request = user_pb2.LoginRequest(email=email, password=password)
                return self.stub.Login(request)
            raise
