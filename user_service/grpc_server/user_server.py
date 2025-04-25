import logging
import bcrypt
import jwt
import os
import traceback
from datetime import datetime, timedelta
from proto import user_pb2, user_pb2_grpc
from models.user_model import User
from db.database import get_db
from broker.producer import get_kafka_producer, CLIENT_REGISTRATION_TOPIC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserServicer(user_pb2_grpc.UserServiceServicer):
    def Register(self, request, context):
        db = get_db()
        try:
            logger.info(f"Register: {request.email}")

            if not request.username or not request.email or not request.password:
                logger.warning("Fields missing")
                return user_pb2.RegisterResponse(message="Fields required", success=False)

            user = db.query(User).filter(User.email == request.email).first()
            if user:
                logger.warning(f"Exists: {request.email}")
                return user_pb2.RegisterResponse(message="Already exists", success=False)

            hashed_password = bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt())

            new_user = User(
                username=request.username,
                email=request.email,
                password=hashed_password.decode("utf-8"),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            user_id = str(new_user.id)
            registration_time = datetime.now().isoformat()
            event = {
                "client_id": user_id,
                "username": request.username,
                "email": request.email,
                "registration_time": registration_time
            }

            sent = get_kafka_producer().send_message(CLIENT_REGISTRATION_TOPIC, event)
            if sent:
                logger.info(f"Registration event sent to Kafka: client_id={user_id}")
            else:
                logger.warning(f"Failed to send registration event to Kafka: client_id={user_id}")

            logger.info(f"Registered: {request.email}")
            return user_pb2.RegisterResponse(message="Success", success=True)
        except Exception as e:
            db.rollback()
            logger.error(f"Register error: {str(e)}")
            logger.error(traceback.format_exc())
            return user_pb2.RegisterResponse(message=f"Register error", success=False)
        finally:
            db.close()

    def Login(self, request, context):
        db = get_db()
        try:
            logger.info(f"Login: {request.email}")

            if not request.email or not request.password:
                logger.warning("Fields missing")
                return user_pb2.LoginResponse(message="Fields required", success=False)

            user = db.query(User).filter(User.email == request.email).first()
            if not user:
                logger.warning(f"Not found: {request.email}")
                return user_pb2.LoginResponse(message="Invalid credentials", success=False)

            valid = bcrypt.checkpw(
                request.password.encode("utf-8"), user.password.encode("utf-8")
            )
            if not valid:
                logger.warning(f"Wrong pass: {request.email}")
                return user_pb2.LoginResponse(message="Invalid credentials", success=False)

            secret = os.getenv("JWT_SECRET", "your_jwt_secret")
            expiration = datetime.now() + timedelta(hours=1)
            payload = {
                "id": str(user.id),
                "email": user.email,
                "exp": expiration.timestamp(),
            }
            token = jwt.encode(payload, secret, algorithm="HS256")

            user_info = user_pb2.UserInfo(
                id=str(user.id),
                username=user.username,
                email=user.email
            )

            logger.info(f"Logged in: {request.email}")
            return user_pb2.LoginResponse(
                message="Success", success=True, token=token, user=user_info
            )
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            logger.error(traceback.format_exc())
            return user_pb2.LoginResponse(message="Login error", success=False)
        finally:
            db.close()