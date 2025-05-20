from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Boolean, DateTime, Table, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from db.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    creator_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_private = Column(Boolean, default=False)
    tags = Column(ARRAY(String), default=[])

    views = relationship("PostView", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")


class PostView(Base):
    __tablename__ = "post_views"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, nullable=False)
    viewed_at = Column(DateTime, default=datetime.now)
    
    post = relationship("Post", back_populates="views")
    
    def __repr__(self):
        return f"<PostView(id='{self.id}', post_id='{self.post_id}', user_id='{self.user_id}')>"


class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, nullable=False)
    liked_at = Column(DateTime, default=datetime.now)
    
    post = relationship("Post", back_populates="likes")
    
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="post_id_and_user_id"),
    )
    
    def __repr__(self):
        return f"<PostLike(id='{self.id}', post_id='{self.post_id}', user_id='{self.user_id}')>"


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    post = relationship("Post", back_populates="comments")
    
    def __repr__(self):
        return f"<Comment(id='{self.id}', post_id='{self.post_id}', user_id='{self.user_id}')>"
