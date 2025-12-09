import arcade
import pyglet.gl as gl
from arcade import AnimatedWalkingSprite

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "RPG Medieval - Camera Fix"

PLAYER_SPEED = 4
TILE_SCALING = 1.0

DEBUG_COLLISION = False


class Game(arcade.Window):
    def __init__(self):
        super().__init__(fullscreen=True, title=SCREEN_TITLE)

        # Caméras
        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()


        self.scene = None
        self.player_sprite = None
        self.pressed_keys = set()
        self.walls = None


    def setup(self):
        # --- Charger la map ---
        self.tile_map = arcade.load_tilemap(
            "data/maps/village.tmx",
            scaling=TILE_SCALING
        )

        self.scene = arcade.Scene.from_tilemap(self.tile_map)


        # --- COLLISIONS DEPUIS TILED ---
        self.walls = arcade.SpriteList()

        if "Collision" in self.tile_map.object_lists:
            for obj in self.tile_map.object_lists["Collision"]:
                shape = obj.shape

                # Cas polygon (liste de points)
                if isinstance(shape, list):
                    xs = [p[0] for p in shape]
                    ys = [p[1] for p in shape]

                    x_min = min(xs)
                    x_max = max(xs)
                    y_min = min(ys)
                    y_max = max(ys)

                    w = x_max - x_min
                    h = y_max - y_min

                    # Rectangle rouge semi-transparent pour debug
                    wall = arcade.SpriteSolidColor(int(w), int(h), (255, 255, 255, 0))

                    wall.center_x = x_min + w / 2
                    wall.center_y = y_min + h / 2

                    self.walls.append(wall)


        # --- Création du joueur animé ---
        self.player_sprite = arcade.AnimatedWalkingSprite(scale=1.0)

        # FRONT
        self.player_sprite.stand_down_textures = [arcade.load_texture("assets/sprites/player/player_front_0.png")]
        self.player_sprite.walk_down_textures = [
            arcade.load_texture(f"assets/sprites/player/player_front_{i}.png") for i in range(4)
        ]

        # BACK
        self.player_sprite.stand_up_textures = [arcade.load_texture("assets/sprites/player/player_back_0.png")]
        self.player_sprite.walk_up_textures = [
            arcade.load_texture(f"assets/sprites/player/player_back_{i}.png") for i in range(4)
        ]

        # LEFT
        self.player_sprite.stand_left_textures = [arcade.load_texture("assets/sprites/player/player_left_0.png")]
        self.player_sprite.walk_left_textures = [
            arcade.load_texture(f"assets/sprites/player/player_left_{i}.png") for i in range(4)
        ]

        # RIGHT
        self.player_sprite.stand_right_textures = [arcade.load_texture("assets/sprites/player/player_right_0.png")]
        self.player_sprite.walk_right_textures = [
            arcade.load_texture(f"assets/sprites/player/player_right_{i}.png") for i in range(4)
        ]



        # --- Lire point de spawn --- #
        spawn_layer = self.tile_map.object_lists.get("Spawn", [])

        for obj in spawn_layer:
            if obj.name == "spawn_player":
                try:
                    # Tiled stocke souvent la position dans shape[0], shape[1]
                    x, y = obj.shape  
                except:
                    # Compatibilité alternative
                    x = obj.properties.get("x", 0)
                    y = obj.properties.get("y", 0)

                self.player_sprite.center_x = x
                self.player_sprite.center_y = y
        
        if "Player" not in self.scene._sprite_lists:
            self.scene.add_sprite_list("Player")

        self.scene.add_sprite("Player", self.player_sprite)


        # --- CHARGER LES PNJ DE TILED ---
        self.npc_list = arcade.SpriteList()

        if "NPCs" in self.tile_map.object_lists:
            npc_objects = self.tile_map.object_lists["NPCs"]

            for npc in npc_objects:
                npc_name = npc.name

                # Choisir sprite
                if "maire" in npc_name:
                    texture = "assets/npcs/maire.png"
                elif "comptesse" in npc_name or "comtesse" in npc_name:
                    texture = "assets/npcs/comtesse.png"
                elif "hotelier" in npc_name:
                    texture = "assets/npcs/hotelier.png"
                elif "serveur" in npc_name:
                    texture = "assets/npcs/serveur.png"
                else:
                    continue

                sprite = arcade.Sprite(texture, scale=0.10)

                # --- LA BONNE LIGNE POUR TA VERSION ---
                x, y = npc.shape

                sprite.center_x = x
                sprite.center_y = y

                self.npc_list.append(sprite)

            self.scene.add_sprite_list("NPCs", sprite_list=self.npc_list)


        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw()
        self.npc_list.draw()
        if DEBUG_COLLISION:
            self.walls.draw()
        self.gui_camera.use()


    def on_update(self, dt):
        # Sauvegarder l'ancienne position
        self.player_sprite.previous_x = self.player_sprite.center_x
        self.player_sprite.previous_y = self.player_sprite.center_y

        # Reset mouvement
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

        if arcade.key.UP in self.pressed_keys:
            self.player_sprite.change_y = PLAYER_SPEED
        if arcade.key.DOWN in self.pressed_keys:
            self.player_sprite.change_y = -PLAYER_SPEED
        if arcade.key.LEFT in self.pressed_keys:
            self.player_sprite.change_x = -PLAYER_SPEED
        if arcade.key.RIGHT in self.pressed_keys:
            self.player_sprite.change_x = PLAYER_SPEED

        # Appliquer le mouvement
        self.player_sprite.update()
        self.player_sprite.update_animation(dt)


        # --- COLLISIONS MURS ---
        if arcade.check_for_collision_with_list(self.player_sprite, self.walls):
            self.player_sprite.center_x = self.player_sprite.previous_x
            self.player_sprite.center_y = self.player_sprite.previous_y


        self.update_camera()


    def update_camera(self):

        # Taille du monde
        world_w = self.tile_map.width * self.tile_map.tile_width
        world_h = self.tile_map.height * self.tile_map.tile_height

        # Récupérer la taille réelle de la fenêtre
        screen_w, screen_h = self.get_size()

        # Position visée
        target_x = self.player_sprite.center_x
        target_y = self.player_sprite.center_y

        # Limites caméra
        min_x = screen_w / 2
        max_x = world_w - screen_w / 2

        min_y = screen_h / 2
        max_y = world_h - screen_h / 2

        # Clamp
        cam_x = min(max(target_x, min_x), max_x)
        cam_y = min(max(target_y, min_y), max_y)

        # Mise à jour position caméra
        self.camera.position = (cam_x, cam_y)



    def on_key_press(self, key, modifiers):
        # Quitter le jeu avec Échap
        if key == arcade.key.ESCAPE:
            arcade.exit()

        self.pressed_keys.add(key)


    def on_key_release(self, key, modifiers):
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)


if __name__ == "__main__":
    game = Game()
    game.setup()
    arcade.enable_timings()
    arcade.run()
