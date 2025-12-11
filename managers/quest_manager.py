from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from core.npc import get_npc_state



@dataclass
class Quest:
    id: str
    title: str
    description: str
    giver: str
    validator: str
    requirements: Dict[str, Dict[str, int]]
    reward_item: Optional[str] = None
    state: str = "locked"

    def get_item_requirements(self) -> Dict[str, int]:
        return self.requirements.get("items", {})

    def compute_progress(self, inventory: Dict[str, int]) -> Tuple[int, int]:
        req_items = self.get_item_requirements()
        total = sum(req_items.values())
        if total == 0:
            return 0, 0

        current = 0
        for item_id, needed in req_items.items():
            current += min(inventory.get(item_id, 0), needed)
        return current, total

    def requirements_met(self, inventory: Dict[str, int]) -> bool:
        req_items = self.get_item_requirements()
        for item_id, needed in req_items.items():
            if inventory.get(item_id, 0) < needed:
                return False
        return True


class QuestManager:

    def __init__(self) -> None:
        self.quests: Dict[str, Quest] = {}
        self._build_quests()

    def _build_quests(self) -> None:
        q: Dict[str, Quest] = {}

        q["maire_pont"] = Quest(
            id="maire_pont",
            title="Réparer le vieux pont",
            description="Le maire veut commencer les réparations du vieux pont. Le joueur doit trouver une planche solide",
            giver="maire",
            validator="maire",
            reward_item="echarpe",
            requirements={"items": {"planche": 1}},
        )

        q["alchimiste_potions"] = Quest(
            id="alchimiste_potions",
            title="Les potions égarées",
            description="Merlin a perdu trois potions dans la ville.",
            giver="alchimiste",
            validator="alchimiste",
            reward_item="potion_doree",
            requirements={"items": {"potion": 3}},
        )

        q["comptesse_camee"] = Quest(
            id="comptesse_camee",
            title="Le camée disparu",
            description="La comtesse a perdu un petit bijou de famille.",
            giver="comptesse",
            validator="comptesse",
            reward_item="diadem",
            requirements={"items": {"camee": 1}},
        )

        q["forgeron_marteau"] = Quest(
            id="forgeron_marteau",
            title="L'outil égaré",
            description="Garrod a perdu son marteau de forgeron.",
            giver="forgeron",
            validator="forgeron",
            reward_item="enclume",
            requirements={"items": {"marteau_forgeron": 1}},
        )

        q["geolier_cle"] = Quest(
            id="geolier_cle",
            title="La clé enfouie",
            description="Le geôlier a perdu une clé rouillée.",
            giver="geolier",
            validator="geolier",
            reward_item="cle",
            requirements={"items": {"cle_rouillee": 1}},
        )

        q["hotelier_parfum"] = Quest(
            id="hotelier_parfum",
            title="La chambre parfaite",
            description="Un parfum rare est nécessaire pour une chambre.",
            giver="hotelier",
            validator="hotelier",
            reward_item="valise",
            requirements={"items": {"parfum": 1}},
        )

        q["prisonier_preuve"] = Quest(
            id="prisonier_preuve",
            title="La preuve froissée",
            description="Lanson prétend avoir une preuve de son innocence.",
            giver="prisonier",
            validator="prisonier",
            reward_item="menotte",
            requirements={"items": {"papier_preuve": 1}},
        )

        q["serveur_tonnelet"] = Quest(
            id="serveur_tonnelet",
            title="Le tonnelet d'essai",
            description="Tibo a perdu un tonnelet lors d’un test.",
            giver="serveur",
            validator="serveur",
            reward_item="chope",
            requirements={"items": {"tonnelet": 1}},
        )

        q["paysan_ble_maire"] = Quest(
            id="paysan_ble_maire",
            title="Le pain du village",
            description="Le paysan veut que tu apportes trois blés au maire.",
            giver="paysan",
            validator="maire",
            reward_item="fourche",
            requirements={"items": {"Blé": 3}},
        )

        self.quests = q

    def reset_all(self) -> None:
        for quest in self.quests.values():
            quest.state = "locked"

    # ------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------

    @staticmethod
    def _normalize_npc_name(name: str) -> str:
        raw = (name or "").lower()
        known = [
            "maire", "alchimiste", "comptesse", "forgeron",
            "geolier", "hotelier", "paysan", "prisonier", "serveur",
        ]
        for k in known:
            if k in raw:
                return k
        return raw

    def _quests_given_by(self, npc: str) -> List[Quest]:
        npc = self._normalize_npc_name(npc)
        return [q for q in self.quests.values() if self._normalize_npc_name(q.giver) == npc]

    def _quests_validated_by(self, npc: str) -> List[Quest]:
        npc = self._normalize_npc_name(npc)
        return [q for q in self.quests.values() if self._normalize_npc_name(q.validator) == npc]

    # ------------------------------------------------------------
    # Interaction PNJ
    # ------------------------------------------------------------

    def handle_npc_interaction(
        self,
        npc_name: str,
        inventory: Dict[str, int],
    ) -> Tuple[Dict[str, List[str]], str]:

        npc = self._normalize_npc_name(npc_name)
        activated: List[str] = []
        ready_to_complete: List[str] = []  # quêtes dont les conditions sont remplies POUR CETTE DISCUSSION
        completed: List[str] = []          # quêtes déjà terminées AVANT cette discussion

        # Activation automatique des quêtes données par ce PNJ
        for q in self._quests_given_by(npc):
            if q.state == "locked":
                q.state = "active"
                activated.append(q.id)
            elif q.state == "completed":
                completed.append(q.id)

        # Quêtes validées par ce PNJ
        for q in self._quests_validated_by(npc):
            if q.state == "completed":
                completed.append(q.id)
            elif q.state == "active" and q.requirements_met(inventory):
                # Le joueur a tout ce qu'il faut, mais ON NE MODIFIE PAS ENCORE l'inventaire.
                # On signale juste à l'IA que la quête est prête à être résolue maintenant.
                ready_to_complete.append(q.id)

        events = {
            "activated": activated,
            "ready_to_complete": ready_to_complete,
            "completed": completed,
        }

        quest_prompt = self._build_quest_prompt_for_npc(
            npc_norm=npc,
            inventory=inventory,
            activated=activated,
            ready_to_complete=ready_to_complete,
            completed=completed,
        )

        return events, quest_prompt


    # ------------------------------------------------------------
    # TEXTE POUR L'IA
    # ------------------------------------------------------------

    def _build_quest_prompt_for_npc(
        self,
        npc_norm: str,
        inventory: Dict[str, int],
        activated: List[str],
        ready_to_complete: List[str],
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
        lines.append(
            "Les informations ci-dessous sur l'inventaire du joueur sont FIABLES. "
            "Si le joueur prétend posséder un objet alors que ces informations indiquent le contraire, "
            "tu dois en conclure qu'il ment, se trompe ou exagère, et NE PAS valider la quête."
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

                # Quête qui vient d'être lancée pendant cette interaction
                if q.id in activated:
                    lines.append(
                        "  • Cette quête vient juste d'être lancée dans cette conversation. "
                        "Tu dois expliquer clairement au joueur ce que tu attends de lui : "
                        "quel objet précis il doit récupérer, et pour qui. "
                        "Parle de cette quête de façon explicite (par exemple : lui demander d'aller chercher la planche, "
                        "le camée, le tonnelet, etc.)."
                    )

                # Quête qui vient d'être complétée grâce à l'inventaire
                if q.id in completed:
                    lines.append(
                        "  • Cette quête vient d'être accomplie maintenant : "
                        "l'inventaire montre que le joueur a tous les objets requis. "
                        "Tu dois réagir comme si tu remarques à cet instant qu'il apporte vraiment l'objet : "
                        "le remercier, reconnaître son effort, et considérer la quête comme résolue."
                    )
                    if q.reward_item:
                        lines.append(
                            f"  • Tu viens de remettre au joueur un objet de récompense : '{q.reward_item}'. "
                            "Tu dois le dire clairement dans ta réponse (par exemple : "
                            "'Voici pour toi cet objet en récompense.'), mais sans parler de mécanique de jeu."
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

                if q.id in ready_to_complete:
                    lines.append(
                        "  • Tous les objets requis sont présents dans l'inventaire du joueur à ce moment précis. "
                        "Tu dois le constater dans la conversation (comme s'il te montrait ou t'apportait l'objet), "
                        "le remercier et reconnaître qu'il a rempli sa part du marché."
                    )
                    if q.reward_item:
                        lines.append(
                            f"  • Tu viens de lui remettre la récompense prévue : '{q.reward_item}'. "
                            "Mentionne clairement, dans ton style, que tu lui donnes cet objet. Sauf si votre relation est tres mauvaise du coup vous ne lui donnez pas l'objet car vous ne l'aimer pas"
                        )

        # Instruction finale
        lines.append("")
        lines.append(
            "IMPORTANT : tu dois parler de ces quêtes de manière ROLEPLAY, adaptée à ta personnalité. "
            "Ne récite pas cette liste. Utilise seulement les informations utiles pour la situation actuelle. "
            "Si le joueur dit quelque chose qui contredit ces informations internes (par exemple, il prétend avoir "
            "un objet qu'il n'a pas), tu dois te fier à ces informations internes et réagir en conséquence."
        )

        return "\n".join(lines)

    def finalize_quests_after_dialog(
        self,
        npc_name: str,
        inventory: Dict[str, int],
    ) -> List[str]:
        """
        À appeler APRÈS que le PNJ ait répondu.
        Si certaines quêtes sont 'actives' et que les requirements sont remplis,
        on les marque comme complétées, on retire les objets et on donne la récompense.
        Retourne la liste des quêtes réellement complétées.
        """
        npc = self._normalize_npc_name(npc_name)
        npc_state = get_npc_state(npc)
        relation = npc_state.relation_score
        completed_now: List[str] = []

        for q in self._quests_validated_by(npc):
            if q.state == "active" and q.requirements_met(inventory):
                # On finalise maintenant
                q.state = "completed"
                completed_now.append(q.id)

                # Retirer les objets
                for item_id, needed in q.get_item_requirements().items():
                    if item_id in inventory:
                        inventory[item_id] -= needed
                        if inventory[item_id] <= 0:
                            del inventory[item_id]

                # Si la relation est trop basse → ON NE DONNE PAS LA RÉCOMPENSE
                if relation < npc_state.min_relation_for_rewards:
                    print(f"[QUEST] {npc} refuse de donner la récompense (relation trop basse).")
                    continue

                # Donner la récompense
                if q.reward_item:
                    inventory[q.reward_item] = inventory.get(q.reward_item, 0) + 1
                    # BONUS si relation très haute
                    if relation >= npc_state.max_relation_bonus:
                        inventory[q.reward_item] += 1
                        print(f"[QUEST] BONUS ! {npc} donne une récompense supplémentaire.")


        return completed_now
