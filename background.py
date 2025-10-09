import pygame
import random
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

        # Draw bg motif overlay by theme
        motif = self.theme.get('bg_motif')
        if motif == 'stars':
            # Night - little white stars
            for _ in range(38):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, int(SCREEN_HEIGHT*0.7))
                pygame.draw.circle(screen, (255,255,255), (x,y), random.randint(1,3))
        elif motif == 'bubbles':
            # Underwater
            for _ in range(14):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(20, SCREEN_HEIGHT-80)
                pygame.draw.circle(screen, (220,255,255), (x,y), random.randint(6,15), 2)
        elif motif == 'rainbow':
            # Sky - rainbow arc at top
            for i,c in enumerate([(255,140,200),(255,255,0),(120,200,255),(180,255,180)]):
                pygame.draw.arc(screen,c,(120,24,560,180),0,3.14, 8-i*2)
        elif motif == 'flowers':
            # Meadow
            for _ in range(24):
                x = random.randint(24,SCREEN_WIDTH-24)
                y = SCREEN_HEIGHT-50-random.randint(0,20)
                pygame.draw.circle(screen,(255,200,240),(x,y),3); pygame.draw.circle(screen,(255,255,128),(x,y),1)
        elif motif == 'ice_shards':
            for _ in range(14):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(SCREEN_HEIGHT//2, SCREEN_HEIGHT)
                pygame.draw.polygon(screen, (190,240,255), [(x,y),(x+7,y-20),(x+14,y)])
        elif motif == 'embers':
            # Fire world
            for _ in range(16):
                x = random.randint(0, SCREEN_WIDTH-5)
                y = random.randint(10, SCREEN_HEIGHT)
                c = random.choice([(255,160,80),(255,220,120),(180,90,0)])
                pygame.draw.circle(screen, c, (x,y), 3)
        elif motif == 'ash':
            # Volcano
            for _ in range(18):
                x = random.randint(0,SCREEN_WIDTH-7)
                y = random.randint(10, SCREEN_HEIGHT-6)
                pygame.draw.circle(screen,(90,90,90),(x,y),2)
        elif motif == 'sand':
            # Desert
            for _ in range(16):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(SCREEN_HEIGHT//2,SCREEN_HEIGHT-4)
                pygame.draw.ellipse(screen, (245, 224, 119), (x,y,13,5))
        elif motif == 'glow':
            # Neon
            for _ in range(12):
                c = random.choice([(255,80,220),(100,255,220),(255,250,150),(90,250,250)])
                x,y = random.randint(22,SCREEN_WIDTH-22), random.randint(24,SCREEN_HEIGHT-24)
                pygame.draw.circle(screen, c, (x,y), 10, 0)
        elif motif == 'vines':
            # Forest
            for _ in range(5):
                x = random.randint(80,SCREEN_WIDTH-80)
                y0 = 0
                width = random.randint(4,8)
                for seg in range(38):
                    col = (90,150,100)
                    pygame.draw.line(screen, col, (x,y0), (x+random.randint(-6,6),y0+18), width)
                    x += random.randint(-6,7); y0+=18


