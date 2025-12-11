from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass
class Quest:
    """
    Représente une quête simple :
    - id : identifiant interne
    - title : nom lisible
    - description : résumé pour l'IA
    - giver : nom du PNJ qui donne la quête (ex: 'alchimiste')
    - validator : PNJ qui valide la quête (peut être = giver)
    - requirements : {"items": {"item_id": quantité}}
    - state : "locked" | "active" | "completed"
    """
    id: str
    title: str
    description: str
    giver: str
    validator: str
    requirements: Dict[str, Dict[str, int]]
    state: str = "locked"

    def get_item_requirements(self) -> Dict[str, int]:
        return self.requirements.get("items", {})

    def compute_progress(self, inventory: Dict[str, int]) -> Tuple[int, int]:
        """
        Renvoie (actuel, total) sur les objets requis.
        Exemple : 2/3 potions, 1/1 marteau → actuel=3, total=4
        """
        req_items = self.get_item_requirements()
        total = sum(req_items.values())
        if total == 0:
            return 0, 0

        current = 0
        for item_id, needed in req_items.items():
            current += min(inventory.get(item_id, 0), needed)
        return current, total

    def requirements_met(self, inventory: Dict[str, int]) -> bool:
        """Vérifie si tous les objets requis sont présents dans l'inventaire."""
        req_items = self.get_item_requirements()
        for item_id, needed in req_items.items():
            if inventory.get(item_id, 0) < needed:
                return False
        return True


