from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from grpc_client.user_client import UserClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

user_client = UserClient()


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    try:
        logger.info(f"Register: {user.email}")
        response = user_client.register(user.username, user.email, user.password)
        if not response.success:
            logger.warning(f"Register err: {response.message}")
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=response.message)
        logger.info(f"Registered: {user.email}")
        return {"message": response.message}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Register error: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")


@router.post("/login")
async def login_user(user: UserLogin):
    try:
        logger.info(f"Login: {user.email}")
        response = user_client.login(user.email, user.password)
        if not response.success:
            logger.warning(f"Login err: {response.message}")
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=response.message)
        logger.info(f"Logged in: {user.email}")
        return {
            "message": response.message,
            "token": response.token,
            "user": {
                "id": response.user.id,
                "username": response.user.username,
                "email": response.user.email,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")
