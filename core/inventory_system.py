import arcade

class InventorySystem:
    def __init__(self, game):
        self.game = game

    def detect_item_pick(self):
        g = self.game
        hits = arcade.check_for_collision_with_list(g.player, g.map_manager.items)

        if hits:
            nearest = hits[0]

            cam_x, cam_y = g.camera.position
            win_w, win_h = g.get_size()

            g.bubble_sprite.center_x = g.player.center_x - cam_x + win_w / 2
            g.bubble_sprite.center_y = g.player.center_y - cam_y + win_h / 2 + 50

            g.item_to_pick = nearest
        else:
            g.item_to_pick = None

    def pick_item(self):
        g = self.game
        if g.item_to_pick:
            item = g.item_to_pick
            g.inventory[item.item_id] = g.inventory.get(item.item_id, 0) + 1
            item.remove_from_sprite_lists()
            print(f"Ramassé : {item.item_id} → inventaire : {g.inventory}")

    def update(self):
        self.detect_item_pick()
