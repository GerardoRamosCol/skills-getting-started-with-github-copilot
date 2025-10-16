"""
Test cases for the Activities API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


class TestActivitiesAPI:
    """Test class for activities API endpoints."""
    
    def test_root_redirect(self, client, reset_activities):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "static/index.html" in response.headers["location"]
    
    def test_get_activities(self, client, reset_activities):
        """Test retrieving all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Check structure of activity data
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test signup for non-existent activity returns 404."""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_participant(self, client, reset_activities):
        """Test that duplicate signup is prevented."""
        # Try to sign up an already registered participant
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_unregister_participant_success(self, client, reset_activities):
        """Test successful participant unregistration."""
        # Verify participant exists first
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" in activities_data["Chess Club"]["participants"]
        
        # Unregister the participant
        response = client.delete(
            "/activities/Chess Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregistration from non-existent activity returns 404."""
        response = client.delete(
            "/activities/Nonexistent Club/participants/student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_non_registered_participant(self, client, reset_activities):
        """Test unregistering a participant who is not registered."""
        response = client.delete(
            "/activities/Chess Club/participants/notregistered@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "not registered" in data["detail"].lower()
    
    def test_activity_capacity_tracking(self, client, reset_activities):
        """Test that activity capacity is properly tracked."""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        initial_participants = len(chess_club["participants"])
        max_participants = chess_club["max_participants"]
        
        # Calculate expected spots
        expected_spots = max_participants - initial_participants
        
        # This test verifies the data structure is consistent
        assert initial_participants <= max_participants
        assert expected_spots >= 0
    
    def test_multiple_activity_operations(self, client, reset_activities):
        """Test multiple signup and unregister operations."""
        # Sign up a new participant
        signup_response = client.post(
            "/activities/Programming Class/signup?email=testuser@mergington.edu"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "testuser@mergington.edu" in activities_data["Programming Class"]["participants"]
        
        # Unregister the participant
        unregister_response = client.delete(
            "/activities/Programming Class/participants/testuser@mergington.edu"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        final_activities_response = client.get("/activities")
        final_activities_data = final_activities_response.json()
        assert "testuser@mergington.edu" not in final_activities_data["Programming Class"]["participants"]