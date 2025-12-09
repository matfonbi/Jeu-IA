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

        arcade.set_background_color(arcade.color.BLACK)

        # Valeurs par défaut
        self.default_zoom = 1.0
        self.default_player_scale = 1.1

        # -------------------- BULLE D’INTERACTION --------------------
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

        # -------------------- TRANSITION FADE --------------------
        self.transition_alpha = 0.0
        self.transition_target = 0.0
        self.transition_speed = 10.0
        self.transition_callback = None

        # -------------------- DIALOGUES PNJ --------------------
        self.in_dialogue = False
        self.dialog_history = []
        self.dialog_input = ""
        self.current_npc = None
        self.npc_to_talk = None   # PNJ détecté dans zone


    # -------------------- TRANSITION --------------------

    def start_transition(self, callback):
        """Lance un fade-out avant la transition."""
        if self.transition_target != 0 or self.transition_alpha != 0:
            return
        self.transition_target = 255.0
        self.transition_callback = callback


    # -------------------- REGLAGES PAR MAP --------------------

    def apply_map_settings(self, map_name: str):
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


    # -------------------- SETUP --------------------

    def setup(self):
        self.map_manager.load_map("village", "spawn_player", self.player)
        self.apply_map_settings("village")


    # -------------------- DRAW --------------------

    def on_draw(self):
        self.clear()

        # Monde (map + joueur)
        self.camera.use()

        if self.map_manager.scene:
            self.map_manager.scene.draw()

        if DEBUG_COLLISION:
            self.map_manager.walls.draw()
            self.map_manager.transitions.draw()

        # Interface
        self.gui_camera.use()

        # ----------- Overlay noir (transition) -----------
        if self.transition_alpha > 0:
            win_w, win_h = self.get_size()

            arcade.draw_lbwh_rectangle_filled(
                0,
                0,
                win_w,
                win_h,
                (0, 0, 0, int(self.transition_alpha)),
            )

        # ----------- Bulle "Appuyez sur E" (Transitions) -----------
        if self.show_bubble and not self.in_dialogue:
            self.bubble_list.draw()

            arcade.draw_text(
                "Appuyez sur E",
                self.bubble_sprite.center_x,
                self.bubble_sprite.center_y - 7,
                arcade.color.WHITE,
                18,
                anchor_x="center",
            )

        # ----------- Bulle "Parler (E)" (PNJ) -----------
        if self.npc_to_talk and not self.in_dialogue:
            arcade.draw_text(
                "Parler (E)",
                self.bubble_sprite.center_x,
                self.bubble_sprite.center_y - 40,
                arcade.color.WHITE,
                18,
                anchor_x="center"
            )

        # ----------- FENÊTRE DE DIALOGUE -----------
        if self.in_dialogue:
            win_w, win_h = self.get_size()

            # Boîte noire
            arcade.draw_lbwh_rectangle_filled(
                50,
                50,
                win_w - 100,
                200,
                (0, 0, 0, 200),
            )

            # Historique
            y = 220
            for speaker, message in self.dialog_history[-4:]:
                arcade.draw_text(
                    f"{speaker}: {message}",
                    70,
                    y,
                    arcade.color.WHITE,
                    16,
                )
                y -= 28

            # Zone d’écriture
            arcade.draw_lbwh_rectangle_outline(
                60,
                60,
                win_w - 120,
                40,
                arcade.color.WHITE,
                2,
            )

            arcade.draw_text(
                self.dialog_input,
                70,
                70,
                arcade.color.WHITE,
                18
            )


    # -------------------- UPDATE --------------------

    def on_update(self, delta_time: float):
        if self.in_dialogue:
            return  # on freeze le joueur

        self.player.remember_position()

        # Reset
        self.player.change_x = 0
        self.player.change_y = 0

        # Contrôles
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

        # Collisions
        if arcade.check_for_collision_with_list(self.player, self.map_manager.walls):
            self.player.center_x = self.player.previous_x
            self.player.center_y = self.player.previous_y

        # Caméra
        self.update_camera()

        # Trigger map
        if arcade.key.E in self.pressed_keys:
            self.check_for_map_transition()

        # -------------------------------------------------
        # Détection PNJ + Bulle PNJ
        # -------------------------------------------------
        self.npc_to_talk = None

        npc_zones = self.map_manager.npc_interactions  # PAS dans la scene

        if npc_zones:
            detected = arcade.check_for_collision_with_list(self.player, npc_zones)
            if detected:
                zone = detected[0]
                self.npc_to_talk = zone.npc_ref
        
        # -------------------------------------------------
        # Bulle PNJ lorsqu’on est dans une zone d’interaction
        # -------------------------------------------------
        if self.npc_to_talk and not self.in_dialogue:
            cam_x, cam_y = self.camera.position
            win_w, win_h = self.get_size()

            # Position de la bulle au-dessus du joueur
            screen_x = self.player.center_x - cam_x + win_w / 2
            screen_y = self.player.center_y - cam_y + win_h / 2 + 50

            self.bubble_sprite.center_x = screen_x
            self.bubble_sprite.center_y = screen_y




        # -------------------------------------------------
        # Bulle transition
        # -------------------------------------------------
        hits = arcade.check_for_collision_with_list(
            self.player, self.map_manager.transitions
        )

        if hits and not self.in_dialogue:
            cam_x, cam_y = self.camera.position
            win_w, win_h = self.get_size()

            screen_x = self.player.center_x - cam_x + win_w / 2
            screen_y = self.player.center_y - cam_y + win_h / 2 + 50

            self.bubble_sprite.center_x = screen_x
            self.bubble_sprite.center_y = screen_y
            self.show_bubble = True
        else:
            self.show_bubble = False

        # -------------------------------------------------
        # Animation du fade-in / fade-out
        # -------------------------------------------------
        if self.transition_alpha != self.transition_target:
            if self.transition_alpha < self.transition_target:
                self.transition_alpha += self.transition_speed

                if self.transition_alpha >= self.transition_target:
                    self.transition_alpha = self.transition_target
                    if self.transition_alpha >= 255 and self.transition_callback:
                        self.transition_callback()
                        self.transition_callback = None
                        self.transition_target = 0  # fade-in

            else:
                self.transition_alpha -= self.transition_speed
                if self.transition_alpha <= self.transition_target:
                    self.transition_alpha = self.transition_target


    # -------------------- CAMERA --------------------

    def update_camera(self):
        if not self.map_manager.tile_map:
            return

        zoom = self.camera.zoom
        screen_w, screen_h = self.get_size()
        visible_w = screen_w / zoom
        visible_h = screen_h / zoom

        world_w = self.map_manager.tile_map.width * self.map_manager.tile_map.tile_width
        world_h = self.map_manager.tile_map.height * self.map_manager.tile_map.tile_height

        target_x = self.player.center_x
        target_y = self.player.center_y

        min_x = visible_w / 2
        max_x = world_w - visible_w / 2
        min_y = visible_h / 2
        max_y = world_h - visible_h / 2

        if world_w < visible_w:
            cam_x = world_w / 2
        else:
            cam_x = min(max(target_x, min_x), max_x)

        if world_h < visible_h:
            cam_y = world_h / 2
        else:
            cam_y = min(max(target_y, min_y), max_y)

        self.camera.position = (cam_x, cam_y)


    # -------------------- TRANSITIONS DE MAP --------------------

    def check_for_map_transition(self):
        hits = arcade.check_for_collision_with_list(
            self.player, self.map_manager.transitions
        )
        if not hits or self.in_dialogue:
            return

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


    # -------------------- DIALOGUES --------------------

    def start_npc_dialog(self, npc):
        self.in_dialogue = True
        self.current_npc = npc

        self.dialog_history = [
            ("PNJ", "Bonjour, voyageur. Comment puis-je vous aider ?")
        ]
        self.dialog_input = ""


    def send_player_dialog(self):
        """Le joueur valide son message."""
        msg = self.dialog_input.strip()
        if not msg:
            return

        self.dialog_history.append(("Vous", msg))

        # ------ Réponse PNJ (version statique pour l'instant) ------
        response = "Je suis un PNJ simple… mais bientôt connecté à une IA !"
        self.dialog_history.append(("PNJ", response))

        self.dialog_input = ""


    # -------------------- INPUT --------------------

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            if self.in_dialogue:
                self.in_dialogue = False
                return
            arcade.exit()
            return

        if self.in_dialogue:
            if key == arcade.key.BACKSPACE:
                self.dialog_input = self.dialog_input[:-1]
            elif key == arcade.key.ENTER:
                self.send_player_dialog()
            return

        if key == arcade.key.E:
            if self.npc_to_talk and not self.in_dialogue:
                self.start_npc_dialog(self.npc_to_talk)

        self.pressed_keys.add(key)

    def on_text(self, text):
        if self.in_dialogue:
            self.dialog_input += text

    def on_key_release(self, key, modifiers):
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)


# -------------------- MAIN --------------------

def main():
    game = Game()
    game.setup()
    arcade.enable_timings()
    arcade.run()


if __name__ == "__main__":
    main()
