import json
from groq import Groq
from dotenv import load_dotenv
import os
load_dotenv() 

class NPC_Agent:
    def __init__(self, npc_name, context_path, memory_path):
        self.npc_name = npc_name
        self.context_path = context_path
        self.memory_path = memory_path

        self.client = Groq(api_key=os.environ["GROQ_KEY"])

        # Charger contexte perso
        with open(context_path, "r", encoding="utf-8") as f:
            self.context = f.read()

        # Charger mémoire
        if os.path.exists(memory_path):
            with open(memory_path, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        else:
            self.history = []

    # Sauvegarde continue de la mémoire
    def save_memory(self):
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

    # Le PNJ répond via Groq
    def ask(self, player_message, inventory_list, model="openai/gpt-oss-120b"):

        messages = [
            # Contexte fixe du PNJ
            {
                "role": "system",
                "content": self.context
            },
            # Inventaire du joueur
            {
                "role": "system",
                "content": f"Le joueur possède actuellement : {inventory_list}"
            }
        ]

        # Ajouter historique
        messages += self.history

        # Ajouter dernier message joueur
        messages.append({"role": "user", "content": player_message})

        response = self.client.chat.completions.create(
            messages=messages,
            model=model
        ).choices[0].message.content

        # Mémorisation
        self.history.append({"role": "user", "content": player_message})
        self.history.append({"role": "assistant", "content": response})
        self.save_memory()

        return response

    # Réplique initiale quand on commence à parler
    def start_dialog(self, inventory_list):
        greeting = "Le joueur approche. Comment l'accueilles-tu ?"

        return self.ask(greeting, inventory_list)
