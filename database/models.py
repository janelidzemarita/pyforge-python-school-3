# src/models.py
from sqlalchemy import Column, String
from .database import Base


class Molecule(Base):
    __tablename__ = "molecules"

    identifier = Column(String, primary_key=True, index=True)
    smiles = Column(String, index=True)
