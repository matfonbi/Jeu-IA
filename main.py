import arcade

from player import Player
from map_manager import MapManager, TILE_SCALING
from npc_agent import NPC_Agent
from dotenv import load_dotenv
import os
import json
import textwrap

load_dotenv()

SCREEN_TITLE = "RPG Medieval"
BASE_PLAYER_SPEED = 4
DEBUG_COLLISION = False


# ============================================================
#        UTILITAIRES TEXTE : WRAP + COMPTAGE LIGNES
# ============================================================

def wrap_text_to_width(text: str, max_width_px: float, font_size: int = 18):
    """
    Approximates wrapping by converting pixel width → max characters.
    Works on all Arcade versions without needing text measurement.
    """
    approx_char_width = font_size * 0.6  # heuristique : 0.6 * font_size
    max_chars = max(1, int(max_width_px / approx_char_width))
    return textwrap.wrap(text, width=max_chars)


def wrap_dialog_history(dialog_history, max_width_px: float, font_size: int = 18):
    """
    Transforme l'historique [(speaker, msg), ...] en une liste de lignes déjà wrap.
    Chaque entrée est un simple string prêt à être affiché.
    """
    lines = []
    for speaker, message in dialog_history:
        full = f"{speaker}: {message}"
        lines.extend(wrap_text_to_width(full, max_width_px, font_size))
    return lines


def count_wrapped_lines(dialog_history, max_width_px: float, font_size: int = 18):
    """Nombre total de lignes une fois le wrapping appliqué."""
    return len(wrap_dialog_history(dialog_history, max_width_px, font_size))


# ============================================================
#                           GAME
# ============================================================

