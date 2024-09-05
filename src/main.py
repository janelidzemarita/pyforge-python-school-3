import json
import logging
from os import getenv
from typing import List

import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from rdkit import Chem
from sqlalchemy.orm import Session

from database.database import init_db, SessionLocal
from . import crud, schemas

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - '
                           '%(name)s - '
                           '%(levelname)s - '
                           '%(message)s')
logger = logging.getLogger(__name__)


class PrettyJSONResponse(JSONResponse):
    def render(self, content: any) -> bytes:
        return json.dumps(content, indent=4, sort_keys=True).encode("utf-8")


app = FastAPI(
    title="Molecule Management API",
    version="2.2.0",
    description="An API for managing molecules "
                "and performing substructure searches "
                "using RDKit and PostgreSQL.",
    default_response_class=PrettyJSONResponse

)

# Initialize the database
init_db()

not_found = "Molecule not found."

redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)


@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


@app.on_event("shutdown")
async def shutdown_event():
    await redis_client.close()


# Function to get cached result
async def get_cached_result(key: str) -> List[dict]:
    try:
        result = await redis_client.get(key)
        if result:
            # Decode JSON string back to list of dictionaries
            return json.loads(result)
        return []
    except Exception as e:
        logger.error(f"Error getting cache: {e}")
        return []


# Function to set cache
async def set_cache(key: str, molecules: List[dict], expiration: int = 60):
    try:
        # Convert list of dictionaries to JSON string
        json_value = json.dumps(molecules)
        await redis_client.setex(key, expiration, json_value)
    except Exception as e:
        logger.error(f"Error setting cache: {e}")


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


@app.get("/", summary="Get Server ID")
def get_server():
    """
    Retrieve the server ID.

    Returns:
        dict: A dictionary containing the server ID.
    """
    logger.info("Server ID endpoint called.")
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
    logger.info(f"Adding molecule: {molecule.identifier}")
    try:
        db_molecule = crud.create_molecule(db, molecule)
        return db_molecule
    except Exception as e:
        logger.error(f"Error adding molecule: {e}")
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
    logger.info(f"Getting molecule with identifier: {identifier}")
    try:
        db_molecule = crud.get_molecule(db, identifier)
        if db_molecule is None:
            raise HTTPException(status_code=404, detail=not_found)
        return db_molecule
    except Exception as e:
        logger.error(f"Error getting molecule: {e}")
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
    logger.info(f"Updating molecule with identifier: {identifier}")
    try:
        db_molecule = crud.update_molecule(db, identifier, molecule)
        if db_molecule is None:
            raise HTTPException(status_code=404, detail=not_found)
        return db_molecule
    except Exception as e:
        logger.error(f"Error updating molecule: {e}")
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
    logger.info(f"Deleting molecule with identifier: {identifier}")
    try:
        db_molecule = crud.delete_molecule(db, identifier)
        if db_molecule is None:
            raise HTTPException(status_code=404, detail=not_found)
        return {"message": "Molecule deleted successfully."}
    except Exception as e:
        logger.error(f"Error deleting molecule: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/molecules/",
         summary="List all Molecules",
         response_model=List[schemas.MoleculeResponse])
async def list_molecules(
        limit: int = 100,
        db: Session = Depends(get_db)):
    """
    List all molecules in the database.

    Args:
        db (Session): The database session.

    Returns:
        list: A list of dictionaries,
        each containing a molecule's identifier and SMILES string.

    Raises:
        HTTPException: If an error occurs while retrieving the molecules.
        :param db:
        :param limit:
    """
    logger.info(f"Listing up to {limit} molecules.")
    try:
        # Convert iterator to list
        molecules = list(crud.list_molecules(db, limit))
        return molecules
    except Exception as e:
        logger.error(f"Error listing molecules: {e}")
        raise HTTPException(status_code=400, detail=str(e))


def substructure_search(mols, mol):
    """
    :param mols: list of molecules
    :param mol: substructure
    :return: matching molecules
    """
    # List to store molecules that contain the substructure (mol)
    molecule = Chem.MolFromSmiles(mol)
    logger.info(f"Searching for substructure matches: {mol}")
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
    logger.info(f"Searching for substructure: {query.substructure}")
    try:
        logger.info("Performing search in cache.")
        # Check if result is in cache
        cache_key = f"substructure:{query.substructure}"
        cached_result = await get_cached_result(cache_key)
        if cached_result:
            return {"source": "cache", "data": cached_result}

        logger.info("Cache miss. Performing search.")
        # Convert the substructure SMILES string to an RDKit molecule
        sub_mol = Chem.MolFromSmiles(query.substructure)
        if sub_mol is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid substructure SMILES string."
            )

        # Get all molecules from the database
        all_molecules = crud.list_molecules(db, limit=500)

        # Perform the substructure search
        matching_molecules = [
            {"identifier": mol.identifier, "smiles": mol.smiles}
            for mol in all_molecules
            if Chem.MolFromSmiles(mol.smiles).HasSubstructMatch(sub_mol)
        ]

        # Cache the search result
        await set_cache(cache_key, matching_molecules)

        return matching_molecules

    except Exception as e:
        logger.error(f"Error searching for substructure: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
