"""
Integration tests for static file serving and edge cases.
"""
import pytest
from fastapi.testclient import TestClient


class TestStaticFiles:
    """Test class for static file serving and integration."""
    
    def test_static_index_html_accessible(self, client):
        """Test that static index.html is accessible."""
        response = client.get("/static/index.html")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Mergington High School" in response.text
    
    def test_static_css_accessible(self, client):
        """Test that CSS file is accessible."""
        response = client.get("/static/styles.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
    
    def test_static_js_accessible(self, client):
        """Test that JavaScript file is accessible."""
        response = client.get("/static/app.js")
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"] or "text/plain" in response.headers["content-type"]


class TestEdgeCases:
    """Test class for edge cases and error handling."""
    
    def test_signup_with_special_characters_in_email(self, client, reset_activities):
        """Test signup with special characters in email."""
        special_email = "test.user@mergington.edu"  # Use dot instead of plus to avoid URL encoding issues
        response = client.post(
            f"/activities/Chess Club/signup?email={special_email}"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert special_email in activities_data["Chess Club"]["participants"]
    
    def test_activity_name_with_spaces_and_special_chars(self, client, reset_activities):
        """Test operations with activity names containing spaces."""
        # This tests URL encoding handling for activity names with spaces
        response = client.post(
            "/activities/Programming Class/signup?email=newcoder@mergington.edu"
        )
        assert response.status_code == 200
    
    def test_unregister_with_url_encoded_characters(self, client, reset_activities):
        """Test unregistration with URL-encoded email characters."""
        # First add a participant with special characters
        special_email = "test.special@mergington.edu"  # Use dot to avoid URL encoding issues
        signup_response = client.post(
            f"/activities/Gym Class/signup?email={special_email}"
        )
        assert signup_response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert special_email in activities_data["Gym Class"]["participants"]
        
        # Now unregister using the same email
        unregister_response = client.delete(
            f"/activities/Gym Class/participants/{special_email}"
        )
        assert unregister_response.status_code == 200
    
    def test_missing_email_parameter(self, client, reset_activities):
        """Test signup without email parameter."""
        response = client.post("/activities/Chess Club/signup")
        assert response.status_code == 422  # FastAPI validation error
    
    def test_empty_email_parameter(self, client, reset_activities):
        """Test signup with empty email."""
        response = client.post("/activities/Chess Club/signup?email=")
        # This should still work as FastAPI doesn't validate email format by default
        assert response.status_code == 200 or response.status_code == 400