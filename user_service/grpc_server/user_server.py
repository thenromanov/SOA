import logging
import bcrypt
import jwt
import os
import traceback
from datetime import datetime, timedelta
from proto import user_pb2, user_pb2_grpc
from models.user_model import find_user_by_email, create_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserServicer(user_pb2_grpc.UserServiceServicer):
    def Register(self, request, context):
        try:
            logger.info(f"Register: {request.email}")

            if not request.username or not request.email or not request.password:
                logger.warning("Fields missing")
                return user_pb2.RegisterResponse(message="Fields required", success=False)

            existing_user = find_user_by_email(request.email)
            if existing_user:
                logger.warning(f"Exists: {request.email}")
                return user_pb2.RegisterResponse(message="Already exists", success=False)

            hashed_password = bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt())

            user_data = {
                "username": request.username,
                "email": request.email,
                "password": hashed_password.decode("utf-8"),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            create_user(user_data)
            logger.info(f"Registered: {request.email}")
            return user_pb2.RegisterResponse(message="Success", success=True)
        except Exception as e:
            logger.error(f"Register error: {str(e)}")
            logger.error(traceback.format_exc())
            return user_pb2.RegisterResponse(message=f"Register error", success=False)

    def Login(self, request, context):
        try:
            logger.info(f"Login: {request.email}")

            if not request.email or not request.password:
                logger.warning("Fields missing")
                return user_pb2.LoginResponse(message="Fields required", success=False)

            user = find_user_by_email(request.email)
            if not user:
                logger.warning(f"Not found: {request.email}")
                return user_pb2.LoginResponse(message="Invalid credentials", success=False)

            valid = bcrypt.checkpw(
                request.password.encode("utf-8"), user["password"].encode("utf-8")
            )
            if not valid:
                logger.warning(f"Wrong pass: {request.email}")
                return user_pb2.LoginResponse(message="Invalid credentials", success=False)

            secret = os.getenv("JWT_SECRET", "your_jwt_secret")
            expiration = datetime.now() + timedelta(hours=1)
            payload = {
                "id": str(user["_id"]),
                "email": user["email"],
                "exp": expiration.timestamp(),
            }
            token = jwt.encode(payload, secret, algorithm="HS256")

            user_info = user_pb2.UserInfo(
                id=str(user["_id"]), username=user["username"], email=user["email"]
            )

            logger.info(f"Logged in: {request.email}")
            return user_pb2.LoginResponse(
                message="Success", success=True, token=token, user=user_info
            )
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            logger.error(traceback.format_exc())
            return user_pb2.LoginResponse(message="Login error", success=False)
