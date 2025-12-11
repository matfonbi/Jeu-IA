# main.py
import arcade
import json
import os
from dotenv import load_dotenv

load_dotenv()

from core.game import Game

def reset_all_memories():
    base = "npc"
    if not os.path.exists(base):
        return
    for folder in os.listdir(base):
        memory_path = os.path.join(base, folder, "memory.json")
        if os.path.isfile(memory_path):
            with open(memory_path, "w", encoding="utf-8") as f:
                json.dump([], f)

def main():
    reset_all_memories()
    game = Game()
    game.setup()
    arcade.run()

if __name__ == "__main__":
    main()
