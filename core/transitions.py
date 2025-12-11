import arcade

class TransitionSystem:
    def __init__(self, game):
        self.game = game

    def start_transition(self, callback):
        g = self.game
        if g.transition_target != 0 or g.transition_alpha != 0:
            return
        g.transition_target = 255.0
        g.transition_callback = callback

    def update_fade(self):
        g = self.game

        if g.transition_alpha != g.transition_target:
            if g.transition_alpha < g.transition_target:
                g.transition_alpha += g.transition_speed

                if g.transition_alpha >= g.transition_target:
                    g.transition_alpha = g.transition_target

                    if g.transition_alpha >= 255 and g.transition_callback:
                        g.transition_callback()
                        g.transition_callback = None
                        g.transition_target = 0

            else:
                g.transition_alpha -= g.transition_speed
                if g.transition_alpha <= g.transition_target:
                    g.transition_alpha = g.transition_target

    def update(self):
        """Handle transition bubble detection + positioning."""
        g = self.game

        hits = arcade.check_for_collision_with_list(g.player, g.map_manager.transitions)

        if hits and not g.in_dialogue:
            # Position bulle de transition
            cam_x, cam_y = g.camera.position
            win_w, win_h = g.get_size()

            g.bubble_sprite.center_x = g.player.center_x - cam_x + win_w / 2
            g.bubble_sprite.center_y = g.player.center_y - cam_y + win_h / 2 + 50

            g.show_bubble = True
        else:
            g.show_bubble = False


    def check_map_transition(self):
        g = self.game

        hits = arcade.check_for_collision_with_list(
            g.player, g.map_manager.transitions
        )

        if not hits or g.in_dialogue:
            return

        if g.transition_target != 0 or g.transition_alpha != 0:
            return

        trigger = hits[0]
        target_map = getattr(trigger, "target_map", None)
        target_spawn = getattr(trigger, "target_spawn", None)

        if not target_map or not target_spawn:
            return

        def do_change():
            g.map_manager.load_map(target_map, target_spawn, g.player)
            g.apply_map_settings(target_map)

        self.start_transition(do_change)
