import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from src.main import app
from database.database import Base
from database.models import Molecule

# Test database URL
DATABASE_URL = "postgresql://postgres:password@localhost:5432/test_database"

# Create an engine and session local
test_engine = create_engine(DATABASE_URL)

# Initialize the database
Molecule.metadata.create_all(bind=test_engine)
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


def test_substructure_search_single_atom(setup_teardown):
    # Test searching for a single atom substructure
    response = client.post("/search/", json={"substructure": "C"})
    result = response.json()
    assert {"identifier": "methane", "smiles": "C"} in result
    assert {"identifier": "ethanol", "smiles": "CCO"} in result
    assert {"identifier": "acetic_acid", "smiles": "CC(O)=O"} in result
    assert {"identifier": "aspirin",
            "smiles": "CC(=O)Oc1ccccc1C(=O)O"} in result


def test_substructure_search_ring(setup_teardown):
    # Test searching for a benzene ring substructure
    response = client.post("/search/", json={"substructure": "c1ccccc1"})
    assert response.status_code == 200
    result = response.json()
    assert {"identifier": "benzene", "smiles": "c1ccccc1"} in result
    assert {"identifier": "aspirin",
            "smiles": "CC(=O)Oc1ccccc1C(=O)O"} in result


def test_substructure_search_exact_match(setup_teardown):
    # Test searching for an exact match
    response = client.post("/search/", json={"substructure": "CC(=O)O"})
    assert response.status_code == 200
    result = response.json()
    assert {"identifier": "acetic_acid", "smiles": "CC(O)=O"} in result
    assert {"identifier": "aspirin",
            "smiles": "CC(=O)Oc1ccccc1C(=O)O"} in result


def test_substructure_search_multiple_matches(setup_teardown):
    # Test searching for a substructure that appears in multiple molecules
    response = client.post("/search/", json={"substructure": "CC"})
    assert response.status_code == 200
    result = response.json()
    assert {"identifier": "ethanol", "smiles": "CCO"} in result
    assert {"identifier": "acetic_acid", "smiles": "CC(O)=O"} in result
    assert {"identifier": "aspirin",
            "smiles": "CC(=O)Oc1ccccc1C(=O)O"} in result


def test_substructure_search_no_matches(setup_teardown):
    # Test searching for a substructure that doesn't exist in any molecule
    response = client.post("/search/", json={"substructure": "N"})
    assert response.status_code == 200
    result = response.json()
    assert result == []


def test_substructure_search_special_case(setup_teardown):
    # Test searching with a special or complex substructure
    response = client.post("/search/", json={"substructure": "O=O"})
    assert response.status_code == 200
    result = response.json()
    assert result == []  # No sample molecule has this exact substructure


def test_substructure_search_large_molecule(setup_teardown):
    # Test searching with a large molecule substructure
    response = client.post("/search/",
                           json={"substructure": "CC(=O)Oc1ccccc1"})
    assert response.status_code == 200
    result = response.json()
    assert {"identifier": "aspirin",
            "smiles": "CC(=O)Oc1ccccc1C(=O)O"} in result
