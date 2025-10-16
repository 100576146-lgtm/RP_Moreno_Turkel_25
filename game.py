"""Main game loop and level orchestration for Rat Race.

This module contains the primary `Game` class, responsible for:
- Loading themes/levels and building their content
- Creating and updating sprites (player, platforms, enemies, obstacles, powerups)
- Handling game states (menu, playing, bonus room, level complete, game over)
- Drawing frames and handling input

See README for how to run the game. For a quick start, run `python3 mario_platformer.py`.
"""

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
    """Top-level game controller.

    Manages lifecycle (start, restart, advance), state transitions, content
    creation for each themed level, player instantiation, and rendering.
    """
    def __init__(self, fullscreen=False):
        if fullscreen:
            self.screen = pygame.display.set_mode((FULLSCREEN_WIDTH, FULLSCREEN_HEIGHT), pygame.FULLSCREEN)
            self.screen_width = FULLSCREEN_WIDTH
            self.screen_height = FULLSCREEN_HEIGHT
            self.fullscreen = True
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
            self.screen_width = SCREEN_WIDTH
            self.screen_height = SCREEN_HEIGHT
            self.fullscreen = False
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
        
        # Reset Geometry Dash mode for non-Geometry Dash levels
        if not (self.theme.get("name") == "404: Floor Not Found"):
            self.geometry_dash_mode = False
            self.player_speed_multiplier = 1.0
            self.countdown_active = False
        
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
        # Skip checkpoints for Level 6 (Geometry Dash - 404: Floor Not Found)
        if self.theme.get("name") != "404: Floor Not Found":
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
            enemy_count += 20  # Many enemies to make Level 5 very hard
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
        
        # Add extra floor enemies specifically for Level 2 (Moss-t Be Joking)
        if self.theme.get("name") == "Moss-t Be Joking":
            floor_enemy_rng = random.Random(1234 + self.current_level)
            # Add 8-12 additional enemies on the floor for more challenge
            floor_enemy_count = 8 + level_def["difficulty"] * 2
            for _ in range(floor_enemy_count):
                x = floor_enemy_rng.randint(400, level_def["width"] - 400)
                y = level_def["height"] - 64  # Floor level
                # Prefer ground-based enemy types for floor placement
                floor_enemy_types = ["basic", "fast", "jumper", "big"]
                etype = floor_enemy_rng.choice(floor_enemy_types)
                floor_enemy = Enemy(x, y, etype, theme=self.theme)
                self.enemies.add(floor_enemy)
                self.all_sprites.add(floor_enemy)
        
        # Add many strategic enemies for Level 5 (Boo Who?) to make it very challenging
        if self.theme.get("name") == "Boo Who?":
            strategic_enemy_rng = random.Random(7777 + self.current_level)
            # Add many enemies at strategic heights for maximum challenge
            strategic_enemy_count = 8 + level_def["difficulty"] * 3  # Many enemies for hard level
            for _ in range(strategic_enemy_count):
                x = strategic_enemy_rng.randint(200, level_def["width"] - 200)
                y = strategic_enemy_rng.randint(100, level_def["height"] - 250)
                # Use a mix of air enemies for maximum challenge
                enemy_types = ["air_bat", "air_dragon", "jumper"]
                etype = strategic_enemy_rng.choice(enemy_types)
                strategic_enemy = Enemy(x, y, etype, theme=self.theme)
                self.enemies.add(strategic_enemy)
                self.all_sprites.add(strategic_enemy)

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
        
        # Add moving cloud platforms for Level 5 (Boo Who?)
        if self.theme.get("name") == "Boo Who?":
            cloud_rng = random.Random(1111 + self.current_level)
            cloud_count = 6 + level_def["difficulty"]  # Reasonable amount of moving platforms
            for _ in range(cloud_count):
                x = cloud_rng.randint(300, level_def["width"] - 200)
                y = cloud_rng.randint(200, level_def["height"] - 200)
                cloud_platform = Platform(x, y, 120, 30, platform_type="moving", theme=self.theme)
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
            
            # Add spiky platforms that kill the player
            spiky_rng = random.Random(3333 + self.current_level)
            spiky_count = 4 + level_def["difficulty"]  # Reasonable amount of spiky platforms
            for _ in range(spiky_count):
                x = spiky_rng.randint(250, level_def["width"] - 250)
                y = spiky_rng.randint(200, level_def["height"] - 200)
                # Create spiky platform that kills player
                spiky_platform = Platform(x, y, 100, 30, platform_type="spiky_platform", theme=self.theme)
                self.platforms.add(spiky_platform)
                self.all_sprites.add(spiky_platform)
            
            # Add a few vertical moving platforms for Level 5
            vertical_rng = random.Random(4444 + self.current_level)
            vertical_count = 3 + level_def["difficulty"]  # Small amount of vertical platforms
            for _ in range(vertical_count):
                x = vertical_rng.randint(300, level_def["width"] - 300)
                y = vertical_rng.randint(200, level_def["height"] - 250)
                # Create vertically moving platform
                vertical_platform = Platform(x, y, 120, 25, platform_type="vertical_moving", theme=self.theme)
                self.platforms.add(vertical_platform)
                self.all_sprites.add(vertical_platform)
        
        # Create Geometry Dash-style Level 6 (404: Floor Not Found)
        if self.theme.get("name") == "404: Floor Not Found":
            self._create_geometry_dash_level()
            return  # Skip normal enemy generation for Geometry Dash level
        
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
            
            # Add tons of floor spikes everywhere, but keep spawn area safe
            spike_count = 50 + level_def["difficulty"] * 10
            spawn_safe_zone = 400  # keep first 400px free of floor spikes
            for _ in range(spike_count):
                x = neon_rng.randint(50, level_def["width"] - 50)
                # Skip spikes near initial spawn
                if x < spawn_safe_zone + 100:
                    continue
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
            
            # Add neon platforms with reachability checks
            from constants import SAFE_JUMP_HEIGHT
            neon_platform_count = 20 + level_def["difficulty"] * 5
            placed_neon_platforms = []
            max_horizontal_gap = 250  # Maximum horizontal distance between platforms
            
            for i in range(neon_platform_count):
                attempts = 0
                placed = False
                
                while attempts < 30 and not placed:
                    attempts += 1
                    x = neon_rng.randint(100, level_def["width"] - 200)
                    y = neon_rng.randint(200, level_def["height"] - 200)
                    
                    # First platform or check if reachable from any existing platform
                    if not placed_neon_platforms:
                        # First platform should be near ground
                        y = max(y, level_def["height"] - SAFE_JUMP_HEIGHT - 50)
                        placed = True
                    else:
                        # Check if reachable from at least one existing platform
                        for px, py in placed_neon_platforms:
                            horiz_dist = abs(x - px)
                            vert_dist = abs(y - py)
                            
                            # Check if within jump range
                            if horiz_dist <= max_horizontal_gap and vert_dist <= SAFE_JUMP_HEIGHT - 20:
                                placed = True
                                break
                
                # If couldn't place after attempts, force placement near last platform
                if not placed and placed_neon_platforms:
                    last_x, last_y = placed_neon_platforms[-1]
                    x = last_x + neon_rng.randint(150, 220)
                    if x > level_def["width"] - 200:
                        x = last_x - neon_rng.randint(150, 220)
                    y = last_y + neon_rng.randint(-80, 80)
                    y = max(200, min(level_def["height"] - 200, y))
                
                # Create neon platform
                neon_platform = Platform(x, y, 80, 30, platform_type="neon_platform", theme=self.theme)
                self.platforms.add(neon_platform)
                self.all_sprites.add(neon_platform)
                placed_neon_platforms.append((x, y))

        # Create one star powerup in an accessible but challenging location
        star_pos = generator.find_accessible_star_position()
        star_powerup = StarPowerup(star_pos['x'], star_pos['y'])
        self.star_powerups.add(star_powerup)
        self.all_sprites.add(star_powerup)
        

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    self.resize_screen(event.w, event.h)
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
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
            self.screen_width = SCREEN_WIDTH
            self.screen_height = SCREEN_HEIGHT
            self.fullscreen = False
        else:
            # Switch to fullscreen
            self.screen = pygame.display.set_mode((FULLSCREEN_WIDTH, FULLSCREEN_HEIGHT), pygame.FULLSCREEN)
            self.screen_width = FULLSCREEN_WIDTH
            self.screen_height = FULLSCREEN_HEIGHT
            self.fullscreen = True
        
        # Update components with new screen dimensions
        self._update_components_for_resize()
    
    def resize_screen(self, width, height):
        """Handle window resize event."""
        # Set minimum dimensions to prevent too small windows
        min_width, min_height = 640, 480
        width = max(width, min_width)
        height = max(height, min_height)
        
        # Update screen
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.screen_width = width
        self.screen_height = height
        
        # Update components with new screen dimensions
        self._update_components_for_resize()
    
    def _update_components_for_resize(self):
        """Update all components that depend on screen dimensions."""
        # Update camera
        self.camera.set_screen_dimensions(self.screen_width, self.screen_height)
        
        # Update background (clear cache to force regeneration)
        self.bg.set_screen_dimensions(self.screen_width, self.screen_height)
        
        # Update UI
        self.ui.set_screen_dimensions(self.screen_width, self.screen_height)
        
        # Reload mouse images with new screen dimensions
        self._load_mouse_images()

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
        
        # Add enemies based on difficulty (skip for Level 7's secret room)
        if difficulty >= 2 and self.current_level != 6:
            # Level 5+ - Add 1-3 enemies
            enemy_count = min(difficulty, 3)
            for i in range(enemy_count):
                x = 300 + i * 100  # Spread enemies across the room
                y = 400 - i * 50   # Different heights
                enemy = Enemy(x, y, "basic", theme=self.theme)
                self.enemies.add(enemy)
                self.all_sprites.add(enemy)
        
        # Create blue star in bonus room worth 500 points and 1 extra heart
        blue_star = Powerup(400, 200, "blue_star")  # High up on middle platform
        self.powerups.add(blue_star)
        self.all_sprites.add(blue_star)
        
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
    
    def _create_geometry_dash_level(self):
        """Create a high-speed speedrun level with ground obstacles and wall of death."""
        level_def = self.levels[self.current_level]
        
        # Clear existing enemies for speedrun level
        self.enemies.empty()
        
        # Make level extra long for speedrun
        level_width = level_def["width"] * 2
        level_def["width"] = level_width
        
        # Update level dimensions for enemies to work properly
        set_level_dimensions(level_width, level_def["height"])
        self.camera.set_level_dimensions(level_width, level_def["height"])
        
        # Create solid ground floor for running with reachability checks
        ground_y = level_def["height"] - 40
        platforms_list = []
        for x in range(0, level_width, 200):
            ground_platform = Platform(x, ground_y, 200, 40, platform_type="ground", theme=self.theme)
            platforms_list.append(ground_platform)
            self.platforms.add(ground_platform)
            self.all_sprites.add(ground_platform)
        
        # Verify platform reachability (check if platforms are within jump height)
        from constants import SAFE_JUMP_HEIGHT
        for i in range(len(platforms_list) - 1):
            current_plat = platforms_list[i]
            next_plat = platforms_list[i + 1]
            vertical_distance = abs(next_plat.rect.y - current_plat.rect.y)
            horizontal_distance = abs(next_plat.rect.x - (current_plat.rect.x + current_plat.rect.width))
            
            # If platform is unreachable, adjust it or add intermediate platform
            if vertical_distance > SAFE_JUMP_HEIGHT - 20:
                # Adjust next platform to be reachable
                if next_plat.rect.y < current_plat.rect.y:
                    # Platform is above, lower it to be reachable
                    next_plat.rect.y = current_plat.rect.y - (SAFE_JUMP_HEIGHT - 30)
        
        # Add ground-level obstacles (spikes) optimized for high-speed gameplay
        spike_positions = []
        spawn_safe_zone = 400  # Safe spawn area
        
        # Create spike patterns that are jumpable at high speed
        # Rhythm: groups of spikes with consistent gaps
        spike_x = spawn_safe_zone
        pattern_index = 0
        
        # Define spike patterns for variety
        patterns = [
            # Pattern 0: Single spike with gap
            [(0, 0)],
            # Pattern 1: Double spike with gap
            [(0, 0), (60, 0)],
            # Pattern 2: Triple spike with gap
            [(0, 0), (60, 0), (120, 0)],
            # Pattern 3: Wide double with gap
            [(0, 0), (100, 0)],
        ]
        
        while spike_x < level_width - 200:
            # Select pattern
            pattern = patterns[pattern_index % len(patterns)]
            
            # Place spikes according to pattern
            for offset_x, offset_y in pattern:
                if spike_x + offset_x < level_width - 100:
                    spike_y = ground_y - 30 + offset_y  # Spikes on ground
                    spike_positions.append((spike_x + offset_x, spike_y))
            
            # Gap between patterns (200-250 pixels for high-speed jumping)
            gap_size = 200 + (spike_x // 1000) % 50
            spike_x += max([p[0] for p in pattern]) + 60 + gap_size
            pattern_index += 1
        
        # Create spike obstacles
        for x, y in spike_positions:
            spike_obstacle = Obstacle(x, y, "spike")
            self.obstacles.add(spike_obstacle)
            self.all_sprites.add(spike_obstacle)
        
        # Add enemies for additional challenge
        enemy_rng = random.Random(6000 + self.current_level)
        enemy_count = 15  # Moderate number of enemies for level 6
        for i in range(enemy_count):
            # Place enemies throughout the level
            x = enemy_rng.randint(spawn_safe_zone + 200, level_width - 300)
            y = ground_y - 50  # Slightly above ground
            enemy_type = enemy_rng.choice(["basic", "fast", "jumper"])
            enemy = Enemy(x, y, enemy_type, theme=self.theme)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)
        
        # Store level properties for speedrun mechanics
        self.geometry_dash_mode = True
        self.spike_wall_x = 0  # Starting position of wall of death
        self.spike_wall_speed = 2.4  # Doubled speed for more intense challenge (was 1.2)
        self.player_speed_multiplier = 0.6  # Reduced by 70% (30% of 2.0)
        self.countdown_timer = 180  # 3 seconds countdown at 60 FPS
        self.countdown_active = True  # Countdown active initially
        
        # Warning sign at spawn
        self.run_sign_x = 350
        self.run_sign_y = ground_y - 100
        self.computer_warning_text = "RUN!"
        
        # Spawn position on ground
        self.geometry_dash_spawn_x = 150
        self.geometry_dash_spawn_y = ground_y - 60  # On ground (60 is player height)
        
        print(f"Speedrun Level 6 created: {level_width} pixels wide, wall of death at {self.spike_wall_speed}x speed!")
    
    def _create_underwater_maze(self):
        """Create an underwater scrolling level (Level 9: Kraken Me Up)."""
        import random
        level_def = self.levels[self.current_level]
        width = level_def["width"]
        height = level_def["height"]

        # Use level 9 dimensions
        set_level_dimensions(width, height)
        self.camera.set_level_dimensions(width, height)

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

        # Sea floor
        ground_y = height - 40
        for x in range(0, width, 200):
            floor_segment = Platform(x, ground_y, 200, 40, platform_type="ground", theme=self.theme)
            self.platforms.add(floor_segment)
            self.all_sprites.add(floor_segment)

        # Floating underwater platforms (some moving) - fewer and spaced out
        rng = random.Random(9090 + self.current_level)
        segment = width // 8  # Fewer segments for wider spacing
        placed_platforms = []  # Track placed platforms to enforce spacing
        min_dx, min_dy = 160, 110  # Minimum gaps so the character fits between
        for s in range(1, 8):
            base_x = s * segment
            count = 2 + (level_def["difficulty"] // 3)
            attempts = 0
            made = 0
            max_attempts = count * 6
            while made < count and attempts < max_attempts:
                attempts += 1
                x = base_x + rng.randint(-220, -40)
                y = rng.randint(160, height - 200)
                w = rng.choice([120, 140, 160])
                h = 20
                # Enforce spacing from already placed platforms
                too_close = False
                for px, py, pw, ph in placed_platforms:
                    if abs(x - px) < min_dx and abs(y - py) < min_dy:
                        too_close = True
                        break
                if too_close:
                    continue
                ptype = rng.choice(["normal", "vertical_moving", "normal"])  # Bias to normal
                # Make all non-vertical platforms move horizontally
                effective_type = "vertical_moving" if ptype == "vertical_moving" else "moving"
                plat = Platform(x, y, w, h, platform_type=effective_type, theme=self.theme)
                if effective_type == "vertical_moving":
                    plat.original_y = y
                else:
                    plat.original_x = x
                plat.move_offset = 0
                self.platforms.add(plat)
                self.all_sprites.add(plat)
                placed_platforms.append((x, y, w, h))

        # Reduced scatter pass: fewer extra platforms with spacing
        chaos_rng = random.Random(9091 + self.current_level)
        chaos_count = 28 + level_def["difficulty"] * 6
        attempts = 0
        max_attempts = chaos_count * 8
        added = 0
        while added < chaos_count and attempts < max_attempts:
            attempts += 1
            x = chaos_rng.randint(240, width - 260)
            y = chaos_rng.randint(140, height - 220)
            w = chaos_rng.choice([80, 100, 120])
            h = 18
            too_close = False
            for px, py, pw, ph in placed_platforms:
                if abs(x - px) < min_dx and abs(y - py) < min_dy:
                    too_close = True
                    break
            if too_close:
                continue
            effective_type = "vertical_moving" if chaos_rng.random() < 0.15 else "moving"
            plat = Platform(x, y, w, h, platform_type=effective_type, theme=self.theme)
            if effective_type == "vertical_moving":
                plat.original_y = y
            else:
                plat.original_x = x
            plat.move_offset = 0
            self.platforms.add(plat)
            self.all_sprites.add(plat)
            placed_platforms.append((x, y, w, h))
            added += 1

        # Spiky corals along the floor and occasional ceiling
        coral_rng = random.Random(9191 + self.current_level)
        coral_spacing = 240
        spawn_safe_zone = 400
        for x in range(spawn_safe_zone + 200, width - 100, coral_spacing):
            if coral_rng.random() < 0.85:
                coral = Obstacle(x, ground_y - 30, "spiky_coral")
                self.obstacles.add(coral)
                self.all_sprites.add(coral)
            # Rare ceiling coral for challenge
            if coral_rng.random() < 0.25:
                coral_top = Obstacle(x + 100, 70, "spiky_coral")
                self.obstacles.add(coral_top)
                self.all_sprites.add(coral_top)

        # Coins for guidance
        coin_rng = random.Random(9292 + self.current_level)
        for s in range(2, 10):
            cx = s * segment - 100
            cy = coin_rng.randint(160, height - 220)
            coin = Powerup(cx, cy, "coin")
            self.powerups.add(coin)
            self.all_sprites.add(coin)

        # Evil fish enemies, avoid spawn safe zone
        fish_rng = random.Random(9393 + self.current_level)
        fish_count = 10 + level_def["difficulty"] * 2
        safe_x = 100
        safe_y = ground_y - 120
        safe_radius = 200
        for _ in range(fish_count):
            attempts = 0
            while attempts < 40:
                ex = fish_rng.randint(spawn_safe_zone + 200, width - 200)
                ey = fish_rng.randint(140, height - 220)
                dx = ex - safe_x
                dy = ey - safe_y
                if (dx * dx + dy * dy) ** 0.5 >= safe_radius:
                    break
                attempts += 1
            evil_fish = Enemy(ex, ey, "evil_fish", theme=self.theme)
            self.enemies.add(evil_fish)
            self.all_sprites.add(evil_fish)

        # Three checkpoints along the way
        checkpoint_count = 3
        spacing = width // (checkpoint_count + 1)
        for i in range(1, checkpoint_count + 1):
            cx = spacing * i
            cy = ground_y - 100
            checkpoint = Checkpoint(cx, cy, theme=self.theme)
            self.checkpoints.add(checkpoint)
            self.all_sprites.add(checkpoint)

        # Safe spawn near start
        self.geometry_dash_spawn_x = 100
        self.geometry_dash_spawn_y = ground_y - 120

        # Reset camera
        self.camera.x = 0
        self.camera.y = 0
    
    def _create_maze_walls(self):
        """Create maze walls with spiky underwater obstacles."""
        maze_rng = random.Random(1111 + self.current_level)
        
        # Create maze walls (spiky underwater obstacles)
        wall_count = 25 + self.levels[self.current_level]["difficulty"] * 5
        
        # Define safe spawn zone (player spawns at 400, 100)
        spawn_safe_x = 400
        spawn_safe_y = 100
        safe_radius = 150  # Keep obstacles at least 150 pixels away from spawn
        
        for _ in range(wall_count):
            # Keep trying until we find a position outside the safe zone
            attempts = 0
            while attempts < 50:  # Prevent infinite loop
                x = maze_rng.randint(50, 950)
                y = maze_rng.randint(50, 750)
                
                # Check if position is outside safe zone
                distance = ((x - spawn_safe_x)**2 + (y - spawn_safe_y)**2)**0.5
                if distance >= safe_radius:
                    break
                attempts += 1
            
            # Only create obstacle if we found a safe position
            if attempts < 50:
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
            # Create underwater coin (using regular coin type)
            underwater_coin = Powerup(x, y, "coin")
            self.powerups.add(underwater_coin)
            self.all_sprites.add(underwater_coin)
    
    def _create_maze_enemies(self):
        """Create evil fish enemies that move through the maze."""
        enemy_rng = random.Random(3333 + self.current_level)
        
        # Create evil fish enemies
        fish_count = 8 + self.levels[self.current_level]["difficulty"] * 3
        
        # Define safe spawn zone (player spawns at 400, 100)
        spawn_safe_x = 400
        spawn_safe_y = 100
        safe_radius = 150  # Keep enemies at least 150 pixels away from spawn
        
        for _ in range(fish_count):
            # Keep trying until we find a position outside the safe zone
            attempts = 0
            while attempts < 50:  # Prevent infinite loop
                x = enemy_rng.randint(150, 850)
                y = enemy_rng.randint(150, 650)
                
                # Check if position is outside safe zone
                distance = ((x - spawn_safe_x)**2 + (y - spawn_safe_y)**2)**0.5
                if distance >= safe_radius:
                    break
                attempts += 1
            
            # Only create enemy if we found a safe position
            if attempts < 50:
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
                # Moving platforms (like Boo Who? level)
                platform = Platform(x, y, 80, 20, platform_type="moving", theme=self.theme)
            
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
            # Create player with speed multiplier for Geometry Dash mode
            speed_multiplier = getattr(self, 'player_speed_multiplier', 1.0)
            # Level 10 gets 5% higher jump
            jump_multiplier = 1.05 if self.current_level == 9 else 1.0
            # Use special spawn position for Geometry Dash level
            if hasattr(self, 'geometry_dash_spawn_x') and hasattr(self, 'geometry_dash_spawn_y'):
                spawn_x, spawn_y = self.geometry_dash_spawn_x, self.geometry_dash_spawn_y
            else:
                spawn_x, spawn_y = 100, 400
            self.player = Player(spawn_x, spawn_y, self.sound_manager, speed_multiplier, jump_multiplier)
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
        # Create player with speed multiplier and honor special spawn if provided
        speed_multiplier = getattr(self, 'player_speed_multiplier', 1.0)
        # Level 10 gets 5% higher jump
        jump_multiplier = 1.05 if self.current_level == 9 else 1.0
        if hasattr(self, 'geometry_dash_spawn_x') and hasattr(self, 'geometry_dash_spawn_y'):
            spawn_x, spawn_y = self.geometry_dash_spawn_x, self.geometry_dash_spawn_y
        else:
            spawn_x, spawn_y = 100, 400
        self.player = Player(spawn_x, spawn_y, self.sound_manager, speed_multiplier, jump_multiplier)
        self.all_sprites.add(self.player)
        self.camera.x = 0
        self.camera.y = 0
        self.state = GameState.PLAYING

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
        self.create_level()
        # Create player with speed multiplier for Geometry Dash mode
        speed_multiplier = getattr(self, 'player_speed_multiplier', 1.0)
        # Level 10 gets 5% higher jump
        jump_multiplier = 1.05 if self.current_level == 9 else 1.0
        # Use special spawn position for Geometry Dash level
        if hasattr(self, 'geometry_dash_spawn_x') and hasattr(self, 'geometry_dash_spawn_y'):
            spawn_x, spawn_y = self.geometry_dash_spawn_x, self.geometry_dash_spawn_y
        else:
            spawn_x, spawn_y = 100, 400
        self.player = Player(spawn_x, spawn_y, self.sound_manager, speed_multiplier, jump_multiplier)
        self.all_sprites.add(self.player)
        self.camera.x = 0
        self.camera.y = 0

    def update(self):
        try:
            if self._needs_initial_load and self.state == GameState.LOADING:
                # Perform heavy setup now that we've shown at least one frame
                self.create_level()
                # Create player with speed multiplier for Geometry Dash mode
                speed_multiplier = getattr(self, 'player_speed_multiplier', 1.0)
                # Level 10 gets 5% higher jump
                jump_multiplier = 1.05 if self.current_level == 9 else 1.0
                # Use special spawn position for Geometry Dash level
                if hasattr(self, 'geometry_dash_spawn_x') and hasattr(self, 'geometry_dash_spawn_y'):
                    spawn_x, spawn_y = self.geometry_dash_spawn_x, self.geometry_dash_spawn_y
                else:
                    spawn_x, spawn_y = 100, 400
                self.player = Player(spawn_x, spawn_y, self.sound_manager, speed_multiplier, jump_multiplier)
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
            
            # Handle Geometry Dash spike wall mechanics
            if hasattr(self, 'geometry_dash_mode') and self.geometry_dash_mode:
                # Handle course vertical movement
                if hasattr(self, 'course_vertical_offset'):
                    self.course_vertical_offset += self.course_vertical_speed * self.course_vertical_direction
                    
                    # Reverse direction when hitting limits
                    if self.course_vertical_offset > self.course_vertical_range:
                        self.course_vertical_direction = -1
                    elif self.course_vertical_offset < -self.course_vertical_range:
                        self.course_vertical_direction = 1
                    
                    # Move all platforms and obstacles vertically
                    for platform in self.platforms:
                        platform.rect.y += int(self.course_vertical_speed * self.course_vertical_direction)
                    for obstacle in self.obstacles:
                        obstacle.rect.y += int(self.course_vertical_speed * self.course_vertical_direction)
                
                # Handle countdown timer
                if hasattr(self, 'countdown_active') and self.countdown_active:
                    self.countdown_timer -= 1
                    if self.countdown_timer <= 0:
                        self.countdown_active = False
                        print("COUNTDOWN OVER! Spike wall is now moving!")
                
                # Only move spike wall after countdown is over
                if hasattr(self, 'countdown_active') and not self.countdown_active:
                    # Move spike wall closer to player
                    self.spike_wall_x += self.spike_wall_speed
                    
                    # Check if spike wall caught up to player
                    if self.spike_wall_x >= self.player.rect.x - 50:
                        # Player is caught by spike wall - death
                        result = "hit"
                    else:
                        result = self.player.update(self.platforms, self.enemies, self.powerups, self.obstacles, self.camera.x, self.camera.level_width)
                else:
                    # During countdown, normal player movement
                    result = self.player.update(self.platforms, self.enemies, self.powerups, self.obstacles, self.camera.x, self.camera.level_width)
            else:
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
                        # Use special spawn position for Geometry Dash level
                        if hasattr(self, 'geometry_dash_spawn_x') and hasattr(self, 'geometry_dash_spawn_y'):
                            respawn_x = self.geometry_dash_spawn_x
                            respawn_y = self.geometry_dash_spawn_y
                        else:
                            respawn_x = 100
                            respawn_y = 400
                        self.player.respawn(respawn_x, respawn_y)
                    
                    # Reset Geometry Dash mechanics on respawn
                    if hasattr(self, 'geometry_dash_mode') and self.geometry_dash_mode:
                        self.spike_wall_x = 0  # Reset wall position
                        self.countdown_timer = 180  # Reset countdown
                        self.countdown_active = True  # Restart countdown
                        print("RESPAWN: Spike wall reset, countdown restarted!")
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
            elif result == "blue_star":
                # Blue star gives 500 points and 1 extra heart, then transports back to main level
                self.score += 500
                self.lives += 1
                if self.sound_manager:
                    self.sound_manager.play('coin')
                # Transport back to original level after collecting blue star
                self._return_from_bonus_room()
                return
            elif result == "powerup":
                # Regular coin in bonus room
                self.score += 100
                if self.sound_manager:
                    self.sound_manager.play('coin')
            
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
                # Create player with speed multiplier for Geometry Dash mode
                speed_multiplier = getattr(self, 'player_speed_multiplier', 1.0)
                # Level 10 gets 5% higher jump
                jump_multiplier = 1.05 if self.current_level == 9 else 1.0
                # Use special spawn position for Geometry Dash level
                if hasattr(self, 'geometry_dash_spawn_x') and hasattr(self, 'geometry_dash_spawn_y'):
                    spawn_x, spawn_y = self.geometry_dash_spawn_x, self.geometry_dash_spawn_y
                else:
                    spawn_x, spawn_y = 100, 400
                self.player = Player(spawn_x, spawn_y, self.sound_manager, speed_multiplier, jump_multiplier)
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
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(80)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Title
        self.ui.draw_cheese_title(self.screen, "Rat Race", self.screen_width//2, self.screen_height//4, center=True, size=96)
        self.ui.draw_bubble_text(self.screen, "Cheese-fueled platformer", self.screen_width//2, self.screen_height//4 + 60, center=True, size=36, max_width=self.screen_width - 80)
        # Buttons
        start_y = self.screen_height//2 + 20
        self.ui.draw_cheese_button(self.screen, "Start (SPACE/ENTER)", self.screen_width//2, start_y)
        self.ui.draw_cheese_button(self.screen, "Level Select (L)", self.screen_width//2, start_y + 60)
        self.ui.draw_cheese_button(self.screen, "ESC to Quit", self.screen_width//2, start_y + 120)
        
        # Keyboard instructions
        instructions_y = start_y + 200
        self.ui.draw_bubble_text(self.screen, "Controls:", self.screen_width//2, instructions_y, center=True, size=28)
        self.ui.draw_bubble_text(self.screen, "Arrow Keys: Move • SPACE: Jump", self.screen_width//2, instructions_y + 35, center=True, size=24)
        self.ui.draw_bubble_text(self.screen, "Down Arrow: Crouch • ESC: Pause", self.screen_width//2, instructions_y + 65, center=True, size=24)
        
        # High score display
        if hasattr(self, 'high_score') and self.high_score > 0:
            self.ui.draw_bubble_text(self.screen, f"High Score: {self.high_score:,}", self.screen_width//2, self.screen_height - 60, center=True, size=28)
        
        self.ui.draw_bubble_text(self.screen, "Sound effects enabled", self.screen_width//2, self.screen_height - 30, center=True, size=24)
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
        self.ui.draw_cheese_title(self.screen, "Loading...", self.screen_width//2, self.screen_height//2 - 20, center=True, size=72)
        self.ui.draw_bubble_text(self.screen, "Tip: Holes make the best shortcuts.", self.screen_width//2, self.screen_height//2 + 40, center=True, size=28)
        self.bg.set_theme(old_theme)

    def _draw_game(self):
        self.bg.draw(self.screen, self.current_level, is_bonus_room=False)
        for sprite in self.all_sprites:
            screen_x = sprite.rect.x - self.camera.x
            screen_y = sprite.rect.y - self.camera.y
            if (-sprite.rect.width < screen_x < self.screen_width and -sprite.rect.height < screen_y < self.screen_height):
                # Apply sprite offset for player to center visual on smaller hitbox
                if hasattr(sprite, 'sprite_offset_x'):
                    draw_x = screen_x - sprite.sprite_offset_x
                    draw_y = screen_y - sprite.sprite_offset_y
                    self.screen.blit(sprite.image, (draw_x, draw_y))
                else:
                    self.screen.blit(sprite.image, (screen_x, screen_y))
        
        # Draw Geometry Dash mode elements
        if hasattr(self, 'geometry_dash_mode') and self.geometry_dash_mode:
            # Draw countdown timer
            if hasattr(self, 'countdown_active') and self.countdown_active:
                countdown_seconds = max(1, ((self.countdown_timer - 1) // 60) + 1)
                
                # Computer terminal-style countdown display in center of screen
                countdown_rect = pygame.Rect(self.screen_width//2 - 100, self.screen_height//2 - 100, 200, 200)
                pygame.draw.rect(self.screen, (0, 0, 0), countdown_rect)  # Black terminal background
                pygame.draw.rect(self.screen, (0, 255, 0), countdown_rect, 5)  # Green terminal border
                
                # Draw countdown number in computer style
                self.ui.draw_cheese_title(self.screen, str(countdown_seconds), self.screen_width//2, self.screen_height//2 - 20, center=True, size=120)
                
                # Add computer-style status text
                self.ui.draw_bubble_text(self.screen, "SYSTEM READY", self.screen_width//2, self.screen_height//2 + 40, center=True, size=16)
                self.ui.draw_bubble_text(self.screen, ">>> INITIALIZING <<<", self.screen_width//2, self.screen_height//2 + 60, center=True, size=14)
                
                # Draw computer-themed warning sign
                if hasattr(self, 'run_sign_x') and hasattr(self, 'run_sign_y'):
                    run_sign_screen_x = self.run_sign_x - self.camera.x
                    run_sign_screen_y = self.run_sign_y - self.camera.y
                    
                    if -100 < run_sign_screen_x < self.screen_width + 100:
                        # Draw computer terminal-style sign background
                        sign_rect = pygame.Rect(run_sign_screen_x - 70, run_sign_screen_y - 45, 140, 90)
                        pygame.draw.rect(self.screen, (0, 0, 0), sign_rect)  # Black terminal background
                        pygame.draw.rect(self.screen, (0, 255, 0), sign_rect, 3)  # Green terminal border
                        
                        # Draw computer-themed warning text
                        warning_text = getattr(self, 'computer_warning_text', 'EXECUTE!')
                        self.ui.draw_bubble_text(self.screen, warning_text, run_sign_screen_x, run_sign_screen_y - 10, center=True, size=20, max_width=120)
                        
                        # Add computer-style details
                        self.ui.draw_bubble_text(self.screen, ">>>", run_sign_screen_x, run_sign_screen_y + 15, center=True, size=16, max_width=120)
            else:
                # Countdown over - draw computer-themed spike wall
                spike_wall_screen_x = self.spike_wall_x - self.camera.x
                if -100 < spike_wall_screen_x < self.screen_width + 100:
                    # Draw computer terminal-style spike wall
                    spike_wall_rect = pygame.Rect(spike_wall_screen_x, 0, 50, self.screen_height)
                    pygame.draw.rect(self.screen, (0, 0, 0), spike_wall_rect)  # Black terminal background
                    pygame.draw.rect(self.screen, (255, 0, 0), spike_wall_rect, 3)  # Red danger border
                    
                    # Draw computer-style error spikes
                    for y in range(0, self.screen_height, 25):
                        spike_points = [
                            (spike_wall_screen_x + 50, y),
                            (spike_wall_screen_x + 35, y + 12),
                            (spike_wall_screen_x + 50, y + 25)
                        ]
                        pygame.draw.polygon(self.screen, (255, 0, 0), spike_points)  # Red spikes
                        pygame.draw.polygon(self.screen, (255, 100, 100), spike_points, 2)
                        
                        # Add computer error symbols
                        if y % 50 == 0:  # Every other spike
                            self.ui.draw_bubble_text(self.screen, "!", spike_wall_screen_x + 25, y + 12, center=True, size=12)
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
            star_panel_rect = pygame.Rect(self.screen_width - 210, 10, 200, 60)
            pygame.draw.rect(self.screen, SOFT_YELLOW, star_panel_rect)
            pygame.draw.rect(self.screen, BLACK, star_panel_rect, 3)
            
            # Draw star icon
            import math
            star_center_x = self.screen_width - 180
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
            timer_x = self.screen_width - 200
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
            self.ui.draw_bubble_text(self.screen, f"{seconds_remaining}s", self.screen_width - 130, 30, center=False, size=24)

    def _draw_level_complete(self):
        self.bg.draw(self.screen, self.current_level, is_bonus_room=False)
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Level complete title
        self.ui.draw_cheese_title(self.screen, "Level Complete!!", self.screen_width//2, self.screen_height//4, center=True, size=72)
        
        # Show current level info
        level_name = self.theme.get("name", f"Level {self.current_level + 1}")
        self.ui.draw_bubble_text(self.screen, level_name, self.screen_width//2, self.screen_height//4 + 60, center=True, size=36)
        
        # Show current score
        self.ui.draw_bubble_text(self.screen, f"Final Score: {self.score:,}", self.screen_width//2, self.screen_height//2 - 40, center=True, size=48)
        
        # Continue options
        if self.current_level < len(self.levels) - 1:
            self.ui.draw_bubble_text(self.screen, "Continue?", self.screen_width//2, self.screen_height//2 + 20, center=True, size=36)
            self.ui.draw_cheese_button(self.screen, "Next Level (SPACE/ENTER)", self.screen_width//2, self.screen_height//2 + 80)
            self.ui.draw_cheese_button(self.screen, "Main Menu (M)", self.screen_width//2, self.screen_height//2 + 140)
        else:
            # All levels complete!
            self.ui.draw_bubble_text(self.screen, "All Levels Complete!", self.screen_width//2, self.screen_height//2 + 20, center=True, size=48)
            self.ui.draw_bubble_text(self.screen, "Congratulations!", self.screen_width//2, self.screen_height//2 + 80, center=True, size=36)
            self.ui.draw_cheese_button(self.screen, "Main Menu (M)", self.screen_width//2, self.screen_height//2 + 140)
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
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(120)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        self.ui.draw_cheese_title(self.screen, "Game Over", self.screen_width//2, self.screen_height//3, center=True, size=96)
        
        # Stats
        self.ui.draw_bubble_text(self.screen, f"Final Score: {self.score}", self.screen_width//2, self.screen_height//2 + 20, center=True, size=48)
        self.ui.draw_bubble_text(self.screen, f"Level Reached: {self.level_progress + 1}", self.screen_width//2, self.screen_height//2 + 60, center=True, size=32)
        # Cheese buttons
        base_y = self.screen_height//2 + 110
        self.ui.draw_cheese_button(self.screen, "Restart (R/SPACE)", self.screen_width//2, base_y)
        self.ui.draw_cheese_button(self.screen, "Main Menu (M)", self.screen_width//2, base_y + 60)
        self.ui.draw_cheese_button(self.screen, "ESC to Quit", self.screen_width//2, base_y + 120)
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
            if (-sprite.rect.width < screen_x < self.screen_width and -sprite.rect.height < screen_y < self.screen_height):
                # Apply sprite offset for player to center visual on smaller hitbox
                if hasattr(sprite, 'sprite_offset_x'):
                    draw_x = screen_x - sprite.sprite_offset_x
                    draw_y = screen_y - sprite.sprite_offset_y
                    self.screen.blit(sprite.image, (draw_x, draw_y))
                else:
                    self.screen.blit(sprite.image, (screen_x, screen_y))
        
        # Draw HUD
        for i in range(self.lives):
            self.ui.draw_heart(self.screen, 14 + i * 28, 18, 10, SOFT_PINK, BLACK)
        panel_rect = pygame.Rect(10, 44, 200, 40)
        pygame.draw.rect(self.screen, SOFT_YELLOW, panel_rect)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)
        self.ui.draw_bubble_text(self.screen, f"Score: {self.score}", panel_rect.left + 10, panel_rect.centery, center=False, size=28, max_width=panel_rect.width - 20)
        
        # Bonus room title
        self.ui.draw_cheese_title(self.screen, "BONUS ROOM!", self.screen_width//2, 80, center=True, size=72)
        
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
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(100)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        self.ui.draw_cheese_title(self.screen, "Select Level", self.screen_width//2, 90, center=True, size=84)
        
        top = 180
        for i, level in enumerate(self.levels):
            name = f"{i+1}. {level['theme'].get('name', 'Level')}"
            y = top + i * 36
            if i == self.current_level:
                bar = pygame.Rect(self.screen_width//2 - 180, y - 16, 360, 32)
                pygame.draw.rect(self.screen, MINT_GREEN, bar)
                pygame.draw.rect(self.screen, BLACK, bar, 2)
            self.ui.draw_bubble_text(self.screen, name, self.screen_width//2, y, center=True, size=28)
        # Instruction cheese button
        self.ui.draw_cheese_button(self.screen, "UP/DOWN to choose, ENTER to play, M for menu", self.screen_width//2, self.screen_height - 50, width=560, height=44)
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
