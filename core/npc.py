from dataclasses import dataclass
from typing import Dict

@dataclass
class NPC:
    """
    État logique d'un PNJ (persistant, indépendant des sprites Arcade).
    """
    name: str
    relation_score: int = 10
    min_relation_for_rewards: int = 5     # en dessous : pas de récompense
    max_relation_bonus: int = 25         # au-dessus : bonus

# Petit registre global : on garde 1 état par PNJ (par nom)
_NPC_REGISTRY: Dict[str, NPC] = {}

def get_npc_state(name: str) -> NPC:
    """
    Récupère (ou crée) l'état persistant d'un PNJ, normalisé par son nom.
    """
    key = (name or "").lower()
    if key not in _NPC_REGISTRY:
        _NPC_REGISTRY[key] = NPC(name=name)
    return _NPC_REGISTRY[key]
