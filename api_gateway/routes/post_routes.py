from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import grpc
import jwt
import os

from grpc_client.post_client import PostClient

router = APIRouter()
post_client = PostClient()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
JWT_SECRET = os.getenv("JWT_SECRET", "thenromanov-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


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


class CommentCreate(BaseModel):
    text: str


class Comment(BaseModel):
    id: str
    post_id: str
    user_id: str
    text: str
    created_at: datetime


class GetCommentsResponse(BaseModel):
    comments: List[Comment]
    total: int
    page: int
    page_size: int


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("id")
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
                detail=f"Internal server error: {e.details()}",
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
        return Response(status_code=status.HTTP_204_NO_CONTENT)
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


@router.post("/{post_id}/view", status_code=status.HTTP_200_OK)
async def view_post(post_id: str, current_user: dict = Depends(get_current_user)):
    try:
        post_client.view_post(post_id=post_id, user_id=current_user["user_id"])
        return {"message": "Post viewed successfully"}
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Post ID {post_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error viewing post: {e.details()}",
        )


@router.post("/{post_id}/like", status_code=status.HTTP_200_OK)
async def like_post(post_id: str, current_user: dict = Depends(get_current_user)):
    try:
        post_client.like_post(post_id=post_id, user_id=current_user["user_id"])
        return {"message": "Post liked successfully"}
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Post ID {post_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error liking post: {e.details()}",
        )


@router.post("/{post_id}/comment", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def add_comment(
    post_id: str, 
    comment_data: CommentCreate,
    current_user: dict = Depends(get_current_user)
):
    try:
        comment = post_client.add_comment(
            post_id=post_id,
            user_id=current_user["user_id"],
            text=comment_data.text
        )
        
        return {
            "id": comment.id,
            "post_id": comment.post_id,
            "user_id": comment.user_id,
            "text": comment.text,
            "created_at": datetime.fromisoformat(comment.created_at)
        }
    except grpc.RpcError as e:
        handle_grpc_error(e, "adding comment", post_id)


@router.get("/{post_id}/comments", response_model=GetCommentsResponse)
async def get_comments(
    post_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    try:
        response = post_client.get_comments(
            post_id=post_id,
            page=page,
            page_size=page_size
        )
        
        comments = []
        for c in response.comments:
            comments.append({
                "id": c.id,
                "post_id": c.post_id,
                "user_id": c.user_id,
                "text": c.text,
                "created_at": datetime.fromisoformat(c.created_at)
            })
        
        return {
            "comments": comments,
            "total": response.total,
            "page": response.page,
            "page_size": response.page_size
        }
    except grpc.RpcError as e:
        handle_grpc_error(e, "getting comments", post_id)