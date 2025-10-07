import pygame
from constants import BLACK, SOFT_PINK, MINT_GREEN, SOFT_YELLOW, PEACH, SKY_BLUE, LIGHT_PURPLE, SCREEN_WIDTH, SCREEN_HEIGHT


class UI:
    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)

    def draw_heart(self, screen, cx, cy, r, color_fill, color_outline):
        pygame.draw.circle(screen, color_fill, (cx - r//2, cy - r//4), r//2)
        pygame.draw.circle(screen, color_fill, (cx + r//2, cy - r//4), r//2)
        pygame.draw.polygon(screen, color_fill, [(cx - r, cy - r//4), (cx + r, cy - r//4), (cx, cy + r)])
        pygame.draw.circle(screen, color_outline, (cx - r//2, cy - r//4), r//2, 2)
        pygame.draw.circle(screen, color_outline, (cx + r//2, cy - r//4), r//2, 2)
        pygame.draw.polygon(screen, color_outline, [(cx - r, cy - r//4), (cx + r, cy - r//4), (cx, cy + r)], 2)

    def draw_bubble_text(self, screen, text, x, y, center=False, size=36):
        font = pygame.font.Font(None, size)
        rainbow = [SOFT_PINK, MINT_GREEN, SOFT_YELLOW, PEACH, LIGHT_PURPLE, SKY_BLUE]
        surfaces = []
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
        total_w = sum(s.get_width() for s in surfaces)
        max_h = max((s.get_height() for s in surfaces), default=0)
        start_x = x - total_w // 2 if center else x
        cur_x = start_x
        for s in surfaces:
            screen.blit(s, (cur_x, y - max_h // 2))
            cur_x += s.get_width()


