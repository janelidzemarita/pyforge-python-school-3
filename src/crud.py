from sqlalchemy.orm import Session
from . import schemas
from database import models
from typing import Iterator
from database.models import Molecule


def create_molecule(db: Session, molecule: schemas.MoleculeCreate):
    db_molecule = models.Molecule(**molecule.model_dump())
    db.add(db_molecule)
    db.commit()
    db.refresh(db_molecule)
    return db_molecule


def get_molecule(db: Session, identifier: str):
    return db.query(models.Molecule)\
        .filter(identifier == models.Molecule.identifier)\
        .first()


def update_molecule(
        db: Session, identifier: str,
        molecule: schemas.MoleculeCreate
):
    db_molecule = db.query(models.Molecule)\
        .filter(identifier == models.Molecule.identifier)\
        .first()
    if db_molecule:
        db_molecule.smiles = molecule.smiles
        db.commit()
        db.refresh(db_molecule)
        return db_molecule
    return None


def delete_molecule(db: Session, identifier: str):
    db_molecule = db.query(models.Molecule)\
        .filter(identifier == models.Molecule.identifier)\
        .first()
    if db_molecule:
        db.delete(db_molecule)
        db.commit()
        return db_molecule
    return None


def list_molecules(db: Session, limit: int) -> Iterator[Molecule]:
    """
    List molecules from the database using an iterator.

    Args:
        db (Session): The database session.
        limit (int): The maximum number of molecules to return.

    Returns:
        Iterator[Molecule]: An iterator that yields Molecule objects.
    """
    batch_size = 50
    offset = 0
    count = 0

    while count < limit:
        # Fetch the batch of molecules
        batch = db.query(Molecule).offset(offset).limit(batch_size).all()
        if not batch:
            break

        for molecule in batch:
            if count >= limit:
                return  # Stop yielding if limit is reached
            yield molecule
            count += 1

        offset += batch_size

        # If batch is smaller than batch_size, it means we've reached the end
        if len(batch) < batch_size:
            break
