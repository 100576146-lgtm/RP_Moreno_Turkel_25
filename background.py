import pygame
import os
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


class Background:
    def __init__(self, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.theme = {"name": ""}
        self._custom_bg_images = {}  # Cache for custom background images

    def set_theme(self, theme):
        self.theme = theme

    def _load_custom_background(self, level_name, is_bonus_room=False):
        """Load custom background image for specific level or bonus room."""
        # Map level names to background files
        bg_mapping = {
            "The Big Melt-down": "cheese.jpeg",
            "Moss-t Be Joking": "jungle.jpeg", 
            "Smelted Dreams": "lava.jpeg",
            "Frost and Furious": "ice.jpeg",
            "Boo Who?": "ghost.jpeg",
            "404: Floor Not Found": "space.jpeg",
            "Pasta La Vista": "pasta.jpeg",
            "Concrete Jungle": "city.jpeg",
            "Kraken Me Up": "underwater.jpeg",
            "Neon Night": "tetris.jpeg"
        }
        
        # Use unicorn background for bonus rooms
        if is_bonus_room:
            bg_file = "unicorn.jpeg"
            cache_key = "bonus_unicorn"
        else:
            if level_name in bg_mapping:
                bg_file = bg_mapping[level_name]
                cache_key = bg_file
            else:
                return None
        
        bg_path = os.path.join(os.path.dirname(__file__), bg_file)
        
        if cache_key in self._custom_bg_images:
            return self._custom_bg_images[cache_key]
        
        try:
            if os.path.exists(bg_path):
                # Load and scale the image to fit the screen with high quality
                bg_image = pygame.image.load(bg_path)
                # Use smoothscale for better quality
                bg_image = pygame.transform.smoothscale(bg_image, (self.screen_width, self.screen_height))
                self._custom_bg_images[cache_key] = bg_image
                return bg_image
        except pygame.error as e:
            print(f"Could not load background image {bg_file}: {e}")
        
        return None

    def draw(self, screen: pygame.Surface, current_level_index: int, is_bonus_room=False):
        # Always try to load custom background first
        level_name = self.theme.get("name", "")
        custom_bg = self._load_custom_background(level_name, is_bonus_room)
        
        if custom_bg is not None:
            # Use custom background image
            screen.blit(custom_bg, (0, 0))
        else:
            # If no custom background, use a simple fallback
            screen.fill((50, 50, 50))  # Simple dark gray fallback