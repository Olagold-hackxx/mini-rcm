"""Pytest configuration and fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

try:
    from models.database import Base, User
    from main import app
    from utils.security import get_password_hash
    from db.session import get_db
    from config import get_settings
except ImportError:
    # Handle imports for testing
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.database import Base, User
    from main import app
    from utils.security import get_password_hash
    from db.session import get_db
    from config import get_settings

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite:///./test_claims.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        tenant_id="default",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(client, test_user):
    """Get authentication token for test user."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "testpass123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def authenticated_client(client, auth_token):
    """Create an authenticated test client."""
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch("openai.OpenAI") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        
        # Mock embeddings
        mock_instance.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        
        # Mock chat completions
        mock_instance.chat.completions.create.return_value = Mock(
            choices=[Mock(
                message=Mock(
                    content='{"technical_validation_status": "PASS", "medical_validation_status": "PASS", "explanation": "Valid claim"}'
                )
            )]
        )
        
        yield mock_instance


@pytest.fixture
def sample_claim_data():
    """Sample claim data for testing."""
    return {
        "claim_id": "TEST001",
        "encounter_type": "OUTPATIENT",
        "service_date": "2025-01-15",
        "national_id": "NID001",
        "member_id": "M001",
        "facility_id": "FAC001",
        "unique_id": "NID0-M001-FAC0",
        "diagnosis_codes": ["E11.9"],
        "service_code": "SRV2007",
        "paid_amount_aed": 500.0,
        "approval_number": "APRV001",
    }


@pytest.fixture
def sample_claims_file(tmp_path):
    """Create a sample CSV file for testing."""
    import csv
    import pandas as pd
    
    file_path = tmp_path / "test_claims.csv"
    df = pd.DataFrame({
        "claim_id": ["C001", "C002"],
        "encounter_type": ["OUTPATIENT", "INPATIENT"],
        "service_date": ["2025-01-15", "2025-01-16"],
        "national_id": ["NID001", "NID002"],
        "member_id": ["M001", "M002"],
        "facility_id": ["FAC001", "FAC002"],
        "unique_id": ["NID0-M001-FAC0", "NID0-M002-FAC0"],
        "diagnosis_codes": ["E11.9", "J45.909"],
        "service_code": ["SRV2007", "SRV1001"],
        "paid_amount_aed": [500.0, 1000.0],
        "approval_number": ["APRV001", "APRV002"],
    })
    df.to_csv(file_path, index=False)
    return str(file_path)

