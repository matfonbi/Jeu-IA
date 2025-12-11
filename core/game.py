import arcade
from managers.map_manager import MapManager
from managers.quest_manager import QuestManager
from managers.player import Player

from core.camera_system import CameraSystem
from core.dialog_system import DialogSystem
from core.inventory_system import InventorySystem
from core.transitions import TransitionSystem
from core.input_system import InputSystem
from core.ui_drawer import UIDrawer

SCREEN_TITLE = "RPG Medieval"
BASE_PLAYER_SPEED = 4
DEBUG_COLLISION = False

class Game(arcade.Window):
    def __init__(self):
        super().__init__(fullscreen=True, title=SCREEN_TITLE)

        arcade.set_background_color(arcade.color.BLACK)

        # Caméras
        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        # Modules
        self.camera_system = CameraSystem(self)
        self.dialog_system = DialogSystem(self)
        self.inventory_system = InventorySystem(self)
        self.transition_system = TransitionSystem(self)
        self.input_system = InputSystem(self)
        self.ui = UIDrawer(self)

        # Game state
        self.player = Player(scale=1.0)
        self.map_manager = MapManager(self)
        self.quest_manager = QuestManager()

        self.player_speed = BASE_PLAYER_SPEED
        self.inventory = {}
        self.item_to_pick = None
        self.inventory_open = False

        self.default_zoom = 1.0
        self.default_player_scale = 1.1

        self.pressed_keys = set()

        # Dialog
        self.in_dialogue = False
        self.dialog_history = []
        self.dialog_input = ""
        self.dialog_scroll = 0
        self.current_npc = None
        self.npc_to_talk = None

        # Bulle
        self.bubble_texture = arcade.make_soft_square_texture(
            64, color=(0, 0, 0, 180), outer_alpha=180
        )
        self.bubble_sprite = arcade.Sprite(self.bubble_texture)
        self.bubble_sprite.width = 160
        self.bubble_sprite.height = 40
        self.show_bubble = False

        # Transition fade
        self.transition_alpha = 0.0
        self.transition_target = 0.0
        self.transition_speed = 10.0
        self.transition_callback = None

    def setup(self):
        self.map_manager.load_map("village", "spawn_player", self.player)

    def on_draw(self):
        self.ui.draw()

    def on_update(self, dt):
        self.input_system.update_movement(dt)
        self.camera_system.update()
        self.inventory_system.update()
        self.dialog_system.update()
        self.transition_system.update_fade()

        if arcade.key.E in self.pressed_keys:
            self.transition_system.check_map_transition()

    # -- Inputs wrappers --
    def on_key_press(self, key, modifiers):
        self.input_system.on_key_press(key, modifiers)

    def on_key_release(self, key, modifiers):
        self.input_system.on_key_release(key, modifiers)

    def on_text(self, text):
        self.input_system.on_text(text)

    def on_mouse_scroll(self, x, y, sx, sy):
        self.input_system.on_mouse_scroll(x, y, sx, sy)
