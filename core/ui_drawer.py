import os
import arcade
from core.utils_text import wrap_dialog_history

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))  
ASSETS_DIR = os.path.join(ROOT_DIR, "assets", "objet")


class UIDrawer:
    def __init__(self, game):
        self.game = game

    def draw(self):
        g = self.game
        g.clear()

        # Monde
        self.draw_world()

        # Interface GUI
        g.gui_camera.use()

        self.draw_fade_overlay()
        self.draw_interaction_bubble()
        self.draw_pickup_text()
        self.draw_dialog_box()
        self.draw_inventory()

    # ---------------------------------------------------------
    #                        WORLD
    # ---------------------------------------------------------
    def draw_world(self):
        g = self.game

        g.camera.use()

        if g.map_manager.scene:
            g.map_manager.scene.draw()

        if g.map_manager.items:
            g.map_manager.items.draw()

        # debug walls & transitions
        from core.game import DEBUG_COLLISION
        if DEBUG_COLLISION:
            g.map_manager.walls.draw()
            g.map_manager.transitions.draw()

    # ---------------------------------------------------------
    #                    FADE TRANSITION
    # ---------------------------------------------------------
    def draw_fade_overlay(self):
        g = self.game
        if g.transition_alpha <= 0:
            return

        win_w, win_h = g.get_size()
        arcade.draw_lbwh_rectangle_filled(
            0, 0, win_w, win_h,
            (0, 0, 0, int(g.transition_alpha))
        )

    # ---------------------------------------------------------
    #                INTERACTION BUBBLE (E)
    # ---------------------------------------------------------
    def draw_interaction_bubble(self):
        g = self.game

        if g.in_dialogue:
            return

        # Transition bubble
        if g.show_bubble:
            g.bubble_list.draw()
            arcade.draw_text(
                "Appuyez sur E",
                g.bubble_sprite.center_x,
                g.bubble_sprite.center_y - 7,
                arcade.color.WHITE, 18,
                anchor_x="center"
            )

        # NPC bubble
        if g.npc_to_talk:
            arcade.draw_text(
                "Parler (E)",
                g.bubble_sprite.center_x,
                g.bubble_sprite.center_y - 40,
                arcade.color.WHITE, 18,
                anchor_x="center"
            )

    # ---------------------------------------------------------
    #                PICK UP ITEM (E)
    # ---------------------------------------------------------
    def draw_pickup_text(self):
        g = self.game
        if g.item_to_pick and not g.in_dialogue:
            arcade.draw_text(
                f"Ramasser {g.item_to_pick.item_id} (E)",
                g.bubble_sprite.center_x,
                g.bubble_sprite.center_y - 40,
                arcade.color.WHITE, 18,
                anchor_x="center"
            )

    # ---------------------------------------------------------
    #                       DIALOG BOX
    # ---------------------------------------------------------
    def draw_dialog_box(self):
        g = self.game
        if not g.in_dialogue:
            return

        win_w, win_h = g.get_size()
        box_margin = 50
        box_width = win_w - box_margin * 2
        box_height = int(win_h * 0.40)
        box_x = box_margin
        box_y = box_margin

        # Background
        arcade.draw_lbwh_rectangle_filled(
            box_x, box_y, box_width, box_height,
            (0, 0, 0, 200)
        )

        # --------- Input Zone ----------
        input_height = 45
        input_box_x = box_x + 15
        input_box_y = box_y + 10
        input_box_w = box_width - 30

        arcade.draw_lbwh_rectangle_outline(
            input_box_x, input_box_y, input_box_w, input_height,
            arcade.color.WHITE, 2
        )

        # User typing text
        arcade.draw_text(
            g.dialog_input,
            input_box_x + 10,
            input_box_y + 12,
            arcade.color.WHITE, 18
        )

        # --------- History Zone ----------
        history_top = box_y + box_height - 20
        history_bottom = input_box_y + input_height + 15

        available_height = history_top - history_bottom
        line_height = 24
        max_lines_on_screen = max(1, available_height // line_height)

        wrapped_lines = wrap_dialog_history(g.dialog_history, box_width - 40, font_size=18)
        total_lines = len(wrapped_lines)

        if total_lines > 0:
            max_scroll = max(0, total_lines - max_lines_on_screen)
            g.dialog_scroll = min(g.dialog_scroll, max_scroll)

            start = max(0, total_lines - max_lines_on_screen - g.dialog_scroll)
            end = start + max_lines_on_screen
            display_lines = wrapped_lines[start:end]
        else:
            display_lines = []

        y = history_top
        for line in display_lines:
            arcade.draw_text(line, box_x + 20, y, arcade.color.WHITE, 18)
            y -= line_height

    # ---------------------------------------------------------
    #                       INVENTORY
    # ---------------------------------------------------------
    def draw_inventory(self):
        g = self.game
        if not g.inventory_open:
            return

        win_w, win_h = g.get_size()
        width, height = 600, 400
        x = (win_w - width) / 2
        y = (win_h - height) / 2

        # Background
        arcade.draw_lbwh_rectangle_filled(
            x, y, width, height,
            (20, 20, 20, 230)
        )

        arcade.draw_lbwh_rectangle_outline(
            x, y, width, height,
            arcade.color.WHITE, 3
        )

        arcade.draw_text(
            "Inventaire",
            x + width / 2,
            y + height - 40,
            arcade.color.WHITE,
            28,
            anchor_x="center"
        )

        # Slots
        slot = g.inventory_slot_size
        pad = g.inventory_padding

        row = 0
        col = 0

        for item_name, quantity in g.inventory.items():
            sx = x + 40 + col * (slot + pad)
            sy = y + height - 120 - row * (slot + pad)

            arcade.draw_lbwh_rectangle_filled(sx, sy, slot, slot, (60,60,60,200))
            arcade.draw_lbwh_rectangle_outline(sx, sy, slot, slot, arcade.color.WHITE, 2)

            texture_path = os.path.join(ASSETS_DIR, f"{item_name}.png")
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
                anchor_x="right"
            )

            col += 1
            if col >= 4:
                col = 0
                row += 1
