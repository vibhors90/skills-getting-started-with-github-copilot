"""
FastAPI Activity Tests using AAA (Arrange-Act-Assert) Pattern

Tests follow the AAA pattern where each test is structured as:
- Arrange: Set up test data and preconditions
- Act: Execute the action being tested
- Assert: Verify the results
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, sample_activities):
        """
        Arrange: Client is ready
        Act: GET /activities
        Assert: Response contains activities with expected structure
        """
        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Verify at least the sample activities exist
        for activity_name in sample_activities.keys():
            assert activity_name in data

    def test_get_activities_response_structure(self, client):
        """
        Arrange: Client is ready
        Act: GET /activities
        Assert: Response structure contains all required fields
        """
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert - verify first activity has required fields
        first_activity = next(iter(data.values()))
        assert "description" in first_activity
        assert "schedule" in first_activity
        assert "max_participants" in first_activity
        assert "participants" in first_activity
        assert isinstance(first_activity["participants"], list)

    def test_get_activities_participants_is_list(self, client):
        """
        Arrange: Client is ready
        Act: GET /activities
        Assert: Participants field is a list
        """
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity in data.values():
            assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_student_success(self, client, valid_email):
        """
        Arrange: Student email not yet registered, activity exists
        Act: POST signup with valid email and activity name
        Assert: Student is added to participants, returns 200
        """
        activity_name = "Chess Club"

        # Arrange - verify student not yet registered
        response_before = client.get("/activities")
        participants_before = response_before.json()[activity_name]["participants"]
        assert valid_email not in participants_before

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": valid_email}
        )

        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert valid_email in response.json()["message"]

        # Assert - verify participant was added
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity_name]["participants"]
        assert valid_email in participants_after

    def test_signup_duplicate_student_returns_conflict(self, client, registered_email):
        """
        Arrange: Student already registered for activity
        Act: POST signup with email of already-registered student
        Assert: Returns 400 error, student not duplicated
        """
        activity_name = "Chess Club"

        # Arrange - verify student is already registered
        response_check = client.get("/activities")
        participants = response_check.json()[activity_name]["participants"]
        initial_count = len(participants)
        assert registered_email in participants

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": registered_email}
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

        # Assert - verify participant list unchanged
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity_name]["participants"]
        assert len(participants_after) == initial_count

    def test_signup_nonexistent_activity_returns_not_found(self, client, valid_email):
        """
        Arrange: Activity does not exist
        Act: POST signup for non-existent activity
        Assert: Returns 404 error
        """
        activity_name = "NonexistentActivity"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": valid_email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_different_activities(self, client, valid_email):
        """
        Arrange: Student not registered for multiple activities
        Act: POST signup to multiple activities
        Assert: Student successfully added to all activities
        """
        activities = ["Chess Club", "Programming Class"]

        # Act & Assert for each activity
        for activity_name in activities:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": valid_email}
            )
            assert response.status_code == 200

        # Assert - verify student in all activities
        response_check = client.get("/activities")
        data = response_check.json()
        for activity_name in activities:
            assert valid_email in data[activity_name]["participants"]

    @pytest.mark.parametrize("email", [
        "student@mergington.edu",
        "another.student@mergington.edu",
        "student+tag@mergington.edu",
    ])
    def test_signup_various_email_formats(self, client, email):
        """
        Arrange: Various valid email formats
        Act: POST signup with different email formats
        Assert: All emails accepted and added to participants
        """
        activity_name = "Art Studio"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200

        # Verify added
        response_check = client.get("/activities")
        assert email in response_check.json()[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_registered_student_success(self, client, registered_email):
        """
        Arrange: Student is registered for activity
        Act: POST unregister for registered student
        Assert: Student removed from participants, returns 200
        """
        activity_name = "Chess Club"

        # Arrange - verify student is registered
        response_check = client.get("/activities")
        participants_before = response_check.json()[activity_name]["participants"]
        assert registered_email in participants_before

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": registered_email}
        )

        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

        # Assert - verify participant was removed
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity_name]["participants"]
        assert registered_email not in participants_after

    def test_unregister_non_registered_student_returns_error(self, client, valid_email):
        """
        Arrange: Student is NOT registered for activity
        Act: POST unregister for non-registered student
        Assert: Returns 400 error, no changes made
        """
        activity_name = "Programming Class"

        # Arrange - verify student not registered
        response_check = client.get("/activities")
        participants_before = response_check.json()[activity_name]["participants"]
        assert valid_email not in participants_before
        initial_count = len(participants_before)

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": valid_email}
        )

        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

        # Assert - verify participants unchanged
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity_name]["participants"]
        assert len(participants_after) == initial_count

    def test_unregister_from_nonexistent_activity_returns_not_found(self, client, registered_email):
        """
        Arrange: Activity does not exist
        Act: POST unregister from non-existent activity
        Assert: Returns 404 error
        """
        activity_name = "NonexistentActivity"

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": registered_email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_then_signup_again(self, client, registered_email):
        """
        Arrange: Student is registered for activity
        Act: Unregister, then sign up again
        Assert: Student successfully re-registered
        """
        activity_name = "Basketball Team"

        # Arrange - verify student is registered
        response_check = client.get("/activities")
        assert registered_email in response_check.json()[activity_name]["participants"]

        # Act - unregister
        response_unregister = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": registered_email}
        )
        assert response_unregister.status_code == 200

        # Assert - verify removed
        response_after_unregister = client.get("/activities")
        assert registered_email not in response_after_unregister.json()[activity_name]["participants"]

        # Act - sign up again
        response_signup = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": registered_email}
        )

        # Assert
        assert response_signup.status_code == 200
        response_final = client.get("/activities")
        assert registered_email in response_final.json()[activity_name]["participants"]


class TestActivityStateConsistency:
    """Tests to verify data integrity across operations"""

    def test_participant_count_after_signup(self, client, valid_email):
        """
        Arrange: Known participant count
        Act: Add new participant
        Assert: Count increases by exactly 1
        """
        activity_name = "Theater Club"

        # Arrange
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])

        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": valid_email}
        )

        # Assert
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])
        assert count_after == count_before + 1

    def test_participant_count_after_unregister(self, client, registered_email):
        """
        Arrange: Known participant count with registered student
        Act: Remove participant
        Assert: Count decreases by exactly 1
        """
        activity_name = "Chess Club"

        # Arrange
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])

        # Act
        client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": registered_email}
        )

        # Assert
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])
        assert count_after == count_before - 1

    def test_no_duplicate_participants_after_multiple_operations(self, client, valid_email):
        """
        Arrange: Activity with initial participants
        Act: Signup new student multiple times (should fail after first)
        Assert: No duplicates in participant list
        """
        activity_name = "Debate Team"

        # Act - first signup should succeed
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": valid_email}
        )
        assert response1.status_code == 200

        # Act - duplicate signup should fail
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": valid_email}
        )
        assert response2.status_code == 400

        # Assert - verify only one instance in participants
        response_check = client.get("/activities")
        participants = response_check.json()[activity_name]["participants"]
        count = participants.count(valid_email)
        assert count == 1
