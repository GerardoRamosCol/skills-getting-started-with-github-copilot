"""
Performance and load tests for the Activities API.
"""
import pytest
import asyncio
import concurrent.futures
from fastapi.testclient import TestClient


class TestPerformance:
    """Test class for performance and concurrent operations."""
    
    def test_concurrent_signups_different_activities(self, client, reset_activities):
        """Test concurrent signups to different activities."""
        def signup_user(activity_email_pair):
            activity, email = activity_email_pair
            return client.post(f"/activities/{activity}/signup?email={email}")
        
        # Prepare test data for concurrent signups
        signup_data = [
            ("Chess Club", "concurrent1@mergington.edu"),
            ("Programming Class", "concurrent2@mergington.edu"),
            ("Gym Class", "concurrent3@mergington.edu"),
        ]
        
        # Execute concurrent signups
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(signup_user, data) for data in signup_data]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All signups should succeed
        for result in results:
            assert result.status_code == 200
        
        # Verify all participants were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        assert "concurrent1@mergington.edu" in activities_data["Chess Club"]["participants"]
        assert "concurrent2@mergington.edu" in activities_data["Programming Class"]["participants"]
        assert "concurrent3@mergington.edu" in activities_data["Gym Class"]["participants"]
    
    def test_rapid_signup_unregister_operations(self, client, reset_activities):
        """Test rapid signup and unregister operations."""
        test_email = "rapidtest@mergington.edu"
        activity = "Programming Class"
        
        # Perform multiple rapid operations
        for i in range(5):
            # Signup
            signup_response = client.post(f"/activities/{activity}/signup?email={test_email}")
            assert signup_response.status_code == 200
            
            # Verify signup
            activities_response = client.get("/activities")
            activities_data = activities_response.json()
            assert test_email in activities_data[activity]["participants"]
            
            # Unregister
            unregister_response = client.delete(f"/activities/{activity}/participants/{test_email}")
            assert unregister_response.status_code == 200
            
            # Verify unregistration
            activities_response = client.get("/activities")
            activities_data = activities_response.json()
            assert test_email not in activities_data[activity]["participants"]
    
    def test_multiple_api_calls_performance(self, client, reset_activities):
        """Test performance of multiple API calls."""
        import time
        
        start_time = time.time()
        
        # Make multiple calls to different endpoints
        for i in range(10):
            # Get activities
            activities_response = client.get("/activities")
            assert activities_response.status_code == 200
            
            # Try signup (some will fail due to duplicates, which is expected)
            client.post(f"/activities/Chess Club/signup?email=test{i}@mergington.edu")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time (less than 2 seconds for 20 operations)
        assert total_time < 2.0, f"Operations took {total_time} seconds, which is too long"


class TestDataConsistency:
    """Test class for data consistency and integrity."""
    
    def test_activity_data_immutable_structure(self, client, reset_activities):
        """Test that activity data structure remains consistent."""
        # Get initial state
        response1 = client.get("/activities")
        initial_data = response1.json()
        
        # Perform some operations
        client.post("/activities/Chess Club/signup?email=consistency@mergington.edu")
        client.delete("/activities/Chess Club/participants/michael@mergington.edu")
        
        # Get final state
        response2 = client.get("/activities")
        final_data = response2.json()
        
        # Structure should remain the same
        for activity_name in initial_data:
            assert activity_name in final_data
            for key in ["description", "schedule", "max_participants", "participants"]:
                assert key in final_data[activity_name]
                
        # Only participants should have changed
        assert initial_data["Chess Club"]["description"] == final_data["Chess Club"]["description"]
        assert initial_data["Chess Club"]["schedule"] == final_data["Chess Club"]["schedule"]
        assert initial_data["Chess Club"]["max_participants"] == final_data["Chess Club"]["max_participants"]
    
    def test_participant_count_consistency(self, client, reset_activities):
        """Test that participant counts remain consistent."""
        # Get initial participant count
        response = client.get("/activities")
        initial_data = response.json()
        initial_count = len(initial_data["Programming Class"]["participants"])
        
        # Add a participant
        client.post("/activities/Programming Class/signup?email=counter@mergington.edu")
        
        # Check count increased by 1
        response = client.get("/activities")
        data = response.json()
        new_count = len(data["Programming Class"]["participants"])
        assert new_count == initial_count + 1
        
        # Remove a participant
        client.delete("/activities/Programming Class/participants/counter@mergington.edu")
        
        # Check count is back to original
        response = client.get("/activities")
        data = response.json()
        final_count = len(data["Programming Class"]["participants"])
        assert final_count == initial_count