class QuestManager:
    """
    Gestionnaire centralisé des quêtes.
    - Toutes les quêtes sont définies ici.
    - Aucune persistance disque : tout est réinitialisé à chaque run.
    - La logique de début / validation se fait lorsque le joueur parle à un PNJ.
    """

    def __init__(self) -> None:
        self.quests: Dict[str, Quest] = {}
        self._build_quests()

    # ============================================================
    #             INITIALISATION ET RESET
    # ============================================================

    def _build_quests(self) -> None:
        """Définit toutes les quêtes du jeu."""
        q: Dict[str, Quest] = {}

        # --- Maire : réparation du vieux pont ---
        q["maire_pont"] = Quest(
            id="maire_pont",
            title="Réparer le vieux pont",
            description="Le maire veut commencer les réparations du vieux pont. "
                        "Il a besoin d'une planche solide pour lancer les travaux.",
            giver="maire",
            validator="maire",
            requirements={"items": {"planche": 1}},
        )

        # --- Alchimiste : retrouver 3 potions ---
        q["alchimiste_potions"] = Quest(
            id="alchimiste_potions",
            title="Les potions égarées",
            description="Merlin Floche a perdu trois de ses potions. "
                        "Il veut que le joueur les retrouve.",
            giver="alchimiste",
            validator="alchimiste",
            requirements={"items": {"potion": 3}},
        )

        # --- Comtesse : retrouver le camée ---
        q["comptesse_camee"] = Quest(
            id="comptesse_camee",
            title="Le camée disparu",
            description="La comtesse a perdu un petit bijou de famille, un camée. "
                        "Elle souhaite qu'on le lui rapporte discrètement.",
            giver="comptesse",
            validator="comptesse",
            requirements={"items": {"camee": 1}},
        )

        # --- Forgeron : marteau égaré ---
        q["forgeron_marteau"] = Quest(
            id="forgeron_marteau",
            title="L'outil égaré",
            description="Garrod a perdu son marteau de forgeron en allant boire. "
                        "Il a besoin qu'on le lui ramène.",
            giver="forgeron",
            validator="forgeron",
            requirements={"items": {"marteau_forgeron": 1}},
        )

        # --- Geôlier : clé rouillée ---
        q["geolier_cle"] = Quest(
            id="geolier_cle",
            title="La clé enfouie",
            description="Le geôlier a perdu une vieille clé rouillée dans le labyrinthe. "
                        "Il ne veut pas que le maire le découvre.",
            giver="geolier",
            validator="geolier",
            requirements={"items": {"cle_rouillee": 1}},
        )

        # --- Hôtelier : parfum spécial ---
        q["hotelier_parfum"] = Quest(
            id="hotelier_parfum",
            title="La chambre parfaite",
            description="L'hôtelier cherche un parfum particulier pour rendre parfaite "
                        "une de ses chambres.",
            giver="hotelier",
            validator="hotelier",
            requirements={"items": {"parfum": 1}},
        )

        # --- Prisonnier : papier de 'preuve' ---
        q["prisonier_preuve"] = Quest(
            id="prisonier_preuve",
            title="La preuve froissée",
            description="Lanson affirme qu'un petit papier froissé contient une preuve "
                        "de son innocence. Il veut que le joueur le retrouve.",
            giver="prisonier",
            validator="prisonier",
            requirements={"items": {"papier_preuve": 1}},
        )

        # --- Serveur : tonnelet d'essai ---
        q["serveur_tonnelet"] = Quest(
            id="serveur_tonnelet",
            title="Le tonnelet d'essai",
            description="Tibo teste un nouveau vin et a égaré un petit tonnelet. "
                        "Il veut qu'on le lui rapporte sans impliquer l'hôtelier.",
            giver="serveur",
            validator="serveur",
            requirements={"items": {"tonnelet": 1}},
        )

        # --- Paysan → validée chez le maire ---
        q["paysan_ble_maire"] = Quest(
            id="paysan_ble_maire",
            title="Le pain du village",
            description="Guillaume Courbet veut que le joueur apporte trois blés "
                        "au maire pour assurer le pain du village.",
            giver="paysan",
            validator="maire",
            requirements={"items": {"Blé": 3}},  # IMPORTANT : doit matcher exactement l'item_id des sprites
        )

        self.quests = q

    def reset_all(self) -> None:
        """Remet toutes les quêtes à l'état 'locked'."""
        for quest in self.quests.values():
            quest.state = "locked"

    # ============================================================
    #             OUTILS INTERNES
    # ============================================================

    @staticmethod
    def _normalize_npc_name(name: str) -> str:
        """
        Normalise légèrement un nom de PNJ pour les comparaisons.
        Si un jour tu as 'maire_exterieur', ça le ramènera à 'maire'.
        """
        raw = (name or "").lower()
        known = [
            "maire",
            "alchimiste",
            "comptesse",
            "forgeron",
            "geolier",
            "hotelier",
            "paysan",
            "prisonier",
            "serveur",
        ]
        for k in known:
            if k in raw:
                return k
        return raw

    def _quests_given_by(self, npc_name: str) -> List[Quest]:
        npc = self._normalize_npc_name(npc_name)
        return [q for q in self.quests.values() if self._normalize_npc_name(q.giver) == npc]

    def _quests_validated_by(self, npc_name: str) -> List[Quest]:
        npc = self._normalize_npc_name(npc_name)
        return [q for q in self.quests.values() if self._normalize_npc_name(q.validator) == npc]

    # ============================================================
    #             INTERACTION AVEC UN PNJ
    # ============================================================

    def handle_npc_interaction(
        self,
        npc_name: str,
        inventory: Dict[str, int],
    ) -> Tuple[Dict[str, List[str]], str]:
        """
        À appeler à chaque fois que le joueur commence / poursuit un dialogue avec un PNJ.

        - Active automatiquement la quête donnée par ce PNJ si elle est encore 'locked'.
        - Vérifie si ce PNJ peut valider des quêtes (les siennes ou celles d'autres PNJ).
        - Retourne :
            events = {
                "activated": [quest_id, ...],
                "completed": [quest_id, ...]
            }
            quest_prompt = texte à injecter dans le prompt système de l'IA.
        """

        npc_norm = self._normalize_npc_name(npc_name)

        activated: List[str] = []
        completed: List[str] = []

        giver_quests = self._quests_given_by(npc_norm)
        validator_quests = self._quests_validated_by(npc_norm)

        # --- Activer la quête donnée par ce PNJ (si pas encore démarrée) ---
        for q in giver_quests:
            if q.state == "locked":
                q.state = "active"
                activated.append(q.id)

        # --- Vérifier les quêtes validées par ce PNJ ---
        for q in validator_quests:
            if q.state == "active" and q.requirements_met(inventory):
                q.state = "completed"
                completed.append(q.id)

        events = {
            "activated": activated,
            "completed": completed,
        }

        quest_prompt = self._build_quest_prompt_for_npc(npc_norm, inventory, activated, completed)

        return events, quest_prompt

    # ============================================================
    #             CONSTRUCTION DU TEXTE POUR L'IA
    # ============================================================

    def _build_quest_prompt_for_npc(
        self,
        npc_norm: str,
        inventory: Dict[str, int],
        activated: List[str],
        completed: List[str],
    ) -> str:
        """
        Construit un texte explicatif à destination EXCLUSIVE de l'IA.
        Ce texte sera ajouté au message "system" du PNJ.
        """

        giver_qs = self._quests_given_by(npc_norm)
        validator_qs = self._quests_validated_by(npc_norm)

        lines: List[str] = []

        lines.append(
            "INFORMATIONS INTERNES (NE PAS ÉNONCER TELLES QUELLES) SUR LES QUÊTES LIÉES À CE PNJ."
        )
        lines.append(
            "Tu dois t'en servir pour parler de manière naturelle au joueur, "
            "dans ton style, sans jamais mentionner de termes techniques comme "
            "'state', 'variable', 'quest_id' ou des compteurs bruts."
        )

        # --- Quête dont ce PNJ est le donneur principal ---
        if giver_qs:
            lines.append("")
            lines.append("Quête(s) que TU as donnée(s) au joueur :")
            for q in giver_qs:
                cur, total = q.compute_progress(inventory)
                state_label = {
                    "locked": "non commencée",
                    "active": "en cours",
                    "completed": "terminée",
                }.get(q.state, q.state)

                lines.append(f"- {q.title} : {q.description}")
                lines.append(f"  • État actuel : {state_label}.")
                if total > 0:
                    lines.append(
                        f"  • Progression estimée d'après l'inventaire du joueur : {cur} / {total} objet(s) requis."
                    )

                if q.id in activated:
                    lines.append(
                        "  • Cette quête vient juste d'être lancée dans cette conversation. "
                        "Présente-la naturellement au joueur."
                    )
                if q.id in completed:
                    lines.append(
                        "  • Cette quête vient d'être accomplie (tous les objets requis sont présents). "
                        "Tu peux féliciter le joueur, le remercier, et considérer cette quête comme résolue."
                    )

        # --- Quêtes validées par ce PNJ mais données par d'autres ---
        others = [
            q for q in validator_qs
            if self._normalize_npc_name(q.giver) != npc_norm
        ]
        if others:
            lines.append("")
            lines.append(
                "Quête(s) données par un autre PNJ mais que TU dois valider lorsque le joueur vient te voir :"
            )
            for q in others:
                cur, total = q.compute_progress(inventory)
                state_label = {
                    "locked": "non commencée",
                    "active": "en cours",
                    "completed": "terminée",
                }.get(q.state, q.state)

                lines.append(f"- {q.title} : {q.description}")
                lines.append(f"  • Donnée par : {q.giver}.")
                lines.append(f"  • État actuel : {state_label}.")
                if total > 0:
                    lines.append(
                        f"  • Progression estimée d'après l'inventaire du joueur : {cur} / {total} objet(s) requis."
                    )
                if q.id in completed:
                    lines.append(
                        "  • Tous les objets requis semblent présents dans l'inventaire du joueur. "
                        "Tu peux reconnaître qu'il a rempli sa part du marché et réagir en conséquence."
                    )

        # Instruction finale
        lines.append("")
        lines.append(
            "IMPORTANT : tu dois parler de ces quêtes de manière ROLEPLAY, adaptée à ta personnalité, "
            "sans étaler toute cette description. Concentre-toi sur ce qui est utile au joueur "
            "dans la conversation actuelle."
        )

        return "\n".join(lines)
