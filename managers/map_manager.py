import os
from typing import Tuple, Optional

import arcade

TILE_SCALING = 1.0


def _extract_point(shape) -> Tuple[float, float]:
    """Retourne un (x, y) depuis shape d'un TiledObject."""
    if shape is None:
        return 0.0, 0.0

    # Point (x, y)
    if isinstance(shape, (tuple, list)) and len(shape) == 2 and isinstance(shape[0], (int, float)):
        return float(shape[0]), float(shape[1])

    # Polygone / rectangle
    if isinstance(shape, list) and shape and isinstance(shape[0], (tuple, list)):
        xs = [p[0] for p in shape]
        ys = [p[1] for p in shape]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        return (x_min + x_max) / 2.0, (y_min + y_max) / 2.0

    return 0.0, 0.0


def _extract_bbox(shape) -> Tuple[float, float, float, float]:
    """Retourne (center_x, center_y, width, height) depuis shape."""
    if isinstance(shape, list) and shape and isinstance(shape[0], (tuple, list)):
        xs = [p[0] for p in shape]
        ys = [p[1] for p in shape]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        w = x_max - x_min
        h = y_max - y_min
        return x_min + w / 2.0, y_min + h / 2.0, w, h

    # Si c'est un point : boîte 1x1
    x, y = _extract_point(shape)
    return x, y, 1.0, 1.0


class MapManager:
    """Gère le chargement des maps Tiled : collisions, PNJ, transitions."""

    def __init__(self, window: arcade.Window, maps_folder: str = "data/maps"):
        self.window = window
        self.maps_folder = maps_folder

        self.current_map: Optional[str] = None
        self.tile_map: Optional[arcade.TileMap] = None
        self.scene: Optional[arcade.Scene] = None

        self.walls = arcade.SpriteList()
        self.transitions = arcade.SpriteList()
        self.npc_list = arcade.SpriteList()
        self.npc_interactions = arcade.SpriteList()

    # ------------------------------------------------------------------
    def _tmx_path(self, map_name: str) -> str:
        """Retourne le chemin vers la map."""
        if not map_name.lower().endswith(".tmx"):
            map_name = f"{map_name}.tmx"
        return os.path.join(self.maps_folder, map_name)

    # ------------------------------------------------------------------
    def load_map(self, map_name: str, spawn_name: str, player_sprite: arcade.Sprite):
        """Charge une map et configure ses éléments."""
        self.current_map = map_name

        map_file = self._tmx_path(map_name)
        self.tile_map = arcade.load_tilemap(map_file, scaling=TILE_SCALING)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)


        # --------------------------- COLLISIONS ---------------------------
        self.walls = arcade.SpriteList()

        if "Collision" in self.tile_map.object_lists:
            for obj in self.tile_map.object_lists["Collision"]:
                cx, cy, w, h = _extract_bbox(obj.shape)
                wall = arcade.SpriteSolidColor(int(w), int(h), (255, 255, 255, 0))
                wall.center_x = cx
                wall.center_y = cy
                self.walls.append(wall)


        # --------------------------- TRANSITIONS -------------------------
        self.transitions = arcade.SpriteList()

        if "Transitions" in self.tile_map.object_lists:
            for obj in self.tile_map.object_lists["Transitions"]:
                cx, cy, w, h = _extract_bbox(obj.shape)
                sprite = arcade.SpriteSolidColor(int(w), int(h), (0, 255, 0, 80))
                sprite.center_x = cx
                sprite.center_y = cy

                sprite.target_map = obj.properties.get("target_map")
                sprite.target_spawn = obj.properties.get("target_spawn")

                self.transitions.append(sprite)


        # --------------------------- PNJ + interaction ---------------------------
        self.npc_list = arcade.SpriteList()
        self.npc_interactions = arcade.SpriteList()

        if "NPCs" in self.tile_map.object_lists:
            for npc in self.tile_map.object_lists["NPCs"]:
                name = npc.name or ""

                if "maire" in name:
                    texture_path = "assets/npcs/maire.png"
                elif "comtesse" in name or "comptesse" in name:
                    texture_path = "assets/npcs/comtesse.png"
                elif "hotelier" in name:
                    texture_path = "assets/npcs/hotelier.png"
                elif "serveur" in name:
                    texture_path = "assets/npcs/serveur.png"
                elif "geolier" in name:
                    texture_path = "assets/npcs/geolier.png"
                elif "prisonier" in name:
                    texture_path = "assets/npcs/prisonier.png"
                elif "alchimiste" in name:
                    texture_path = "assets/npcs/alchimiste.png"
                elif "paysan" in name:
                    texture_path = "assets/npcs/paysan.png"
                elif "forgeron" in name:
                    texture_path = "assets/npcs/forgeron.png"
                else:
                    continue

                # Récupération éventuelle du scale personnalisé
                custom_scale = npc.properties.get("scale", 0.10)

                sprite = arcade.Sprite(texture_path, scale=custom_scale)
                sprite.npc_name = name
                x, y = _extract_point(npc.shape)
                sprite.center_x = x
                sprite.center_y = y

                self.npc_list.append(sprite)

                # Zone d'interaction
                interaction_size = custom_scale * 400  # ajuste selon ta préférence
                zone = arcade.SpriteSolidColor(int(interaction_size), int(interaction_size), (0, 0, 0, 0))
                zone.center_x = x
                zone.center_y = y
                zone.npc_ref = sprite
                self.npc_interactions.append(zone)

        # Ajout PNJ
        if "NPCs" not in self.scene:
            self.scene.add_sprite_list("NPCs")

        npc_layer = self.scene["NPCs"]
        npc_layer.clear()
        for n in self.npc_list:
            npc_layer.append(n)


        # --------------------------- JOUEUR ------------------------------
        spawn_layer = self.tile_map.object_lists.get("Spawn", [])
        spawn_obj = None

        for obj in spawn_layer:
            if obj.name == spawn_name:
                spawn_obj = obj
                break

        # Si aucun spawn spécifique, on prend le premier
        if spawn_obj is None and spawn_layer:
            spawn_obj = spawn_layer[0]

        # Position du joueur
        if spawn_obj:
            px, py = _extract_point(spawn_obj.shape)
            player_sprite.center_x = px
            player_sprite.center_y = py

        # -------- Joueur dans la scène --------
        # Si la SpriteList Player n’existe pas encore, on la crée
        if "Player" not in self.scene:
            self.scene.add_sprite_list("Player")

        # On vide la liste Player pour éviter les doublons quand on change de map
        player_layer = self.scene["Player"]
        player_layer.clear()

        # On ajoute le joueur
        player_layer.append(player_sprite)

        # --------------------------- OBJETS RAMASSABLES ---------------------------
        self.items = arcade.SpriteList()

        if "Items" in self.tile_map.object_lists:
            for obj in self.tile_map.object_lists["Items"]:
                item_name = obj.name or "unknown"

                # Texture depuis propriété Tiled
                texture_path = obj.properties.get("texture", f"assets/objet/{item_name}.png")

                # Option de scale (depuis Tiled)
                item_scale = obj.properties.get("scale", 0.8)

                sprite = arcade.Sprite(texture_path, scale=item_scale)

                x, y = _extract_point(obj.shape)
                sprite.center_x = x
                sprite.center_y = y

                sprite.item_id = item_name  # identifiant de l'objet
                self.items.append(sprite)


