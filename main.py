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

        # Entrées clavier
        self.pressed_keys: set[int] = set()

        # Fond
        arcade.set_background_color(arcade.color.BLACK)

        # Valeurs par défaut
        self.default_zoom = 1.0
        self.default_player_scale = 1.1

        # ---------- Bulle "Appuyez sur E" ----------
        self.bubble_texture = arcade.make_soft_square_texture(
            64,
            color=(0, 0, 0, 180),
            outer_alpha=180,
        )

        self.bubble_list = arcade.SpriteList()
        self.bubble_sprite = arcade.Sprite()
        self.bubble_sprite.texture = self.bubble_texture
        self.bubble_sprite.width = 160
        self.bubble_sprite.height = 40
        self.bubble_list.append(self.bubble_sprite)

        self.show_bubble = False

        # ---------- Transition fade in/out ----------
        self.transition_alpha = 0.0        # opacité actuelle (0-255)
        self.transition_target = 0.0       # cible (0 ou 255)
        self.transition_speed = 10.0       # vitesse du fade par frame
        self.transition_callback = None    # appelé quand fade-out est terminé

    # -------------------- Transition --------------------

    def start_transition(self, callback):
        """
        Lance un fade-out (vers noir). Quand alpha atteint 255, `callback` est appelé.
        Ensuite, le fade-in (retour à 0) se fait automatiquement.
        """
        # Si une transition est déjà en cours, on ne relance pas
        if self.transition_target != 0 or self.transition_alpha != 0:
            return
        self.transition_target = 255.0
        self.transition_callback = callback

    # -------------------- Réglages par map --------------------

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
            self.camera.zoom = self.default_zoom
            self.player.scale = self.default_player_scale

    # ------------------------ Setup ------------------------

    def setup(self):
        # On démarre sur la map "village", à l'objet "spawn_player"
        self.map_manager.load_map("village", "spawn_player", self.player)
        self.apply_map_settings("village")

    # ------------------------- Draw ------------------------

    def on_draw(self):
        self.clear()

        # Monde (map + joueur)
        self.camera.use()

        if self.map_manager.scene:
            self.map_manager.scene.draw()

        if DEBUG_COLLISION:
            self.map_manager.walls.draw()
            self.map_manager.transitions.draw()

        # Interface (bulle, HUD, fade, etc.)
        self.gui_camera.use()

        # --------- Overlay noir de transition ---------
        if self.transition_alpha > 0:
            win_w, win_h = self.get_size()
            # Rectangle plein couvrant tout l'écran
            arcade.draw_lbwh_rectangle_filled(
                0,
                0,
                win_w,
                win_h,
                (0, 0, 0, int(self.transition_alpha)),
            )

        # --------- Bulle "Appuyez sur E" ---------
        if self.show_bubble:
            self.bubble_list.draw()
            arcade.draw_text(
                "Appuyez sur E",
                self.bubble_sprite.center_x,
                self.bubble_sprite.center_y - 7,
                arcade.color.WHITE,
                18,
                anchor_x="center",
            )

    # ------------------------ Update ------------------------

    def on_update(self, delta_time: float):
        # Sauvegarde de la position avant déplacement (pour corriger collisions)
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

        # Gestion de la bulle "Appuyez sur E"
        hits = arcade.check_for_collision_with_list(
            self.player, self.map_manager.transitions
        )

        if hits:
            cam_x, cam_y = self.camera.position
            win_w, win_h = self.get_size()

            screen_x = self.player.center_x - cam_x + win_w / 2
            screen_y = self.player.center_y - cam_y + win_h / 2 + 50

            self.bubble_sprite.center_x = screen_x
            self.bubble_sprite.center_y = screen_y
            self.show_bubble = True
        else:
            self.show_bubble = False

        # --- Animation de transition (fade in/out) ---
        if self.transition_alpha != self.transition_target:
            if self.transition_alpha < self.transition_target:
                self.transition_alpha += self.transition_speed
                if self.transition_alpha >= self.transition_target:
                    self.transition_alpha = self.transition_target
                    # Quand on est arrivé à 255 (écran noir) on change la map
                    if self.transition_alpha >= 255 and self.transition_callback:
                        self.transition_callback()
                        self.transition_callback = None
                        # Maintenant on lance le fade-in
                        self.transition_target = 0.0
            else:
                self.transition_alpha -= self.transition_speed
                if self.transition_alpha <= self.transition_target:
                    self.transition_alpha = self.transition_target

    # --------------------- Caméra ---------------------

    def update_camera(self):
        if not self.map_manager.tile_map:
            return

        # Taille visible à l'écran (corrigée par le zoom)
        zoom = self.camera.zoom
        screen_w, screen_h = self.get_size()
        visible_w = screen_w / zoom
        visible_h = screen_h / zoom

        # Taille totale de la map en pixels
        world_w = (
            self.map_manager.tile_map.width * self.map_manager.tile_map.tile_width
        )
        world_h = (
            self.map_manager.tile_map.height * self.map_manager.tile_map.tile_height
        )

        # Position idéale (center on player)
        target_x = self.player.center_x
        target_y = self.player.center_y

        # Limites caméra
        min_x = visible_w / 2
        max_x = world_w - visible_w / 2
        min_y = visible_h / 2
        max_y = world_h - visible_h / 2

        # Si la map est plus petite que l’écran → on centre
        if world_w < visible_w:
            cam_x = world_w / 2
        else:
            cam_x = min(max(target_x, min_x), max_x)

        if world_h < visible_h:
            cam_y = world_h / 2
        else:
            cam_y = min(max(target_y, min_y), max_y)

        self.camera.position = (cam_x, cam_y)

    # ----------------- Transitions de map -----------------

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

        # On ne lance pas une nouvelle transition si une est déjà en cours
        if self.transition_target != 0 or self.transition_alpha != 0:
            return

        trigger = hits[0]
        target_map = getattr(trigger, "target_map", None)
        target_spawn = getattr(trigger, "target_spawn", None)

        if not target_map or not target_spawn:
            return

        def do_change():
            self.map_manager.load_map(target_map, target_spawn, self.player)
            self.apply_map_settings(target_map)

        self.start_transition(do_change)

    # ----------------------- Input -----------------------

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
