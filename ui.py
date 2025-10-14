import pygame
from constants import BLACK, SOFT_PINK, MINT_GREEN, SOFT_YELLOW, PEACH, SKY_BLUE, LIGHT_PURPLE, SCREEN_WIDTH, SCREEN_HEIGHT


class UI:
    def __init__(self, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)

    def draw_heart(self, screen, cx, cy, r, color_fill, color_outline):
        pygame.draw.circle(screen, color_fill, (cx - r//2, cy - r//4), r//2)
        pygame.draw.circle(screen, color_fill, (cx + r//2, cy - r//4), r//2)
        pygame.draw.polygon(screen, color_fill, [(cx - r, cy - r//4), (cx + r, cy - r//4), (cx, cy + r)])
        pygame.draw.circle(screen, color_outline, (cx - r//2, cy - r//4), r//2, 2)
        pygame.draw.circle(screen, color_outline, (cx + r//2, cy - r//4), r//2, 2)
        pygame.draw.polygon(screen, color_outline, [(cx - r, cy - r//4), (cx + r, cy - r//4), (cx, cy + r)], 2)

    def draw_bubble_text(self, screen, text, x, y, center=False, size=36, max_width=None):
        font = pygame.font.Font(None, size)
        # Yellow-biased multicolor palette while keeping multicolor vibe
        rainbow = [(255, 240, 150), (235, 210, 90), (255, 200, 120), (255, 235, 180), (240, 220, 130), (255, 210, 160)]
        surfaces = []
        total_w = 0
        max_h = 0
        for idx, ch in enumerate(text):
            color = rainbow[idx % len(rainbow)]
            core = font.render(ch, True, color)
            outline = font.render(ch, True, BLACK)
            w, h = core.get_size()
            char_surf = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
            for dx in (-2, -1, 0, 1, 2):
                for dy in (-2, -1, 0, 1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    char_surf.blit(outline, (dx + 3, dy + 3))
            char_surf.blit(core, (3, 3))
            surfaces.append(char_surf)
            total_w += char_surf.get_width()
            max_h = max(max_h, char_surf.get_height())
        # If max_width provided and text exceeds it, reduce size recursively
        if max_width is not None and total_w > max_width and size > 12:
            return self.draw_bubble_text(screen, text, x, y, center=center, size=int(size * 0.9), max_width=max_width)
        start_x = x - total_w // 2 if center else x
        cur_x = start_x
        for s in surfaces:
            screen.blit(s, (cur_x, y - max_h // 2))
            cur_x += s.get_width()

    def draw_cheese_title(self, screen, text, x, y, center=False, size=84):
        font = pygame.font.Font(None, size)
        cheese_yellow = (248, 240, 202)
        cheese_outline = (183, 140, 30)
        shadow = (130, 100, 25)
        surface = font.render(text, True, cheese_yellow)
        # Drop shadow
        shadow_surface = font.render(text, True, shadow)
        rect = surface.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        # Draw drippy underline effect
        screen.blit(shadow_surface, (rect.x + 4, rect.y + 4))
        screen.blit(surface, rect)
        # Outline
        for dx in (-2, -1, 1, 2):
            for dy in (-2, -1, 1, 2):
                screen.blit(font.render(text, True, cheese_outline), (rect.x + dx, rect.y + dy))
        screen.blit(surface, rect)
        # Cheese holes punched into the text by small circles along baseline
        import random
        rng = random.Random(42)
        baseline_y = rect.bottom - 10
        for _ in range(max(6, len(text))):
            r = rng.randint(3, 8)
            cx = rect.left + rng.randint(10, rect.width - 10)
            pygame.draw.circle(screen, (200, 180, 140), (cx, baseline_y + rng.randint(-6, 4)), r)

    def draw_cheese_button(self, screen, text, centerx, centery, width=360, height=44):
        # Rounded cheese rectangle with holes
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (centerx, centery)
        cheese_yellow = (248, 240, 202)
        cheese_outline = (183, 140, 30)
        pygame.draw.rect(screen, cheese_yellow, rect, border_radius=14)
        pygame.draw.rect(screen, cheese_outline, rect, 3, border_radius=14)
        # Holes
        import random
        rng = random.Random(centerx * 17 + centery * 31)
        for _ in range(5):
            r = rng.randint(3, 8)
            x = rng.randint(rect.left + 10, rect.right - 10)
            y = rng.randint(rect.top + 8, rect.bottom - 8)
            pygame.draw.circle(screen, (210, 190, 150), (x, y), r)
        # Label - ensure text fits within button
        self.draw_bubble_text(screen, text, rect.centerx, rect.centery - 1, center=True, size=28, max_width=width - 24)


