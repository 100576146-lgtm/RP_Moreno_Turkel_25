import pygame
from enum import Enum

# Initialize pygame subsystems needed by fonts/colors
pygame.init()

# Screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

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

# Physics
GRAVITY = 0.8
JUMP_STRENGTH = -15
PLAYER_SPEED = 5
ENEMY_SPEED = 2

# Level dimensions (mutable; set per-level)
LEVEL_WIDTH = 3200
LEVEL_HEIGHT = 600

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    PAUSED = 4
    LEVEL_COMPLETE = 5
    LEVEL_SELECT = 6

def set_level_dimensions(width: int, height: int) -> None:
    global LEVEL_WIDTH, LEVEL_HEIGHT
    LEVEL_WIDTH = width
    LEVEL_HEIGHT = height


