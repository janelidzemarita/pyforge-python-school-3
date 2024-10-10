from rdkit import Chem
from src.celery_worker import celery_app


@celery_app.task
def substructure_search_task(smiles: str, all_molecules):
    """
    Perform substructure search as a background task.

    Args:
        smiles (str): The SMILES string of the substructure.
        all_molecules (list): List of all molecules to search in.

    Returns:
        list: A list of dictionaries with matching molecules.
    """
    substructure = Chem.MolFromSmiles(smiles)
    if substructure is None:
        raise ValueError("Invalid SMILES string")

    matching_molecules = [
        {"identifier": mol.identifier, "smiles": mol.smiles}
        for mol in all_molecules
        if Chem.MolFromSmiles(mol.smiles).HasSubstructMatch(substructure)
    ]
    return matching_molecules
