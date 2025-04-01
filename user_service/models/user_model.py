import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from db.database import Base, get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


def find_user_by_email(email):
    try:
        db = get_db()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.info(f"Not found: {email}")
            return None

        return {
            "_id": str(user.id),
            "username": user.username,
            "email": user.email,
            "password": user.password,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
    except Exception as e:
        logger.error(f"Find error: {e}")
        raise


def create_user(user_data):
    db = get_db()
    try:
        new_user = User(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            created_at=user_data.get("created_at", datetime.now()),
            updated_at=user_data.get("updated_at", datetime.now()),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"Created: {new_user.email}")

        return {"_id": str(new_user.id), "username": new_user.username, "email": new_user.email}
    except Exception as e:
        db.rollback()
        logger.error(f"Create error: {e}")
        raise
