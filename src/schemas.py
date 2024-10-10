from pydantic import BaseModel


class MoleculeBase(BaseModel):
    smiles: str


class MoleculeCreate(MoleculeBase):
    identifier: str


class MoleculeResponse(MoleculeBase):
    identifier: str

    class Config:
        from_attributes = True


class SubstructureQuery(BaseModel):
    substructure: str
