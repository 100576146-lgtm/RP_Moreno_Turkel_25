from constants import SCREEN_WIDTH, SCREEN_HEIGHT, LEVEL_WIDTH, LEVEL_HEIGHT


class Camera:
    def __init__(self, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT):
        self.x = 0
        self.y = 0
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.level_width = LEVEL_WIDTH  # Store current level width
        self.level_height = LEVEL_HEIGHT  # Store current level height

    def update(self, target):
        # Horizontal camera
        self.x = target.rect.centerx - self.screen_width // 2
        if self.x < 0:
            self.x = 0
        if self.x > self.level_width - self.screen_width:
            self.x = self.level_width - self.screen_width
        
        # Vertical camera - keep bottom of screen at ground level
        # This ensures the world is always visible and not cut off at bottom
        self.y = self.level_height - self.screen_height
        if self.y < 0:
            self.y = 0
    
    def set_level_dimensions(self, width, height):
        """Update the level dimensions when level changes."""
        self.level_width = width
        self.level_height = height


