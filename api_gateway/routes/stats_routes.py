from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime, date
import grpc
import jwt
import os

from grpc_client.stats_client import StatsClient

router = APIRouter()
stats_client = StatsClient()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
JWT_SECRET = os.getenv("JWT_SECRET", "thenromanov-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


class PostStats(BaseModel):
    post_id: str
    views: int
    likes: int
    comments: int


class TimelineEntry(BaseModel):
    date: str
    count: int


class PostTimeline(BaseModel):
    entries: List[TimelineEntry]


class TopPostEntry(BaseModel):
    post_id: str
    title: str
    count: int


class TopUserEntry(BaseModel):
    user_id: str
    username: str
    count: int


class TopPosts(BaseModel):
    posts: List[TopPostEntry]


class TopUsers(BaseModel):
    users: List[TopUserEntry]


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


@router.get("/posts/{post_id}", response_model=PostStats)
async def get_post_stats(post_id: str, current_user: dict = Depends(get_current_user)):
    try:
        response = stats_client.get_post_stats(post_id=post_id)
        return {
            "post_id": post_id,
            "views": response.views,
            "likes": response.likes,
            "comments": response.comments
        }
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Stats for post ID {post_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error getting post stats: {e.details()}",
        )


@router.get("/posts/{post_id}/views/timeline", response_model=PostTimeline)
async def get_post_views_timeline(
    post_id: str, 
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_current_user)
):
    try:
        response = stats_client.get_post_views_timeline(post_id=post_id, days=days)
        return {"entries": [{"date": entry.date, "count": entry.count} for entry in response.entries]}
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Stats for post ID {post_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error getting views timeline: {e.details()}",
        )


@router.get("/posts/{post_id}/likes/timeline", response_model=PostTimeline)
async def get_post_likes_timeline(
    post_id: str, 
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_current_user)
):
    try:
        response = stats_client.get_post_likes_timeline(post_id=post_id, days=days)
        return {"entries": [{"date": entry.date, "count": entry.count} for entry in response.entries]}
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Stats for post ID {post_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error getting likes timeline: {e.details()}",
        )


@router.get("/posts/{post_id}/comments/timeline", response_model=PostTimeline)
async def get_post_comments_timeline(
    post_id: str, 
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_current_user)
):
    try:
        response = stats_client.get_post_comments_timeline(post_id=post_id, days=days)
        return {"entries": [{"date": entry.date, "count": entry.count} for entry in response.entries]}
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Stats for post ID {post_id} not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error getting comments timeline: {e.details()}",
        )


@router.get("/top/posts", response_model=TopPosts)
async def get_top_posts(
    metric: str = Query("views", description="Metric to use: views, likes, or comments"),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    try:
        response = stats_client.get_top_posts(metric_type=metric, limit=limit)
        return {
            "posts": [
                {"post_id": post.post_id, "title": post.title, "count": post.count}
                for post in response.posts
            ]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error getting top posts: {e.details()}",
        )


@router.get("/top/users", response_model=TopUsers)
async def get_top_users(
    metric: str = Query("views", description="Metric to use: views, likes, or comments"),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    try:
        response = stats_client.get_top_users(metric_type=metric, limit=limit)
        return {
            "users": [
                {"user_id": user.user_id, "username": user.username, "count": user.count}
                for user in response.users
            ]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except grpc.RpcError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error getting top users: {e.details()}",
        )
