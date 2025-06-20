import pytest
import requests
import time
from .utils import check_stats, check_top_posts, check_top_users

BASE_URL = os.getenv("BASE_URL", "http://api-gateway:3000")

def test_create_post_and_view_stats(wait_for_services, test_user, auth_headers, generate_random_string):
    create_post_url = f"{BASE_URL}/posts/create"
    post_data = {
        "title": f"Test Post {generate_random_string(6)}",
        "description": "Test post content",
        "is_private": False,
        "tags": ["test", "e2e"]
    }
    
    create_response = requests.post(create_post_url, json=post_data, headers=auth_headers)
    assert create_response.status_code == 201, "Post creation failed"
    post = create_response.json()
    post_id = post.get("id")
    assert post_id, "Post ID not returned"
    
    view_post_url = f"{BASE_URL}/posts/{post_id}/view"
    view_response = requests.post(view_post_url, headers=auth_headers)
    assert view_response.status_code == 200, "Post view failed"
    
    assert check_stats(BASE_URL, post_id, auth_headers, expected_views=1), "View count not updated"

def test_likes_and_top_posts(wait_for_services, test_user, auth_headers, generate_random_string):
    create_post_url = f"{BASE_URL}/posts/create"
    post_data = {
        "title": f"Top Post {generate_random_string(6)}",
        "description": "Content for top post",
        "is_private": False
    }
    
    create_response = requests.post(create_post_url, json=post_data, headers=auth_headers)
    assert create_response.status_code == 201, "Post creation failed"
    post = create_response.json()
    post_id = post.get("id")
    assert post_id, "Post ID not returned"
    
    like_post_url = f"{BASE_URL}/posts/{post_id}/like"
    like_response = requests.post(like_post_url, headers=auth_headers)
    assert like_response.status_code == 200, "Post like failed"
    
    assert check_top_posts(BASE_URL, auth_headers, post_id, metric="likes"), "Post not found in top likes"

def test_comments_and_top_users(wait_for_services, test_user, auth_headers, generate_random_string):
    create_post_url = f"{BASE_URL}/posts/create"
    post_data = {
        "title": f"Comment Test {generate_random_string(6)}",
        "description": "Post for comments",
        "is_private": False
    }
    
    create_response = requests.post(create_post_url, json=post_data, headers=auth_headers)
    assert create_response.status_code == 201, "Post creation failed"
    post = create_response.json()
    post_id = post.get("id")
    assert post_id, "Post ID not returned"
    
    comment_url = f"{BASE_URL}/posts/{post_id}/comment"
    comment_data = {"text": f"Test comment {generate_random_string(6)}"}
    comment_response = requests.post(comment_url, json=comment_data, headers=auth_headers)
    assert comment_response.status_code == 201, "Comment creation failed"

    username = test_user['username']
    assert check_top_users(BASE_URL, auth_headers, username, metric="comments"), "User not found in top commenters"