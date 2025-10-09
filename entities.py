import random
import pygame
from constants import GRAVITY, JUMP_STRENGTH, PLAYER_SPEED, ENEMY_SPEED, LEVEL_WIDTH, LEVEL_HEIGHT, WHITE, BLACK, SOFT_PURPLE, LIGHT_PURPLE, SOFT_PINK, DUSTY_ROSE, PEACH, CORAL, MOUNTAIN_BLUE, BEIGE, LIGHT_BROWN, SAGE_GREEN, PASTEL_GREEN, MINT_GREEN, SOFT_YELLOW, SOFT_BLUE, CREAM


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, sound_manager=None):
        super().__init__()
        self.image = pygame.Surface((32, 48), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.jump_count = 0
        self.max_jumps = 1
        self.facing_right = True
        self.sound_manager = sound_manager
        self.draw_character()

    def draw_character(self):
        self.image.fill((0, 0, 0, 0))
        body_color = SOFT_PURPLE
        outline = DUSTY_ROSE
        pygame.draw.ellipse(self.image, body_color, (4, 18, 24, 26))
        pygame.draw.ellipse(self.image, outline, (4, 18, 24, 26), 2)
        pygame.draw.ellipse(self.image, body_color, (6, 4, 22, 18))
        pygame.draw.ellipse(self.image, outline, (6, 4, 22, 18), 2)
        pygame.draw.ellipse(self.image, LIGHT_PURPLE, (3, 6, 8, 12))
        pygame.draw.ellipse(self.image, LIGHT_PURPLE, (23, 6, 8, 12))
        snout_x = 18 if self.facing_right else 10
        pygame.draw.ellipse(self.image, LIGHT_PURPLE, (snout_x, 10, 8, 6))
        pygame.draw.circle(self.image, SOFT_PINK, (snout_x + (6 if self.facing_right else 2), 13), 2)
        if self.facing_right:
            pygame.draw.circle(self.image, WHITE, (14, 10), 3)
            pygame.draw.circle(self.image, WHITE, (20, 10), 3)
            pygame.draw.circle(self.image, BLACK, (14, 10), 1)
            pygame.draw.circle(self.image, BLACK, (20, 10), 1)
        else:
            pygame.draw.circle(self.image, WHITE, (12, 10), 3)
            pygame.draw.circle(self.image, WHITE, (18, 10), 3)
            pygame.draw.circle(self.image, BLACK, (12, 10), 1)
            pygame.draw.circle(self.image, BLACK, (18, 10), 1)
        pygame.draw.arc(self.image, LIGHT_PURPLE, (0, 22, 14, 16), 1.5, 3.0, 3)
        pygame.draw.ellipse(self.image, DUSTY_ROSE, (6, 42, 8, 6))
        pygame.draw.ellipse(self.image, DUSTY_ROSE, (18, 42, 8, 6))
        pygame.draw.circle(self.image, SOFT_PINK, (10, 44), 1)
        pygame.draw.circle(self.image, SOFT_PINK, (22, 44), 1)

    def update(self, platforms, enemies, powerups, obstacles, camera_x):
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        old_facing = self.facing_right
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True
        if old_facing != self.facing_right:
            self.draw_character()
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False
            if self.sound_manager:
                self.sound_manager.play('jump')
        self.vel_y += GRAVITY
        self.rect.x += self.vel_x
        collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collisions:
            if self.vel_x > 0:
                self.rect.right = platform.rect.left
            elif self.vel_x < 0:
                self.rect.left = platform.rect.right
        self.rect.y += int(self.vel_y)
        self.on_ground = False
        collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collisions:
            if self.vel_y > 0:
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
                self.on_ground = True
                self.jump_count = 0
            elif self.vel_y < 0:
                self.rect.top = platform.rect.bottom
                self.vel_y = 0
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > LEVEL_WIDTH:
            self.rect.right = LEVEL_WIDTH
        if self.rect.top > LEVEL_HEIGHT:
            return "death"
        enemy_collisions = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in enemy_collisions:
            if self.vel_y > 0 and self.rect.bottom < enemy.rect.centery:
                enemy.kill()
                self.vel_y = int(JUMP_STRENGTH * 1.15)
                if self.sound_manager:
                    self.sound_manager.play('enemy_kill')
                return "enemy_killed"
            else:
                if self.sound_manager:
                    self.sound_manager.play('hit')
                return "hit"
        powerup_collisions = pygame.sprite.spritecollide(self, powerups, True)
        if powerup_collisions:
            if self.sound_manager:
                self.sound_manager.play('coin')
            return "powerup"
        obstacle_collisions = pygame.sprite.spritecollide(self, obstacles, False)
        if obstacle_collisions:
            if self.sound_manager:
                self.sound_manager.play('hit')
            return "hit"
        return None


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type="basic", theme=None):
        super().__init__()
        self.enemy_type = enemy_type
        self.theme = theme or {}
        # Make all enemies much larger and rounder for visibility
        if enemy_type == "basic":
            self.image = pygame.Surface((56, 56), pygame.SRCALPHA)
            self.speed = ENEMY_SPEED
        elif enemy_type == "fast":
            self.image = pygame.Surface((44, 44), pygame.SRCALPHA)
            self.speed = ENEMY_SPEED * 1.5
        elif enemy_type == "big":
            self.image = pygame.Surface((72, 72), pygame.SRCALPHA)
            self.speed = ENEMY_SPEED * 0.7
        else:
            self.image = pygame.Surface((52, 62), pygame.SRCALPHA)
            self.speed = ENEMY_SPEED
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = random.choice([-self.speed, self.speed])
        self.vel_y = 0
        self.jump_timer = 0
        self.jump_cooldown = random.randint(60, 120)
        self.draw_enemy()

    def draw_enemy(self):
        self.image.fill((0, 0, 0, 0))
        w, h = self.image.get_size()
        colors = self.theme.get('enemy_palette', [CORAL, SOFT_PINK, DUSTY_ROSE])
        if self.enemy_type == "basic":
            # Big blobby critter - themed color
            base_c = colors[0]
            sec_c = colors[1] if len(colors) > 1 else DUSTY_ROSE
            pygame.draw.ellipse(self.image, base_c, (6, 20, w-12, h-32))
            pygame.draw.ellipse(self.image, sec_c, (6, 20, w-12, h-32), 4)
            pygame.draw.circle(self.image, colors[2%len(colors)], (w//3, h//2), 9)
            pygame.draw.circle(self.image, colors[2%len(colors)], (2*w//3, h//2), 9)
            pygame.draw.circle(self.image, BLACK, (w//3, h//2), 4)
            pygame.draw.circle(self.image, BLACK, (2*w//3, h//2), 4)
            pygame.draw.line(self.image, BLACK, (w//2 - 8, h//2 + 18), (w//2 + 8, h//2 + 18), 4)
        elif self.enemy_type == "fast":
            base_c = colors[0]
            sec_c = colors[1] if len(colors) > 1 else SOFT_PINK
            pygame.draw.ellipse(self.image, sec_c, (7, 11, w-14, h-22))
            pygame.draw.ellipse(self.image, base_c, (7, 11, w-14, h-22), 4)
            pygame.draw.polygon(self.image, base_c, [(w//4, 12), (w//2, 2), (3*w//4, 12)])
            pygame.draw.circle(self.image, BLACK, (w//3, h//2), 4)
            pygame.draw.circle(self.image, BLACK, (2*w//3, h//2), 4)
        elif self.enemy_type == "big":
            base_c = colors[0]
            sec_c = colors[1] if len(colors) > 1 else CORAL
            pygame.draw.rect(self.image, sec_c, (12, 18, w-24, h-32), border_radius=14)
            pygame.draw.rect(self.image, base_c, (12, 18, w-24, h-32), 5, border_radius=14)
            pygame.draw.circle(self.image, colors[2%len(colors)], (w//3, h//2), 14)
            pygame.draw.circle(self.image, colors[2%len(colors)], (2*w//3, h//2), 14)
            pygame.draw.circle(self.image, BLACK, (w//3, h//2), 5)
            pygame.draw.circle(self.image, BLACK, (2*w//3, h//2), 5)
            pygame.draw.line(self.image, BLACK, (w//2 - 12, h//2 + 25), (w//2 + 12, h//2 + 25), 6)
        else:
            base_c = colors[0]
            sec_c = colors[1] if len(colors) > 1 else LIGHT_PURPLE
            pygame.draw.ellipse(self.image, sec_c, (10, h//2-12, w-20, h//2-10))
            pygame.draw.ellipse(self.image, base_c, (10, h//2-12, w-20, h//2-10), 3)
            pygame.draw.circle(self.image, base_c, (w//3, h//2-9), 10)
            pygame.draw.circle(self.image, sec_c, (2*w//3, h//2-9), 10)
            pygame.draw.circle(self.image, BLACK, (w//3, h//2-9), 3)
            pygame.draw.circle(self.image, BLACK, (2*w//3, h//2-9), 3)
        # Feet for all types
        foot_y = h - 10
        pygame.draw.ellipse(self.image, BLACK, (w//4, foot_y, w//6, 8))
        pygame.draw.ellipse(self.image, BLACK, (3*w//4 - w//6, foot_y, w//6, 8))

    def update(self, platforms):
        self.vel_y += GRAVITY
        if self.enemy_type == "jumper":
            self.jump_timer += 1
            if self.jump_timer >= self.jump_cooldown and self.vel_y == 0:
                self.vel_y = JUMP_STRENGTH * 0.7
                self.jump_timer = 0
                self.jump_cooldown = random.randint(60, 120)
        self.rect.x += int(self.vel_x)
        collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collisions:
            if self.vel_x > 0:
                self.rect.right = platform.rect.left
                self.vel_x = -self.speed
            elif self.vel_x < 0:
                self.rect.left = platform.rect.right
                self.vel_x = self.speed
        self.rect.y += int(self.vel_y)
        collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collisions:
            if self.vel_y > 0:
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
            elif self.vel_y < 0:
                self.rect.top = platform.rect.bottom
                self.vel_y = 0
        if self.rect.left < 0 or self.rect.right > LEVEL_WIDTH:
            self.vel_x *= -1
        if self.rect.top > LEVEL_HEIGHT:
            self.kill()


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, platform_type="normal", theme=None):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = pygame.Rect(x, y, width, height)
        self.platform_type = platform_type
        self.original_x = x
        self.move_offset = 0
        self.theme = theme or {}
        self.draw_platform(width, height)

    def draw_platform(self, width, height):
        style = self.theme.get('platform_style', self.platform_type)
        # Cloud (for sky/neon)
        if style == "cloud":
            self.image.fill((0, 0, 0, 0))
            pygame.draw.ellipse(self.image, WHITE, (0, height//3, width, height//2))
            for x in range(0, width, width//4):
                pygame.draw.circle(self.image, WHITE, (x + width//8, height//2), height//3)
            pygame.draw.ellipse(self.image, LIGHT_PURPLE, (2, height//3 + 2, width-4, height//2 - 4))
        elif style == "ice":
            self.image.fill(SOFT_BLUE)
            for x in range(0, width, 18):
                for y in range(0, height, 8):
                    if random.random() < 0.25:
                        pygame.draw.circle(self.image, WHITE, (x + random.randint(0, 15), y + random.randint(0, 8)), 2)
            pygame.draw.line(self.image, WHITE, (0, 0), (width, 0), 2)
            pygame.draw.line(self.image, LIGHT_PURPLE, (0, height-1), (width, height-1), 2)
        elif style == "lava":
            self.image.fill(CORAL)
            pygame.draw.rect(self.image, DUSTY_ROSE, (0, 0, width, height), 3)
            for x in range(width // 10):
                pygame.draw.arc(self.image, PEACH, (x * 10, height - 12, 10, 18), 0, 3.14, 2)
            # cracks
            for i in range(width // 30):
                rx = random.randint(0, width - 10)
                len_ = random.randint(3, 10)
                pygame.draw.line(self.image, BLACK, (rx, height - 4), (rx + len_, height - 2), 1)
        elif style == "mushroom":
            self.image.fill(MINT_GREEN)
            pygame.draw.circle(self.image, PASTEL_GREEN, (width//2, 0), width//3)
            for i in range(6):
                dotx = random.randint(0, width-8)
                doty = random.randint(0, 8)
                pygame.draw.circle(self.image, SOFT_YELLOW, (dotx, doty + 4), 3)
        elif style == "coral":
            self.image.fill(SKY_BLUE)
            for y in range(0, height, 6):
                pygame.draw.arc(self.image, SOFT_PINK, (0, y, width, 12), 0, 3.1416, 2)
            for cx in range(12, width, 36):
                pygame.draw.circle(self.image, MINT_GREEN, (cx, height-6), 5)
        elif style == "sandstone":
            self.image.fill(BEIGE)
            for x in range(0, width, 16):
                level = random.choice([SOFT_YELLOW, PEACH, CREAM])
                pygame.draw.rect(self.image, level, (x, height-10, 14, 10))
            pygame.draw.rect(self.image, LIGHT_BROWN, (0, 0, width, height), 2)
        elif style == "ghost":
            self.image.fill(LIGHT_PURPLE)
            for i in range(5):
                rx = random.randint(8, width-8); ry = random.randint(0, height-10)
                pygame.draw.ellipse(self.image, WHITE, (rx, ry, 8, 6), 0);
            pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 2)
        elif style == "volcano":
            self.image.fill(DUSTY_ROSE)
            for x in range(width // 11):
                pygame.draw.arc(self.image, CORAL, (x * 10, height-12, 12, 16), 0, 3.1416, 2)
            for _ in range(width//20):
                rx = random.randint(0, width-10)
                pygame.draw.line(self.image, CORAL, (rx, height-5), (rx+random.randint(-3,3), height), 2)
        elif style == "neon":
            self.image.fill(BLACK)
            neon_colors = [SOFT_PINK, MINT_GREEN, SOFT_YELLOW, SKY_BLUE]
            for i in range(height//7):
                nc = random.choice(neon_colors)
                pygame.draw.line(self.image, nc, (0, 2+i*7), (width, 4+i*7), 3)
        else:
            # Default grass
            self.image.fill(LIGHT_BROWN)
            grass_height = min(8, height // 3)
            pygame.draw.rect(self.image, SAGE_GREEN, (0, 0, width, grass_height))
            for x in range(0, width, 4):
                gx = x + random.randint(-1, 1)
                if 0 <= gx < width:
                    pygame.draw.line(self.image, PASTEL_GREEN, (gx, 0), (gx, grass_height - 1))
            for y in range(grass_height, height, 8):
                for x in range(0, width, 12):
                    w2 = min(10, width - x)
                    h2 = min(6, height - y)
                    if w2 > 0 and h2 > 0:
                        shade = random.choice([BEIGE, LIGHT_BROWN, PEACH])
                        pygame.draw.rect(self.image, shade, (x, y, w2, h2))
                        pygame.draw.rect(self.image, DUSTY_ROSE, (x, y, w2, h2), 1)
            pygame.draw.line(self.image, MINT_GREEN, (0, grass_height), (width, grass_height), 1)
            if height > 4:
                pygame.draw.line(self.image, DUSTY_ROSE, (0, height-1), (width, height-1), 1)

    def update(self):
        if self.platform_type == "moving":
            self.move_offset += 0.02
            self.rect.x = self.original_x + int(50 * pygame.math.Vector2(1, 0).rotate(self.move_offset * 180 / 3.14159).x)


class Powerup(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.float_offset = 0
        self.original_y = y
        self.spin_angle = 0
        self.draw_coin()

    def draw_coin(self):
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, SOFT_YELLOW, (12, 12), 10)
        pygame.draw.circle(self.image, PEACH, (12, 12), 10, 2)
        pygame.draw.circle(self.image, CREAM, (12, 12), 7)
        pygame.draw.circle(self.image, PEACH, (12, 12), 7, 1)
        pygame.draw.line(self.image, WHITE, (12, 8), (12, 16), 2)
        pygame.draw.line(self.image, WHITE, (8, 12), (16, 12), 2)
        pygame.draw.line(self.image, CREAM, (9, 9), (15, 15), 1)
        pygame.draw.line(self.image, CREAM, (15, 9), (9, 15), 1)
        pygame.draw.circle(self.image, WHITE, (9, 9), 2)

    def update(self):
        self.float_offset += 0.15
        float_y = int(3 * pygame.math.Vector2(0, 1).rotate(self.float_offset * 180 / 3.14159).y)
        self.rect.y = self.original_y + float_y
        self.spin_angle += 5
        if self.spin_angle >= 360:
            self.spin_angle = 0


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, obstacle_type="spike"):
        super().__init__()
        self.obstacle_type = obstacle_type
        if obstacle_type == "spike":
            self.image = pygame.Surface((20, 24), pygame.SRCALPHA)
        else:
            self.image = pygame.Surface((40, 20), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.draw_obstacle()

    def draw_obstacle(self):
        self.image.fill((0, 0, 0, 0))
        if self.obstacle_type == "spike":
            spike_points = [
                [(2, 24), (10, 4), (18, 24)],
                [(0, 24), (6, 12), (12, 24)],
                [(8, 24), (14, 8), (20, 24)]
            ]
            for spike in spike_points:
                pygame.draw.polygon(self.image, DUSTY_ROSE, spike)
                pygame.draw.polygon(self.image, BLACK, spike, 1)


