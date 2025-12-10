import os
import json
from groq import Groq


class NPC_Agent:
    """
    Un agent PNJ totalement modulaire :
    - Lit tous les blocs du fichier context.txt
    - Utilise first_meeting_prompt / returning_prompt
    - Injecte personnalité / style / relations dans chaque requête
    - Conserve une mémoire persistante (memory.json)
    """

    def __init__(self, npc_folder: str):

        # ---------------------
        # Dossiers / fichiers
        # ---------------------
        self.npc_folder = npc_folder
        self.context_path = os.path.join(npc_folder, "context.txt")
        self.memory_path = os.path.join(npc_folder, "memory.json")

        # ---------------------
        # Lecture du fichier de contexte
        # ---------------------
        self.context = self.load_context_file()

        # Nom du PNJ (défaut si absent)
        self.name = self.context.get("name", "PNJ Inconnu")

        # ---------------------
        # Lecture / création de la mémoire
        # ---------------------
        if not os.path.exists(self.memory_path):
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump([], f)

        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except:
            self.history = []
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump([], f)

        # ---------------------
        # Client Groq
        # ---------------------
        self.client = Groq(api_key=os.environ["GROQ_KEY"])

        # Modèle IA
        self.model = "llama-3.3-70b-versatile"  # modèle actuel recommandé


    # --------------------------------------------------------------
    # LECTURE DU FICHIER CONTEXTE
    # --------------------------------------------------------------
    def load_context_file(self):
        """
        Lit context.txt et renvoie un dict :
        {
          "first_meeting_prompt": "...",
          "returning_prompt": "...",
          "style": "...",
          ...
        }
        """

        if not os.path.exists(self.context_path):
            return {}

        data = {}
        current_key = None
        buffer = []

        with open(self.context_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")

                # Nouveau bloc : [key]
                if line.startswith("[") and line.endswith("]"):
                    # Sauvegarder le bloc précédent
                    if current_key is not None:
                        data[current_key] = "\n".join(buffer).strip()

                    current_key = line[1:-1]  # retire les []
                    buffer = []
                else:
                    buffer.append(line)

            # Sauvegarder le dernier bloc
            if current_key is not None:
                data[current_key] = "\n".join(buffer).strip()

        return data


    # --------------------------------------------------------------
    # GÉNÈRE LE MESSAGE SYSTEM POUR GUIDER L’IA
    # --------------------------------------------------------------
    def build_system_prompt(self):
        """
        Assemble style + personnalité + relations + lore du PNJ
        dans un message system.
        """

        parts = []

        if "style" in self.context:
            parts.append(f"STYLE D'ÉLOCUTION :\n{self.context['style']}")

        if "personality" in self.context:
            parts.append(f"PERSONNALITÉ :\n{self.context['personality']}")

        if "relationships" in self.context:
            parts.append(f"RELATIONS AVEC LES AUTRES PNJ :\n{self.context['relationships']}")

        if "lore" in self.context:
            parts.append(f"LORE :\n{self.context['lore']}")

        # Rappel sur la mémoire
        parts.append(
            "IMPORTANT : Tu dois prendre en compte toutes les conversations précédentes "
            "présentes dans la mémoire. Ne contredis jamais l’historique."
        )

        return "\n\n".join(parts)


    # --------------------------------------------------------------
    # PREMIÈRE PHRASE QUAND LE DIALOGUE COMMENCE
    # --------------------------------------------------------------
    def start_dialog(self, inventory):
        """
        Choisit first_meeting_prompt ou returning_prompt selon la mémoire,
        puis appelle ask().
        """

        if len(self.history) == 0:
            greeting = self.context.get(
                "first_meeting_prompt",
                "Tu vois le joueur pour la première fois. Accueille-le."
            )
        else:
            greeting = self.context.get(
                "returning_prompt",
                "Tu reconnais le joueur car il t'a déjà parlé. Reprends naturellement la discussion."
            )

        return self.ask(greeting, inventory)


    # --------------------------------------------------------------
    # ENVOI D’UN MESSAGE DU JOUEUR ET RÉPONSE DU PNJ
    # --------------------------------------------------------------
    def ask(self, player_message: str, inventory_list):
        """
        message = ce que le joueur dit
        inventory_list = liste des objets
        """

        system_prompt = self.build_system_prompt()

        # Inventaire sous forme de phrase lisible
        inv = ", ".join(inventory_list) if inventory_list else "aucun objet notable"

        # Construction du dialogue pour l’IA
        messages = [
            {
                "role": "system",
                "content": (
                    f"Tu es {self.name}, un personnage dans un RPG narratif.\n\n"
                    f"{system_prompt}\n\n"
                    f"Inventaire actuel du joueur : {inv}"
                )
            }
        ]

        # Ajout de l'historique des conversations
        for h in self.history:
            messages.append({"role": h["role"], "content": h["content"]})

        # Ajout du nouveau message du joueur
        messages.append({"role": "user", "content": player_message})

        # Appel à Groq
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )

        npc_response = response.choices[0].message.content

        # Sauvegarde mémoire
        self.history.append({"role": "user", "content": player_message})
        self.history.append({"role": "assistant", "content": npc_response})

        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

        return npc_response
