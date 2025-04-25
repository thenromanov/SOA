import grpc
from api_gateway.proto import post_pb2, post_pb2_grpc


class PostClient:
    def __init__(self, host="post_service", port=50052):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = post_pb2_grpc.PostServiceStub(self.channel)

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
