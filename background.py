import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


class Background:
    def __init__(self):
        self._bg_cache = None
        self._bg_blobs = []
        self.theme = {"sky_top": (230, 230, 250), "sky_bottom": (135, 206, 235)}

    def set_theme(self, theme):
        self.theme = theme
        self._bg_cache = None

    def _ensure_background_cache(self, current_level_index: int):
        if self._bg_cache is None:
            self._bg_cache = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            top = self.theme["sky_top"]
            bottom = self.theme["sky_bottom"]
            for y in range(SCREEN_HEIGHT):
                t = y / (SCREEN_HEIGHT - 1)
                r = int(top[0] * (1 - t) + bottom[0] * t)
                g = int(top[1] * (1 - t) + bottom[1] * t)
                b = int(top[2] * (1 - t) + bottom[2] * t)
                pygame.draw.line(self._bg_cache, (r, g, b), (0, y), (SCREEN_WIDTH, y))
            # blobs
            import random
            self._bg_blobs = []
            rng = random.Random(101 + current_level_index)
            for _ in range(5):
                blob = {
                    "x": rng.randint(-100, SCREEN_WIDTH + 100),
                    "y": rng.randint(40, SCREEN_HEIGHT - 120),
                    "r": rng.randint(40, 90),
                    "vx": rng.choice([-0.1, 0.08, 0.12, -0.08]),
                    "color": (
                        int((top[0] + bottom[0]) / 2),
                        int((top[1] + bottom[1]) / 2),
                        int((top[2] + bottom[2]) / 2),
                    ),
                }
                self._bg_blobs.append(blob)

    def draw(self, screen: pygame.Surface, current_level_index: int):
        self._ensure_background_cache(current_level_index)
        screen.blit(self._bg_cache, (0, 0))
        blob_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for blob in self._bg_blobs:
            pygame.draw.circle(blob_surface, (*blob["color"], 50), (int(blob["x"]), int(blob["y"])), blob["r"])
            blob["x"] += blob["vx"]
            if blob["x"] < -120:
                blob["x"] = SCREEN_WIDTH + 100
            elif blob["x"] > SCREEN_WIDTH + 120:
                blob["x"] = -100
        screen.blit(blob_surface, (0, 0))


