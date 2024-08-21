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


def test_add_molecule():
    response = client.post(
        "/molecule",
        json={"identifier": "test", "smiles": "CCO"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Molecule added successfully."
    }

    # Test adding a molecule with the same identifier (should fail)
    response = client.post(
        "/molecule",
        json={"identifier": "test", "smiles": "C"}
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Molecule with this identifier already exists."
    }

    # Cleanup
    client.delete("/molecule/test")


def test_get_molecule(setup_teardown):
    response = client.get("/molecule/water")
    assert response.status_code == 200
    assert response.json() == {
        "identifier": "water", "smiles": "O"
    }

    # Test getting a non-existing molecule
    response = client.get(
        "/molecule/non_existing"
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Molecule not found."}


def test_update_molecule(setup_teardown):
    # Update molecule
    response = client.put(
        "/molecule/water",
        json={"identifier": "water", "smiles": "OO"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Molecule updated successfully."
    }

    # Check the update
    response = client.get("/molecule/water")
    assert response.status_code == 200
    assert response.json() == {
        "identifier": "water", "smiles": "OO"
    }

    # Test updating a non-existing molecule
    response = client.put(
        "/molecule/non_existing",
        json={"identifier": "non_existing", "smiles": "C"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Molecule not found."}


def test_delete_molecule(setup_teardown):
    # Delete molecule
    response = client.delete("/molecule/water")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Molecule deleted successfully."
    }

    # Check the deletion
    response = client.get("/molecule/water")
    assert response.status_code == 404
    assert response.json() == {"detail": "Molecule not found."}


def test_list_molecules(setup_teardown):
    response = client.get("/molecules/")
    assert response.status_code == 200
    assert len(response.json()) == len(sample_molecules)


def test_search_substructure(setup_teardown):
    response = client.post("/search/", json={"substructure": "CCO"})
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 3
    assert {"identifier": "ethanol", "smiles": "CCO"} in result
    assert {
               "identifier": "aspirin",
               "smiles": "CC(=O)Oc1ccccc1C(=O)O"} \
           in result


def test_get_server_id():
    response = client.get("/")
    assert response.status_code == 200
    assert "server_id" in response.json()
