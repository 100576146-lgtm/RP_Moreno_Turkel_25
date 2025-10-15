import pygame
import sys
import random
import math
import constants as const
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FULLSCREEN_WIDTH, FULLSCREEN_HEIGHT, FPS, WHITE, BLACK, SOFT_PINK, MINT_GREEN, SOFT_YELLOW, PEACH, CORAL, LIGHT_PURPLE, GameState, set_level_dimensions
from audio import SoundManager
from camera import Camera
from entities import Player, Enemy, Platform, Powerup, Obstacle, Checkpoint, StarPowerup, BigCoin, BonusNPC, Key
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
        self.high_score = 0
        self.load_high_score()
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
        self.big_coins = pygame.sprite.Group()
        self.npcs = pygame.sprite.Group()
        self.keys = pygame.sprite.Group()
        self.last_checkpoint = None  # Track the last activated checkpoint
        self.return_from_bonus = None
        # Track where to return from bonus room

        self.camera = Camera(self.screen_width, self.screen_height)
        self.bg = Background(self.screen_width, self.screen_height)
        self.bg.set_theme(self.theme)
        self.ui = UI(self.screen_width, self.screen_height)
        
        # Load mouse images for different screens
        self._load_mouse_images()

        # Delay heavy setup until first frame so loading screen shows
        self._needs_initial_load = True
    
    def _load_mouse_images(self):
        """Load mouse images for different screens."""
        import os
        try:
            # Load 3 mice for entrance screen - FULL SCREEN
            mice_path = os.path.join(os.path.dirname(__file__), "3mouse.jpeg")
            if os.path.exists(mice_path):
                self.mice_image = pygame.image.load(mice_path)
                # Scale to full screen size
                self.mice_image = pygame.transform.scale(self.mice_image, (self.screen_width, self.screen_height))
            else:
                self.mice_image = None
            
            # Load rat for death screen - FULL SCREEN
            rat_path = os.path.join(os.path.dirname(__file__), "rat.jpeg")
            if os.path.exists(rat_path):
                self.rat_image = pygame.image.load(rat_path)
                # Scale to full screen size
                self.rat_image = pygame.transform.scale(self.rat_image, (self.screen_width, self.screen_height))
            else:
                self.rat_image = None
            
            # Load rat for levels screen (changed from pocketrat) - FULL SCREEN
            rat_levels_path = os.path.join(os.path.dirname(__file__), "rat.jpeg")
            if os.path.exists(rat_levels_path):
                self.pocket_rat_image = pygame.image.load(rat_levels_path)
                # Scale to full screen size
                self.pocket_rat_image = pygame.transform.scale(self.pocket_rat_image, (self.screen_width, self.screen_height))
            else:
                self.pocket_rat_image = None
                
        except pygame.error as e:
            print(f"Could not load mouse images: {e}")
            self.mice_image = None
            self.rat_image = None
            self.pocket_rat_image = None
    
    def load_high_score(self):
        """Load high score from file."""
        try:
            with open('high_score.txt', 'r') as f:
                self.high_score = int(f.read().strip())
        except (FileNotFoundError, ValueError):
            self.high_score = 0
    
    def save_high_score(self):
        """Save high score to file."""
        try:
            with open('high_score.txt', 'w') as f:
                f.write(str(self.high_score))
        except Exception:
            pass  # Silently fail if can't save
    
    def update_high_score(self):
        """Update high score if current score is higher."""
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()

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
            checkpoint_y = level_def["height"] - 140  # Ground level with proper offset
            
            # Check if checkpoint would be over a hole, if so adjust position
            attempts = 0
            while generator.is_position_over_hole(checkpoint_x, checkpoint_y, width=80) and attempts < 10:
                checkpoint_x += 100  # Move right until we find solid ground
                attempts += 1
            
            if attempts < 10:  # Only place if we found a valid position
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
        # Increase jungle level difficulty - add twice as many enemies for stepping stones
        if self.theme.get("name") == "Moss-t Be Joking":
            enemy_count += 8  # Doubled from 4 to 8
        # Make ghost level challenging with lots of ghost enemies
        elif self.theme.get("name") == "Boo Who?":
            enemy_count += 10  # Many ghost enemies for challenge
        # Make ice level extremely hard with no safe ground
        elif self.theme.get("name") == "Frost and Furious":
            enemy_count += 15  # Lots of sky enemies since no safe ground
        # Make computer level challenging with virus worms and special mechanics
        elif self.theme.get("name") == "404: Floor Not Found":
            enemy_count += 8  # Computer virus worms for challenge
        # Make pasta level very hard with lots of ground enemies
        elif self.theme.get("name") == "Pasta La Vista":
            enemy_count += 12  # Lots of ground enemies for challenge
        # Make city level challenging with urban enemies
        elif self.theme.get("name") == "Concrete Jungle":
            enemy_count += 10  # City enemies for challenge
        # Special underwater maze level - different mechanics
        elif self.theme.get("name") == "Kraken Me Up":
            # This level has completely different mechanics - handled separately
            self._create_underwater_maze()
            return  # Skip normal level generation
        # Ultimate challenge level - Neon Night
        elif self.theme.get("name") == "Neon Night":
            enemy_count += 20  # Maximum enemies for ultimate challenge
        rng = random.Random(9000 + self.current_level)
        for _ in range(enemy_count):
            x = rng.randint(300, level_def["width"] - 300)
            # Air enemies spawn higher up
            air_chance = 0.3
            if self.theme.get("name") == "Moss-t Be Joking":
                air_chance = 0.5
            elif self.theme.get("name") == "Smelted Dreams":
                air_chance = 0.45
            elif self.theme.get("name") == "Boo Who?":
                air_chance = 0.7  # Most enemies are ghosts in the sky
            elif self.theme.get("name") == "Frost and Furious":
                air_chance = 0.8  # Most enemies are in the sky (no safe ground!)
            if rng.random() < air_chance:
                y = rng.randint(100, 300)  # Higher up for air enemies
            else:
                y = rng.randint(240, 460)  # Normal ground level
            
            # Weighted selection for enemy types
            if self.theme.get("name") == "Boo Who?":
                # Prefer air enemies (ghosts) for ghost level
                weights = [1, 1, 1, 1, 1, 8, 6]  # Favor air_bat and air_dragon
            elif self.theme.get("name") == "404: Floor Not Found":
                # Prefer ground enemies (virus worms) for computer level
                weights = [6, 5, 4, 3, 2, 1, 1]  # Favor basic, fast, jumper, big enemies
            elif self.theme.get("name") == "Pasta La Vista":
                # Prefer ground enemies for pasta level challenge
                weights = [8, 7, 6, 5, 4, 1, 1]  # Strongly favor ground enemies
            elif self.theme.get("name") == "Concrete Jungle":
                # Prefer air enemies (birds) for city level
                weights = [3, 3, 3, 3, 3, 8, 6]  # Favor air_bat and air_dragon (birds)
            else:
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
        
        # Create exactly one rainbow star on odd levels (1, 3, 5, 7, 9)
        if self.current_level % 2 == 0:  # Odd levels (0-indexed)
            # Choose a random position for the rainbow star
            star_x, star_y = random.choice(powerup_positions)
            rainbow_star = Powerup(star_x, star_y, "rainbow_star")
            self.powerups.add(rainbow_star)
            self.all_sprites.add(rainbow_star)
            
            # Create regular coins for all other positions
            for x, y in powerup_positions:
                if (x, y) != (star_x, star_y):  # Skip the rainbow star position
                    coin = Powerup(x, y, "coin")
                    self.powerups.add(coin)
                    self.all_sprites.add(coin)
        else:
            # On even levels, create only regular coins
            for x, y in powerup_positions:
                coin = Powerup(x, y, "coin")
                self.powerups.add(coin)
                self.all_sprites.add(coin)

        obstacle_positions = []
        rng = random.Random(555 + self.current_level)
        spike_count = 3 + level_def["difficulty"]
        
        # Add more obstacles for ice level (no safe ground!)
        if self.theme.get("name") == "Frost and Furious":
            spike_count += 10  # Many more spikes since entire floor is dangerous
        for _ in range(spike_count):
            # Replace spikes with cheese globs on level 1 (The Big Melt-down)
            if self.theme.get("name") == "The Big Melt-down":
                otype = "cheese_glob"
            elif self.theme.get("name") == "Smelted Dreams" and rng.random() < 0.6:
                otype = "lava_pit"
            elif self.theme.get("name") == "Moss-t Be Joking" and rng.random() < 0.7:
                otype = "rock"
            elif self.theme.get("name") == "Frost and Furious":
                # Mostly ice spikes for frost level - make it extremely dangerous
                otype = "ice_spike" if rng.random() < 0.95 else "spike"
            else:
                otype = "spike"
            x = rng.randint(600, level_def["width"] - 400)
            y = level_def["height"] - 64
            # Check if obstacle would be over a hole
            if not generator.is_position_over_hole(x, y, width=40):
                obstacle_positions.append((x, y, otype))
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
            
            # Add essential starting platform to make level completable
            start_platform = Platform(150, 450, 100, 30, platform_type="tree_block", theme=self.theme)
            self.platforms.add(start_platform)
            self.all_sprites.add(start_platform)
            
            # Add more tree blocks as interactive platforms
            tree_rng = random.Random(5432 + self.current_level)
            tree_count = 8 + level_def["difficulty"] * 2  # More trees for interaction
            for _ in range(tree_count):
                x = tree_rng.randint(400, level_def["width"] - 200)
                y = tree_rng.randint(200, level_def["height"] - 150)
                tree_platform = Platform(x, y, 60, 40, platform_type="tree_block", theme=self.theme)
                self.platforms.add(tree_platform)
                self.all_sprites.add(tree_platform)
            
            # Add more rock blocks as interactive platforms
            rock_rng = random.Random(6543 + self.current_level)
            rock_count = 6 + level_def["difficulty"] * 2  # More rocks for interaction
            for _ in range(rock_count):
                x = rock_rng.randint(500, level_def["width"] - 150)
                y = rock_rng.randint(250, level_def["height"] - 120)
                rock_platform = Platform(x, y, 80, 30, platform_type="rock_block", theme=self.theme)
                self.platforms.add(rock_platform)
                self.all_sprites.add(rock_platform)
        
        # Add rock blocks to Level 3 (Smelted Dreams) as well
        if self.theme.get("name") == "Smelted Dreams":
            rock_rng = random.Random(9876 + self.current_level)
            rock_count = 5 + level_def["difficulty"] * 2  # Rock blocks for metal level
            for _ in range(rock_count):
                x = rock_rng.randint(400, level_def["width"] - 150)
                y = rock_rng.randint(200, level_def["height"] - 120)
                rock_platform = Platform(x, y, 80, 30, platform_type="rock_block", theme=self.theme)
                self.platforms.add(rock_platform)
                self.all_sprites.add(rock_platform)
        
        # Add ice shards covering 100% of the floor for Frost and Furious level
        if self.theme.get("name") == "Frost and Furious":
            ice_rng = random.Random(7654 + self.current_level)
            # Calculate 100% of floor coverage - NO SAFE GROUND!
            floor_width = level_def["width"]
            
            # Add a safe starting platform for the player
            safe_start_platform = Platform(100, level_def["height"] - 100, 120, 30, platform_type="normal", theme=self.theme)
            self.platforms.add(safe_start_platform)
            self.all_sprites.add(safe_start_platform)
            
            # Create DEADLY ice shard obstacles covering the ENTIRE floor
            for x in range(0, floor_width, 40):
                if not generator.is_position_over_hole(x, level_def["height"] - 60, width=40):
                    # Create as deadly obstacle, not platform
                    deadly_ice = Obstacle(x, level_def["height"] - 60, "ice_spike")
                    self.obstacles.add(deadly_ice)
                    self.all_sprites.add(deadly_ice)
            
            # Add floating ice islands for platforms (player must use these!)
            ice_island_count = 12 + level_def["difficulty"] * 2
            for i in range(ice_island_count):
                x = ice_rng.randint(200, level_def["width"] - 200)
                y = ice_rng.randint(150, 400)  # Floating islands at various heights
                # Make some islands larger for easier navigation
                width = ice_rng.choice([80, 120, 160])
                ice_island = Platform(x, y, width, 30, platform_type="ice_shard", theme=self.theme)
                self.platforms.add(ice_island)
                self.all_sprites.add(ice_island)
        
        # Add more fire coverage for lava level (Smelted Dreams)
        if self.theme.get("name") == "Smelted Dreams":
            fire_rng = random.Random(8765 + self.current_level)
            # Add fire obstacles covering more of the floor
            fire_count = 15 + level_def["difficulty"] * 3  # More fire coverage
            for _ in range(fire_count):
                x = fire_rng.randint(400, level_def["width"] - 200)
                y = level_def["height"] - 60  # Floor level
                if not generator.is_position_over_hole(x, y, width=60):
                    fire_obstacle = Obstacle(x, y, "lava_pit")
                    self.obstacles.add(fire_obstacle)
                    self.all_sprites.add(fire_obstacle)
        
        # Add falling cloud platforms for Level 5 (Boo Who?)
        if self.theme.get("name") == "Boo Who?":
            cloud_rng = random.Random(1111 + self.current_level)
            cloud_count = 8 + level_def["difficulty"] * 2  # Falling cloud platforms
            for _ in range(cloud_count):
                x = cloud_rng.randint(300, level_def["width"] - 200)
                y = cloud_rng.randint(150, level_def["height"] - 200)
                cloud_platform = Platform(x, y, 120, 30, platform_type="falling_cloud", theme=self.theme)
                self.platforms.add(cloud_platform)
                self.all_sprites.add(cloud_platform)
        
        # Add large space rocks for Level 5 (Boo Who?)
        if self.theme.get("name") == "Boo Who?":
            rock_rng = random.Random(2222 + self.current_level)
            rock_count = 4 + level_def["difficulty"]  # Large space rocks
            for _ in range(rock_count):
                x = rock_rng.randint(200, level_def["width"] - 250)
                y = rock_rng.randint(200, level_def["height"] - 150)
                # Large rocks - hard to navigate around
                rock_size = rock_rng.choice([(150, 80), (180, 100), (200, 120)])
                space_rock = Platform(x, y, rock_size[0], rock_size[1], platform_type="space_rock", theme=self.theme)
                self.platforms.add(space_rock)
                self.all_sprites.add(space_rock)
        
        # Add moving Tetris platforms for Level 6 (404: Floor Not Found)
        if self.theme.get("name") == "404: Floor Not Found":
            tetris_rng = random.Random(3333 + self.current_level)
            tetris_count = 6 + level_def["difficulty"] * 2  # Moving Tetris platforms
            for _ in range(tetris_count):
                x = tetris_rng.randint(200, level_def["width"] - 200)
                y = tetris_rng.randint(200, level_def["height"] - 200)
                # Different Tetris block shapes
                tetris_shapes = [(80, 40), (120, 30), (60, 60), (100, 50)]
                shape = tetris_rng.choice(tetris_shapes)
                tetris_platform = Platform(x, y, shape[0], shape[1], platform_type="tetris_moving", theme=self.theme)
                self.platforms.add(tetris_platform)
                self.all_sprites.add(tetris_platform)
        
        # Add fading platforms for Level 6 (404: Floor Not Found)
        if self.theme.get("name") == "404: Floor Not Found":
            fade_rng = random.Random(4444 + self.current_level)
            fade_count = 8 + level_def["difficulty"] * 2  # Fading platforms
            for _ in range(fade_count):
                x = fade_rng.randint(300, level_def["width"] - 200)
                y = fade_rng.randint(250, level_def["height"] - 150)
                fade_platform = Platform(x, y, 100, 30, platform_type="fading_platform", theme=self.theme)
                self.platforms.add(fade_platform)
                self.all_sprites.add(fade_platform)
        
        # Add pasta slides and moving platforms for Level 7 (Pasta La Vista)
        if self.theme.get("name") == "Pasta La Vista":
            pasta_rng = random.Random(6666 + self.current_level)
            
            # Add pasta slides (sloped platforms)
            slide_count = 8 + level_def["difficulty"] * 2
            for _ in range(slide_count):
                x = pasta_rng.randint(200, level_def["width"] - 300)
                y = pasta_rng.randint(300, level_def["height"] - 200)
                # Create pasta slide platform
                pasta_slide = Platform(x, y, 150, 40, platform_type="pasta_slide", theme=self.theme)
                self.platforms.add(pasta_slide)
                self.all_sprites.add(pasta_slide)
            
            # Add vertically moving platforms to help escape meatballs
            moving_count = 6 + level_def["difficulty"] * 2
            for _ in range(moving_count):
                x = pasta_rng.randint(300, level_def["width"] - 200)
                y = pasta_rng.randint(250, level_def["height"] - 150)
                # Create vertically moving platforms
                moving_platform = Platform(x, y, 120, 30, platform_type="pasta_moving", theme=self.theme)
                self.platforms.add(moving_platform)
                self.all_sprites.add(moving_platform)
            
            # Add ground gaps (no platforms in certain areas)
            gap_count = 10 + level_def["difficulty"] * 3
            for _ in range(gap_count):
                x = pasta_rng.randint(100, level_def["width"] - 200)
                y = level_def["height"] - 100  # At ground level
                gap_width = pasta_rng.randint(80, 150)
                # Create gap by removing ground in this area
                # This will be handled by modifying the ground platform generation
        
        # Add city-themed obstacles and platforms for Level 8 (Concrete Jungle)
        if self.theme.get("name") == "Concrete Jungle":
            city_rng = random.Random(8888 + self.current_level)
            
            # Add concrete platforms (building ledges)
            concrete_count = 10 + level_def["difficulty"] * 2
            for _ in range(concrete_count):
                x = city_rng.randint(200, level_def["width"] - 200)
                y = city_rng.randint(200, level_def["height"] - 200)
                # Create concrete platform
                concrete_platform = Platform(x, y, 120, 25, platform_type="concrete_platform", theme=self.theme)
                self.platforms.add(concrete_platform)
                self.all_sprites.add(concrete_platform)
            
            # Add fire escapes (ladder-like platforms)
            fire_escape_count = 6 + level_def["difficulty"]
            for _ in range(fire_escape_count):
                x = city_rng.randint(300, level_def["width"] - 300)
                y = city_rng.randint(300, level_def["height"] - 300)
                # Create fire escape platform
                fire_escape = Platform(x, y, 80, 20, platform_type="fire_escape", theme=self.theme)
                self.platforms.add(fire_escape)
                self.all_sprites.add(fire_escape)
        
        # Add 2 firewalls with keys for Level 6 (404: Floor Not Found)
        if self.theme.get("name") == "404: Floor Not Found":
            firewall_rng = random.Random(5555 + self.current_level)
            # Create 2 firewalls at strategic positions
            firewall_positions = [
                (level_def["width"] // 3, level_def["height"] - 100),  # First firewall
                (2 * level_def["width"] // 3, level_def["height"] - 100),  # Second firewall
            ]
            
            for i, (x, y) in enumerate(firewall_positions):
                # Create firewall obstacle
                firewall_color = ["red", "blue"][i]  # Red and blue firewalls
                firewall = Obstacle(x, y, f"firewall_{firewall_color}")
                self.obstacles.add(firewall)
                self.all_sprites.add(firewall)
                
                # Create key enemy near each firewall
                key_enemy_x = x + firewall_rng.randint(-150, 150)
                key_enemy_y = y - firewall_rng.randint(50, 150)
                # Ensure key enemy is within level bounds
                key_enemy_x = max(200, min(level_def["width"] - 200, key_enemy_x))
                key_enemy_y = max(100, min(level_def["height"] - 200, key_enemy_y))
                
                # Create special key enemy (will be drawn as virus worm)
                key_enemy = Enemy(key_enemy_x, key_enemy_y, "key_enemy", theme=self.theme)
                key_enemy.key_color = firewall_color  # Store which key this enemy drops
                self.enemies.add(key_enemy)
                self.all_sprites.add(key_enemy)
        
        # Add giant rolling meatballs for Level 7 (Pasta La Vista)
        if self.theme.get("name") == "Pasta La Vista":
            meatball_rng = random.Random(7777 + self.current_level)
            meatball_count = 3 + level_def["difficulty"]  # 3-6 giant meatballs
            
            for _ in range(meatball_count):
                x = meatball_rng.randint(100, level_def["width"] - 200)
                y = level_def["height"] - 150  # At ground level
                # Create giant rolling meatball
                meatball = Obstacle(x, y, "giant_meatball")
                self.obstacles.add(meatball)
                self.all_sprites.add(meatball)
        
        # Add trains for Level 8 (Concrete Jungle)
        if self.theme.get("name") == "Concrete Jungle":
            train_rng = random.Random(9999 + self.current_level)
            train_count = 2 + level_def["difficulty"]  # 2-5 trains
            
            for _ in range(train_count):
                x = train_rng.randint(50, level_def["width"] - 300)
                y = level_def["height"] - 180  # Train tracks at ground level
                # Create train obstacle
                train = Obstacle(x, y, "city_train")
                self.obstacles.add(train)
                self.all_sprites.add(train)
        
        # Add ultimate challenge features for Level 10 (Neon Night)
        if self.theme.get("name") == "Neon Night":
            neon_rng = random.Random(10101 + self.current_level)
            
            # Add tons of floor spikes everywhere
            spike_count = 50 + level_def["difficulty"] * 10
            for _ in range(spike_count):
                x = neon_rng.randint(50, level_def["width"] - 50)
                y = level_def["height"] - 50  # Floor spikes
                # Create floor spike
                floor_spike = Obstacle(x, y, "floor_spike")
                self.obstacles.add(floor_spike)
                self.all_sprites.add(floor_spike)
            
            # Add falling Tetris pieces from the sky
            tetris_count = 15 + level_def["difficulty"] * 5
            for _ in range(tetris_count):
                x = neon_rng.randint(100, level_def["width"] - 100)
                y = neon_rng.randint(50, 200)  # Start from top
                # Create falling Tetris piece
                falling_tetris = Obstacle(x, y, "falling_tetris")
                self.obstacles.add(falling_tetris)
                self.all_sprites.add(falling_tetris)
            
            # Add neon platforms everywhere
            neon_platform_count = 20 + level_def["difficulty"] * 5
            for _ in range(neon_platform_count):
                x = neon_rng.randint(100, level_def["width"] - 200)
                y = neon_rng.randint(200, level_def["height"] - 200)
                # Create neon platform
                neon_platform = Platform(x, y, 80, 30, platform_type="neon_platform", theme=self.theme)
                self.platforms.add(neon_platform)
                self.all_sprites.add(neon_platform)

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

    def create_bonus_room(self, difficulty=0):
        """Create a simple bonus room with floor, platforms, and a special coin."""
        # Set bonus room dimensions (normal size)
        set_level_dimensions(800, 600)  # Normal sized bonus room
        
        # Update camera with new level dimensions
        self.camera.set_level_dimensions(800, 600)
        
        # Create golden theme for bonus room
        golden_theme = {
            "name": f"Bonus Room {self.current_level + 1}",
            "sky_top": (255, 215, 0),  # Gold
            "sky_bottom": (255, 255, 224),  # Light gold
            "enemy_palette": [(255, 215, 0), (255, 255, 0), (255, 255, 224)],
            "ground_texture": "golden_ground.png",
            "platform_texture": "golden_platform.png",
            "background_image": "bonus_room_bg.png",
            "quirks": "bonus_room"
        }
        
        # Save main level state (before changing theme)
        original_theme = self.theme
        self.saved_level_state = {
            'current_level': self.current_level,
            'lives': self.lives,
            'score': self.score,
            'level_progress': self.level_progress,
            'theme': original_theme,
            'player_pos': (self.player.rect.x, self.player.rect.y) if hasattr(self, 'player') else (100, 400)
        }
        
        # Now change to bonus room theme
        self.theme = golden_theme
        self.bg.set_theme(self.theme)
        
        # Clear existing sprites
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()
        self.powerups.empty()
        self.star_powerups.empty()
        self.plants.empty()
        self.obstacles.empty()
        self.checkpoints.empty()
        self.keys.empty()
        self.npcs.empty()
        self.big_coins.empty()
        
        # Create floor
        floor = Platform(0, 550, 800, 50, platform_type="golden_platform", theme=self.theme)
        self.platforms.add(floor)
        self.all_sprites.add(floor)
        
        # Create platforms based on difficulty
        if difficulty == 0:
            # Level 1 - Simple static platforms
            platform_positions = [
                (200, 450, 100, 20),  # Left platform
                (400, 350, 100, 20),  # Middle platform
                (600, 450, 100, 20),  # Right platform
                (300, 250, 80, 20),   # High left platform
                (500, 250, 80, 20),   # High right platform
            ]
            for x, y, w, h in platform_positions:
                platform = Platform(x, y, w, h, platform_type="golden_platform", theme=self.theme)
                self.platforms.add(platform)
                self.all_sprites.add(platform)
        else:
            # Higher levels - Mix of static and moving platforms
            static_platforms = [
                (200, 450, 80, 20),   # Left platform
                (600, 450, 80, 20),   # Right platform
            ]
            
            for x, y, w, h in static_platforms:
                platform = Platform(x, y, w, h, platform_type="golden_platform", theme=self.theme)
                self.platforms.add(platform)
                self.all_sprites.add(platform)
            
            # Add moving platforms based on difficulty
            if difficulty >= 1:
                # Horizontal moving platform
                moving_h = Platform(350, 350, 100, 20, platform_type="golden_platform", theme=self.theme)
                moving_h.move_offset = 0
                moving_h.original_x = 350
                self.platforms.add(moving_h)
                self.all_sprites.add(moving_h)
            
            if difficulty >= 2:
                # Vertical moving platform
                moving_v = Platform(450, 250, 80, 20, platform_type="golden_platform", theme=self.theme)
                moving_v.move_offset = 0
                moving_v.original_y = 250
                self.platforms.add(moving_v)
                self.all_sprites.add(moving_v)
            
            if difficulty >= 3:
                # Another horizontal moving platform (higher)
                moving_h2 = Platform(250, 200, 120, 20, platform_type="golden_platform", theme=self.theme)
                moving_h2.move_offset = 0
                moving_h2.original_x = 250
                self.platforms.add(moving_h2)
                self.all_sprites.add(moving_h2)
            
            if difficulty >= 4:
                # Fast vertical moving platform
                moving_v2 = Platform(550, 300, 100, 20, platform_type="golden_platform", theme=self.theme)
                moving_v2.move_offset = 0
                moving_v2.original_y = 300
                self.platforms.add(moving_v2)
                self.all_sprites.add(moving_v2)
        
        # Add enemies based on difficulty
        if difficulty >= 2:
            # Level 5+ - Add 1-3 enemies
            enemy_count = min(difficulty, 3)
            for i in range(enemy_count):
                x = 300 + i * 100  # Spread enemies across the room
                y = 400 - i * 50   # Different heights
                enemy = Enemy(x, y, "basic")
                self.enemies.add(enemy)
                self.all_sprites.add(enemy)
        
        # Create the special bonus rainbow star that gives lives and points
        bonus_rainbow_star = Powerup(400, 200, "rainbow_star")  # High up on middle platform
        self.powerups.add(bonus_rainbow_star)
        self.all_sprites.add(bonus_rainbow_star)
        
        # Create player at bottom left
        self.player = Player(100, 500, self.sound_manager)  # Start on floor
        self.all_sprites.add(self.player)
        
        # Position camera normally
        self.camera.x = 0
        self.camera.y = 0
    
    def _return_from_bonus_room(self):
        """Return to the main level from the bonus room."""
        if not hasattr(self, 'saved_level_state'):
            return
        
        # Restore main level state
        saved = self.saved_level_state
        
        # Restore the original level theme and recreate the level
        self.theme = saved['theme']
        self.bg.set_theme(self.theme)
        
        # Set original level dimensions
        level_def = self.levels[saved['current_level']]
        set_level_dimensions(level_def["width"], level_def["height"])
        self.camera.set_level_dimensions(level_def["width"], level_def["height"])
        
        # Recreate the main level
        self.create_level()
        
        # Restore player position
        player_x, player_y = saved['player_pos']
        self.player = Player(player_x, player_y, self.sound_manager)
        self.all_sprites.add(self.player)
        
        # Reset camera
        self.camera.x = 0
        self.camera.y = 0
        
        # Return to playing state
        self.state = GameState.PLAYING
        
        # Clean up saved state
        delattr(self, 'saved_level_state')
    
    def _create_underwater_maze(self):
        """Create the special underwater maze level."""
        # Set maze dimensions
        set_level_dimensions(1000, 800)  # Maze level dimensions
        self.camera.set_level_dimensions(1000, 800)
        
        # Clear existing sprites
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()
        self.powerups.empty()
        self.star_powerups.empty()
        self.plants.empty()
        self.obstacles.empty()
        self.checkpoints.empty()
        self.keys.empty()
        self.npcs.empty()
        self.big_coins.empty()
        
        # Create underwater maze layout
        self._create_maze_walls()
        self._create_maze_coins()
        self._create_maze_enemies()
        self._create_maze_checkpoints()
        
        # Create regular player for bonus room
        self.player = Player(400, 1100, self.sound_manager)  # Use regular Player class
        self.all_sprites.add(self.player)
        
        # Reset camera
        self.camera.x = 0
        self.camera.y = 0
    
    def _create_maze_walls(self):
        """Create maze walls with spiky underwater obstacles."""
        maze_rng = random.Random(1111 + self.current_level)
        
        # Create maze walls (spiky underwater obstacles)
        wall_count = 25 + self.levels[self.current_level]["difficulty"] * 5
        
        for _ in range(wall_count):
            x = maze_rng.randint(50, 950)
            y = maze_rng.randint(50, 750)
            # Create spiky wall obstacle
            spiky_wall = Obstacle(x, y, "spiky_coral")
            self.obstacles.add(spiky_wall)
            self.all_sprites.add(spiky_wall)
    
    def _create_maze_coins(self):
        """Create coins scattered throughout the maze."""
        coin_rng = random.Random(2222 + self.current_level)
        
        # Create lots of coins for collection
        coin_count = 30 + self.levels[self.current_level]["difficulty"] * 10
        
        for _ in range(coin_count):
            x = coin_rng.randint(100, 900)
            y = coin_rng.randint(100, 700)
            # Create underwater coin
            underwater_coin = Powerup(x, y, "underwater_coin")
            self.powerups.add(underwater_coin)
            self.all_sprites.add(underwater_coin)
    
    def _create_maze_enemies(self):
        """Create evil fish enemies that move through the maze."""
        enemy_rng = random.Random(3333 + self.current_level)
        
        # Create evil fish enemies
        fish_count = 8 + self.levels[self.current_level]["difficulty"] * 3
        
        for _ in range(fish_count):
            x = enemy_rng.randint(150, 850)
            y = enemy_rng.randint(150, 650)
            # Create evil fish enemy
            evil_fish = Enemy(x, y, "evil_fish", theme=self.theme)
            self.enemies.add(evil_fish)
            self.all_sprites.add(evil_fish)
    
    def _create_maze_checkpoints(self):
        """Create fish checkpoints in the maze."""
        checkpoint_rng = random.Random(4444 + self.current_level)
        
        # Create 3 fish checkpoints
        checkpoint_positions = [
            (250, 200),  # First checkpoint
            (500, 400),  # Middle checkpoint
            (750, 600),  # Final checkpoint
        ]
        
        for x, y in checkpoint_positions:
            fish_checkpoint = Checkpoint(x, y, self.theme)
            self.checkpoints.add(fish_checkpoint)
            self.all_sprites.add(fish_checkpoint)
    
    def _create_bonus_platforms(self, difficulty):
        """Create vertical platform progression for bonus room."""
        platform_rng = random.Random(7777 + self.current_level)
        
        # Base platforms for vertical progression
        base_y_positions = list(range(1000, 200, -120))  # Every 120 pixels up
        
        for i, y in enumerate(base_y_positions):
            x = 400  # Center horizontally
            
            # Different platform types based on position and difficulty
            if i % 3 == 0:
                # Golden platforms (move vertically)
                platform = Platform(x, y, 120, 30, platform_type="golden_platform", theme=self.theme)
            elif i % 3 == 1:
                # Rainbow platforms (move horizontally)
                platform = Platform(x, y, 100, 25, platform_type="rainbow_platform", theme=self.theme)
            else:
                # Falling cloud platforms (like Boo Who? level)
                platform = Platform(x, y, 80, 20, platform_type="falling_cloud", theme=self.theme)
            
            self.platforms.add(platform)
            self.all_sprites.add(platform)
            
            # Add side platforms for more challenge
            if difficulty > 0 and i % 2 == 0:
                # Left side platform
                left_platform = Platform(x - 200, y - 30, 80, 20, platform_type="golden_platform", theme=self.theme)
                self.platforms.add(left_platform)
                self.all_sprites.add(left_platform)
                
                # Right side platform
                right_platform = Platform(x + 200, y - 30, 80, 20, platform_type="rainbow_platform", theme=self.theme)
                self.platforms.add(right_platform)
                self.all_sprites.add(right_platform)
    
    def _create_bonus_enemies(self, difficulty):
        """Create bonus animal enemies."""
        enemy_rng = random.Random(8888 + self.current_level)
        
        # Number of enemies increases with difficulty
        enemy_count = 3 + difficulty * 2
        
        for _ in range(enemy_count):
            x = enemy_rng.randint(100, 700)
            y = enemy_rng.randint(300, 1000)  # Scattered throughout the vertical space
            
            # Create bonus animal enemy
            animal_enemy = Enemy(x, y, "bonus_animal", theme=self.theme)
            self.enemies.add(animal_enemy)
            self.all_sprites.add(animal_enemy)
    
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
        self.big_coins.empty()
        self.npcs.empty()
        self.last_checkpoint = None
        self.return_from_bonus = None
        # Clear any remaining door state when starting a new game
        # Recreate level for the selected level
        try:
            self.create_level()
            self.player = Player(100, 400, self.sound_manager)
            self.all_sprites.add(self.player)
            self.camera.x = 0
            self.camera.y = 0
        except Exception as e:
            print(f"Error creating level {self.current_level + 1}: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to menu if level creation fails
            self.state = GameState.MENU

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
            self.keys.empty()
            self.last_checkpoint = None
            self.create_level()
            self.player = Player(100, 400, self.sound_manager)
            self.all_sprites.add(self.player)
            self.camera.x = 0
            self.camera.y = 0
            self.state = GameState.PLAYING
        else:
            # All levels complete - update high score and return to menu
            self.update_high_score()
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
        self.big_coins.empty()
        self.npcs.empty()
        self.last_checkpoint = None
        self.return_from_bonus = None
        # Clear accessed doors when restarting
        self.accessed_hidden_doors.clear()
        self.create_level()
        self.player = Player(100, 400, self.sound_manager)
        self.all_sprites.add(self.player)
        self.camera.x = 0
        self.camera.y = 0

    def update(self):
        try:
            if self._needs_initial_load and self.state == GameState.LOADING:
                # Perform heavy setup now that we've shown at least one frame
                self.create_level()
                self.player = Player(100, 400, self.sound_manager)
                self.all_sprites.add(self.player)
                self._needs_initial_load = False
                self.state = GameState.MENU
                return
        except Exception as e:
            print(f"Error during initial load: {e}")
            import traceback
            traceback.print_exc()
            self.state = GameState.MENU
            return
        if self.state == GameState.PLAYING:
            self.camera.update(self.player)
            result = self.player.update(self.platforms, self.enemies, self.powerups, self.obstacles, self.camera.x, self.camera.level_width)
            
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
            
            # Handle rainbow star collection (bonus room trigger)
            if result == "rainbow_star":
                # Rainbow star only transports to bonus room (no points)
                # Trigger bonus room only on odd levels (1, 3, 5, 7, 9) - 0-indexed
                if self.current_level % 2 == 0 and self.current_level < len(self.levels):
                    # Calculate difficulty based on level (Level 9 = hardest)
                    # Level 1 (index 0) -> difficulty 0, Level 3 (index 2) -> difficulty 1, etc.
                    bonus_difficulty = min(self.current_level // 2, 4)  # Max difficulty of 4
                    self.create_bonus_room(bonus_difficulty)
                    self.state = GameState.BONUS_ROOM
                    return
            elif result == "powerup":
                # Regular coin
                self.score += 100
            
                    
                    # Hidden doors no longer trigger bonus rooms - only rainbow stars do
            
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
            elif result == "key_enemy_killed":
                self.score += 100  # Extra points for key enemies
                # Create a key at the enemy location
                for enemy in self.enemies:
                    if hasattr(enemy, 'enemy_type') and enemy.enemy_type == "key_enemy":
                        key = Key(enemy.rect.centerx, enemy.rect.centery, enemy.key_color)
                        self.keys.add(key)
                        self.all_sprites.add(key)
                        break
            elif result == "enemy_damaged":
                self.score += 50  # Half points for damaging but not killing
            
            # Check for key collisions
            key_collisions = pygame.sprite.spritecollide(self.player, self.keys, True)
            for key in key_collisions:
                self.score += 300  # Points for collecting keys
                # Store the key color for firewall unlocking
                if not hasattr(self, 'collected_keys'):
                    self.collected_keys = []
                self.collected_keys.append(key.key_color)
                if self.sound_manager:
                    self.sound_manager.play('coin')  # Use coin sound for key collection
            
            # Check for firewall collisions
            firewall_collisions = pygame.sprite.spritecollide(self.player, self.obstacles, False)
            for firewall in firewall_collisions:
                if firewall.obstacle_type.startswith("firewall_"):
                    firewall_color = firewall.obstacle_type.split("_")[1]
                    if hasattr(self, 'collected_keys') and firewall_color in self.collected_keys:
                        # Remove the key and destroy the firewall
                        self.collected_keys.remove(firewall_color)
                        firewall.kill()
                        if self.sound_manager:
                            self.sound_manager.play('coin')  # Success sound
            
            if self.player.rect.right >= self.camera.level_width - 5:
                self.state = GameState.LEVEL_COMPLETE
            self.enemies.update(self.platforms)
            self.powerups.update()
            self.star_powerups.update()
            self.platforms.update()
            self.keys.update()
        
        elif self.state == GameState.BONUS_ROOM:
            # Vertical bonus room logic - treat it like a normal level
            self.camera.update(self.player)
            result = self.player.update(self.platforms, self.enemies, self.powerups, self.obstacles, self.camera.x, self.camera.level_width)
            
            # Handle player death in bonus room
            if result == "death" or result == "hit":
                self.lives -= 1
                if self.lives <= 0:
                    self.state = GameState.GAME_OVER
                else:
                    # Respawn at bottom of bonus room
                    self.player = Player(400, 1100, self.sound_manager)
                    self.all_sprites.add(self.player)
                    # Position camera to show player
                    self.camera.y = 1100 - self.screen_height + 100
            
            # Handle enemy kills and other interactions
            if result == "enemy_killed":
                self.score += 100
            elif result == "enemy_damaged":
                self.score += 50
            elif result == "rainbow_star":
                # Rainbow star gives lives and points
                self.score += 500
                self.lives += 1
                if self.sound_manager:
                    self.sound_manager.play('coin')
                # Return to main level after collecting rainbow star
                self._return_from_bonus_room()
                return
            elif result == "powerup":
                # Regular coin
                self.score += 100
            
            # Check for big coin collection (at the top)
            big_coin_collisions = pygame.sprite.spritecollide(self.player, self.big_coins, True)
            if big_coin_collisions:
                # Give rewards: 1000 points and 3 hearts
                self.score += 1000
                self.lives += 3
                if self.sound_manager:
                    self.sound_manager.play('coin')
                
                # Return to main level
                self.create_level()  # Recreate the main level
                self.player = Player(100, 400, self.sound_manager)
                self.all_sprites.add(self.player)
                self.camera.x = 0
                self.camera.y = 0
                self.state = GameState.PLAYING
            
            # Update all sprites (same as main game)
            self.enemies.update(self.platforms)
            self.powerups.update()
            self.star_powerups.update()
            self.platforms.update()
            self.keys.update()
            self.npcs.update()
            self.big_coins.update()
            
            # Update moving platforms in bonus room
            for platform in self.platforms:
                if hasattr(platform, 'move_offset') and hasattr(platform, 'original_x'):
                    # Horizontal moving platform
                    platform.move_offset += 0.02
                    platform.rect.x = platform.original_x + int(100 * math.sin(platform.move_offset))
                elif hasattr(platform, 'move_offset') and hasattr(platform, 'original_y'):
                    # Vertical moving platform
                    platform.move_offset += 0.03
                    platform.rect.y = platform.original_y + int(80 * math.sin(platform.move_offset))

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
        elif self.state == GameState.BONUS_ROOM:
            self._draw_bonus_room()
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over()
        elif self.state == GameState.LEVEL_COMPLETE:
            self._draw_level_complete()
        elif self.state == GameState.LEVEL_SELECT:
            self._draw_level_select()
        pygame.display.flip()

    def _draw_menu(self):
        # Draw 3 mice image - FULL SCREEN BACKGROUND
        if hasattr(self, 'mice_image') and self.mice_image is not None:
            self.screen.blit(self.mice_image, (0, 0))
            old_theme = None  # No theme change needed
        else:
            # Fallback to cheese themed background
            cheese_theme = {"sky_top": (248, 240, 202), "sky_bottom": (230, 210, 175), "bg_motif": "cheese"}
            old_theme = self.bg.theme
            self.bg.set_theme(cheese_theme)
            self.bg.draw(self.screen, self.current_level, is_bonus_room=False)
        
        # Semi-transparent overlay for text readability
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(80)
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
        
        # Keyboard instructions
        instructions_y = start_y + 200
        self.ui.draw_bubble_text(self.screen, "Controls:", SCREEN_WIDTH//2, instructions_y, center=True, size=28)
        self.ui.draw_bubble_text(self.screen, "Arrow Keys: Move • SPACE: Jump", SCREEN_WIDTH//2, instructions_y + 35, center=True, size=24)
        self.ui.draw_bubble_text(self.screen, "Down Arrow: Crouch • ESC: Pause", SCREEN_WIDTH//2, instructions_y + 65, center=True, size=24)
        
        # High score display
        if hasattr(self, 'high_score') and self.high_score > 0:
            self.ui.draw_bubble_text(self.screen, f"High Score: {self.high_score:,}", SCREEN_WIDTH//2, SCREEN_HEIGHT - 60, center=True, size=28)
        
        self.ui.draw_bubble_text(self.screen, "Sound effects enabled", SCREEN_WIDTH//2, SCREEN_HEIGHT - 30, center=True, size=24)
        # Restore level theme for gameplay drawing (only if we changed it)
        if old_theme is not None:
            self.bg.set_theme(old_theme)

    def _draw_loading(self):
        # Distinct cheese loading screen with big drips
        cheese_theme = {"sky_top": (248, 240, 202), "sky_bottom": (230, 210, 175), "bg_motif": "cheese"}
        old_theme = self.bg.theme
        self.bg.set_theme(cheese_theme)
        self.bg.draw(self.screen, self.current_level, is_bonus_room=False)
        # Loading text
        self.ui.draw_cheese_title(self.screen, "Loading...", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20, center=True, size=72)
        self.ui.draw_bubble_text(self.screen, "Tip: Holes make the best shortcuts.", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40, center=True, size=28)
        self.bg.set_theme(old_theme)

    def _draw_game(self):
        self.bg.draw(self.screen, self.current_level, is_bonus_room=False)
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
        self.bg.draw(self.screen, self.current_level, is_bonus_room=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Level complete title
        self.ui.draw_cheese_title(self.screen, "Level Complete!!", SCREEN_WIDTH//2, SCREEN_HEIGHT//4, center=True, size=72)
        
        # Show current level info
        level_name = self.theme.get("name", f"Level {self.current_level + 1}")
        self.ui.draw_bubble_text(self.screen, level_name, SCREEN_WIDTH//2, SCREEN_HEIGHT//4 + 60, center=True, size=36)
        
        # Show current score
        self.ui.draw_bubble_text(self.screen, f"Final Score: {self.score:,}", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40, center=True, size=48)
        
        # Continue options
        if self.current_level < len(self.levels) - 1:
            self.ui.draw_bubble_text(self.screen, "Continue?", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20, center=True, size=36)
            self.ui.draw_cheese_button(self.screen, "Next Level (SPACE/ENTER)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80)
            self.ui.draw_cheese_button(self.screen, "Main Menu (M)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 140)
        else:
            # All levels complete!
            self.ui.draw_bubble_text(self.screen, "All Levels Complete!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20, center=True, size=48)
            self.ui.draw_bubble_text(self.screen, "Congratulations!", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80, center=True, size=36)
            self.ui.draw_cheese_button(self.screen, "Main Menu (M)", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 140)
            # Update high score
            self.update_high_score()

    def _draw_game_over(self):
        # Draw rat image - FULL SCREEN BACKGROUND
        if hasattr(self, 'rat_image') and self.rat_image is not None:
            self.screen.blit(self.rat_image, (0, 0))
            old_theme = None  # No theme change needed
        else:
            # Fallback to cheese themed background
            cheese_theme = {"sky_top": (248, 240, 202), "sky_bottom": (230, 210, 175), "bg_motif": "cheese"}
            old_theme = self.bg.theme
            self.bg.set_theme(cheese_theme)
            self.bg.draw(self.screen, self.current_level, is_bonus_room=False)
        
        # Semi-transparent overlay for text readability
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(120)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        self.ui.draw_cheese_title(self.screen, "Game Over", SCREEN_WIDTH//2, SCREEN_HEIGHT//3, center=True, size=96)
        
        # Stats
        self.ui.draw_bubble_text(self.screen, f"Final Score: {self.score}", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20, center=True, size=48)
        self.ui.draw_bubble_text(self.screen, f"Level Reached: {self.level_progress + 1}", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60, center=True, size=32)
        # Cheese buttons
        base_y = SCREEN_HEIGHT//2 + 110
        self.ui.draw_cheese_button(self.screen, "Restart (R/SPACE)", SCREEN_WIDTH//2, base_y)
        self.ui.draw_cheese_button(self.screen, "Main Menu (M)", SCREEN_WIDTH//2, base_y + 60)
        self.ui.draw_cheese_button(self.screen, "ESC to Quit", SCREEN_WIDTH//2, base_y + 120)
        # Restore theme (only if we changed it)
        if old_theme is not None:
            self.bg.set_theme(old_theme)

    def _draw_bonus_room(self):
        # Use unicorn background for bonus rooms
        bonus_theme = {"name": "bonus_room", "sky_top": (255, 240, 180), "sky_bottom": (255, 220, 140)}
        old_theme = self.bg.theme
        self.bg.set_theme(bonus_theme)
        self.bg.draw(self.screen, 0, is_bonus_room=True)
        
        # Draw all sprites
        for sprite in self.all_sprites:
            screen_x = sprite.rect.x - self.camera.x
            screen_y = sprite.rect.y - self.camera.y
            if (-sprite.rect.width < screen_x < SCREEN_WIDTH and -sprite.rect.height < screen_y < SCREEN_HEIGHT):
                self.screen.blit(sprite.image, (screen_x, screen_y))
        
        # Draw HUD
        for i in range(self.lives):
            self.ui.draw_heart(self.screen, 14 + i * 28, 18, 10, SOFT_PINK, BLACK)
        panel_rect = pygame.Rect(10, 44, 200, 40)
        pygame.draw.rect(self.screen, SOFT_YELLOW, panel_rect)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)
        self.ui.draw_bubble_text(self.screen, f"Score: {self.score}", panel_rect.left + 10, panel_rect.centery, center=False, size=28, max_width=panel_rect.width - 20)
        
        # Bonus room title
        self.ui.draw_cheese_title(self.screen, "BONUS ROOM!", SCREEN_WIDTH//2, 80, center=True, size=72)
        
        self.bg.set_theme(old_theme)
    
    def _draw_level_select(self):
        # Draw pocket rat image - FULL SCREEN BACKGROUND
        if hasattr(self, 'pocket_rat_image') and self.pocket_rat_image is not None:
            self.screen.blit(self.pocket_rat_image, (0, 0))
            old_theme = None  # No theme change needed
        else:
            # Fallback to cheese themed background
            cheese_theme = {"sky_top": (248, 240, 202), "sky_bottom": (230, 210, 175), "bg_motif": "cheese"}
            old_theme = self.bg.theme
            self.bg.set_theme(cheese_theme)
            self.bg.draw(self.screen, self.current_level, is_bonus_room=False)
        
        # Semi-transparent overlay for text readability
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(100)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        self.ui.draw_cheese_title(self.screen, "Select Level", SCREEN_WIDTH//2, 90, center=True, size=84)
        
        top = 180
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
        # Restore theme (only if we changed it)
        if old_theme is not None:
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


if __name__ == "__main__":
    run_game()
