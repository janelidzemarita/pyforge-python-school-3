from os import getenv
from typing import List

from rdkit import Chem
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import json
from sqlalchemy.orm import Session
from . import crud, schemas
from database.database import init_db, SessionLocal


class PrettyJSONResponse(JSONResponse):
    def render(self, content: any) -> bytes:
        return json.dumps(content, indent=4, sort_keys=True).encode("utf-8")


app = FastAPI(
    title="Molecule Management API",
    version="2.0.0",
    description="An API for managing molecules "
                "and performing substructure searches "
                "using RDKit and PostgreSQL.",
    default_response_class=PrettyJSONResponse

)


# Initialize the database
init_db()


# Dependency to get the database session
def get_db():
    """
    Provides a database session to the endpoints.

    Yields:
        db (Session): A SQLAlchemy session object.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


not_found = "Molecule not found."


@app.get("/", summary="Get Server ID")
def get_server():
    """
    Retrieve the server ID.

    Returns:
        dict: A dictionary containing the server ID.
    """
    return {"server_id": getenv("SERVER_ID", "1")}


@app.post("/molecule",
          summary="Add Molecule",
          response_model=schemas.MoleculeResponse)
async def add_molecule(
        molecule: schemas.MoleculeCreate,
        db: Session = Depends(get_db)):
    """
    Add a new molecule to the database.

    Args:
        molecule (schemas.MoleculeCreate): A Pydantic model
        containing the molecule's identifier and SMILES string.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing the added molecule's
        identifier and SMILES string.

    Raises:
        HTTPException: If an error occurs while adding the molecule.
    """
    try:
        db_molecule = crud.create_molecule(db, molecule)
        return db_molecule
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/molecule/{identifier}",
         summary="Get Molecule",
         response_model=schemas.MoleculeResponse)
async def get_molecule(
        identifier: str,
        db: Session = Depends(get_db)):
    """
    Retrieve a molecule by its identifier.

    Args:
        identifier (str): The unique identifier of the molecule.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing the molecule's
        identifier and SMILES string.

    Raises:
        HTTPException: If the molecule is not found
        or another error occurs.
    """
    try:
        db_molecule = crud.get_molecule(db, identifier)
        if db_molecule is None:
            raise HTTPException(status_code=404, detail=not_found)
        return db_molecule
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/molecule/{identifier}",
         summary="Update Molecule",
         response_model=schemas.MoleculeResponse)
async def update_molecule(
        identifier: str,
        molecule: schemas.MoleculeCreate,
        db: Session = Depends(get_db)):
    """
    Update an existing molecule's SMILES representation.

    Args:
        identifier (str): The unique identifier
        of the molecule to update.
        molecule (schemas.MoleculeCreate): A Pydantic model
        containing the updated SMILES string.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing the updated molecule's
        identifier and SMILES string.

    Raises:
        HTTPException: If the molecule is not found
        or another error occurs.
    """
    try:
        db_molecule = crud.update_molecule(db, identifier, molecule)
        if db_molecule is None:
            raise HTTPException(status_code=404, detail=not_found)
        return db_molecule
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/molecule/{identifier}", summary="Delete Molecule")
async def delete_molecule(identifier: str, db: Session = Depends(get_db)):
    """
    Delete a molecule by its identifier.

    Args:
        identifier (str): The unique identifier of the molecule to delete.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing a message confirming the deletion.

    Raises:
        HTTPException: If the molecule is not found or another error occurs.
    """
    try:
        db_molecule = crud.delete_molecule(db, identifier)
        if db_molecule is None:
            raise HTTPException(status_code=404, detail=not_found)
        return {"message": "Molecule deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/molecules/",
         summary="List all Molecules",
         response_model=List[schemas.MoleculeResponse])
async def list_molecules(db: Session = Depends(get_db)):
    """
    List all molecules in the database.

    Args:
        db (Session): The database session.

    Returns:
        list: A list of dictionaries,
        each containing a molecule's identifier and SMILES string.

    Raises:
        HTTPException: If an error occurs while retrieving the molecules.
    """
    try:
        return crud.list_molecules(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def substructure_search(mols, mol):
    """
    :param mols: list of molecules
    :param mol: substructure
    :return: matching molecules
    """
    # List to store molecules that contain the substructure (mol)
    molecule = Chem.MolFromSmiles(mol)
    matching_molecules = [
        smiles for smiles in mols if
        Chem.MolFromSmiles(smiles).HasSubstructMatch(molecule)
    ]
    return matching_molecules


@app.post("/search/",
          summary="Substructure Search",
          response_model=List[schemas.MoleculeResponse])
async def search_substructure(
        query: schemas.SubstructureQuery,
        db: Session = Depends(get_db)):
    """
    Search for molecules containing a given substructure.

    Args:
        query (schemas.SubstructureQuery): A Pydantic model
        containing the substructure's SMILES string.
        db (Session): The database session.

    Returns:
        list: A list of dictionaries,
        each containing a molecule's identifier
        and SMILES string that matches the substructure.

    Raises:
        HTTPException: If the substructure SMILES
        string is invalid or another error occurs.
    """
    try:
        # Convert the substructure SMILES string to an RDKit molecule
        sub_mol = Chem.MolFromSmiles(query.substructure)
        if sub_mol is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid substructure SMILES string."
            )

        # Get all molecules from the database
        all_molecules = crud.list_molecules(db)

        # Perform the substructure search
        matching_molecules = [
            mol for mol in all_molecules
            if Chem.MolFromSmiles(mol.smiles).HasSubstructMatch(sub_mol)
        ]

        return matching_molecules

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
