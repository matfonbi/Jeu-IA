import json
import os

class MapSettingsLoader:
    def __init__(self):
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config",
            "map_settings.json"
        )

        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Map settings file missing at: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self.settings = json.load(f)

    def get_settings_for(self, map_name: str):
        """
        Trouve les réglages correspondant à une map :
        - match exact
        - match prefix (startswith)
        - sinon None
        """
        name = map_name.lower()

        # Match exact
        if name in self.settings:
            return self.settings[name]

        # Match par prefix ("dungeon1_A" correspond à "dungeon1")
        for key in self.settings:
            if name.startswith(key):
                return self.settings[key]

        # Rien trouvé
        return None
