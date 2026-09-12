import os
import pytest
from db import DatabaseRepository

# Setup a clean in-memory database for testing
@pytest.fixture
def test_repo():
    repo = DatabaseRepository("sqlite:///:memory:")
    # Initialize the schema
    from db import Base
    Base.metadata.create_all(repo.engine)
    return repo

def test_user_creation_and_verification(test_repo):
    # Test user creation
    assert test_repo.create_user("testuser", "securepassword") == True
    # Test duplicate creation
    assert test_repo.create_user("testuser", "anotherpassword") == False

    # Test verification
    uid, msg = test_repo.verify_user("testuser", "securepassword")
    assert uid is not None
    assert msg == "Success"

    # Test invalid password
    uid, msg = test_repo.verify_user("testuser", "wrongpassword")
    assert uid is None
    assert "Invalid credentials" in msg

def test_project_save_and_load(test_repo):
    test_repo.create_user("arch_user", "password123")
    uid, _ = test_repo.verify_user("arch_user", "password123")
    
    test_repo.save_project(
        user_id=uid,
        project_name="Test Villa",
        plot_length=100,
        plot_width=50,
        num_floors=2,
        prompt_data={"style": "Modern"}
    )
    
    projects = test_repo.load_user_projects(uid)
    assert len(projects) == 1
    assert projects[0]["name"] == "Test Villa"
    assert projects[0]["l"] == 100
    assert projects[0]["w"] == 50
    assert projects[0]["floors"] == 2
    assert projects[0]["data"]["style"] == "Modern"
