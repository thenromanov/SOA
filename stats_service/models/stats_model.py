from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

class StatsView:
    def __init__(self, 
                 view_id: str = None, 
                 post_id: str = None, 
                 user_id: str = None, 
                 viewed_at: datetime = None):
        self.view_id = view_id or str(uuid.uuid4())
        self.post_id = post_id
        self.user_id = user_id
        self.viewed_at = viewed_at or datetime.now()
        self.event_date = self.viewed_at.date()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'view_id': self.view_id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'viewed_at': self.viewed_at,
            'event_date': self.event_date
        }
    
    def __repr__(self):
        return f"<StatsView(view_id='{self.view_id}', post_id='{self.post_id}', user_id='{self.user_id}')>"


class StatsLike:
    def __init__(self, 
                 like_id: str = None, 
                 post_id: str = None, 
                 user_id: str = None, 
                 liked_at: datetime = None):
        self.like_id = like_id or str(uuid.uuid4())
        self.post_id = post_id
        self.user_id = user_id
        self.liked_at = liked_at or datetime.now()
        self.event_date = self.liked_at.date()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'like_id': self.like_id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'liked_at': self.liked_at,
            'event_date': self.event_date
        }
    
    def __repr__(self):
        return f"<StatsLike(like_id='{self.like_id}', post_id='{self.post_id}', user_id='{self.user_id}')>"


class StatsComment:
    def __init__(self, 
                 comment_id: str = None, 
                 post_id: str = None, 
                 user_id: str = None, 
                 text: str = None, 
                 created_at: datetime = None):
        self.comment_id = comment_id or str(uuid.uuid4())
        self.post_id = post_id
        self.user_id = user_id
        self.text = text
        self.created_at = created_at or datetime.now()
        self.event_date = self.created_at.date()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'comment_id': self.comment_id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'text': self.text,
            'created_at': self.created_at,
            'event_date': self.event_date
        }
    
    def __repr__(self):
        return f"<StatsComment(comment_id='{self.comment_id}', post_id='{self.post_id}', user_id='{self.user_id}')>"
