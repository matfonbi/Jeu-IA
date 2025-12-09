import arcade


PLAYER_SPEED = 4  # juste pour référence, pas utilisé ici directement


class Player(arcade.AnimatedWalkingSprite):
    """
    Joueur animé 4 directions.

    Fichiers attendus :
      assets/sprites/player/player_front_0.png .. player_front_3.png
      assets/sprites/player/player_back_0.png  .. player_back_3.png
      assets/sprites/player/player_left_0.png  .. player_left_3.png
      assets/sprites/player/player_right_0.png .. player_right_3.png
    """

    def __init__(self, scale: float = 1.0) -> None:
        super().__init__(scale=scale)

        # --- FRONT (vers le bas) ---
        self.stand_down_textures = [
            arcade.load_texture("assets/sprites/player/player_front_0.png")
        ]
        self.walk_down_textures = [
            arcade.load_texture(f"assets/sprites/player/player_front_{i}.png")
            for i in range(4)
        ]

        # --- BACK (vers le haut) ---
        self.stand_up_textures = [
            arcade.load_texture("assets/sprites/player/player_back_0.png")
        ]
        self.walk_up_textures = [
            arcade.load_texture(f"assets/sprites/player/player_back_{i}.png")
            for i in range(4)
        ]

        # --- LEFT ---
        self.stand_left_textures = [
            arcade.load_texture("assets/sprites/player/player_left_0.png")
        ]
        self.walk_left_textures = [
            arcade.load_texture(f"assets/sprites/player/player_left_{i}.png")
            for i in range(4)
        ]

        # --- RIGHT ---
        self.stand_right_textures = [
            arcade.load_texture("assets/sprites/player/player_right_0.png")
        ]
        self.walk_right_textures = [
            arcade.load_texture(f"assets/sprites/player/player_right_{i}.png")
            for i in range(4)
        ]

        # Texture par défaut au démarrage
        self.texture = self.stand_down_textures[0]

        # Position précédente (pour rollback en cas de collision)
        self.previous_x = 0
        self.previous_y = 0

    def remember_position(self) -> None:
        """Mémorise la position actuelle (avant déplacement)."""
        self.previous_x = self.center_x
        self.previous_y = self.center_y
