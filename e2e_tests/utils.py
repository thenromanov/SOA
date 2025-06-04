import requests
import time

def wait_for_condition(condition_func, timeout=10, interval=1):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False

def check_stats(base_url, post_id, auth_headers, expected_views=None, expected_likes=None, expected_comments=None):
    def condition():
        stats_url = f"{base_url}/stats/posts/{post_id}"
        stats_response = requests.get(stats_url, headers=auth_headers)
        if stats_response.status_code != 200:
            return False
        
        stats = stats_response.json()
        
        if expected_views is not None and stats['views'] != expected_views:
            return False
        if expected_likes is not None and stats['likes'] != expected_likes:
            return False
        if expected_comments is not None and stats['comments'] != expected_comments:
            return False
        return True
    
    return wait_for_condition(condition, timeout=15)

def check_top_posts(base_url, auth_headers, expected_post_id, min_count=1, metric="likes", limit=1):
    def condition():
        top_url = f"{base_url}/stats/top/posts?metric={metric}&limit={limit}"
        top_response = requests.get(top_url, headers=auth_headers)
        if top_response.status_code != 200:
            return False
        
        top_posts = top_response.json().get("posts", [])
        
        if not top_posts:
            return False
        
        for post in top_posts:
            if post["post_id"] == expected_post_id and post["count"] >= min_count:
                return True
        return False
    
    return wait_for_condition(condition, timeout=15)

def check_top_users(base_url, auth_headers, expected_user_id, min_count=1, metric="comments", limit=1):
    def condition():
        top_url = f"{base_url}/stats/top/users?metric={metric}&limit={limit}"
        top_response = requests.get(top_url, headers=auth_headers)
        if top_response.status_code != 200:
            return False
        
        top_users = top_response.json().get("users", [])
        
        if not top_users:
            return False
        
        for user in top_users:
            if user["user_id"] == expected_user_id and user["count"] >= min_count:
                return True
        return False
    
    return wait_for_condition(condition, timeout=15)