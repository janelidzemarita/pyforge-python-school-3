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
    autoflush=False,
    bind=test_engine)

# Create a TestClient instance
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_teardown():
    client.post(
        "/molecule",
        json={"identifier": "water", "smiles": "O"}
    )
    client.post(
        "/molecule",
        json={"identifier": "methane", "smiles": "C"}
    )
    client.post(
        "/molecule",
        json={"identifier": "ethanol", "smiles": "CCO"}
    )
    client.post(
        "/molecule",
        json={"identifier": "benzene", "smiles": "c1ccccc1"}
    )
    client.post(
        "/molecule",
        json={"identifier": "acetic_acid", "smiles": "CC(O)=O"}
    )
    client.post(
        "/molecule",
        json={"identifier": "aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"}
    )
    yield

    # Teardown: Drop the database tables
    Base.metadata.drop_all(bind=test_engine)


def test_delete_molecule(setup_teardown):
    response = client.delete("/molecule/ethanol")
    assert response.status_code == 200
    assert response.json() == {"message": "Molecule deleted successfully."}

    # Check the deletion
    response = client.get("/molecule/ethanol")
    assert response.status_code == 400


# Run the tests with the following command:
# pytest tests/test_delete_molecule.py
