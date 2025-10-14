import pygame
import sys
import random
import constants as const
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FULLSCREEN_WIDTH, FULLSCREEN_HEIGHT, FPS, WHITE, BLACK, SOFT_PINK, MINT_GREEN, SOFT_YELLOW, PEACH, CORAL, LIGHT_PURPLE, GameState, set_level_dimensions
from audio import SoundManager
from camera import Camera
from entities import Player, Enemy, Platform, Powerup, Obstacle, Checkpoint, StarPowerup
from background import Background
from ui import UI
from levels import load_levels
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
        pygame.display.set_caption("Rat Race")
        self.clock = pygame.time.Clock()

        self.sound_manager = SoundManager()
        self.state = GameState.LOADING
        self.lives = 3
        self.score = 0
        self.level_progress = 0
        self.current_level = 0
        self.levels = load_levels()
        self.theme = self.levels[self.current_level]["theme"]

        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.star_powerups = pygame.sprite.Group()
        self.plants = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.checkpoints = pygame.sprite.Group()
        self.last_checkpoint = None  # Track the last activated checkpoint

        self.camera = Camera(self.screen_width, self.screen_height)
        self.bg = Background(self.screen_width, self.screen_height)
        self.bg.set_theme(self.theme)
        self.ui = UI(self.screen_width, self.screen_height)

        # Delay heavy setup until first frame so loading screen shows
        self._needs_initial_load = True

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
        
        # Validate accessibility and add fixes if needed
        is_accessible = generator.validate_platform_accessibility()
        if not is_accessible:
            print(f"Level {self.current_level + 1}: Adding accessibility fixes...")
            generator.add_accessibility_fixes()
            # Re-validate
            generator.validate_platform_accessibility()
        
        # Get updated platform data after fixes
        platform_data = generator.platforms
        
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
        
        # Get enemy stepping stones from generator
        stepping_stone_enemies = generator.get_enemy_stepping_stones()

        # Generate checkpoints (houses or cheese wheels) at regular intervals
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
        
        # First, add stepping stone enemies from generator
        for enemy_info in stepping_stone_enemies:
            enemy_data.append((enemy_info['x'], enemy_info['y'], enemy_info['type']))
        
        # Then add regular enemies
        enemy_kinds = ["basic", "fast", "jumper", "big", "double_hit", "air_bat", "air_dragon"]
        enemy_count = 8 + level_def["difficulty"] * 2
        if self.theme.get("name") == "Smelted Dreams":
            enemy_count += 6  # harder lava level
        # Increase jungle level difficulty
        if self.theme.get("name") == "Moss-t Be Joking":
            enemy_count += 4
        rng = random.Random(9000 + self.current_level)
        for _ in range(enemy_count):
            x = rng.randint(300, level_def["width"] - 300)
            # Air enemies spawn higher up
            air_chance = 0.3
            if self.theme.get("name") == "Moss-t Be Joking":
                air_chance = 0.5
            elif self.theme.get("name") == "Smelted Dreams":
                air_chance = 0.45
            if rng.random() < air_chance:
                y = rng.randint(100, 300)  # Higher up for air enemies
            else:
                y = rng.randint(240, 460)  # Normal ground level
            
            # Weighted selection for enemy types
            weights = [4, 3 + level_def["difficulty"], 3, 1 + level_def["difficulty"]//2, 
                     2 + level_def["difficulty"], 1 + level_def["difficulty"]//3, 1 + level_def["difficulty"]//4]
            etype = rng.choices(enemy_kinds, weights=weights)[0]
            enemy_data.append((x, y, etype))
        
        # Create all enemies
        for x, y, etype in enemy_data:
            enemy = Enemy(x, y, etype, theme=self.theme)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

        # Place powerups on or near platforms for accessibility
        powerup_positions = []
        rng = random.Random(777 + self.current_level)
        
        # Get non-ground platforms for powerup placement
        floating_platforms = [p for p in platform_data if p['type'] != 'ground']
        
        if floating_platforms:
            # Place powerups on random platforms
            num_powerups = min(7, len(floating_platforms))
            selected_platforms = rng.sample(floating_platforms, num_powerups)
            
            for platform_info in selected_platforms:
                # Place powerup slightly above the platform
                x = platform_info['x'] + platform_info['width'] // 2
                y = platform_info['y'] - 30
                powerup_positions.append((x, y))
        else:
            # Fallback to random positions if no floating platforms
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
            # Replace spikes with cheese globs on level 1 (The Big Melt-down)
            if self.theme.get("name") == "The Big Melt-down":
                otype = "cheese_glob"
            elif self.theme.get("name") == "Smelted Dreams" and rng.random() < 0.6:
                otype = "lava_pit"
            elif self.theme.get("name") == "Moss-t Be Joking" and rng.random() < 0.7:
                otype = "rock"
            elif self.theme.get("name") == "Frost and Furious":
                # Mostly ice spikes for frost level
                otype = "ice_spike" if rng.random() < 0.85 else "spike"
            else:
                otype = "spike"
            obstacle_positions.append((rng.randint(600, level_def["width"] - 400), level_def["height"] - 64, otype))
        for x, y, otype in obstacle_positions:
            obstacle = Obstacle(x, y, otype)
            self.obstacles.add(obstacle)
            self.all_sprites.add(obstacle)

        # Jungle plants on some platforms to block the way
        if self.theme.get("name") == "Moss-t Be Joking":
            plant_rng = random.Random(4321 + self.current_level)
            candidate_platforms = [p for p in self.platforms if p.rect.y < level_def["height"] - 80 and p.rect.width >= 100]
            for p in candidate_platforms[::3]:
                if plant_rng.random() < 0.6:
                    plant_x = p.rect.centerx + plant_rng.randint(-p.rect.width//4, p.rect.width//4)
                    plant = Obstacle(plant_x, p.rect.y - 46, "jungle_plant")
                    self.obstacles.add(plant)
                    self.all_sprites.add(plant)

        # Create one star powerup in an accessible but challenging location
        star_pos = generator.find_accessible_star_position()
        star_powerup = StarPowerup(star_pos['x'], star_pos['y'])
        self.star_powerups.add(star_powerup)
        self.all_sprites.add(star_powerup)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                # Handle global ESC first for consistent quitting from menus
                elif event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.MENU
                    else:
                        return False
                elif self.state == GameState.LOADING:
                    # Allow skip loading to menu
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.state = GameState.MENU
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
        self.star_powerups.empty()
        self.plants.empty()
        self.obstacles.empty()
        self.checkpoints.empty()
        self.last_checkpoint = None
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
            self.star_powerups.empty()
            self.plants.empty()
            self.obstacles.empty()
            self.checkpoints.empty()
            self.last_checkpoint = None
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
        self.star_powerups.empty()
        self.plants.empty()
        self.obstacles.empty()
        self.checkpoints.empty()
        self.last_checkpoint = None
        self.create_level()
        self.player = Player(100, 400, self.sound_manager)
        self.all_sprites.add(self.player)
        self.camera.x = 0
        self.camera.y = 0

    def update(self):
        if self._needs_initial_load:
            # Perform heavy setup now that we've shown at least one frame
            self.create_level()
            self.player = Player(100, 400, self.sound_manager)
            self.all_sprites.add(self.player)
            self._needs_initial_load = False
            self.state = GameState.MENU
            return
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
            
            # Check for star powerup collisions
            star_collisions = pygame.sprite.spritecollide(self.player, self.star_powerups, True)
            if star_collisions:
                self.player.activate_star_powerup()
                self.score += 500  # Bonus score for star powerup
            
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
            self.star_powerups.update()
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
        if self.state == GameState.LOADING:
            self._draw_loading()
        elif self.state == GameState.MENU:
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
        # Cheese themed menu
        cheese_theme = {"sky_top": (248, 240, 202), "sky_bottom": (230, 210, 175), "bg_motif": "cheese"}
        old_theme = self.bg.theme
        self.bg.set_theme(cheese_theme)
        self.bg.draw(self.screen, self.current_level)
        # Semi-transparent vignette
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(50)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        # Title
        self.ui.draw_cheese_title(self.screen, "Rat Race", SCREEN_WIDTH//2, SCREEN_HEIGHT//4, center=True, size=96)
        self.ui.draw_bubble_text(self.screen, "Cheese-fueled platformer", SCREEN_WIDTH//2, SCREEN_HEIGHT//4 + 60, center=True, size=36, max_width=SCREEN_WIDTH - 80)
        # Buttons
        start_y = SCREEN_HEIGHT//2 + 20
        self.ui.draw_cheese_button(self.screen, "Start (SPACE/ENTER)", SCREEN_WIDTH//2, start_y)
        self.ui.draw_cheese_button(self.screen, "Level Select (L)", SCREEN_WIDTH//2, start_y + 60)
        self.ui.draw_cheese_button(self.screen, "ESC to Quit", SCREEN_WIDTH//2, start_y + 120)
        self.ui.draw_bubble_text(self.screen, "Sound effects enabled", SCREEN_WIDTH//2, SCREEN_HEIGHT - 30, center=True, size=24)
        # Restore level theme for gameplay drawing
        self.bg.set_theme(old_theme)

    def _draw_loading(self):
        # Distinct cheese loading screen with big drips
        cheese_theme = {"sky_top": (248, 240, 202), "sky_bottom": (230, 210, 175), "bg_motif": "cheese"}
        old_theme = self.bg.theme
        self.bg.set_theme(cheese_theme)
        self.bg.draw(self.screen, self.current_level)
        # Loading text
        self.ui.draw_cheese_title(self.screen, "Loading...", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20, center=True, size=72)
        self.ui.draw_bubble_text(self.screen, "Tip: Holes make the best shortcuts.", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40, center=True, size=28)
        self.bg.set_theme(old_theme)

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
        self.ui.draw_bubble_text(self.screen, f"Score: {self.score}", panel_rect.left + 10, panel_rect.centery, center=False, size=28, max_width=panel_rect.width - 20)
        self.ui.draw_bubble_text(self.screen, f"Level: {self.current_level + 1}/{len(self.levels)}", 10, 94, center=False, size=28)
        
        # Draw star powerup timer if active
        if self.player.star_active:
            # Draw star powerup indicator
            star_panel_rect = pygame.Rect(SCREEN_WIDTH - 210, 10, 200, 60)
            pygame.draw.rect(self.screen, SOFT_YELLOW, star_panel_rect)
            pygame.draw.rect(self.screen, BLACK, star_panel_rect, 3)
            
            # Draw star icon
            import math
            star_center_x = SCREEN_WIDTH - 180
            star_center_y = 30
            star_points = []
            for i in range(10):
                angle = (i * 36 - 90) * math.pi / 180
                if i % 2 == 0:
                    radius = 12
                else:
                    radius = 5
                x = star_center_x + radius * math.cos(angle)
                y = star_center_y + radius * math.sin(angle)
                star_points.append((x, y))
            pygame.draw.polygon(self.screen, WHITE, star_points)
            pygame.draw.polygon(self.screen, BLACK, star_points, 2)
            
            # Draw timer bar
            timer_width = 140
            timer_height = 15
            timer_x = SCREEN_WIDTH - 200
            timer_y = 48
            
            # Background bar
            pygame.draw.rect(self.screen, BLACK, (timer_x, timer_y, timer_width, timer_height))
            
            # Progress bar
            progress = self.player.star_timer / self.player.star_duration
            progress_width = int(timer_width * progress)
            
            # Color gradient from green to yellow to red based on time remaining
            if progress > 0.5:
                bar_color = MINT_GREEN
            elif progress > 0.25:
                bar_color = SOFT_YELLOW
            else:
                bar_color = CORAL
            
            pygame.draw.rect(self.screen, bar_color, (timer_x, timer_y, progress_width, timer_height))
            pygame.draw.rect(self.screen, BLACK, (timer_x, timer_y, timer_width, timer_height), 2)
            
            # Draw time remaining text
            seconds_remaining = int(self.player.star_timer / 60) + 1
            self.ui.draw_bubble_text(self.screen, f"{seconds_remaining}s", SCREEN_WIDTH - 130, 30, center=False, size=24)

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
        # Cheese themed game over screen
        cheese_theme = {"sky_top": (248, 240, 202), "sky_bottom": (230, 210, 175), "bg_motif": "cheese"}
        old_theme = self.bg.theme
        self.bg.set_theme(cheese_theme)
        self.bg.draw(self.screen, self.current_level)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(110)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        self.ui.draw_cheese_title(self.screen, "Game Over", SCREEN_WIDTH//2, SCREEN_HEIGHT//3, center=True, size=96)
        # Stats
        self.ui.draw_bubble_text(self.screen, f"Final Score: {self.score}", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 10, center=True, size=48)
        self.ui.draw_bubble_text(self.screen, f"Level Reached: {self.level_progress + 1}", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30, center=True, size=32)
        # Cheese buttons
        base_y = SCREEN_HEIGHT//2 + 110
        self.ui.draw_cheese_button(self.screen, "Restart (R/SPACE)", SCREEN_WIDTH//2, base_y)
        self.ui.draw_cheese_button(self.screen, "Main Menu (M)", SCREEN_WIDTH//2, base_y + 60)
        self.ui.draw_cheese_button(self.screen, "ESC to Quit", SCREEN_WIDTH//2, base_y + 120)
        self.bg.set_theme(old_theme)

    def _draw_level_select(self):
        # Cheese themed level select
        cheese_theme = {"sky_top": (248, 240, 202), "sky_bottom": (230, 210, 175), "bg_motif": "cheese"}
        old_theme = self.bg.theme
        self.bg.set_theme(cheese_theme)
        self.bg.draw(self.screen, self.current_level)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(90)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        self.ui.draw_cheese_title(self.screen, "Select Level", SCREEN_WIDTH//2, 90, center=True, size=84)
        top = 160
        for i, level in enumerate(self.levels):
            name = f"{i+1}. {level['theme'].get('name', 'Level')}"
            y = top + i * 36
            if i == self.current_level:
                bar = pygame.Rect(SCREEN_WIDTH//2 - 180, y - 16, 360, 32)
                pygame.draw.rect(self.screen, MINT_GREEN, bar)
                pygame.draw.rect(self.screen, BLACK, bar, 2)
            self.ui.draw_bubble_text(self.screen, name, SCREEN_WIDTH//2, y, center=True, size=28)
        # Instruction cheese button
        self.ui.draw_cheese_button(self.screen, "UP/DOWN to choose, ENTER to play, M for menu", SCREEN_WIDTH//2, SCREEN_HEIGHT - 50, width=560, height=44)
        self.bg.set_theme(old_theme)


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


