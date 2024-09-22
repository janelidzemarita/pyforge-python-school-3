import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app
from database.database import Base
from database.models import Molecule

# Test database URL
DATABASE_URL = "postgresql://postgres:password@localhost:5432/test_database"

# Create an engine and session local
test_engine = create_engine(DATABASE_URL)

# Initialize the database
Molecule.metadata.create_all(bind=test_engine)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    bind=test_engine)

# Create a TestClient instance
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_teardown():

    yield

    # Teardown: Drop the database tables
    Base.metadata.drop_all(bind=test_engine)


def test_add_molecule(setup_teardown):

    response = client.post(
        "/molecule",
        json={"identifier": "new_test", "smiles": "CCO"}
    )
    assert response.status_code == 200
    assert response.json() == {"identifier": "new_test", "smiles": "CCO"}

    # Test adding a molecule with the same identifier (should fail)
    response = client.post(
        "/molecule",
        json={"identifier": "new_test", "smiles": "C"}
    )
    assert response.status_code == 400

    # Cleanup
    client.delete("/molecule/new_test")