class Game(arcade.Window):
    def __init__(self):
        super().__init__(fullscreen=True, title=SCREEN_TITLE)

        # Caméras
        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        # Joueur + gestionnaire de maps
        self.player = Player(scale=1.0)
        self.map_manager = MapManager(self)

        self.player_speed = BASE_PLAYER_SPEED

        # Entrées clavier
        self.pressed_keys: set[int] = set()
        self.dialog_scroll = 0  # offset de scroll (en lignes)

        arcade.set_background_color(arcade.color.BLACK)

        # ---------- INVENTAIRE & ITEMS ----------
        self.inventory = {}        # {item_id: quantité}
        self.item_to_pick = None   # sprite d'item détecté proche
        self.inventory_open = False
        self.inventory_slot_size = 64
        self.inventory_padding = 12

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
        self.dialog_history = []   # liste de (speaker, message)
        self.dialog_input = ""     # texte en cours de saisie
        self.current_npc = None
        self.npc_to_talk = None   # PNJ détecté dans zone

    # ============================================================
    #                       TRANSITION
    # ============================================================

    def start_transition(self, callback):
        """Lance un fade-out avant la transition."""
        if self.transition_target != 0 or self.transition_alpha != 0:
            return
        self.transition_target = 255.0
        self.transition_callback = callback

    # ============================================================
    #                  REGLAGES PAR MAP
    # ============================================================

    def apply_map_settings(self, map_name: str):
        name = map_name.lower()

        if name.startswith("dungeon1"):
            self.camera.zoom = 1.7
            self.player.scale = 0.6
            self.player_speed = 2
        elif name.startswith("big_tavern"):
            self.camera.zoom = 1.7
            self.player.scale = 1.1
            self.player_speed = 1.5
        elif name.startswith("small_tavern"):
            self.camera.zoom = 1.7
            self.player.scale = 1.1
            self.player_speed = 1.5
        elif name.startswith("middle_tavern"):
            self.camera.zoom = 1.7
            self.player.scale = 1.1
            self.player_speed = 1.5
        elif name.startswith("beginning"):
            self.camera.zoom = 1.7
            self.player.scale = 0.7
            self.player_speed = 2
        elif name.startswith("interior1"):
            self.camera.zoom = 2.0
            self.player.scale = 0.6
            self.player_speed = 1
        else:
            self.camera.zoom = self.default_zoom
            self.player.scale = self.default_player_scale
            self.player_speed = BASE_PLAYER_SPEED

    # ============================================================
    #                          SETUP
    # ============================================================

    def setup(self):
        self.map_manager.load_map("village", "spawn_player", self.player)
        self.apply_map_settings("village")

    # ============================================================
    #                          DRAW
    # ============================================================

    def on_draw(self):
        self.clear()

        # Monde (map + joueur)
        self.camera.use()

        if self.map_manager.scene:
            self.map_manager.scene.draw()

        if DEBUG_COLLISION:
            self.map_manager.walls.draw()
            self.map_manager.transitions.draw()

        self.map_manager.items.draw()

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
                anchor_x="center",
            )

        # ==========================
        #     BOÎTE DE DIALOGUE
        # ==========================
        if self.in_dialogue:
            win_w, win_h = self.get_size()

            # Dimensions dynamiques
            box_margin = 50
            box_width = win_w - box_margin * 2
            box_height = int(win_h * 0.40)  # 40 % de la hauteur écran
            box_x = box_margin
            box_y = box_margin

            # Fond
            arcade.draw_lbwh_rectangle_filled(
                box_x, box_y, box_width, box_height,
                (0, 0, 0, 200),
            )

            # ----- Zone d’écriture -----
            input_height = 45
            input_box_y = box_y + 10
            input_box_x = box_x + 15
            input_box_w = box_width - 30

            arcade.draw_lbwh_rectangle_outline(
                input_box_x,
                input_box_y,
                input_box_w,
                input_height,
                arcade.color.WHITE,
                2,
            )

            arcade.draw_text(
                self.dialog_input,
                input_box_x + 10,
                input_box_y + 12,
                arcade.color.WHITE,
                18,
            )

            # ----- Zone d’historique -----
            history_top = box_y + box_height - 20
            history_bottom = input_box_y + input_height + 15

            available_height = history_top - history_bottom
            line_height = 24
            max_lines_on_screen = max(1, available_height // line_height)

            # Toutes les lignes wrap
            max_width_px = box_width - 40
            wrapped_lines = wrap_dialog_history(
                self.dialog_history,
                max_width_px,
                font_size=18,
            )

            total_lines = len(wrapped_lines)
            if total_lines == 0:
                display_lines = []
            else:
                # Clamp du scroll
                max_scroll = max(0, total_lines - max_lines_on_screen)
                self.dialog_scroll = max(0, min(self.dialog_scroll, max_scroll))

                # On part du bas (dernières lignes) + offset de scroll
                start_index = max(0, total_lines - max_lines_on_screen - self.dialog_scroll)
                end_index = start_index + max_lines_on_screen
                display_lines = wrapped_lines[start_index:end_index]

            # Affichage des lignes
            y = history_top
            for line in display_lines:
                arcade.draw_text(
                    line,
                    box_x + 20,
                    y,
                    arcade.color.WHITE,
                    18,
                )
                y -= line_height

        # ---------- Texte "Ramasser (E)" pour les items ----------
        if self.item_to_pick and not self.in_dialogue:
            arcade.draw_text(
                f"Ramasser {self.item_to_pick.item_id} (E)",
                self.bubble_sprite.center_x,
                self.bubble_sprite.center_y - 40,
                arcade.color.WHITE,
                18,
                anchor_x="center",
            )

        # ==========================
        #        INVENTAIRE (I)
        # ==========================
        if self.inventory_open:
            win_w, win_h = self.get_size()

            width = 600
            height = 400
            x = (win_w - width) / 2
            y = (win_h - height) / 2

            arcade.draw_lbwh_rectangle_filled(
                x,
                y,
                width,
                height,
                (20, 20, 20, 230),
            )

            arcade.draw_lbwh_rectangle_outline(
                x,
                y,
                width,
                height,
                arcade.color.WHITE,
                3,
            )

            arcade.draw_text(
                "Inventaire",
                x + width / 2,
                y + height - 40,
                arcade.color.WHITE,
                28,
                anchor_x="center",
            )

            slot = self.inventory_slot_size
            pad = self.inventory_padding

            row = 0
            col = 0

            for item_name, quantity in self.inventory.items():
                sx = x + 40 + col * (slot + pad)
                sy = y + height - 120 - row * (slot + pad)

                arcade.draw_lbwh_rectangle_filled(sx, sy, slot, slot, (60, 60, 60, 200))
                arcade.draw_lbwh_rectangle_outline(sx, sy, slot, slot, arcade.color.WHITE, 2)

                texture_path = f"assets/objet/{item_name}.png"
                texture = arcade.load_texture(texture_path)

                icon = arcade.Sprite(texture, scale=1.0)
                icon.center_x = sx + slot / 2
                icon.center_y = sy + slot / 2
                icon.width = slot * 0.8
                icon.height = slot * 0.8
                temp_list = arcade.SpriteList()
                temp_list.append(icon)
                temp_list.draw()

                arcade.draw_text(
                    str(quantity),
                    sx + slot - 10,
                    sy + 5,
                    arcade.color.WHITE,
                    14,
                    anchor_x="right",
                )

                col += 1
                if col >= 4:
                    col = 0
                    row += 1

    # ============================================================
    #                          UPDATE
    # ============================================================

    def on_update(self, delta_time: float):
        if self.in_dialogue:
            return

        if self.inventory_open:
            return

        self.player.remember_position()

        # Reset
        self.player.change_x = 0
        self.player.change_y = 0

        speed = self.player_speed

        # Contrôles
        if arcade.key.UP in self.pressed_keys or arcade.key.Z in self.pressed_keys:
            self.player.change_y += speed
        if arcade.key.DOWN in self.pressed_keys or arcade.key.S in self.pressed_keys:
            self.player.change_y -= speed
        if arcade.key.LEFT in self.pressed_keys or arcade.key.Q in self.pressed_keys:
            self.player.change_x -= speed
        if arcade.key.RIGHT in self.pressed_keys or arcade.key.D in self.pressed_keys:
            self.player.change_x += speed

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

        # ----------------- Détection PNJ -----------------
        self.npc_to_talk = None
        npc_zones = self.map_manager.npc_interactions

        if npc_zones:
            detected = arcade.check_for_collision_with_list(self.player, npc_zones)
            if detected:
                zone = detected[0]
                self.npc_to_talk = zone.npc_ref

        # Position de la bulle PNJ
        if self.npc_to_talk and not self.in_dialogue:
            cam_x, cam_y = self.camera.position
            win_w, win_h = self.get_size()
            screen_x = self.player.center_x - cam_x + win_w / 2
            screen_y = self.player.center_y - cam_y + win_h / 2 + 50
            self.bubble_sprite.center_x = screen_x
            self.bubble_sprite.center_y = screen_y

        # ----------------- Bulle transition -----------------
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

        # ----------------- Animation du fade -----------------
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

        # ----------------- Détection d’un objet ramassable -----------------
        hits = arcade.check_for_collision_with_list(self.player, self.map_manager.items)

        if hits:
            nearest = hits[0]

            cam_x, cam_y = self.camera.position
            win_w, win_h = self.get_size()
            screen_x = self.player.center_x - cam_x + win_w / 2
            screen_y = self.player.center_y - cam_y + win_h / 2 + 50

            self.bubble_sprite.center_x = screen_x
            self.bubble_sprite.center_y = screen_y

            self.item_to_pick = nearest
        else:
            self.item_to_pick = None

    # ============================================================
    #                          CAMERA
    # ============================================================

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

    # ============================================================
    #                    TRANSITIONS DE MAP
    # ============================================================

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

    # ============================================================
    #                      DIALOGUES
    # ============================================================

    def start_npc_dialog(self, npc):
        """Démarre une discussion avec un PNJ."""
        self.in_dialogue = True
        self.current_npc = npc
        self.dialog_scroll = 0

        # Déterminer le dossier du PNJ (ex: npc/maire/)
        npc_folder = f"npc/{npc.npc_name}"

        # Création de l'agent IA (NOUVEAU : il ne prend qu'un argument)
        self.npc_agent = NPC_Agent(npc_folder)

        # Inventaire sous forme de liste
        inventory_items = list(self.inventory.keys())

        # Choix automatique first_meeting / returning dans NPC_Agent
        first_message = self.npc_agent.start_dialog(inventory_items)

        # Affichage dans la boîte de dialogue
        display_name = npc.npc_name.capitalize()
        self.dialog_history = [(display_name, first_message)]
        self.dialog_input = ""


    def send_player_dialog(self):
        """Traitement du message joueur + réponse IA."""
        msg = self.dialog_input.strip()
        if not msg:
            return

        # Ajout dans l'affichage
        self.dialog_history.append(("Vous", msg))

        # Réponse de l'IA
        npc_response = self.npc_agent.ask(
            player_message=msg,
            inventory_list=list(self.inventory.keys()),
        )

        display_name = self.current_npc.npc_name.capitalize()
        self.dialog_history.append((display_name, npc_response))

        # Scroll au bas et reset input
        self.dialog_scroll = 0
        self.dialog_input = ""


    # ============================================================
    #                          INPUT
    # ============================================================

    def on_key_press(self, key, modifiers):
        # ESC
        if key == arcade.key.ESCAPE:
            if self.in_dialogue:
                self.in_dialogue = False
                return
            arcade.exit()
            return

        # Ouvrir / fermer inventaire
        if key == arcade.key.I and not self.in_dialogue:
            self.inventory_open = not self.inventory_open
            return

        # Démarrer dialogue avec PNJ
        if key == arcade.key.E:
            if self.npc_to_talk and not self.in_dialogue:
                self.start_npc_dialog(self.npc_to_talk)

        self.pressed_keys.add(key)

        # Saisie texte du dialogue
        if self.in_dialogue:
            if key == arcade.key.BACKSPACE:
                self.dialog_input = self.dialog_input[:-1]
            elif key == arcade.key.ENTER:
                self.send_player_dialog()
            return

        # Ramasser un item
        if key == arcade.key.E:
            if self.item_to_pick:
                item = self.item_to_pick
                self.inventory[item.item_id] = self.inventory.get(item.item_id, 0) + 1
                item.remove_from_sprite_lists()
                print(f"Ramassé : {item.item_id} → inventaire : {self.inventory}")
                return

    def on_text(self, text):
        if self.in_dialogue:
            self.dialog_input += text

    def on_key_release(self, key, modifiers):
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Scroll dans la boîte de dialogue avec la molette."""
        if not self.in_dialogue:
            return

        # Recalcule le total de lignes wrap
        win_w, win_h = self.get_size()
        box_width = win_w - 100
        total_lines = count_wrapped_lines(self.dialog_history, box_width - 40, font_size=18)

        history_height = int(win_h * 0.40) - 80
        line_height = 24
        max_visible_lines = max(1, history_height // line_height)
        max_scroll = max(0, total_lines - max_visible_lines)

        # scroll_y > 0 = roue vers le haut
        if scroll_y > 0:
            self.dialog_scroll = min(self.dialog_scroll + 1, max_scroll)
        else:
            self.dialog_scroll = max(self.dialog_scroll - 1, 0)

def reset_all_memories():
    base = "npc"
    if not os.path.exists(base):
        return
    for folder in os.listdir(base):
        memory_path = os.path.join(base, folder, "memory.json")
        if os.path.isfile(memory_path):
            with open(memory_path, "w", encoding="utf-8") as f:
                json.dump([], f)

# ============================================================
#                           MAIN
# ============================================================

def main():
    reset_all_memories()
    game = Game()
    game.setup()
    arcade.enable_timings()
    arcade.run()


if __name__ == "__main__":
    main()
