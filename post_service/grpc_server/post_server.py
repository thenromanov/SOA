import uuid
import grpc
from concurrent import futures
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from post_service.proto import post_pb2, post_pb2_grpc
from post_service.models.post_model import Post
from post_service.db.database import SessionLocal, engine, Base


class PostServicer(post_pb2_grpc.PostServiceServicer):
    def __init__(self):
        Base.metadata.create_all(bind=engine)

    def CreatePost(self, request, context):
        db = SessionLocal()
        try:
            post_id = str(uuid.uuid4())
            now = datetime.now()

            post = Post(
                id=post_id,
                title=request.title,
                description=request.description,
                creator_id=request.creator_id,
                created_at=now,
                updated_at=now,
                is_private=request.is_private,
                tags=list(request.tags),
            )

            db.add(post)
            db.commit()
            db.refresh(post)

            return post_pb2.Post(
                id=post.id,
                title=post.title,
                description=post.description,
                creator_id=post.creator_id,
                created_at=post.created_at.isoformat(),
                updated_at=post.updated_at.isoformat(),
                is_private=post.is_private,
                tags=post.tags,
            )
        except Exception as e:
            db.rollback()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error creating post: {str(e)}")
            return post_pb2.Post()
        finally:
            db.close()

    def UpdatePost(self, request, context):
        db = SessionLocal()
        try:
            post = db.query(Post).filter(Post.id == request.id).first()

            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post ID {request.id} not found")
                return post_pb2.Post()

            if post.creator_id != request.creator_id:
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("Permission denied")
                return post_pb2.Post()

            post.title = request.title
            post.description = request.description
            post.is_private = request.is_private
            post.tags = list(request.tags)
            post.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(post)

            return post_pb2.Post(
                id=post.id,
                title=post.title,
                description=post.description,
                creator_id=post.creator_id,
                created_at=post.created_at.isoformat(),
                updated_at=post.updated_at.isoformat(),
                is_private=post.is_private,
                tags=post.tags,
            )
        except Exception as e:
            db.rollback()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error updating post: {str(e)}")
            return post_pb2.Post()
        finally:
            db.close()

    def DeletePost(self, request, context):
        db = SessionLocal()
        try:
            post = db.query(Post).filter(Post.id == request.id).first()

            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post ID {request.id} not found")
                return post_pb2.DeleteResponse(success=False)

            if post.creator_id != request.creator_id:
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("Permission denied")
                return post_pb2.DeleteResponse(success=False)

            db.delete(post)
            db.commit()

            return post_pb2.DeleteResponse(success=True)
        except Exception as e:
            db.rollback()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error deleting post: {str(e)}")
            return post_pb2.DeleteResponse(success=False)
        finally:
            db.close()

    def GetPost(self, request, context):
        db = SessionLocal()
        try:
            post = db.query(Post).filter(Post.id == request.id).first()

            if not post:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post ID {request.id} not found")
                return post_pb2.Post()

            if post.is_private and post.creator_id != request.user_id:
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("Permission denied")
                return post_pb2.Post()

            return post_pb2.Post(
                id=post.id,
                title=post.title,
                description=post.description,
                creator_id=post.creator_id,
                created_at=post.created_at.isoformat(),
                updated_at=post.updated_at.isoformat(),
                is_private=post.is_private,
                tags=post.tags,
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting post: {str(e)}")
            return post_pb2.Post()
        finally:
            db.close()

    def ListPosts(self, request, context):
        db = SessionLocal()
        try:
            query = db.query(Post).filter(
                or_(
                    Post.is_private == False,
                    and_(Post.is_private == True, Post.creator_id == request.user_id),
                )
            )

            total = query.count()

            posts = (
                query.limit(request.page_size).offset((request.page - 1) * request.page_size).all()
            )

            response = post_pb2.ListPostsResponse(
                total=total, page=request.page, page_size=request.page_size
            )

            for post in posts:
                response.posts.append(
                    post_pb2.Post(
                        id=post.id,
                        title=post.title,
                        description=post.description,
                        creator_id=post.creator_id,
                        created_at=post.created_at.isoformat(),
                        updated_at=post.updated_at.isoformat(),
                        is_private=post.is_private,
                        tags=post.tags,
                    )
                )

            return response
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting post list: {str(e)}")
            return post_pb2.ListPostsResponse()
        finally:
            db.close()
