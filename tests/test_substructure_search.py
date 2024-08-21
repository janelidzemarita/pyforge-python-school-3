import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

# Sample molecules to use in tests
sample_molecules = [
    {"identifier": "water", "smiles": "O"},
    {"identifier": "methane", "smiles": "C"},
    {"identifier": "ethanol", "smiles": "CCO"},
    {"identifier": "benzene", "smiles": "c1ccccc1"},
    {"identifier": "acetic_acid", "smiles": "CC(=O)O"},
    {"identifier": "aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
]


@pytest.fixture
def setup_teardown():
    # Setup: Add the sample molecules to the system
    for molecule in sample_molecules:
        client.post("/molecule", json=molecule)
    yield
    # Teardown: Clear the molecules after tests
    for molecule in sample_molecules:
        client.delete(f"/molecule/{molecule['identifier']}")


def test_substructure_search_single_atom(setup_teardown):
    # Test searching for a single atom substructure
    response = client.post("/search/", json={"substructure": "C"})
    result = response.json()
    expected = [
        {"identifier": "methane", "smiles": "C"},
        {"identifier": "ethanol", "smiles": "CCO"},
        {"identifier": "benzene", "smiles": "c1ccccc1"},
        {"identifier": "acetic_acid", "smiles": "CC(=O)O"},
        {"identifier": "aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
    ]
    assert result == expected


def test_substructure_search_ring(setup_teardown):
    # Test searching for a benzene ring substructure
    response = client.post(
        "/search/",
        json={"substructure": "c1ccccc1"}
    )
    assert response.status_code == 200
    result = response.json()
    expected = [
        {"identifier": "benzene", "smiles": "c1ccccc1"},
        {"identifier": "aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
    ]
    assert result == expected


def test_substructure_search_exact_match(setup_teardown):
    # Test searching for an exact match
    response = client.post(
        "/search/",
        json={"substructure": "CC(=O)O"}
    )
    assert response.status_code == 200
    result = response.json()
    expected = [
        {"identifier": "acetic_acid", "smiles": "CC(=O)O"},
        {"identifier": "aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
    ]
    assert result == expected


def test_substructure_search_multiple_matches(setup_teardown):
    # Test searching for a substructure that appears in multiple molecules
    response = client.post(
        "/search/",
        json={"substructure": "CC"}
    )
    assert response.status_code == 200
    result = response.json()
    expected = [
        {"identifier": "ethanol", "smiles": "CCO"},
        {"identifier": "acetic_acid", "smiles": "CC(=O)O"},
        {"identifier": "aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
    ]
    assert result == expected


def test_substructure_search_no_matches(setup_teardown):
    # Test searching for a substructure that doesn't exist in any molecule
    response = client.post("/search/", json={"substructure": "N"})
    assert response.status_code == 200
    result = response.json()
    assert result == []


def test_substructure_search_invalid_substructure(setup_teardown):
    # Test searching with an empty substructure (should return an error)
    response = client.post(
        "/search/",
        json={"substructure": "some_string"}
    )
    print(response.text)
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid substructure SMILES string."
    }


def test_substructure_search_special_case(setup_teardown):
    # Test searching: special or complex substructure
    response = client.post(
        "/search/",
        json={"substructure": "O=O"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result == []  # No sample molecule has this exact substructure


def test_substructure_search_large_molecule(setup_teardown):
    # Test searching with a large molecule substructure
    response = client.post(
        "/search/",
        json={"substructure": "CC(=O)Oc1ccccc1"}
    )
    assert response.status_code == 200
    result = response.json()
    expected = [
        {"identifier": "aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
    ]
    assert result == expected
