import os
import grpc
import logging
import time
from proto import stats_pb2, stats_pb2_grpc
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatsClient:
    def __init__(self):
        self.server_address = os.getenv("STATS_SERVICE_ADDRESS", "stats-service:50053")
        self.channel = None
        self.stub = None
        self.connect_with_retry()
    
    def connect_with_retry(self, max_retries=5, retry_delay=2):
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to stats service {self.server_address} (attempt {attempt+1})")
                self.channel = grpc.insecure_channel(self.server_address)
                self.stub = stats_pb2_grpc.StatsServiceStub(self.channel)
                grpc.channel_ready_future(self.channel).result(timeout=5)
                logger.info(f"Connected to stats service at {self.server_address}")
                return
            except grpc.FutureTimeoutError:
                logger.warning(f"Connection timeout (attempt {attempt+1})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Connection to stats service failed after all retries")
                    raise Exception("Connection error to stats service")

    def get_post_stats(self, post_id):
        request = stats_pb2.PostStatsRequest(post_id=post_id)
        return self.stub.GetPostStats(request)
    
    def get_post_views_timeline(self, post_id, days=7):
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        request = stats_pb2.PostTimelineRequest(
            post_id=post_id,
            start_date=start_date,
            end_date=end_date
        )
        return self.stub.GetPostViewsTimeline(request)
    
    def get_post_likes_timeline(self, post_id, days=7):
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        request = stats_pb2.PostTimelineRequest(
            post_id=post_id,
            start_date=start_date,
            end_date=end_date
        )
        return self.stub.GetPostLikesTimeline(request)
    
    def get_post_comments_timeline(self, post_id, days=7):
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        request = stats_pb2.PostTimelineRequest(
            post_id=post_id,
            start_date=start_date,
            end_date=end_date
        )
        return self.stub.GetPostCommentsTimeline(request)
    
    def get_top_posts(self, metric_type="VIEWS", limit=10):
        try:
            metric = stats_pb2.TopRequest.MetricType.Value(metric_type.upper())
        except ValueError:
            raise ValueError(f"Invalid metric type: {metric_type}")
            
        request = stats_pb2.TopRequest(
            metric_type=metric,
            limit=limit
        )
        return self.stub.GetTopPosts(request)

    def get_top_users(self, metric_type="VIEWS", limit=10):
        try:
            metric = stats_pb2.TopRequest.MetricType.Value(metric_type.upper())
        except ValueError:
            raise ValueError(f"Invalid metric type: {metric_type}")
            
        request = stats_pb2.TopRequest(
            metric_type=metric,
            limit=limit
        )
        return self.stub.GetTopUsers(request)

