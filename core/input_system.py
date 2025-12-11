import arcade

class InputSystem:
    def __init__(self, game):
        self.game = game

    def update_movement(self, dt):
        g = self.game

        if g.in_dialogue or g.inventory_open:
            return

        g.player.remember_position()
        g.player.change_x = 0
        g.player.change_y = 0

        speed = g.player_speed

        if arcade.key.UP in g.pressed_keys or arcade.key.Z in g.pressed_keys:
            g.player.change_y += speed
        if arcade.key.DOWN in g.pressed_keys or arcade.key.S in g.pressed_keys:
            g.player.change_y -= speed
        if arcade.key.LEFT in g.pressed_keys or arcade.key.Q in g.pressed_keys:
            g.player.change_x -= speed
        if arcade.key.RIGHT in g.pressed_keys or arcade.key.D in g.pressed_keys:
            g.player.change_x += speed

        g.player.update()
        g.player.update_animation(dt)

        if arcade.check_for_collision_with_list(g.player, g.map_manager.walls):
            g.player.center_x = g.player.previous_x
            g.player.center_y = g.player.previous_y

    def on_key_press(self, key, modifiers):
        g = self.game

        if key == arcade.key.ESCAPE:
            if g.in_dialogue:
                g.in_dialogue = False
                return
            arcade.exit()
            return

        if key == arcade.key.I and not g.in_dialogue:
            g.inventory_open = not g.inventory_open
            return

        if key == arcade.key.E:
            if g.npc_to_talk and not g.in_dialogue:
                g.dialog_system.start_dialog(g.npc_to_talk)
                return
            if g.item_to_pick:
                g.inventory_system.pick_item()
                return

        g.pressed_keys.add(key)

        if g.in_dialogue:
            if key == arcade.key.BACKSPACE:
                g.dialog_input = g.dialog_input[:-1]
            elif key == arcade.key.ENTER:
                g.dialog_system.send_player_message()

    def on_key_release(self, key, modifiers):
        g = self.game
        if key in g.pressed_keys:
            g.pressed_keys.remove(key)

    def on_text(self, text):
        g = self.game
        if g.in_dialogue:
            g.dialog_input += text

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        g = self.game
        if g.in_dialogue:
            g.dialog_system.scroll(scroll_y)
