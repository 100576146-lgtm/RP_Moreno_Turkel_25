import pygame
import random
import math
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


class Background:
    def __init__(self, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self._bg_cache = None
        self._bg_blobs = []
        self.theme = {"sky_top": (230, 230, 250), "sky_bottom": (135, 206, 235)}

    def set_theme(self, theme):
        self.theme = theme
        self._bg_cache = None

    def _ensure_background_cache(self, current_level_index: int):
        if self._bg_cache is None:
            self._bg_cache = pygame.Surface((self.screen_width, self.screen_height))
            top = self.theme["sky_top"]
            bottom = self.theme["sky_bottom"]
            for y in range(self.screen_height):
                t = y / (self.screen_height - 1)
                r = int(top[0] * (1 - t) + bottom[0] * t)
                g = int(top[1] * (1 - t) + bottom[1] * t)
                b = int(top[2] * (1 - t) + bottom[2] * t)
                pygame.draw.line(self._bg_cache, (r, g, b), (0, y), (self.screen_width, y))
            # blobs
            self._bg_blobs = []
            rng = random.Random(101 + current_level_index)
            for _ in range(5):
                blob = {
                    "x": rng.randint(-100, self.screen_width + 100),
                    "y": rng.randint(40, self.screen_height - 120),
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
        blob_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        for blob in self._bg_blobs:
            pygame.draw.circle(blob_surface, (*blob["color"], 50), (int(blob["x"]), int(blob["y"])), blob["r"])
            blob["x"] += blob["vx"]
            if blob["x"] < -120:
                blob["x"] = self.screen_width + 100
            elif blob["x"] > self.screen_width + 120:
                blob["x"] = -100
        screen.blit(blob_surface, (0, 0))

        # Draw bg motif overlay by theme
        motif = self.theme.get('bg_motif')
        if motif == 'swiss_cheese':
            # Swiss cheese: uniform cheese color with lots of holes
            rng = random.Random(8888)
            cheese_yellow = (248, 240, 202)
            darker = (230, 210, 175)
            # Base fill
            screen.fill(cheese_yellow)
            # Many holes of varying sizes
            for _ in range(60):
                r = rng.randint(8, 32)
                x = rng.randint(r + 4, self.screen_width - r - 4)
                y = rng.randint(r + 4, self.screen_height - r - 4)
                pygame.draw.circle(screen, darker, (x, y), r)
                # inner shading offset to suggest depth
                pygame.draw.circle(screen, (205, 190, 155), (x + r//5, y + r//5), max(3, r//2))
            return
        if motif == 'jungle':
            # Dense jungle: overlapping big leaves and vines
            rng = random.Random(2468)
            # Large semi-transparent leaves
            for _ in range(18):
                w = rng.randint(80, 160)
                h = rng.randint(40, 90)
                x = rng.randint(-30, self.screen_width - 50)
                y = rng.randint(0, self.screen_height - 60)
                leaf = pygame.Surface((w, h), pygame.SRCALPHA)
                col = rng.choice([(60, 120, 70, 180), (50, 100, 60, 180), (80, 140, 90, 160)])
                pygame.draw.ellipse(leaf, col, (0, 0, w, h))
                pygame.draw.ellipse(leaf, (30, 70, 40, 200), (0, 0, w, h), 3)
                screen.blit(leaf, (x, y))
            # Hanging vines
            for _ in range(8):
                x = rng.randint(40, self.screen_width - 40)
                y = 0
                segments = rng.randint(10, 18)
                px, py = x, y
                for s in range(segments):
                    nx = px + rng.randint(-8, 8)
                    ny = py + rng.randint(14, 22)
                    pygame.draw.line(screen, (40, 100, 50), (px, py), (nx, ny), 6)
                    pygame.draw.line(screen, (20, 60, 30), (px, py), (nx, ny), 2)
                    px, py = nx, ny
            return
        if motif == 'cracking_lava':
            # Cracking lava background: dark base with bright cracks
            screen.fill((30, 20, 20))
            rng = random.Random(97531)
            # Draw random crack veins
            for _ in range(100):
                x = rng.randint(0, self.screen_width)
                y = rng.randint(0, self.screen_height)
                length = rng.randint(40, 140)
                angle = rng.uniform(0, 3.14)
                dx = int(length * 0.8 * math.cos(angle)) if 'math' in globals() else 0
                dy = int(length * 0.8 * math.sin(angle)) if 'math' in globals() else 0
                color = rng.choice([(255, 120, 0), (255, 180, 60), (255, 60, 0)])
                pygame.draw.line(screen, color, (x, y), (x + dx, y + dy), rng.randint(2, 4))
            return
        if motif == 'icy':
            # Icy blue gradient with snowflakes and ice shards at bottom
            top = (200, 230, 255)
            bottom = (140, 190, 230)
            for y in range(self.screen_height):
                t = y / max(1, self.screen_height - 1)
                r = int(top[0] * (1 - t) + bottom[0] * t)
                g = int(top[1] * (1 - t) + bottom[1] * t)
                b = int(top[2] * (1 - t) + bottom[2] * t)
                pygame.draw.line(screen, (r, g, b), (0, y), (self.screen_width, y))
            rng = random.Random(1122)
            # Snowflakes
            for _ in range(80):
                x = rng.randint(0, self.screen_width)
                y = rng.randint(0, self.screen_height)
                pygame.draw.circle(screen, (255, 255, 255), (x, y), rng.randint(1, 2))
            # Ice shards at bottom
            for _ in range(20):
                x = rng.randint(0, self.screen_width)
                w = rng.randint(8, 18)
                h = rng.randint(20, 60)
                pygame.draw.polygon(screen, (190, 240, 255), [(x, self.screen_height), (x + w//2, self.screen_height - h), (x + w, self.screen_height)])
            return
        if motif == 'cheese':
            # Cheese motif: big holes and drips
            rng = random.Random(7777)
            cheese_yellow = (248, 240, 202)
            darker = (230, 210, 175)
            # Drips at the top
            for i in range(6):
                w = rng.randint(60, 120)
                h = rng.randint(30, 70)
                x = rng.randint(10, self.screen_width - w - 10)
                pygame.draw.ellipse(screen, cheese_yellow, (x, 0, w, h))
                pygame.draw.ellipse(screen, darker, (x, 0, w, h), 3)
            # Holes scattered
            for _ in range(22):
                r = rng.randint(8, 26)
                x = rng.randint(r+6, self.screen_width - r - 6)
                y = rng.randint(40, self.screen_height - r - 20)
                pygame.draw.circle(screen, darker, (x, y), r)
                pygame.draw.circle(screen, (205, 190, 155), (x + r//4, y + r//4), max(2, r//3))
            return
        if motif == 'stars':
            # Night - little white stars
            for _ in range(38):
                x = random.randint(0, self.screen_width)
                y = random.randint(0, int(self.screen_height*0.7))
                pygame.draw.circle(screen, (255,255,255), (x,y), random.randint(1,3))
        elif motif == 'bubbles':
            # Underwater
            for _ in range(14):
                x = random.randint(0, self.screen_width)
                y = random.randint(20, self.screen_height-80)
                pygame.draw.circle(screen, (220,255,255), (x,y), random.randint(6,15), 2)
        elif motif == 'rainbow':
            # Sky - rainbow arc at top
            for i,c in enumerate([(255,140,200),(255,255,0),(120,200,255),(180,255,180)]):
                pygame.draw.arc(screen,c,(120,24,560,180),0,3.14, 8-i*2)
        elif motif == 'flowers':
            # Meadow
            for _ in range(24):
                x = random.randint(24,self.screen_width-24)
                y = self.screen_height-50-random.randint(0,20)
                pygame.draw.circle(screen,(255,200,240),(x,y),3); pygame.draw.circle(screen,(255,255,128),(x,y),1)
        elif motif == 'ice_shards':
            for _ in range(14):
                x = random.randint(0, self.screen_width)
                y = random.randint(self.screen_height//2, self.screen_height)
                pygame.draw.polygon(screen, (190,240,255), [(x,y),(x+7,y-20),(x+14,y)])
        elif motif == 'embers':
            # Fire world
            for _ in range(16):
                x = random.randint(0, self.screen_width-5)
                y = random.randint(10, self.screen_height)
                c = random.choice([(255,160,80),(255,220,120),(180,90,0)])
                pygame.draw.circle(screen, c, (x,y), 3)
        elif motif == 'ash':
            # Volcano
            for _ in range(18):
                x = random.randint(0,self.screen_width-7)
                y = random.randint(10, self.screen_height-6)
                pygame.draw.circle(screen,(90,90,90),(x,y),2)
        elif motif == 'sand':
            # Desert
            for _ in range(16):
                x = random.randint(0, self.screen_width)
                y = random.randint(self.screen_height//2,self.screen_height-4)
                pygame.draw.ellipse(screen, (245, 224, 119), (x,y,13,5))
        elif motif == 'glow':
            # Neon
            for _ in range(12):
                c = random.choice([(255,80,220),(100,255,220),(255,250,150),(90,250,250)])
                x,y = random.randint(22,self.screen_width-22), random.randint(24,self.screen_height-24)
                pygame.draw.circle(screen, c, (x,y), 10, 0)
        elif motif == 'vines':
            # Forest
            for _ in range(5):
                x = random.randint(80,self.screen_width-80)
                y0 = 0
                width = random.randint(4,8)
                for seg in range(38):
                    col = (90,150,100)
                    pygame.draw.line(screen, col, (x,y0), (x+random.randint(-6,6),y0+18), width)
                    x += random.randint(-6,7); y0+=18


