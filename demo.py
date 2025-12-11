from groq import Groq
from dotenv import load_dotenv
import os
import json
load_dotenv()



client = Groq(api_key=os.environ["GROQ_KEY"])


def ask_llm(interaction: str) -> dict:
    context = """
            Réponds uniquement en JSON avec les clés obligatoires :
            {
            "poem_textuel" : "......"
            "emotion": "...",
            }
            Tu devras traiter l'interaction de l'utilisateur pour la retranscrire en un poème
            pour les émotions choisis uniquement à partir de ces 3 les plus probables (heureux, neutre, triste)
            """
    response = client.chat.completions.create(
        messages=[

            {
                "role": "system",
                "content": context
            },

            {
                "role": "user",
                "content": interaction,

            }
        ],
        response_format={"type": "json_object"},

        model="openai/gpt-oss-20b",
        temperature=0,
    )
    result = json.loads(response.choices[0].message.content)

    return result


print(ask_llm(f"Je suis en vancances c'est super !"))