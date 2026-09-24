import pytest
from db import DatabaseRepository


@pytest.fixture
def test_repo(tmp_path):
    """Fresh in-memory SQLite DB for each test."""
    db_path = tmp_path / "test.db"
    repo = DatabaseRepository(db_url=f"sqlite:///{db_path}")
    # Create schema from ORM models
    from db import Base
    Base.metadata.create_all(repo.engine)
    return repo


def test_create_and_verify_user(test_repo):
    """User creation and password verification roundtrip."""
    created = test_repo.create_user("testuser", "securepass123")
    assert created is True

    user_id, message = test_repo.verify_user("testuser", "securepass123")
    assert user_id is not None
    assert message == "Success"


def test_duplicate_user_rejected(test_repo):
    """Duplicate usernames must be rejected."""
    test_repo.create_user("alice", "pass1")
    created_again = test_repo.create_user("alice", "pass2")
    assert created_again is False


def test_wrong_password_increments_attempts(test_repo):
    """Wrong password should return None with attempt count message."""
    test_repo.create_user("bob", "correctpass")
    user_id, message = test_repo.verify_user("bob", "wrongpass")
    assert user_id is None
    assert "4 attempts remaining" in message


def test_lockout_after_five_failures(test_repo):
    """Account locks after 5 consecutive failures."""
    test_repo.create_user("charlie", "realpass")
    for _ in range(5):
        test_repo.verify_user("charlie", "wrongpass")
    user_id, message = test_repo.verify_user("charlie", "wrongpass")
    assert user_id is None
    assert "locked" in message.lower()


def test_save_and_load_project(test_repo):
    """Save then load a project for a user."""
    test_repo.create_user("designer", "pass")
    user_id, _ = test_repo.verify_user("designer", "pass")

    test_repo.save_project(
        user_id=user_id,
        project_name="Villa Alpha",
        plot_length=30.0,
        plot_width=20.0,
        num_floors=3,
        prompt_data={"raw_prompt": "Modern villa"}
    )

    projects = test_repo.load_user_projects(user_id)
    assert len(projects) == 1
    assert projects[0]["name"] == "Villa Alpha"
    assert projects[0]["floors"] == 3
    assert projects[0]["data"]["raw_prompt"] == "Modern villa"


def test_nonexistent_user_returns_none(test_repo):
    """Verifying a nonexistent user must return None."""
    user_id, message = test_repo.verify_user("ghost", "anypass")
    assert user_id is None
    assert "Invalid" in message
