import arcade

class CameraSystem:
    def __init__(self, game):
        self.game = game

    def update(self):
        game = self.game
        if not game.map_manager.tile_map:
            return

        zoom = game.camera.zoom
        screen_w, screen_h = game.get_size()
        visible_w = screen_w / zoom
        visible_h = screen_h / zoom

        world_w = game.map_manager.tile_map.width * game.map_manager.tile_map.tile_width
        world_h = game.map_manager.tile_map.height * game.map_manager.tile_map.tile_height

        target_x = game.player.center_x
        target_y = game.player.center_y

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

        game.camera.position = (cam_x, cam_y)
