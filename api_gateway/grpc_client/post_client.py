import os
import grpc
import logging
import time
from proto import post_pb2, post_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostClient:
    def __init__(self):
        self.server_address = os.getenv("POST_SERVICE_ADDRESS", "post-service:50052")
        self.channel = None
        self.stub = None
        self.connect_with_retry()
    
    def connect_with_retry(self,max_retries=5, retry_delay=2):
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting {self.server_address} {attempt+1}")
                self.channel = grpc.insecure_channel(self.server_address)
                self.stub = post_pb2_grpc.PostServiceStub(self.channel)
                grpc.channel_ready_future(self.channel).result(timeout=5)
                logger.info(f"Connected {self.server_address}")
                return
            except grpc.FutureTimeoutError:
                logger.warning(f"Timeout {attempt+1}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Connection failed")
                    raise Exception("Connection error")

    def create_post(self, title, description, creator_id, is_private, tags):
        request = post_pb2.CreatePostRequest(
            title=title,
            description=description,
            creator_id=creator_id,
            is_private=is_private,
            tags=tags,
        )
        return self.stub.CreatePost(request)

    def update_post(self, post_id, title, description, creator_id, is_private, tags):
        request = post_pb2.UpdatePostRequest(
            id=post_id,
            title=title,
            description=description,
            creator_id=creator_id,
            is_private=is_private,
            tags=tags,
        )
        return self.stub.UpdatePost(request)

    def delete_post(self, post_id, creator_id):
        request = post_pb2.DeletePostRequest(id=post_id, creator_id=creator_id)
        return self.stub.DeletePost(request)

    def get_post(self, post_id, user_id):
        request = post_pb2.GetPostRequest(id=post_id, user_id=user_id)
        return self.stub.GetPost(request)

    def list_posts(self, page, page_size, user_id):
        request = post_pb2.ListPostsRequest(page=page, page_size=page_size, user_id=user_id)
        return self.stub.ListPosts(request)

    def view_post(self, post_id, user_id):
        request = post_pb2.ViewPostRequest(
            post_id=post_id,
            user_id=user_id
        )
        return self.stub.ViewPost(request)
    
    def like_post(self, post_id, user_id):
        request = post_pb2.LikePostRequest(
            post_id=post_id,
            user_id=user_id
        )
        return self.stub.LikePost(request)
    
    def add_comment(self, post_id, user_id, text):
        request = post_pb2.AddCommentRequest(
            post_id=post_id,
            user_id=user_id,
            text=text
        )
        return self.stub.AddComment(request)
    
    def get_comments(self, post_id, page=1, page_size=10):
        request = post_pb2.GetCommentsRequest(
            post_id=post_id,
            page=page,
            page_size=page_size
        )
        return self.stub.GetComments(request)