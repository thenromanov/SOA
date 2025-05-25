import logging
import grpc
from datetime import datetime
from concurrent import futures
from proto import stats_pb2, stats_pb2_grpc
from models.stats_model import StatsView, StatsLike, StatsComment
from db.database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StatsServicer(stats_pb2_grpc.StatsServiceServicer):
    def GetPostStats(self, request, context):
        try:
            logger.info(f"Getting stats for post: {request.post_id}")
            
            db = get_db()
            
            views = db.execute(
                "SELECT COUNT(*) FROM post_views WHERE post_id = %(post_id)s",
                {"post_id": request.post_id}
            )[0][0]
            
            likes = db.execute(
                "SELECT COUNT(*) FROM post_likes WHERE post_id = %(post_id)s",
                {"post_id": request.post_id}
            )[0][0]
            
            comments = db.execute(
                "SELECT COUNT(*) FROM post_comments WHERE post_id = %(post_id)s",
                {"post_id": request.post_id}
            )[0][0]
            
            logger.info(f"Retrieved stats for post {request.post_id}: views={views}, likes={likes}, comments={comments}")
            
            return stats_pb2.PostStatsResponse(
                views=views,
                likes=likes,
                comments=comments
            )
        except Exception as e:
            logger.error(f"Error in GetPostStats: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return stats_pb2.PostStatsResponse()

    def GetPostViewsTimeline(self, request, context):
        try:
            logger.info(f"Getting views timeline for post: {request.post_id}")
            
            db = get_db()
            
            params = {
                "post_id": request.post_id
            }
            
            query = """
                SELECT 
                    toDate(viewed_at) as day,
                    COUNT(*) as count
                FROM post_views
                WHERE post_id = %(post_id)s
            """

            params = {"post_id": request.post_id}
            
            if request.start_date:
                try:
                    start_date = datetime.strptime(request.start_date, '%Y-%m-%d').date()
                    query += " AND toDate(viewed_at) >= %(start_date)s"
                    params["start_date"] = start_date
                except ValueError:
                    logger.warning(f"Invalid start_date format: {request.start_date}")
            
            if request.end_date:
                try:
                    end_date = datetime.strptime(request.end_date, '%Y-%m-%d').date()
                    query += " AND toDate(viewed_at) <= %(end_date)s"
                    params["end_date"] = end_date
                except ValueError:
                    logger.warning(f"Invalid end_date format: {request.end_date}")
            
            query += " GROUP BY day ORDER BY day"
            
            result = db.execute(query, params)
            
            entries = [
                stats_pb2.TimelineEntry(date=day.strftime('%Y-%m-%d'), count=count)
                for day, count in result
            ]
            
            logger.info(f"Retrieved views timeline for post {request.post_id}: {len(entries)} entries")
            
            return stats_pb2.PostTimelineResponse(entries=entries)
        except Exception as e:
            logger.error(f"Error in GetPostViewsTimeline: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return stats_pb2.PostTimelineResponse()


    def GetPostLikesTimeline(self, request, context):
        try:
            logger.info(f"Getting likes timeline for post: {request.post_id}")
            
            db = get_db()
            
            query = """
                SELECT 
                    toDate(liked_at) as day,
                    COUNT(*) as count
                FROM post_likes
                WHERE post_id = %(post_id)s
            """
            
            params = {"post_id": request.post_id}
            
            if request.start_date:
                try:
                    start_date = datetime.strptime(request.start_date, '%Y-%m-%d').date()
                    query += " AND toDate(liked_at) >= %(start_date)s"
                    params["start_date"] = start_date
                except ValueError:
                    logger.warning(f"Invalid start_date format: {request.start_date}")
            
            if request.end_date:
                try:
                    end_date = datetime.strptime(request.end_date, '%Y-%m-%d').date()
                    query += " AND toDate(liked_at) <= %(end_date)s"
                    params["end_date"] = end_date
                except ValueError:
                    logger.warning(f"Invalid end_date format: {request.end_date}")
            
            query += " GROUP BY day ORDER BY day"
            
            result = db.execute(query, params)
            
            entries = [
                stats_pb2.TimelineEntry(date=day.strftime('%Y-%m-%d'), count=count)
                for day, count in result
            ]
            
            logger.info(f"Retrieved likes timeline for post {request.post_id}: {len(entries)} entries")
            
            return stats_pb2.PostTimelineResponse(entries=entries)
        except Exception as e:
            logger.error(f"Error in GetPostLikesTimeline: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return stats_pb2.PostTimelineResponse()

    def GetPostCommentsTimeline(self, request, context):
        try:
            logger.info(f"Getting comments timeline for post: {request.post_id}")
            
            db = get_db()
            
            query = """
                SELECT 
                    toDate(created_at) as day,
                    COUNT(*) as count
                FROM post_comments
                WHERE post_id = %(post_id)s
            """
            
            params = {"post_id": request.post_id}
            
            if request.start_date:
                try:
                    start_date = datetime.strptime(request.start_date, '%Y-%m-%d').date()
                    query += " AND toDate(created_at) >= %(start_date)s"
                    params["start_date"] = start_date
                except ValueError:
                    logger.warning(f"Invalid start_date format: {request.start_date}")
            
            if request.end_date:
                try:
                    end_date = datetime.strptime(request.end_date, '%Y-%m-%d').date()
                    query += " AND toDate(created_at) <= %(end_date)s"
                    params["end_date"] = end_date
                except ValueError:
                    logger.warning(f"Invalid end_date format: {request.end_date}")
            
            query += " GROUP BY day ORDER BY day"
            
            result = db.execute(query, params)
            
            entries = [
                stats_pb2.TimelineEntry(date=day.strftime('%Y-%m-%d'), count=count)
                for day, count in result
            ]
            
            logger.info(f"Retrieved comments timeline for post {request.post_id}: {len(entries)} entries")
            
            return stats_pb2.PostTimelineResponse(entries=entries)
        except Exception as e:
            logger.error(f"Error in GetPostCommentsTimeline: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return stats_pb2.PostTimelineResponse()

    def GetTopPosts(self, request, context):
        try:
            metric_type = "views"
            if request.metric_type == stats_pb2.TopRequest.MetricType.LIKES:
                metric_type = "likes"
            elif request.metric_type == stats_pb2.TopRequest.MetricType.COMMENTS:
                metric_type = "comments"
            
            limit = request.limit if request.limit > 0 else 10
            
            logger.info(f"Getting top {limit} posts by {metric_type}")
            
            db = get_db()
            
            if metric_type == "views":
                table = "post_views"
            elif metric_type == "likes":
                table = "post_likes"
            elif metric_type == "comments":
                table = "post_comments"
            
            query = f"""
                SELECT 
                    post_id,
                    COUNT(*) as count
                FROM {table}
                GROUP BY post_id
                ORDER BY count DESC
                LIMIT {limit}
            """
            
            result = db.execute(query)
            
            entries = [
                stats_pb2.TopPostEntry(
                    post_id=post_id,
                    count=count
                )
                for post_id, count in result
            ]
            
            logger.info(f"Retrieved top {len(entries)} posts by {metric_type}")
            
            return stats_pb2.TopPostsResponse(posts=entries)
        except Exception as e:
            logger.error(f"Error in GetTopPosts: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return stats_pb2.TopPostsResponse()

    def GetTopUsers(self, request, context):
        try:
            metric_type = "views"
            if request.metric_type == stats_pb2.TopRequest.MetricType.LIKES:
                metric_type = "likes"
            elif request.metric_type == stats_pb2.TopRequest.MetricType.COMMENTS:
                metric_type = "comments"
            
            limit = request.limit if request.limit > 0 else 10
            
            logger.info(f"Getting top {limit} users by {metric_type}")
            
            db = get_db()
            
            if metric_type == "views":
                table = "post_views"
            elif metric_type == "likes":
                table = "post_likes"
            elif metric_type == "comments":
                table = "post_comments"
            
            query = f"""
                SELECT 
                    user_id,
                    COUNT(*) as count
                FROM {table}
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT {limit}
            """
            
            result = db.execute(query)
            
            entries = [
                stats_pb2.TopUserEntry(
                    user_id=user_id,
                    count=count
                )
                for user_id, count in result
            ]
            
            logger.info(f"Retrieved top {len(entries)} users by {metric_type}")
            
            return stats_pb2.TopUsersResponse(users=entries)
        except Exception as e:
            logger.error(f"Error in GetTopUsers: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return stats_pb2.TopUsersResponse()
