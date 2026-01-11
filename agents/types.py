from typing import TypedDict, List, Dict, Any, Optional


class Metadonnees(TypedDict, total=False):
    titre: str
    code_projet: str
    client: str
    type: str
    numero: str
    annee: str
    type_etude: str
    main_image: str
    client_logo: str
    historique_revisions: List[Dict[str, Any]]


class ConditionDetail(TypedDict, total=False):
    conditions: List[Any]
    valeurs_retenues: str
    commentaire: str
    figures: List[Any]
    tableaux: List[Any]


class ConditionsEnvironnementales(TypedDict, total=False):
    introduction: str
    houle: ConditionDetail
    vent: ConditionDetail
    courant: ConditionDetail
    maree: ConditionDetail
    agitation: ConditionDetail
    synthese: str


class DonneesEntree(TypedDict, total=False):
    introduction: Dict[str, Any]
    plan_de_masse: Dict[str, Any]
    balisage: Dict[str, Any]
    bathymetrie: Dict[str, Any]
    conditions_environnementales: ConditionsEnvironnementales
    synthese_environnementale: str


class RapportData(TypedDict, total=False):
    metadonnees: Metadonnees
    introduction: Dict[str, Any]
    donnees_entree: DonneesEntree
    donnees_navires: Dict[str, Any]
    simulations: Dict[str, Any]
    analyse_synthese: Dict[str, Any]
    conclusion: str
