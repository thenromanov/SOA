import logging
import uuid
import grpc
from concurrent import futures
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from proto import post_pb2, post_pb2_grpc
from models.post_model import Post, PostView, PostLike, Comment
from db.database import get_db
from broker.producer import get_kafka_producer, POST_VIEW_TOPIC, POST_LIKE_TOPIC, POST_COMMENT_TOPIC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostServicer(post_pb2_grpc.PostServiceServicer):
    def CreatePost(self, request, context):
        db = get_db()
        try:
            post_id = str(uuid.uuid4())
            now = datetime.now()

            logger.info(f"Create post: {post_id}")

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
            
            logger.info(f"Post created successfully: {post_id}")

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
            logger.error(f"Create post error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error creating post: {str(e)}")
            return post_pb2.Post()
        finally:
            db.close()

    def UpdatePost(self, request, context):
        db = get_db()
        try:
            logger.info(f"Update post: {request.id}")

            post = db.query(Post).filter(Post.id == request.id).first()

            if not post:
                logger.warning(f"Update post: {request.id} not found")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post ID {request.id} not found")
                return post_pb2.Post()

            if post.creator_id != request.creator_id:
                logger.warning(f"Update post: permission denied for post {request.id} by user {request.creator_id}")
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
            
            logger.info(f"Post updated successfully: {request.id}")

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
            logger.error(f"Update post error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error updating post: {str(e)}")
            return post_pb2.Post()
        finally:
            db.close()

    def DeletePost(self, request, context):
        db = get_db()
        try:
            logger.info(f"Delete post: {request.id}")
            
            post = db.query(Post).filter(Post.id == request.id).first()

            if not post:
                logger.warning(f"Delete post: {request.id} not found")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post ID {request.id} not found")
                return post_pb2.DeleteResponse(success=False)

            if post.creator_id != request.creator_id:
                logger.warning(f"Delete post: permission denied for post {request.id} by user {request.creator_id}")
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("Permission denied")
                return post_pb2.DeleteResponse(success=False)

            db.delete(post)
            db.commit()
            
            logger.info(f"Post deleted successfully: {request.id}")

            return post_pb2.DeleteResponse(success=True)
        except Exception as e:
            db.rollback()
            logger.error(f"Delete post error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error deleting post: {str(e)}")
            return post_pb2.DeleteResponse(success=False)
        finally:
            db.close()

    def GetPost(self, request, context):
        db = get_db()
        try:
            logger.info(f"Get post: {request.id}")
            
            post = db.query(Post).filter(Post.id == request.id).first()

            if not post:
                logger.warning(f"Get post: {request.id} not found")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post ID {request.id} not found")
                return post_pb2.Post()

            if post.is_private and post.creator_id != request.user_id:
                logger.warning(f"Get post: permission denied for private post {request.id} by user {request.user_id}")
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("Permission denied")
                return post_pb2.Post()
            
            logger.info(f"Post retrieved successfully: {request.id}")

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
            logger.error(f"Get post error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting post: {str(e)}")
            return post_pb2.Post()
        finally:
            db.close()

    def ListPosts(self, request, context):
        db = get_db()
        try:
            logger.info(f"List posts: page={request.page}, page_size={request.page_size}, user_id={request.user_id}")
            
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
            
            logger.info(f"Retrieved {len(posts)} posts out of {total}")

            return response
        except Exception as e:
            logger.error(f"List posts error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Error getting post list: {str(e)}")
            return post_pb2.ListPostsResponse()
        finally:
            db.close()

    def ViewPost(self, request, context):
        db = get_db()
        try:
            logger.info(f"View post: {request.post_id} by user {request.user_id}")
            
            post = db.query(Post).filter(Post.id == request.post_id).first()
            if not post:
                logger.warning(f"View post: {request.post_id} not found")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post ID {request.post_id} not found")
                return post_pb2.ViewPostResponse()
            
            if post.is_private and post.creator_id != request.user_id:
                logger.warning(f"View post: permission denied for private post {request.post_id} by user {request.user_id}")
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("You don't have permission to view this post")
                return post_pb2.ViewPostResponse()
            
            view_id = str(uuid.uuid4())
            post_view = PostView(
                id=view_id,
                post_id=request.post_id,
                user_id=request.user_id,
                viewed_at=datetime.now()
            )
            db.add(post_view)
            db.commit()
            
            event = {
                "view_id": view_id,
                "post_id": request.post_id,
                "user_id": request.user_id,
                "viewed_at": post_view.viewed_at.isoformat()
            }
            
            sent = get_kafka_producer().send_message(POST_VIEW_TOPIC, event)
            if sent:
                logger.info(f"Post view event sent: post_id={request.post_id}, user_id={request.user_id}")
            else:
                logger.warning(f"Failed to send post view event to Kafka: post_id={request.post_id}")
            
            logger.info(f"Post view recorded successfully: {request.post_id}")
            
            return post_pb2.ViewPostResponse()
        except Exception as e:
            db.rollback()
            logger.error(f"View post error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal server error: {str(e)}")
            return post_pb2.ViewPostResponse()
        finally:
            db.close()
    
    def LikePost(self, request, context):
        db = get_db()
        try:
            logger.info(f"Like post: {request.post_id} by user {request.user_id}")
            
            post = db.query(Post).filter(Post.id == request.post_id).first()
            if not post:
                logger.warning(f"Like post: {request.post_id} not found")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post ID {request.post_id} not found")
                return post_pb2.LikePostResponse()
            
            if post.is_private and post.creator_id != request.user_id:
                logger.warning(f"Like post: permission denied for private post {request.post_id} by user {request.user_id}")
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("You don't have permission to like this post")
                return post_pb2.LikePostResponse()
            
            existing_like = db.query(PostLike).filter(
                PostLike.post_id == request.post_id,
                PostLike.user_id == request.user_id
            ).first()
            
            if existing_like:
                logger.warning(f"Like post: already liked post {request.post_id} by user {request.user_id}")
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details("You have already liked this post")
                return post_pb2.LikePostResponse()
            
            like_id = str(uuid.uuid4())
            post_like = PostLike(
                id=like_id,
                post_id=request.post_id,
                user_id=request.user_id,
                liked_at=datetime.now()
            )
            db.add(post_like)
            db.commit()

            event = {
                "like_id": like_id,
                "post_id": request.post_id,
                "user_id": request.user_id,
                "liked_at": post_like.liked_at.isoformat()
            }
            
            sent = get_kafka_producer().send_message(POST_LIKE_TOPIC, event)
            if sent:
                logger.info(f"Post like event sent: post_id={request.post_id}, user_id={request.user_id}")
            else:
                logger.warning(f"Failed to send post like event to Kafka: post_id={request.post_id}")
            
            logger.info(f"Post like recorded successfully: {request.post_id}")
            
            return post_pb2.LikePostResponse()
        except Exception as e:
            db.rollback()
            logger.error(f"Like post error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal server error: {str(e)}")
            return post_pb2.LikePostResponse()
        finally:
            db.close()
    
    def AddComment(self, request, context):
        db = get_db()
        try:
            logger.info(f"Add comment to post: {request.post_id} by user {request.user_id}")
            
            post = db.query(Post).filter(Post.id == request.post_id).first()
            if not post:
                logger.warning(f"Add comment: post {request.post_id} not found")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post ID {request.post_id} not found")
                return post_pb2.Comment()
            
            if post.is_private and post.creator_id != request.user_id:
                logger.warning(f"Add comment: permission denied for private post {request.post_id} by user {request.user_id}")
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("You don't have permission to comment on this post")
                return post_pb2.Comment()
            
            comment_id = str(uuid.uuid4())
            created_at = datetime.now()
            
            comment = Comment(
                id=comment_id,
                post_id=request.post_id,
                user_id=request.user_id,
                text=request.text,
                created_at=created_at
            )
            db.add(comment)
            db.commit()

            event = {
                "comment_id": comment_id,
                "post_id": request.post_id,
                "user_id": request.user_id,
                "text": request.text,
                "created_at": created_at.isoformat(),
            }
            
            sent = get_kafka_producer().send_message(POST_COMMENT_TOPIC, event)
            if sent:
                logger.info(f"Post comment event sent: post_id={request.post_id}, user_id={request.user_id}")
            else:
                logger.warning(f"Failed to send post comment event to Kafka: post_id={request.post_id}")
            
            logger.info(f"Comment added successfully: {comment_id} to post {request.post_id}")
            
            return post_pb2.Comment(
                id=comment_id,
                post_id=request.post_id,
                user_id=request.user_id,
                text=request.text,
                created_at=created_at.isoformat()
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Add comment error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal server error: {str(e)}")
            return post_pb2.Comment()
        finally:
            db.close()
    
    def GetComments(self, request, context):
        db = get_db()
        try:
            logger.info(f"Get comments for post: {request.post_id}, page={request.page}, page_size={request.page_size}")

            post = db.query(Post).filter(Post.id == request.post_id).first()
            if not post:
                logger.warning(f"Get comments: post {request.post_id} not found")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Post with ID {request.post_id} not found")
                return post_pb2.GetCommentsResponse()
            
            if post.is_private and post.creator_id != request.user_id:
                logger.warning(f"Get comments: permission denied for private post {request.post_id}")
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                context.set_details("You don't have permission to view comments of this post")
                return post_pb2.GetCommentsResponse()
            
            total_comments = db.query(Comment).filter(
                Comment.post_id == request.post_id
            ).count()
            
            page = max(1, request.page)
            page_size = max(1, min(100, request.page_size))
            
            comments = db.query(Comment).filter(
                Comment.post_id == request.post_id
            ).order_by(
                desc(Comment.created_at)
            ).offset(
                (page - 1) * page_size
            ).limit(
                page_size
            ).all()
            
            comment_list = []
            for c in comments:
                comment_pb = post_pb2.Comment(
                    id=c.id,
                    post_id=c.post_id,
                    user_id=c.user_id,
                    text=c.text,
                    created_at=c.created_at.isoformat()
                )
                comment_list.append(comment_pb)
            
            logger.info(f"Retrieved {len(comments)} comments out of {total_comments} for post {request.post_id}")
            
            return post_pb2.GetCommentsResponse(
                comments=comment_list,
                total=total_comments,
                page=page,
                page_size=page_size,
            )
        except Exception as e:
            logger.error(f"Get comments error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal server error: {str(e)}")
            return post_pb2.GetCommentsResponse()
        finally:
            db.close()
