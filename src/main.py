import json
import logging
from os import getenv
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from contextlib import asynccontextmanager
from celery.result import AsyncResult
from sqlalchemy.orm import Session

from database.database import SessionLocal, init_db
from . import crud, schemas
from .tasks import substructure_search_task
from .celery_worker import celery_app

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

init_db()

not_found = "Molecule not found."

# Initialize Redis client
redis_client: redis.Redis


@asynccontextmanager
async def lifespan():
    global redis_client
    # Startup event: Initialize Redis client
    redis_client = redis.Redis(
        host='redis',
        port=6379,
        db=0,
        decode_responses=True
    )
    try:
        # Yield control back to FastAPI to handle requests
        yield
    finally:
        # Shutdown event: Close Redis connection
        if redis_client:
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


@app.post("/search/", summary="Substructure Search")
async def start_substructure_search(
        query: schemas.SubstructureQuery,
        db: Session = Depends(get_db)):
    """
    Start a background substructure search task.

    Args:
        query (schemas.SubstructureQuery): Substructure SMILES string.
        db (Session): Database session.

    Returns:
        dict: Task ID and task status.
    """
    try:
        logger.info(f"Starting substructure search for: {query.substructure}")

        # Check if the result is already cached
        cached_result = await get_cached_result(query.substructure)
        if cached_result:
            logger.info(
            f"Returning cached result for substructure: {query.substructure}"
            )
            return {"task_id": None,
                    "status": "Completed (from cache)",
                    "result": cached_result}

        # Convert the iterator to a list of SMILES strings
        all_molecules = [molecule.smiles
                         for molecule
                         in crud.list_molecules(db, limit=500)]

        # Start the background task
        task = substructure_search_task.delay(
            query.substructure,
            all_molecules)
        return {"task_id": task.id, "status": task.status}

    except Exception as e:
        logger.error(f"Error starting substructure search: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start substructure search.")


@app.get("/search/search-result/{task_id}",
         summary="Get Substructure Search Result")
async def get_task_result(task_id: str):
    """
    Retrieve the result of a substructure search task.

    Args:
        task_id (str): The ID of the background task.

    Returns:
        dict: Task status and result if completed.
    """
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == 'PENDING':
        return {"task_id": task_id, "status": "Task is still processing"}

    elif task_result.state == 'SUCCESS':
        result = task_result.result

        # Cache the result if it's not already cached
        cache_key = result["substructure"]
        cached_result = await get_cached_result(cache_key)
        if not cached_result:
            await set_cache(cache_key, result)
            logger.info(f"Cached result for substructure: {cache_key}")

        return {"task_id": task_id,
                "status": "Task completed",
                "result": result}

    else:
        return {"task_id": task_id, "status": task_result.state}
