from sqlalchemy.orm import Session
from . import schemas
from database import models


def create_molecule(db: Session, molecule: schemas.MoleculeCreate):
    db_molecule = models.Molecule(**molecule.dict())
    db.add(db_molecule)
    db.commit()
    db.refresh(db_molecule)
    return db_molecule


def get_molecule(db: Session, identifier: str):
    return db.query(models.Molecule)\
        .filter(models.Molecule.identifier == identifier)\
        .first()


def update_molecule(
        db: Session, identifier: str,
        molecule: schemas.MoleculeCreate
):
    db_molecule = db.query(models.Molecule)\
        .filter(models.Molecule.identifier == identifier)\
        .first()
    if db_molecule:
        db_molecule.smiles = molecule.smiles
        db.commit()
        db.refresh(db_molecule)
        return db_molecule
    return None


def delete_molecule(db: Session, identifier: str):
    db_molecule = db.query(models.Molecule)\
        .filter(models.Molecule.identifier == identifier)\
        .first()
    if db_molecule:
        db.delete(db_molecule)
        db.commit()
        return db_molecule
    return None


def list_molecules(db: Session):
    return db.query(models.Molecule).all()
