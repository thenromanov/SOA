from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Boolean, DateTime, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

Base = declarative_base()


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
