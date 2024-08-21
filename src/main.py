from os import getenv

from rdkit import Chem
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Molecule Management API",
    version="1.1.0"
)

# Data structure to store molecules
molecules = {}


class Molecule(BaseModel):
    identifier: str
    smiles: str


def substructure_search(mols, mol):
    """
    :param mols: list of molecules
    :param mol: substructure
    :return: matching molecules
    """
    # List to store molecules that contain the substructure (mol)
    matching_molecules = [smiles for smiles in mols if
                          Chem.MolFromSmiles(smiles).HasSubstructMatch(Chem.MolFromSmiles(mol))]
    return matching_molecules


@app.get("/", summary="Get Server ID")
def get_server():
    """
    Retrieve the server ID.
    """
    return {"server_id": getenv("SERVER_ID", "1")}


@app.post("/molecule", summary="Add Molecule")
async def add_molecule(molecule: Molecule):
    """
    Add a new molecule to the collection.

    - **identifier**: Unique identifier for the molecule.
    - **smiles**: SMILES representation of the molecule.
    """
    if molecule.identifier in molecules:
        raise HTTPException(status_code=400, detail="Molecule with this identifier already exists.")
    try:
        mol = Chem.MolFromSmiles(molecule.smiles)
        if mol is None:
            raise HTTPException(status_code=400, detail="Invalid SMILES string.")
        molecules[molecule.identifier] = molecule.smiles
        return {"message": "Molecule added successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/molecule/{identifier}", summary="Get Molecule")
async def get_molecule(identifier: str):
    """
    Retrieve a molecule by its identifier.

    - **identifier**: Unique identifier of the molecule.
    """
    if identifier not in molecules:
        raise HTTPException(status_code=404, detail="Molecule not found.")
    return {"identifier": identifier, "smiles": molecules[identifier]}


@app.put("/molecule/{identifier}", summary="Update Molecule")
async def update_molecule(identifier: str, molecule: Molecule):
    """
    Update an existing molecule's SMILES representation.

    - **identifier**: Unique identifier of the molecule.
    - **smiles**: New SMILES representation of the molecule.
    """
    if identifier not in molecules:
        raise HTTPException(status_code=404, detail="Molecule not found.")
    try:
        mol = Chem.MolFromSmiles(molecule.smiles)
        if mol is None:
            raise HTTPException(status_code=400, detail="Invalid SMILES string.")
        molecules[identifier] = molecule.smiles
        return {"message": "Molecule updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/molecule/{identifier}", summary="Delete Molecule")
async def delete_molecule(identifier: str):
    """
    Delete a molecule by its identifier.

    - **identifier**: Unique identifier of the molecule.
    """
    if identifier not in molecules:
        raise HTTPException(status_code=404, detail="Molecule not found.")
    del molecules[identifier]
    return {"message": "Molecule deleted successfully."}


@app.get("/molecules/", summary="List all Molecules")
async def list_molecules():
    """
    List all molecules in the collection.
    """
    return [{"identifier": identifier, "smiles": smiles} for identifier, smiles in molecules.items()]


@app.post("/search/", summary="Substructure Search")
async def search_substructure(substructure: str):
    """
    Search for molecules containing a given substructure.

    - **substructure**: SMILES representation of the substructure.
    """
    try:
        sub_mol = Chem.MolFromSmiles(substructure)
        if sub_mol is None:
            raise HTTPException(status_code=400, detail="Invalid substructure SMILES string.")
        matching_molecules = substructure_search(molecules.values(), substructure)
        return [{"identifier": identifier, "smiles": smiles} for identifier, smiles in molecules.items()
                if smiles in matching_molecules]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
