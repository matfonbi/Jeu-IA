import os
from typing import Tuple, Optional

import arcade

TILE_SCALING = 1.0


def _extract_point(shape) -> Tuple[float, float]:
    """
    Retourne un (x, y) depuis shape d'un TiledObject.

    - Point : shape = (x, y)
    - Rectangle/polygone : shape = liste de (x, y) -> centre de la bbox
    """
    if shape is None:
        return 0.0, 0.0

    # Point (x, y)
    if isinstance(shape, (tuple, list)) and len(shape) == 2 and isinstance(
        shape[0], (int, float)
    ):
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

    # Pour un point : petite bbox 1x1
    x, y = _extract_point(shape)
    return x, y, 1.0, 1.0


class MapManager:
    """Gère le chargement des maps Tiled, collisions et zones de transition."""

    def __init__(self, window: arcade.Window, maps_folder: str = "data/maps") -> None:
        self.window = window
        self.maps_folder = maps_folder

        self.current_map: Optional[str] = None
        self.tile_map: Optional[arcade.TileMap] = None
        self.scene: Optional[arcade.Scene] = None

        self.walls: arcade.SpriteList = arcade.SpriteList()
        self.transitions: arcade.SpriteList = arcade.SpriteList()
        self.npc_list: arcade.SpriteList = arcade.SpriteList()

    # ------------------------------------------------------------------ utils
    def _tmx_path(self, map_name: str) -> str:
        """Retourne le chemin complet vers la map.

        Accepte "village" ou "village.tmx".
        """
        if not map_name.lower().endswith(".tmx"):
            map_name = f"{map_name}.tmx"
        return os.path.join(self.maps_folder, map_name)

    # ----------------------------------------------------------------- loading
    def load_map(self, map_name: str, spawn_name: str, player_sprite: arcade.Sprite) -> None:
        """
        Charge une map, positionne le joueur et reconstruit collisions + transitions.

        map_name : "village" ou "village.tmx"
        spawn_name : nom de l'objet dans le calque "Spawn"
        """
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
                # Légèrement visible si on décide de les dessiner en debug
                sprite = arcade.SpriteSolidColor(int(w), int(h), (0, 255, 0, 80))
                sprite.center_x = cx
                sprite.center_y = cy

                # On recopie les propriétés Tiled sur le sprite
                sprite.target_map = obj.properties.get("target_map")
                sprite.target_spawn = obj.properties.get("target_spawn")
                self.transitions.append(sprite)

        # --------------------------- PNJ --------------------------------
        self.npc_list = arcade.SpriteList()

        if "NPCs" in self.tile_map.object_lists:
            npc_objects = self.tile_map.object_lists["NPCs"]
            for npc in npc_objects:
                name = npc.name or ""

                if "maire" in name:
                    texture_path = "assets/npcs/maire.png"
                elif "comptesse" in name or "comtesse" in name:
                    texture_path = "assets/npcs/comtesse.png"
                elif "hotelier" in name:
                    texture_path = "assets/npcs/hotelier.png"
                elif "serveur" in name:
                    texture_path = "assets/npcs/serveur.png"
                else:
                    continue

                sprite = arcade.Sprite(texture_path, scale=0.10)
                x, y = _extract_point(npc.shape)
                sprite.center_x = x
                sprite.center_y = y
                self.npc_list.append(sprite)

            self.scene.add_sprite_list("NPCs", sprite_list=self.npc_list)

        # --------------------------- JOUEUR ------------------------------
        spawn_layer = self.tile_map.object_lists.get("Spawn", [])
        spawn_obj = None
        for obj in spawn_layer:
            if obj.name == spawn_name:
                spawn_obj = obj
                break

        if spawn_obj is None and spawn_layer:
            # fallback : premier objet du calque Spawn
            spawn_obj = spawn_layer[0]

        if spawn_obj is not None:
            px, py = _extract_point(spawn_obj.shape)
            player_sprite.center_x = px
            player_sprite.center_y = py

        # Ajout du joueur dans la nouvelle scène
        if "Player" not in self.scene._sprite_lists:
            self.scene.add_sprite_list("Player")

        player_list = self.scene["Player"]
        if player_sprite not in player_list:
            player_list.append(player_sprite)
