import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities as activities_store, app

client = TestClient(app)
initial_activities = copy.deepcopy(activities_store)


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: restore the in-memory activity state before each test
    activities_store.clear()
    activities_store.update(copy.deepcopy(initial_activities))
    yield
    activities_store.clear()
    activities_store.update(copy.deepcopy(initial_activities))


def test_get_activities_returns_all_activities():
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    encoded_activity = quote(activity_name, safe="")
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{encoded_activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities_store[activity_name]["participants"]


def test_signup_duplicate_returns_400():
    # Arrange
    activity_name = "Chess Club"
    encoded_activity = quote(activity_name, safe="")
    email = "michael@mergington.edu"

    # Act
    response = client.post(f"/activities/{encoded_activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"
    assert activities_store[activity_name]["participants"].count(email) == 1


def test_delete_participant_removes_existing_participant():
    # Arrange
    activity_name = "Chess Club"
    encoded_activity = quote(activity_name, safe="")
    email = "michael@mergington.edu"

    # Act
    response = client.delete(f"/activities/{encoded_activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity_name}"
    assert email not in activities_store[activity_name]["participants"]


def test_delete_unknown_participant_returns_404():
    # Arrange
    activity_name = "Chess Club"
    encoded_activity = quote(activity_name, safe="")
    email = "missing@mergington.edu"

    # Act
    response = client.delete(f"/activities/{encoded_activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
