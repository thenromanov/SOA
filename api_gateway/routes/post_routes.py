from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import grpc
import jwt
import os

from api_gateway.grpc_client.post_client import PostClient

router = APIRouter()
post_client = PostClient()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


class TagList(BaseModel):
    tags: List[str] = []


class PostBase(BaseModel):
    title: str
    description: str
    is_private: bool = False
    tags: List[str] = []


class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    pass


class Post(PostBase):
    id: str
    creator_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class PaginatedResponse(BaseModel):
    posts: List[Post]
    total: int
    page: int
    page_size: int


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"user_id": user_id}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, current_user: dict = Depends(get_current_user)):
    try:
        response = post_client.create_post(
            title=post.title,
            description=post.description,
            creator_id=current_user["user_id"],
            is_private=post.is_private,
            tags=post.tags,
        )
        return {
            "id": response.id,
            "title": response.title,
            "description": response.description,
            "creator_id": response.creator_id,
            "created_at": datetime.fromisoformat(response.created_at),
            "updated_at": datetime.fromisoformat(response.updated_at),
            "is_private": response.is_private,
            "tags": list(response.tags),
        }
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.INTERNAL:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error`: {e.details()}",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating post: {e.details()}",
        )


@router.put("/{post_id}", response_model=Post)
async def update_post(
    post_id: str, post: PostUpdate, current_user: dict = Depends(get_current_user)
):
    try:
        response = post_client.update_post(
            post_id=post_id,
            title=post.title,
            description=post.description,
            creator_id=current_user["user_id"],
            is_private=post.is_private,
            tags=post.tags,
        )
        return {
            "id": response.id,
            "title": response.title,
            "description": response.description,
            "creator_id": response.creator_id,
            "created_at": datetime.fromisoformat(response.created_at),
            "updated_at": datetime.fromisoformat(response.updated_at),
            "is_private": response.is_private,
            "tags": list(response.tags),
        }
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Post ID {post_id} not found"
            )
        elif e.code() == grpc.StatusCode.PERMISSION_DENIED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating post: {e.details()}",
        )


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: str, current_user: dict = Depends(get_current_user)):
    try:
        response = post_client.delete_post(post_id=post_id, creator_id=current_user["user_id"])
        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Post ID {post_id} not found"
            )
        return None
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Post ID {post_id} not found"
            )
        elif e.code() == grpc.StatusCode.PERMISSION_DENIED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error deleting post: {e.details()}",
        )


@router.get("/{post_id}", response_model=Post)
async def get_post(post_id: str, current_user: dict = Depends(get_current_user)):
    try:
        response = post_client.get_post(post_id=post_id, user_id=current_user["user_id"])
        return {
            "id": response.id,
            "title": response.title,
            "description": response.description,
            "creator_id": response.creator_id,
            "created_at": datetime.fromisoformat(response.created_at),
            "updated_at": datetime.fromisoformat(response.updated_at),
            "is_private": response.is_private,
            "tags": list(response.tags),
        }
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Post ID {post_id} not found"
            )
        elif e.code() == grpc.StatusCode.PERMISSION_DENIED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error getting post: {e.details()}",
        )


@router.get("/", response_model=PaginatedResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    try:
        response = post_client.list_posts(
            page=page, page_size=page_size, user_id=current_user["user_id"]
        )

        posts = []
        for post in response.posts:
            posts.append(
                {
                    "id": post.id,
                    "title": post.title,
                    "description": post.description,
                    "creator_id": post.creator_id,
                    "created_at": datetime.fromisoformat(post.created_at),
                    "updated_at": datetime.fromisoformat(post.updated_at),
                    "is_private": post.is_private,
                    "tags": list(post.tags),
                }
            )

        return {
            "posts": posts,
            "total": response.total,
            "page": response.page,
            "page_size": response.page_size,
        }
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error getting post list: {e.details()}",
        )
