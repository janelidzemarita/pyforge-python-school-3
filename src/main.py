from rdkit import Chem
from rdkit.Chem import Draw


def substructure_search(mols, mol):

    # List to store molecules that contain the substructure (mol)
    matching_molecules = [smiles for smiles in mols if Chem.MolFromSmiles(smiles).HasSubstructMatch(Chem.MolFromSmiles(mol))]

    # Visualize the matching molecules
    if matching_molecules:
        matching_structures = [Chem.MolFromSmiles(smiles) for smiles in matching_molecules]
        img = Draw.MolsToGridImage(matching_structures, molsPerRow=2, subImgSize=(500, 500), returnPNG=False)
        img.show()

    return matching_molecules
