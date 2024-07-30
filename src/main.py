from rdkit import Chem
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Data structure to store molecules
molecules = {}


class Molecule(BaseModel):
    identifier: str
    smiles: str


def substructure_search(mols, mol):
    # List to store molecules that contain the substructure (mol)
    matching_molecules = [smiles for smiles in mols if
                          Chem.MolFromSmiles(smiles).HasSubstructMatch(Chem.MolFromSmiles(mol))]
    return matching_molecules


@app.post("/molecule")
async def add_molecule(molecule: Molecule):
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


@app.get("/molecule/{identifier}")
async def get_molecule(identifier: str):
    if identifier not in molecules:
        raise HTTPException(status_code=404, detail="Molecule not found.")
    return {"identifier": identifier, "smiles": molecules[identifier]}


@app.put("/molecule/{identifier}")
async def update_molecule(identifier: str, molecule: Molecule):
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


@app.delete("/molecule/{identifier}")
async def delete_molecule(identifier: str):
    if identifier not in molecules:
        raise HTTPException(status_code=404, detail="Molecule not found.")
    del molecules[identifier]
    return {"message": "Molecule deleted successfully."}


@app.get("/molecules/")
async def list_molecules():
    return [{"identifier": identifier, "smiles": smiles} for identifier, smiles in molecules.items()]


@app.post("/search/")
async def search_substructure(substructure: str):
    try:
        sub_mol = Chem.MolFromSmiles(substructure)
        if sub_mol is None:
            raise HTTPException(status_code=400, detail="Invalid substructure SMILES string.")
        matching_molecules = substructure_search(molecules.values(), substructure)
        return [{"identifier": identifier, "smiles": smiles} for identifier, smiles in molecules.items()
                if smiles in matching_molecules]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
