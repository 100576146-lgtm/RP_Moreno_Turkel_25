import pygame
from enum import Enum

# Initialize pygame subsystems needed by fonts/colors
pygame.init()

# Screen - Support for variable screen sizes
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Fullscreen support
FULLSCREEN_WIDTH = 1920
FULLSCREEN_HEIGHT = 1080

# Colors (Pastel Scheme)
WHITE = (255, 255, 255)
BLACK = (50, 50, 50)
CREAM = (255, 253, 240)
SOFT_BLUE = (173, 216, 230)
SKY_BLUE = (135, 206, 235)
LAVENDER = (230, 230, 250)
SOFT_PURPLE = (221, 160, 221)
LIGHT_PURPLE = (238, 203, 238)
PASTEL_GREEN = (152, 251, 152)
SAGE_GREEN = (159, 197, 159)
MINT_GREEN = (189, 252, 201)
SOFT_YELLOW = (255, 255, 224)
PEACH = (255, 218, 185)
CORAL = (255, 183, 178)
SOFT_PINK = (255, 182, 193)
DUSTY_ROSE = (188, 143, 143)
BEIGE = (245, 245, 220)
LIGHT_BROWN = (205, 183, 158)
MOUNTAIN_PURPLE = (176, 196, 222)
MOUNTAIN_BLUE = (119, 136, 153)

# --- New Theme Color Constants ---
# (Add these to your constants.py file)

# The Big Melt-down
CHEESE_YELLOW = (255, 215, 0)
MELTED_CHEESE = (255, 200, 80)  # Slightly different cheese color for level 1

# Moss-t Be Joking
MOSS_GREEN = (138, 154, 91)

# Smelted Dreams
SLATE_GREY = (112, 128, 144)
DARK_GREY = (45, 45, 45)
SILVER = (192, 192, 192)
MOLTEN_ORANGE = (253, 108, 2)
STEEL_BLUE = (70, 130, 180)

# Frost and Furious
CYAN = (0, 255, 255)

# Boo Who?
DARK_PURPLE = (48, 25, 52)

# 404: Floor Not Found
GLITCH_GREEN = (0, 255, 127)
MAGENTA = (255, 0, 255)

# Pasta La Vista
TOMATO_RED = (255, 99, 71)
BASIL_GREEN = (85, 107, 47)

# Concrete Jungle
CONCRETE_GREY = (149, 149, 149)
RUST_ORANGE = (183, 65, 14)

# Kraken Me Up
DEEP_BLUE = (0, 0, 139)
DARK_BLUE = (0, 0, 128)
TEAL = (0, 128, 128)
SEAWEED_GREEN = (47, 79, 79)
INK_BLACK = (25, 25, 25)

# --- New Color Constants for Themed Levels ---
# (Add these to your constants.py file)

# The Big Melt-down
HAZY_ORANGE = (238, 196, 128)
MOLTEN_RED = (200, 50, 10)
FONDUE_YELLOW = (255, 215, 0)
BURNT_ORANGE = (204, 85, 0)
SOOT_GREY = (58, 58, 58)

# Moss-t Be Joking
MISTY_GREY = (185, 195, 199)
FOREST_FLOOR_GREEN = (77, 98, 62)
MOSS_GREEN = (138, 154, 91)
WET_ROCK_GREY = (115, 128, 126)
DARK_BROWN = (101, 67, 33)

# Smelted Dreams
SMOKE_GREY = (112, 112, 112)
FORGE_GLOW = (255, 153, 0)
STEEL_GREY = (150, 150, 150)
MOLTEN_ORANGE = (253, 108, 2)
ELECTRIC_BLUE = (125, 249, 255)

# Frost and Furious
GLACIER_WHITE = (230, 245, 255)
FROST_BLUE = (143, 204, 251)
ICE_BLUE = (157, 222, 237)
SNOW_WHITE = (250, 250, 250)
WARNING_RED = (255, 30, 30)

# Boo Who?
MIDNIGHT_PURPLE = (40, 26, 56)
ECTOPLASM_GREEN = (152, 251, 152)
GHOSTLY_WHITE = (230, 230, 250)
SHADOW_GREY = (70, 70, 80)

# 404: Floor Not Found
GLITCH_GREEN = (0, 255, 127)
ERROR_RED = (255, 0, 85)
STATIC_WHITE = (220, 220, 220)

# Pasta La Vista
PARMESAN_YELLOW = (248, 240, 202)
MARINARA_RED = (190, 48, 28)
TOMATO_RED = (255, 99, 71)
BASIL_GREEN = (85, 107, 47)
MOZZARELLA_WHITE = (252, 250, 242)

# Concrete Jungle
CITY_SMOG_GREY = (163, 168, 171)
OVERGROWTH_GREEN = (105, 134, 111)
RUST_ORANGE = (183, 65, 14)
CONCRETE_GREY = (149, 149, 149)
IVY_GREEN = (86, 130, 89)

# Kraken Me Up
MURKY_TEAL = (55, 92, 98)
ABYSSAL_BLACK = (12, 15, 23)
DEEP_SEA_BLUE = (0, 82, 112)
BIOLUMINESCENT_GREEN = (60, 255, 150)
INK_BLACK = (25, 25, 25)

# Physics
GRAVITY = 0.8
JUMP_STRENGTH = -15  # Increased by 5% (was -15)
PLAYER_SPEED = 5

# Calculate maximum jump height
# Jump height = (JUMP_STRENGTH^2) / (2 * GRAVITY)
MAX_JUMP_HEIGHT = int((JUMP_STRENGTH * JUMP_STRENGTH) / (2 * GRAVITY))
# Add some buffer for safety
SAFE_JUMP_HEIGHT = MAX_JUMP_HEIGHT + 20
ENEMY_SPEED = 1.6

# Level dimensions (mutable; set per-level)
LEVEL_WIDTH = 6400  # Doubled the level width
LEVEL_HEIGHT = 600  # Match screen height for full visibility

class GameState(Enum):
    LOADING = 0
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    PAUSED = 4
    LEVEL_COMPLETE = 5
    LEVEL_SELECT = 6
    BONUS_ROOM = 7

def set_level_dimensions(width: int, height: int) -> None:
    global LEVEL_WIDTH, LEVEL_HEIGHT
    LEVEL_WIDTH = width
    LEVEL_HEIGHT = height


