import pygame
import sys
import random
import constants as const
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WHITE, BLACK, SOFT_PINK, MINT_GREEN, SOFT_YELLOW, PEACH, CORAL, LIGHT_PURPLE, GameState, set_level_dimensions
from audio import SoundManager
from camera import Camera
from entities import Player, Enemy, Platform, Powerup, Obstacle, Checkpoint
from background import Background
from ui import UI
from levels import generate_levels
from smart_level_generator import SmartLevelGenerator


class Game:
    def __init__(self, fullscreen=False):
        if fullscreen:
            self.screen = pygame.display.set_mode((FULLSCREEN_WIDTH, FULLSCREEN_HEIGHT), pygame.FULLSCREEN)
            self.screen_width = FULLSCREEN_WIDTH
            self.screen_height = FULLSCREEN_HEIGHT
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.screen_width = SCREEN_WIDTH
            self.screen_height = SCREEN_HEIGHT
        pygame.display.set_caption("Puppy Platformer")
        self.clock = pygame.time.Clock()

        self.sound_manager = SoundManager()
        self.state = GameState.MENU
        self.lives = 3
        self.score = 0
        self.level_progress = 0
        self.current_level = 0
        self.levels = generate_levels()
        self.theme = self.levels[self.current_level]["theme"]

        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.plants = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.checkpoints = pygame.sprite.Group()
        self.last_checkpoint = None  # Track the last activated checkpoint

        self.camera = Camera(self.screen_width, self.screen_height)
        self.bg = Background(self.screen_width, self.screen_height)
        self.bg.set_theme(self.theme)
        self.ui = UI(self.screen_width, self.screen_height)

        self.create_level()
        self.player = Player(100, 400, self.sound_manager)
        self.all_sprites.add(self.player)

    def create_level(self):
        level_def = self.levels[self.current_level]
        set_level_dimensions(level_def["width"], level_def["height"])
        self.theme = level_def["theme"]
        self.bg.set_theme(self.theme)
        
        # Update camera with new level dimensions
        self.camera.set_level_dimensions(level_def["width"], level_def["height"])

        # Use smart level generator for accessible platforms
        generator = SmartLevelGenerator(level_def["width"], level_def["height"], level_def["difficulty"])
        platform_data = generator.generate_accessible_platforms()
        
        # Create platforms from generated data
        for platform_info in platform_data:
            platform = Platform(
                platform_info['x'], platform_info['y'], 
                platform_info['width'], platform_info['height'],
                platform_type=platform_info['type'], 
                theme=self.theme
            )
            self.platforms.add(platform)
            self.all_sprites.add(platform)

        # Generate checkpoints (houses) at regular intervals
        checkpoint_count = 3  # 3 checkpoints per level
        checkpoint_spacing = level_def["width"] // (checkpoint_count + 1)
        
        for i in range(1, checkpoint_count + 1):
            checkpoint_x = checkpoint_spacing * i
            # Place checkpoint on ground level (should be visible)
            checkpoint_y = level_def["height"] - 140  # Ground level with proper offset
            checkpoint = Checkpoint(checkpoint_x, checkpoint_y, theme=self.theme)
            self.checkpoints.add(checkpoint)
            self.all_sprites.add(checkpoint)

        enemy_data = []
        # Include new enemy types
        enemy_kinds = ["basic", "fast", "jumper", "big", "double_hit", "air_bat", "air_dragon"]
        enemy_count = 8 + level_def["difficulty"] * 2
        rng = random.Random(9000 + self.current_level)
        for _ in range(enemy_count):
            x = rng.randint(300, level_def["width"] - 300)
            # Air enemies spawn higher up
            if rng.random() < 0.3:  # 30% chance for air enemies
                y = rng.randint(100, 300)  # Higher up for air enemies
            else:
                y = rng.randint(240, 460)  # Normal ground level
            
            # Weighted selection for enemy types
            weights = [4, 3 + level_def["difficulty"], 3, 1 + level_def["difficulty"]//2, 
                     2 + level_def["difficulty"], 1 + level_def["difficulty"]//3, 1 + level_def["difficulty"]//4]
            etype = rng.choices(enemy_kinds, weights=weights)[0]
            enemy_data.append((x, y, etype))
        for x, y, etype in enemy_data:
            enemy = Enemy(x, y, etype, theme=self.theme)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

        powerup_positions = []
        rng = random.Random(777 + self.current_level)
        for s in range(2, 9):
            x = s * (level_def["width"] // 10) + rng.randint(-60, 60)
            y = rng.randint(260, 420)
            powerup_positions.append((x, y))
        for x, y in powerup_positions:
            powerup = Powerup(x, y)
            self.powerups.add(powerup)
            self.all_sprites.add(powerup)

        obstacle_positions = []
        rng = random.Random(555 + self.current_level)
        spike_count = 3 + level_def["difficulty"]
        for _ in range(spike_count):
            obstacle_positions.append((rng.randint(600, level_def["width"] - 400), level_def["height"] - 64, "spike"))
        for x, y, otype in obstacle_positions:
            obstacle = Obstacle(x, y, otype)
            self.obstacles.add(obstacle)
            self.all_sprites.add(obstacle)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif self.state == GameState.MENU:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.start_game()
                    elif event.key == pygame.K_l:
                        self.state = GameState.LEVEL_SELECT
                elif self.state == GameState.LEVEL_COMPLETE:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.continue_to_next_level()
                    elif event.key == pygame.K_m:
                        self.state = GameState.MENU
                elif self.state == GameState.LEVEL_SELECT:
                    if event.key == pygame.K_UP:
                        self.current_level = (self.current_level - 1) % len(self.levels)
                    elif event.key == pygame.K_DOWN:
                        self.current_level = (self.current_level + 1) % len(self.levels)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.start_game()
                    elif event.key == pygame.K_m or event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_r or event.key == pygame.K_SPACE:
                        self.restart_game()
                    elif event.key == pygame.K_m:
                        self.state = GameState.MENU
                elif event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.MENU
                    else:
                        return False
        return True
    
    def toggle_fullscreen(self):
        """Toggle between windowed and fullscreen mode."""
        if self.screen.get_flags() & pygame.FULLSCREEN:
            # Switch to windowed
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.screen_width = SCREEN_WIDTH
            self.screen_height = SCREEN_HEIGHT
        else:
            # Switch to fullscreen
            self.screen = pygame.display.set_mode((FULLSCREEN_WIDTH, FULLSCREEN_HEIGHT), pygame.FULLSCREEN)
            self.screen_width = FULLSCREEN_WIDTH
            self.screen_height = FULLSCREEN_HEIGHT
        
        # Update components with new screen dimensions
        self.camera = Camera(self.screen_width, self.screen_height)
        self.bg = Background(self.screen_width, self.screen_height)
        self.ui = UI(self.screen_width, self.screen_height)

    def start_game(self):
        self.state = GameState.PLAYING
        self.lives = 3
        self.score = 0
        self.level_progress = 0
        # start from currently selected level in selector
        self.theme = self.levels[self.current_level]["theme"]
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()
        self.powerups.empty()
        self.plants.empty()
        self.obstacles.empty()
        self.create_level()
        self.player = Player(100, 400, self.sound_manager)
        self.all_sprites.add(self.player)
        self.camera.x = 0
        self.camera.y = 0

    def continue_to_next_level(self):
        if self.current_level < len(self.levels) - 1:
            self.current_level += 1
            self.theme = self.levels[self.current_level]["theme"]
            self.all_sprites.empty()
            self.platforms.empty()
            self.enemies.empty()
            self.powerups.empty()
            self.plants.empty()
            self.obstacles.empty()
            self.create_level()
            self.player = Player(100, 400, self.sound_manager)
            self.all_sprites.add(self.player)
            self.camera.x = 0
            self.camera.y = 0
            self.state = GameState.PLAYING
        else:
            self.state = GameState.MENU

    def restart_game(self):
        self.state = GameState.PLAYING
        self.lives = 3
        self.score = 0
        self.current_level = 0
        self.theme = self.levels[self.current_level]["theme"]
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()
        self.powerups.empty()
        self.plants.empty()
        self.obstacles.empty()
        self.create_level()
        self.player = Player(100, 400, self.sound_manager)
        self.all_sprites.add(self.player)
        self.camera.x = 0
        self.camera.y = 0

    def update(self):
        if self.state == GameState.PLAYING:
            self.camera.update(self.player)
            result = self.player.update(self.platforms, self.enemies, self.powerups, self.obstacles, self.camera.x)
            
            # Check for checkpoint collisions
            checkpoint_collisions = pygame.sprite.spritecollide(self.player, self.checkpoints, False)
            for checkpoint in checkpoint_collisions:
                if not checkpoint.activated:
                    checkpoint.activate()
                    self.last_checkpoint = checkpoint
                    if self.sound_manager:
                        self.sound_manager.play('coin')  # Use coin sound for checkpoint activation
            
            if result == "death" or result == "hit":
                self.lives -= 1
                if self.lives <= 0:
                    self.state = GameState.GAME_OVER
                else:
                    # Respawn at last checkpoint or start position
                    if self.last_checkpoint:
                        self.player.respawn(self.last_checkpoint.rect.x, self.last_checkpoint.rect.y - 50)
                    else:
                        self.player.respawn(100, 400)
            elif result == "enemy_killed":
                self.score += 100
                if self.score > 0 and self.score % 1000 == 0:
                    self.level_progress += 1
                    self._add_difficulty_enemies()
            elif result == "enemy_damaged":
                self.score += 50  # Half points for damaging but not killing
            elif result == "powerup":
                self.lives += 1
                self.score += 200
            if self.player.rect.right >= self.camera.level_width - 5:
                self.state = GameState.LEVEL_COMPLETE
            self.enemies.update(self.platforms)
            self.powerups.update()
            self.platforms.update()

    def _add_difficulty_enemies(self):
        import random
        if len(self.enemies) >= 25:
            return
        new_enemies = [
            (random.randint(200, self.camera.level_width - 200), random.randint(300, 500), "fast"),
            (random.randint(200, self.camera.level_width - 200), random.randint(300, 500), "jumper"),
        ]
        if self.level_progress > 2:
            new_enemies.append((random.randint(200, self.camera.level_width - 200), random.randint(300, 500), "big"))
        for x, y, etype in new_enemies:
            if len(self.enemies) < 25:
                enemy = Enemy(x, y, etype)
                self.enemies.add(enemy)
                self.all_sprites.add(enemy)

    def draw(self):
        if self.state == GameState.MENU:
            self._draw_menu()
        elif self.state == GameState.PLAYING:
            self._draw_game()
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over()
        elif self.state == GameState.LEVEL_COMPLETE:
            self._draw_level_complete()
        elif self.state == GameState.LEVEL_SELECT:
            self._draw_level_select()
        pygame.display.flip()

    def _draw_menu(self):
        self.bg.draw(self.screen, self.current_level)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(64)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        self.ui.draw_bubble_text(self.screen, "Puppy Platformer", SCREEN_WIDTH//2, SCREEN_HEIGHT//4, center=True, size=84)
        self.ui.draw_bubble_text(self.screen, "A Bubblegum Adventure", SCREEN_WIDTH//2, SCREEN_HEIGHT//4 + 60, center=True, size=36)
        instructions = [
            ("Press SPACE/ENTER to Start", MINT_GREEN),
            ("Press L for Level Select", SOFT_YELLOW),
            ("Arrows/WASD to Move, SPACE to Jump", PEACH),
            ("ESC to Quit", CORAL)
        ]
        start_y = SCREEN_HEIGHT//2 + 40
        for i, (instruction, color) in enumerate(instructions):
            button_width = 350
            button_height = 35
            button_rect = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, start_y + i * 50, button_width, button_height)
            pygame.draw.rect(self.screen, color, button_rect)
            pygame.draw.rect(self.screen, BLACK, button_rect, 2)
            self.ui.draw_bubble_text(self.screen, instruction, button_rect.centerx, button_rect.centery - 2, center=True, size=28)
        self.ui.draw_bubble_text(self.screen, "Sound effects enabled", SCREEN_WIDTH//2, SCREEN_HEIGHT - 30, center=True, size=24)

    def _draw_game(self):
        self.bg.draw(self.screen, self.current_level)
        for sprite in self.all_sprites:
            screen_x = sprite.rect.x - self.camera.x
            screen_y = sprite.rect.y - self.camera.y
            if (-sprite.rect.width < screen_x < SCREEN_WIDTH and -sprite.rect.height < screen_y < SCREEN_HEIGHT):
                self.screen.blit(sprite.image, (screen_x, screen_y))
        for i in range(self.lives):
            self.ui.draw_heart(self.screen, 14 + i * 28, 18, 10, SOFT_PINK, BLACK)
        panel_rect = pygame.Rect(10, 44, 200, 40)
        pygame.draw.rect(self.screen, SOFT_YELLOW, panel_rect)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)
        self.ui.draw_bubble_text(self.screen, f"Score: {self.score}", panel_rect.left + 10, panel_rect.centery, center=False, size=28)
        self.ui.draw_bubble_text(self.screen, f"Level: {self.current_level + 1}/{len(self.levels)}", 10, 94, center=False, size=28)

    def _draw_level_complete(self):
        self.bg.draw(self.screen, self.current_level)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        self.ui.draw_bubble_text(self.screen, f"Level {self.current_level + 1} Complete!", SCREEN_WIDTH//2, SCREEN_HEIGHT//3, center=True, size=84)
        info = "Press SPACE/ENTER to Continue" if self.current_level < len(self.levels) - 1 else "All levels complete! Press M for Menu"
        self.ui.draw_bubble_text(self.screen, info, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, center=True, size=36)
        self.ui.draw_bubble_text(self.screen, "Press M for Menu", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50, center=True, size=28)

    def _draw_game_over(self):
        self.bg.draw(self.screen, self.current_level)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        self.ui.draw_bubble_text(self.screen, "GAME OVER", SCREEN_WIDTH//2, SCREEN_HEIGHT//3, center=True, size=84)
        panel_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 60, 400, 120)
        pygame.draw.rect(self.screen, LIGHT_PURPLE, panel_rect)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 3)
        self.ui.draw_bubble_text(self.screen, f"Final Score: {self.score}", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20, center=True, size=52)
        self.ui.draw_bubble_text(self.screen, f"Level Reached: {self.level_progress + 1}", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20, center=True, size=36)
        instructions = [
            ("Press R or SPACE to Restart", SOFT_YELLOW),
            ("Press M for Main Menu", MINT_GREEN),
            ("Press ESC to Quit", CORAL)
        ]
        for i, (instruction, color) in enumerate(instructions):
            button_width = 300
            button_height = 35
            button_rect = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT//2 + 120 + i * 50, button_width, button_height)
            pygame.draw.rect(self.screen, color, button_rect)
            pygame.draw.rect(self.screen, BLACK, button_rect, 2)
            self.ui.draw_bubble_text(self.screen, instruction, button_rect.centerx, button_rect.centery - 2, center=True, size=28)

    def _draw_level_select(self):
        self.bg.draw(self.screen, self.current_level)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(96)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        self.ui.draw_bubble_text(self.screen, "Select Level", SCREEN_WIDTH//2, 90, center=True, size=72)
        top = 160
        for i, level in enumerate(self.levels):
            name = f"{i+1}. {level['theme'].get('name', 'Level')}"
            y = top + i * 36
            if i == self.current_level:
                bar = pygame.Rect(SCREEN_WIDTH//2 - 180, y - 16, 360, 32)
                pygame.draw.rect(self.screen, MINT_GREEN, bar)
                pygame.draw.rect(self.screen, BLACK, bar, 2)
            self.ui.draw_bubble_text(self.screen, name, SCREEN_WIDTH//2, y, center=True, size=28)
        self.ui.draw_bubble_text(self.screen, "UP/DOWN to choose, ENTER to play, M for menu", SCREEN_WIDTH//2, SCREEN_HEIGHT - 60, center=True, size=24)


def run_game():
    game = Game()
    running = True
    while running:
        running = game.handle_events()
        game.update()
        game.draw()
        game.clock.tick(FPS)
    pygame.quit()
    sys.exit()


