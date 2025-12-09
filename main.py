import arcade

from player import Player
from map_manager import MapManager, TILE_SCALING


SCREEN_TITLE = "RPG Medieval"
PLAYER_SPEED = 4
DEBUG_COLLISION = False


class Game(arcade.Window):
    def __init__(self):
        super().__init__(fullscreen=True, title=SCREEN_TITLE)

        # Caméras
        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        # Joueur + gestionnaire de maps
        self.player = Player(scale=1.0)
        self.map_manager = MapManager(self)

        self.pressed_keys: set[int] = set()

        arcade.set_background_color(arcade.color.BLACK)

        self.default_zoom = 1.0
        self.default_player_scale = 1.1

    # --- NOUVELLE MÉTHODE ---
    def apply_map_settings(self, map_name: str):
        """Ajuste zoom caméra et taille du joueur selon la map."""
        name = map_name.lower()

        if name.startswith("dungeon1"):
            self.camera.zoom = 1.7
            self.player.scale = 0.6       
        elif name.startswith("big_tavern"):
            self.camera.zoom = 1.7       
            self.player.scale = 1.1 
        elif name.startswith("small_tavern"):
            self.camera.zoom = 1.7       
            self.player.scale = 1.1 
        elif name.startswith("middle_tavern"):
            self.camera.zoom = 1.7       
            self.player.scale = 1.1 
        elif name.startswith("beginning"):
            self.camera.zoom = 1.7       
            self.player.scale = 0.7
        elif name.startswith("interior1"):
            self.camera.zoom = 2.0       
            self.player.scale = 0.6 
        else:
            # Toutes les autres maps
            self.camera.zoom = self.default_zoom
            self.player.scale = self.default_player_scale

    # ----------------------------------------------------------------- setup
    def setup(self):
        # On démarre sur la map "village", à l'objet "spawn_player"
        self.map_manager.load_map("village", "spawn_player", self.player)
        self.apply_map_settings("village")

    # ------------------------------------------------------------------ draw
    def on_draw(self):
        self.clear()

        self.camera.use()

        if self.map_manager.scene:
            self.map_manager.scene.draw()

        # Affichage des zones de debug si besoin
        if DEBUG_COLLISION:
            self.map_manager.walls.draw()
            self.map_manager.transitions.draw()

        self.gui_camera.use()

        # --- Affichage "Appuyez sur E" ---
        hits = arcade.check_for_collision_with_list(
            self.player, self.map_manager.transitions
        )
        if hits:
            # Convertit coordonnées monde → écran
            cam_x, cam_y = self.camera.position
            screen_x = self.player.center_x - cam_x + self.get_size()[0] / 2
            screen_y = self.player.center_y - cam_y + self.get_size()[1] / 2

            arcade.draw_text(
                "Appuyez sur E",
                screen_x,
                screen_y + 40,
                arcade.color.WHITE,
                20,
                anchor_x="center"
            )



    # ---------------------------------------------------------------- update
    def on_update(self, delta_time: float):
        # Sauvegarde de la position avant déplacement
        self.player.remember_position()

        # Reset du mouvement
        self.player.change_x = 0
        self.player.change_y = 0

        # ZQSD ou flèches
        if arcade.key.UP in self.pressed_keys or arcade.key.Z in self.pressed_keys:
            self.player.change_y = PLAYER_SPEED
        if arcade.key.DOWN in self.pressed_keys or arcade.key.S in self.pressed_keys:
            self.player.change_y = -PLAYER_SPEED
        if arcade.key.LEFT in self.pressed_keys or arcade.key.Q in self.pressed_keys:
            self.player.change_x = -PLAYER_SPEED
        if arcade.key.RIGHT in self.pressed_keys or arcade.key.D in self.pressed_keys:
            self.player.change_x = PLAYER_SPEED

        # Déplacement + animation
        self.player.update()
        self.player.update_animation(delta_time)

        # Collisions avec les murs
        if arcade.check_for_collision_with_list(self.player, self.map_manager.walls):
            self.player.center_x = self.player.previous_x
            self.player.center_y = self.player.previous_y

        # Caméra qui suit le joueur
        self.update_camera()

        # Interaction : si on maintient E, on teste les transitions
        if arcade.key.E in self.pressed_keys:
            self.check_for_map_transition()

    # ----------------------------------------------------------- camera logic
    def update_camera(self):
        if not self.map_manager.tile_map:
            return

        # Taille réelle visible à l'écran (corrigée par le zoom)
        zoom = self.camera.zoom
        screen_w, screen_h = self.get_size()
        visible_w = screen_w / zoom
        visible_h = screen_h / zoom

        # Taille totale de la map en pixels
        world_w = self.map_manager.tile_map.width * self.map_manager.tile_map.tile_width
        world_h = self.map_manager.tile_map.height * self.map_manager.tile_map.tile_height

        # Position idéale (center on player)
        target_x = self.player.center_x
        target_y = self.player.center_y

        # Limites de caméra (corrigées)
        min_x = visible_w / 2
        max_x = world_w - visible_w / 2
        min_y = visible_h / 2
        max_y = world_h - visible_h / 2

        # Si la map est plus petite que l’écran → centrer automatiquement
        if world_w < visible_w:
            cam_x = world_w / 2
        else:
            cam_x = min(max(target_x, min_x), max_x)

        if world_h < visible_h:
            cam_y = world_h / 2
        else:
            cam_y = min(max(target_y, min_y), max_y)

        self.camera.position = (cam_x, cam_y)


    # ------------------------------------------------------ map transitions
    def check_for_map_transition(self):
        """
        Si le joueur est sur une zone de transition, on change de map.

        Les zones viennent du calque "Transitions" dans Tiled.
        Chaque sprite de transition porte :
          - sprite.target_map   (ex: "big_tavern.tmx")
          - sprite.target_spawn (ex: "big_entrance")
        """
        hits = arcade.check_for_collision_with_list(
            self.player, self.map_manager.transitions
        )
        if not hits:
            return

        trigger = hits[0]
        target_map = getattr(trigger, "target_map", None)
        target_spawn = getattr(trigger, "target_spawn", None)

        if not target_map or not target_spawn:
            return

        # On charge la nouvelle map en gardant le même Player
        self.map_manager.load_map(target_map, target_spawn, self.player)
        self.apply_map_settings(target_map)

    # -------------------------------------------------------------- input
    def on_key_press(self, key, modifiers):
        # ESC = quitter le jeu
        if key == arcade.key.ESCAPE:
            arcade.exit()
            return

        self.pressed_keys.add(key)

    def on_key_release(self, key, modifiers):
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)


def main():
    game = Game()
    game.setup()
    arcade.enable_timings()
    arcade.run()


if __name__ == "__main__":
    main()
