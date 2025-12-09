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

    # ----------------------------------------------------------------- setup
    def setup(self):
        # On démarre sur la map "village", à l'objet "spawn_player"
        self.map_manager.load_map("village", "spawn_player", self.player)

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

        world_w = (
            self.map_manager.tile_map.width * self.map_manager.tile_map.tile_width
        )
        world_h = (
            self.map_manager.tile_map.height * self.map_manager.tile_map.tile_height
        )

        screen_w, screen_h = self.get_size()

        target_x = self.player.center_x
        target_y = self.player.center_y

        min_x = screen_w / 2
        max_x = world_w - screen_w / 2
        min_y = screen_h / 2
        max_y = world_h - screen_h / 2

        cam_x = min(max(target_x, min_x), max_x)
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
