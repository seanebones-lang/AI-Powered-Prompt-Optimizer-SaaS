"""
Tests for database models and utilities.
"""
import pytest
import os
import tempfile
from datetime import date

# Set up test environment before importing database module
test_db_path = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
test_db_path.close()
test_db_url = f"sqlite:///{test_db_path.name}"

os.environ["XAI_API_KEY"] = "test_key"
os.environ["SECRET_KEY"] = "test_secret"
os.environ["DATABASE_URL"] = test_db_url

from database import Database, DailyUsage  # noqa: E402
import bcrypt  # noqa: E402


@pytest.fixture
def db_instance():
    """Create a test database instance."""
    # Clean up any existing test database
    if os.path.exists(test_db_path.name):
        os.remove(test_db_path.name)

    db = Database()
    yield db

    # Cleanup
    if os.path.exists(test_db_path.name):
        os.remove(test_db_path.name)


@pytest.fixture
def db_session(db_instance):
    """Get a database session."""
    return db_instance.get_session()


def test_database_initialization(db_instance):
    """Test database initialization creates tables."""
    assert db_instance.engine is not None
    assert db_instance.SessionLocal is not None


def test_create_user(db_instance):
    """Test user creation."""
    user = db_instance.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    assert user is not None
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.id is not None
    assert user.is_active is True
    assert user.is_premium is False


def test_create_duplicate_user(db_instance):
    """Test that duplicate users cannot be created."""
    db_instance.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    # Try to create duplicate
    duplicate = db_instance.create_user(
        email="test@example.com",
        username="testuser2",
        password="password123"
    )

    assert duplicate is None  # Should fail due to duplicate email


def test_authenticate_user(db_instance):
    """Test user authentication."""
    db_instance.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    user = db_instance.authenticate_user("testuser", "password123")
    assert user is not None
    assert user.username == "testuser"

    # Wrong password
    user = db_instance.authenticate_user("testuser", "wrongpassword")
    assert user is None

    # Wrong username
    user = db_instance.authenticate_user("wronguser", "password123")
    assert user is None


def test_get_user(db_instance):
    """Test getting user by ID."""
    created_user = db_instance.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    user = db_instance.get_user(created_user.id)
    assert user is not None
    assert user.id == created_user.id
    assert user.username == "testuser"


def test_check_usage_limit_beta_mode(db_instance):
    """Test usage limit in beta mode (always returns True)."""
    user = db_instance.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    # Beta mode: check_usage_limit always returns True regardless of usage count
    assert db_instance.check_usage_limit(user.id) is True

    # Increment usage many times
    for _ in range(10):
        db_instance.increment_usage(user.id)

    # Should still return True in beta mode
    assert db_instance.check_usage_limit(user.id) is True


def test_check_usage_limit_anonymous_beta_mode(db_instance):
    """Test usage limit for anonymous users in beta mode."""
    # Anonymous users should also get True in beta mode
    assert db_instance.check_usage_limit(None) is True

    # Increment anonymous usage multiple times
    for _ in range(10):
        db_instance.increment_usage(None)

    # Should still return True in beta mode
    assert db_instance.check_usage_limit(None) is True


def test_increment_usage(db_instance):
    """Test usage increment."""
    user = db_instance.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    # Check initial usage
    db_instance.increment_usage(user.id)

    # Get usage count
    session = db_instance.get_session()
    today = date.today()
    usage = session.query(DailyUsage).filter(
        DailyUsage.user_id == user.id,
        DailyUsage.date == today
    ).first()

    assert usage is not None
    assert usage.usage_count == 1

    # Increment again
    db_instance.increment_usage(user.id)
    session.refresh(usage)
    assert usage.usage_count == 2

    session.close()


def test_save_session(db_instance):
    """Test saving optimization session."""
    user = db_instance.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    session = db_instance.save_session(
        user_id=user.id,
        original_prompt="Test prompt",
        prompt_type="creative",
        optimized_prompt="Optimized prompt",
        sample_output="Sample output",
        quality_score=85
    )

    assert session is not None
    assert session.original_prompt == "Test prompt"
    assert session.prompt_type == "creative"
    assert session.optimized_prompt == "Optimized prompt"
    assert session.quality_score == 85
    assert session.user_id == user.id


def test_save_session_anonymous(db_instance):
    """Test saving session for anonymous user."""
    session = db_instance.save_session(
        user_id=None,
        original_prompt="Test prompt",
        prompt_type="technical"
    )

    assert session is not None
    assert session.user_id is None
    assert session.original_prompt == "Test prompt"


def test_get_user_sessions(db_instance):
    """Test retrieving user sessions."""
    user = db_instance.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    # Create multiple sessions
    for i in range(3):
        db_instance.save_session(
            user_id=user.id,
            original_prompt=f"Prompt {i}",
            prompt_type="creative"
        )

    sessions = db_instance.get_user_sessions(user.id, limit=10)
    assert len(sessions) == 3

    # Test limit
    sessions = db_instance.get_user_sessions(user.id, limit=2)
    assert len(sessions) == 2


def test_password_hashing(db_instance):
    """Test that passwords are properly hashed."""
    user = db_instance.create_user(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    # Password should be hashed, not plain text
    assert user.hashed_password != "password123"
    assert len(user.hashed_password) > 20  # bcrypt hashes are long

    # Should verify correctly
    assert bcrypt.checkpw(
        "password123".encode('utf-8'),
        user.hashed_password.encode('utf-8')
    )
