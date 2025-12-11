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

# ROS Integration
try:
    import rospy
    from std_msgs.msg import Int64, String
    from ros_nodes.srv import SetGameDifficulty
    ROS_ENABLED = True
except ImportError:
    ROS_ENABLED = False


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
        
        # ROS Integration
        self.ros_stats_published = False
        # Initialize player color (1: Red, 2: Purple, 3: Blue)
        self.player_color = 2  # Default purple
        # ROS keyboard input state (for control_node messages)
        self.ros_keyboard_state = {"LEFT": False, "RIGHT": False, "UP": False, "DOWN": False}
        if ROS_ENABLED:
            try:
                # Only initialize node if not already initialized (game_node might have done it)
                if rospy.get_name() == '/unnamed':
                    rospy.init_node('mario_game_gui', anonymous=True)
                self.ros_pub_stats = rospy.Publisher('game_over_stats', Int64, queue_size=10)
                # Subscribe to keyboard_control topic for ROS keyboard input (from control_node)
                self.ros_keyboard_sub = rospy.Subscriber('keyboard_control', String, self.ros_keyboard_callback)
                # Publish keyboard events to keyboard_control topic (so game_node can track them)
                self.ros_pub_keyboard = rospy.Publisher('keyboard_control', String, queue_size=10)
                # Wait a moment for connections
                rospy.sleep(0.1)
                # Read player color from ROS parameter
                try:
                    self.player_color = rospy.get_param('change_player_color', 2)
                except:
                    pass
                rospy.loginfo("GUI Game Node Initialized with keyboard_control subscriber and publisher")
                rospy.loginfo(f"GUI Game: Subscribed to 'keyboard_control' topic")
                rospy.loginfo(f"GUI Game: Publishing to 'keyboard_control' topic")
            except rospy.ROSException as e:
                rospy.logwarn(f"ROS initialization issue (may be normal if already initialized): {e}")
            except Exception as e:
                rospy.logerr(f"Error initializing ROS in game: {e}")

        # Initialize Geometry Dash mode attributes
        self.geometry_dash_mode = False
        self.player_speed_multiplier = 1.0
        self.countdown_active = False
        
        # Initialize bubble wall mode variables
        self.bubble_wall_mode = False
        self.bubble_wall_x = 0
        self.bubble_wall_speed = 0
        self.bubble_wall_countdown_timer = 0
        self.bubble_wall_countdown_active = False

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
            game_images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "game images")
            mice_path = os.path.join(game_images_dir, "3mouse.jpeg")
            if os.path.exists(mice_path):
                self.mice_image = pygame.image.load(mice_path)
                # Scale to full screen size
                self.mice_image = pygame.transform.scale(self.mice_image, (self.screen_width, self.screen_height))
            else:
                self.mice_image = None
            
            # Load rat for death screen - FULL SCREEN
            rat_path = os.path.join(game_images_dir, "rat.jpeg")
            if os.path.exists(rat_path):
                self.rat_image = pygame.image.load(rat_path)
                # Scale to full screen size
                self.rat_image = pygame.transform.scale(self.rat_image, (self.screen_width, self.screen_height))
            else:
                self.rat_image = None
            
            # Load rat for levels screen (changed from pocketrat) - FULL SCREEN
            rat_levels_path = os.path.join(game_images_dir, "rat.jpeg")
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
        
        # Special underwater maze level - completely different mechanics - handle early
        if self.theme.get("name") == "Kraken Me Up":
            # Set underwater mode
            self.underwater_mode = True
            self.bubble_wall_mode = False
            self.bubble_wall_x = 0
            self.bubble_wall_speed = 0
            self.bubble_wall_countdown_timer = 0
            self.bubble_wall_countdown_active = False
            # Reset Geometry Dash mode
            self.geometry_dash_mode = False
            self.player_speed_multiplier = 1.0
            self.countdown_active = False
            # Update camera with new level dimensions
            self.camera.set_level_dimensions(level_def["width"], level_def["height"])
            # Create the underwater maze level
            self._create_underwater_maze_v2()
            return  # Skip normal level generation
        
        # Special tetris level - completely different mechanics - handle early
        if self.theme.get("name") == "Tetris Terror":
            # Reset modes
            self.underwater_mode = False
            self.geometry_dash_mode = False
            self.player_speed_multiplier = 1.0
            self.countdown_active = False
            # Update camera with new level dimensions
            self.camera.set_level_dimensions(level_def["width"], level_def["height"])
            # Create the tetris level
            self._create_tetris_level()
            return  # Skip normal level generation
        
        # Reset Geometry Dash mode for non-Geometry Dash levels
        # Note: "404: Floor Not Found" is now Level 7 (was Level 6)
        if not (self.theme.get("name") == "404: Floor Not Found"):
            self.geometry_dash_mode = False
            self.player_speed_multiplier = 1.0
            self.countdown_active = False
        
        # Reset underwater mode and bubble wall mode for non-underwater levels
        self.underwater_mode = False
        self.bubble_wall_mode = False
        self.bubble_wall_x = 0
        self.bubble_wall_speed = 0
        self.bubble_wall_countdown_timer = 0
        self.bubble_wall_countdown_active = False
        
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
        
        # Add floor gaps for Level 5 (Boo Who?)
        if self.theme.get("name") == "Boo Who?":
            self._add_floor_gaps(level_def, gap_count=4)
        
        # Post-process: Ensure all platforms have minimum spacing for player to fit between
        # This will be done after all platform types are added
        
        # Get enemy stepping stones from generator
        stepping_stone_enemies = generator.get_enemy_stepping_stones()

        # Generate checkpoints (houses or cheese wheels) at regular intervals
        # Skip checkpoints for Level 7 (Geometry Dash - 404: Floor Not Found)
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
        # Basic enemy set used across all levels
        basic_enemy_kinds = ["basic", "fast", "jumper", "big", "double_hit", "air_dragon"]
        
        # Level-specific enemy sets
        if self.theme.get("name") == "Pasta La Vista":
            # Level 6: Only meatball enemies (angry meatballs)
            enemy_kinds = ["meatball"]
        elif self.theme.get("name") == "Boo Who?":
            # Level 5: Include air_bat only in Boo Who?
            enemy_kinds = basic_enemy_kinds + ["air_bat"]
        else:
            # All other levels: Use basic enemy set
            enemy_kinds = basic_enemy_kinds
        
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
        # Skip enemy count for Level 7 (404: Floor Not Found) - handled in _create_geometry_dash_level
        elif self.theme.get("name") == "404: Floor Not Found":
            enemy_count = 0  # No enemies from normal generation - only worms from _create_geometry_dash_level
        # Make pasta level very hard with lots of ground enemies
        elif self.theme.get("name") == "Pasta La Vista":
            enemy_count = (enemy_count + 12) * 2  # Multiply by 2 (reduced from 4)
        # Level 8 (Kraken Me Up) is handled early in create_level() - skip here
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
            elif self.theme.get("name") == "Pasta La Vista":
                air_chance = 0.3  # Half as many sky enemies (was 0.6, now 0.3 = half)
            if rng.random() < air_chance:
                y = rng.randint(100, 300)  # Higher up for air enemies
            else:
                y = rng.randint(240, 460)  # Normal ground level
            
            # Weighted selection for enemy types (weights must match enemy_kinds length)
            if self.theme.get("name") == "Pasta La Vista":
                # Level 6: Only meatball enemies (angry meatballs)
                # enemy_kinds = ["meatball"]
                weights = [1]  # Only meatball enemies (1 weight for 1 enemy type)
            elif self.theme.get("name") == "Boo Who?":
                # Prefer air enemies (ghosts) for ghost level
                # enemy_kinds = ["basic", "fast", "jumper", "big", "double_hit", "air_dragon", "air_bat"]
                weights = [1, 1, 1, 1, 1, 6, 8]  # Favor air_bat and air_dragon (7 weights for 7 enemy types)
            elif self.theme.get("name") == "404: Floor Not Found":
                # Skip - Level 7 uses only worm enemies from _create_geometry_dash_level
                # This code shouldn't be reached due to early return, but set weights just in case
                weights = []  # Empty weights - no enemies from normal generation
            # Level 8 (Concrete Jungle) was removed
            else:
                # Basic enemy set for all other levels
                # enemy_kinds = ["basic", "fast", "jumper", "big", "double_hit", "air_dragon"]
                weights = [4, 3 + level_def["difficulty"], 3, 1 + level_def["difficulty"]//2, 
                         2 + level_def["difficulty"], 1 + level_def["difficulty"]//3]  # 6 weights for 6 enemy types
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
        
        # Create exactly one rainbow star on levels 1, 3, 5, 7, 9 (0-indexed: 0, 2, 4, 6, 8)
        # Skip rainbow stars for Level 7 (404: Floor Not Found) - it has special mechanics
        if self.current_level in [0, 2, 4, 6, 8] and self.theme.get("name") != "404: Floor Not Found":
            # Choose a random position for the rainbow star
            if powerup_positions:  # Make sure we have positions
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
                # Fallback: create coins if no powerup positions
                for x, y in powerup_positions:
                    coin = Powerup(x, y, "coin")
                    self.powerups.add(coin)
                    self.all_sprites.add(coin)
        else:
            # On other levels, create only regular coins
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
        
        # Create Geometry Dash-style Level 7 (404: Floor Not Found)
        # Note: This level was swapped - it's now Level 7, not Level 6
        if self.theme.get("name") == "404: Floor Not Found":
            self._create_geometry_dash_level()
            return  # Skip normal enemy generation for Geometry Dash level
        
        # Add pasta slides and moving platforms for Level 6 (Pasta La Vista)
        if self.theme.get("name") == "Pasta La Vista":
            pasta_rng = random.Random(6666 + self.current_level)
            
            # Player width is ~32 pixels (sprite) with 70% hitbox = ~22 pixels
            # Minimum gap needed: player width + buffer = 32 + 20 = 52 pixels minimum
            # Use 60 pixels as safe minimum gap
            MIN_PLATFORM_GAP = 60  # Minimum horizontal gap between platforms for player to fit
            placed_pasta_platforms = []  # Track placed platforms for spacing
            
            # Add pasta slides (sloped platforms) - doubled
            slide_count = (8 + level_def["difficulty"] * 2) * 2  # Twice as many
            for _ in range(slide_count):
                attempts = 0
                placed = False
                while attempts < 50 and not placed:
                    attempts += 1
                    x = pasta_rng.randint(200, level_def["width"] - 300)
                    y = pasta_rng.randint(300, level_def["height"] - 200)
                    
                    # Check spacing from other platforms
                    too_close = False
                    for px, py, pw in placed_pasta_platforms:
                        # Check horizontal distance
                        horizontal_gap = min(abs(x - px), abs(x + 150 - px), abs(x - (px + pw)))
                        if horizontal_gap < MIN_PLATFORM_GAP:
                            too_close = True
                            break
                    
                    if not too_close:
                        # Create pasta slide platform
                        pasta_slide = Platform(x, y, 150, 40, platform_type="pasta_slide", theme=self.theme)
                        self.platforms.add(pasta_slide)
                        self.all_sprites.add(pasta_slide)
                        placed_pasta_platforms.append((x, y, 150))
                        placed = True
            
            # Add vertically moving platforms to help escape meatballs - doubled
            moving_count = (6 + level_def["difficulty"] * 2) * 2  # Twice as many
            for _ in range(moving_count):
                attempts = 0
                placed = False
                while attempts < 50 and not placed:
                    attempts += 1
                    x = pasta_rng.randint(300, level_def["width"] - 200)
                    y = pasta_rng.randint(250, level_def["height"] - 150)
                    
                    # Check spacing from other platforms
                    too_close = False
                    for px, py, pw in placed_pasta_platforms:
                        # Check horizontal distance
                        horizontal_gap = min(abs(x - px), abs(x + 120 - px), abs(x - (px + pw)))
                        if horizontal_gap < MIN_PLATFORM_GAP:
                            too_close = True
                            break
                    
                    if not too_close:
                        # Create vertically moving platforms
                        moving_platform = Platform(x, y, 120, 30, platform_type="pasta_moving", theme=self.theme)
                        self.platforms.add(moving_platform)
                        self.all_sprites.add(moving_platform)
                        placed_pasta_platforms.append((x, y, 120))
                        placed = True
            
            # No ground gaps - continuous floor
            # (Ground gaps removed - player wants continuous floor)
        
        # Level 8 (Concrete Jungle) was removed - now only 9 levels
        
        # Add 2 firewalls with keys for Level 7 (404: Floor Not Found)
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
        
        # Add giant falling meatballs AND ground meatballs for Level 6 (Pasta La Vista) - raining meatballs + ground obstacles!
        if self.theme.get("name") == "Pasta La Vista":
            meatball_rng = random.Random(7777 + self.current_level)
            falling_meatball_count = (3 + level_def["difficulty"]) * 4  # 4x more falling meatballs!
            ground_meatball_count = 3 + level_def["difficulty"]  # Ground meatballs (evil meatballs on land)
            
            level_width = level_def["width"]
            
            # Add falling meatballs from sky
            spacing = level_width // (falling_meatball_count + 1)  # Even spacing across level
            for i in range(falling_meatball_count):
                # Distribute evenly across the entire level width
                base_x = spacing * (i + 1)
                x = base_x + meatball_rng.randint(-spacing//3, spacing//3)  # Add variation but keep coverage
                x = max(150, min(level_width - 250, x))  # Keep within safe bounds
                y = meatball_rng.randint(-400, -50)  # Start above the screen at different heights for staggered falling
                # Create giant falling meatball that will rain down
                meatball = Obstacle(x, y, "giant_meatball")
                meatball.falling = True  # Mark as falling meatball
                meatball.fall_speed = 2.5 + random.random() * 1.5  # Random fall speed
                meatball.level_width = level_width  # Store level width for respawning across entire level
                self.obstacles.add(meatball)
                self.all_sprites.add(meatball)
        
            # Add ground meatballs (evil meatballs on land) - these don't fall, they're obstacles on the ground
            for _ in range(ground_meatball_count):
                x = meatball_rng.randint(200, level_width - 300)
                y = level_def["height"] - 150  # At ground level
                # Create giant ground meatball obstacle (not falling)
                ground_meatball = Obstacle(x, y, "giant_meatball")
                ground_meatball.falling = False  # Not falling, just a ground obstacle
                self.obstacles.add(ground_meatball)
                self.all_sprites.add(ground_meatball)
        
        # Post-process all platforms to ensure minimum spacing (after all platforms are added)
        self._ensure_platform_spacing(level_def)
        
        # Level 8 (Concrete Jungle) was removed - trains code removed
        
        # Add ultimate challenge features for Level 9 (Neon Night, was Level 10)
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
                # Handle state-specific keys first, then global ESC
                elif self.state == GameState.LOADING:
                    # Allow skip loading to menu
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.state = GameState.MENU
                elif self.state == GameState.MENU:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.start_game()
                    elif event.key == pygame.K_l:
                        # K_l works for both uppercase and lowercase L in pygame
                        self.state = GameState.LEVEL_SELECT
                elif self.state == GameState.LEVEL_COMPLETE:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                            self.continue_to_next_level()
                    elif event.key == pygame.K_m:
                            self.state = GameState.MENU
                elif self.state == GameState.VICTORY:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN or event.key == pygame.K_m:
                        # Stats already published when victory screen was shown
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
                    # Also allow L key to go back to menu from level select
                    elif event.key == pygame.K_l:
                        self.state = GameState.MENU
                elif self.state == GameState.DIFFICULTY_SELECT:
                    if event.key == pygame.K_1:
                        self.set_difficulty("easy")
                    elif event.key == pygame.K_2:
                        self.set_difficulty("medium")
                    elif event.key == pygame.K_3:
                        self.set_difficulty("hard")
                    elif event.key == pygame.K_r:
                        self.set_player_color(1)  # Red
                    elif event.key == pygame.K_b:
                        self.set_player_color(3)  # Blue
                    elif event.key == pygame.K_p:
                        self.set_player_color(2)  # Purple
                elif self.state == GameState.PLAYING:
                    # ESC key to exit level and return to main menu
                    if event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                    # Publish arrow key presses to keyboard_control topic for game_node tracking
                    elif ROS_ENABLED and event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                        try:
                            msg = String()
                            if event.key == pygame.K_LEFT:
                                msg.data = "LEFT"
                            elif event.key == pygame.K_RIGHT:
                                msg.data = "RIGHT"
                            elif event.key == pygame.K_UP:
                                msg.data = "UP"
                            elif event.key == pygame.K_DOWN:
                                msg.data = "DOWN"
                            self.ros_pub_keyboard.publish(msg)
                            rospy.loginfo(f"GUI Game: Published keyboard event to ROS: {msg.data}")
                        except Exception as e:
                            rospy.logerr(f"GUI Game: Error publishing keyboard event: {e}")
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_r or event.key == pygame.K_SPACE:
                        self.restart_game()
                    elif event.key == pygame.K_m:
                        self.state = GameState.MENU
                elif self.state == GameState.BONUS_ROOM:
                    # ESC key to exit bonus room and return to main menu
                    if event.key == pygame.K_ESCAPE:
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
        self.player = Player(100, 500, self.sound_manager, player_color=self.player_color)  # Start on floor
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
        self.player = Player(player_x, player_y, self.sound_manager, player_color=self.player_color)
        self.all_sprites.add(self.player)
        
        # Reset camera
        self.camera.x = 0
        self.camera.y = 0
        
        # Return to playing state
        self.state = GameState.PLAYING
        
        # Clean up saved state
        delattr(self, 'saved_level_state')
    
    def _create_geometry_dash_level(self):
        """Create a multi-floor level with gaps, spikes, and enemies. Player spawns in middle floor."""
        level_def = self.levels[self.current_level]
        
        # Clear existing enemies - we'll add specific ones for this level
        self.enemies.empty()
        
        # Get original base width (before any modifications)
        # Level 7 base width is 10400px, was originally 2x (20800px)
        # Now make it 40% shorter: 20800 * 0.6 = 12480px (or base * 1.2)
        original_base_width = level_def["width"]  # This is the base width (10400px)
        level_width = int(original_base_width * 1.2)  # 40% shorter than 2x (1.2x instead of 2x = 12480px)
        level_def["width"] = level_width
        
        # Update level dimensions for enemies to work properly
        set_level_dimensions(level_width, level_def["height"])
        self.camera.set_level_dimensions(level_width, level_def["height"])
        
        from constants import SAFE_JUMP_HEIGHT, PLAYER_SPEED
        spawn_safe_zone = 400  # Safe spawn area
        
        # Define 3 floors stacked on top of one another
        floor_height = 40  # Platform thickness
        # Floor spacing must be within jump range - use SAFE_JUMP_HEIGHT - 20 for safety margin
        floor_spacing = SAFE_JUMP_HEIGHT - 20  # Vertical spacing between floors (within jump range, ~140px)
        num_floors = 3  # Three floors
        
        # Calculate floor Y positions (from bottom to top)
        ground_y = level_def["height"] - floor_height
        floor_ys = []
        for i in range(num_floors):
            floor_y = ground_y - (i * floor_spacing)
            floor_ys.append(floor_y)
        
        # Middle floor is where player spawns (index 1)
        middle_floor_y = floor_ys[1]
        
        # Create horizontal floor platforms with lots of gaps for each floor
        platforms_list = []
        gap_rng = random.Random(7007 + self.current_level)
        
        for floor_idx, floor_y in enumerate(floor_ys):
            floor_platforms = []
            # Create floor segments with gaps
            segment_width = 200
            gap_width = 150  # Width of gaps (jumpable)
            
            x = 0
            while x < level_width:
                # Decide if this segment should be a gap or platform
                # Create lots of gaps - about 40% of segments are gaps
                if gap_rng.random() < 0.4 and x > spawn_safe_zone and x < level_width - 400:
                    # This is a gap - skip it
                    x += gap_width
                else:
                    # Create platform segment
                    remaining_width = min(segment_width, level_width - x)
                    if remaining_width > 0:
                        floor_platform = Platform(x, floor_y, remaining_width, floor_height, platform_type="ground", theme=self.theme)
                        floor_platforms.append(floor_platform)
                        self.platforms.add(floor_platform)
                        self.all_sprites.add(floor_platform)
                    x += segment_width
            platforms_list.append(floor_platforms)
        
        # Add platforms to bottom floor (floor 1) to allow moving up
        # Add floating platforms very close to bottom floor for easy vertical movement
        bottom_floor_y = floor_ys[0]  # Bottom floor
        platform_rng = random.Random(9009 + self.current_level)
        
        # Add platforms very close to bottom floor (within easy jump range)
        # Focus on platforms within 100px of bottom floor
        close_platform_count = 8  # Platforms very close (60-100px above)
        medium_platform_count = 6  # Platforms medium distance (100-180px above)
        
        # Very close platforms (60-100px above bottom floor)
        for i in range(close_platform_count):
            platform_x = platform_rng.randint(spawn_safe_zone + 200, level_width - 400)
            # Y position: 60-100px above bottom floor
            y_offset = 60 + (i * 5)  # Start at 60px, increase by 5px each
            platform_y = bottom_floor_y - y_offset
            
            if platform_y >= bottom_floor_y - 100:
                platform_width = platform_rng.randint(160, 240)
                platform_height = 20
                
                intermediate_platform = Platform(
                    platform_x, platform_y, platform_width, platform_height,
                    platform_type="normal", theme=self.theme
                )
                self.platforms.add(intermediate_platform)
                self.all_sprites.add(intermediate_platform)
        
        # Medium distance platforms (100-180px above bottom floor)
        for i in range(medium_platform_count):
            platform_x = platform_rng.randint(spawn_safe_zone + 200, level_width - 400)
            # Y position: 100-180px above bottom floor
            y_offset = 100 + (i * 13)  # Start at 100px, increase by 13px each
            platform_y = bottom_floor_y - y_offset
            
            if platform_y >= bottom_floor_y - 180:
                platform_width = platform_rng.randint(150, 220)
                platform_height = 20
                
                intermediate_platform = Platform(
                    platform_x, platform_y, platform_width, platform_height,
                    platform_type="normal", theme=self.theme
                )
                self.platforms.add(intermediate_platform)
                self.all_sprites.add(intermediate_platform)
        
        # Add additional platforms between bottom and middle floors for better path
        middle_floor_y = floor_ys[1]  # Middle floor
        floor_gap = bottom_floor_y - middle_floor_y  # Gap between floors
        platform_spacing = SAFE_JUMP_HEIGHT - 20  # Spacing between platforms (within jump range)
        num_platform_layers = max(4, int(floor_gap / platform_spacing))  # Number of platform layers needed
        
        # Add platforms in layers between bottom and middle floors
        for layer in range(num_platform_layers):
            # Y position for this layer
            y_offset = 80 + (layer * platform_spacing)  # Start 80px above bottom, then spaced
            platform_y = bottom_floor_y - y_offset
            
            # Make sure we don't go above middle floor
            if platform_y <= middle_floor_y - 40:
                break
            
            # Add 3-4 platforms per layer for good coverage
            platforms_per_layer = platform_rng.randint(3, 4)
            for p in range(platforms_per_layer):
                platform_x = platform_rng.randint(spawn_safe_zone + 200, level_width - 400)
                platform_width = platform_rng.randint(160, 240)
                platform_height = 20
                
                intermediate_platform = Platform(
                    platform_x, platform_y, platform_width, platform_height,
                    platform_type="normal", theme=self.theme
                )
                self.platforms.add(intermediate_platform)
                self.all_sprites.add(intermediate_platform)
        
        # Also add platforms between middle and top floors to ensure all vertical jumps are possible
        top_floor_y = floor_ys[2]  # Top floor
        middle_to_top_gap = middle_floor_y - top_floor_y
        
        if middle_to_top_gap > SAFE_JUMP_HEIGHT - 40:
            # Need intermediate platforms between middle and top floors
            num_middle_layers = max(1, int(middle_to_top_gap / platform_spacing))
            for layer in range(num_middle_layers):
                y_offset = 60 + (layer * platform_spacing)
                platform_y = middle_floor_y - y_offset
                
                if platform_y <= top_floor_y - 40:
                    break
                
                # Verify this platform is within jump range
                if layer > 0:
                    prev_y = middle_floor_y - (60 + ((layer - 1) * platform_spacing))
                    vertical_gap = prev_y - platform_y
                    if vertical_gap > SAFE_JUMP_HEIGHT:
                        # Adjust to be within jump range
                        platform_y = prev_y - SAFE_JUMP_HEIGHT + 10
                
                # Add 2-3 platforms per layer
                platforms_per_layer = platform_rng.randint(2, 3)
                for p in range(platforms_per_layer):
                    platform_x = platform_rng.randint(spawn_safe_zone + 200, level_width - 400)
                    platform_width = platform_rng.randint(160, 240)
                    platform_height = 20
                    
                    intermediate_platform = Platform(
                        platform_x, platform_y, platform_width, platform_height,
                        platform_type="normal", theme=self.theme
                    )
                    self.platforms.add(intermediate_platform)
                    self.all_sprites.add(intermediate_platform)
        
        # Add green spikes on both floor and ceiling of each floor
        spike_positions = []
        spike_rng = random.Random(7007 + self.current_level)
        
        # Floor spikes (on top of each floor) - match floor color, jumpable groupings
        from constants import SAFE_JUMP_HEIGHT
        for floor_y in floor_ys:
            spike_x = spawn_safe_zone + 200
        pattern_index = 0
        
            # Jumpable spike patterns - only single and double spikes (no triple spikes)
            # Triple spikes are too hard to jump over, so we'll use only single and double
        patterns = [
                [(0, 0)],  # Single spike
                [(0, 0), (60, 0)],  # Double spike (60px wide - jumpable)
        ]
        
        while spike_x < level_width - 200:
                # Place spikes with reduced frequency (25% chance - even less frequent)
                if spike_rng.random() < 0.25:  # 25% chance to place spikes here
                    # Prefer single spikes (70% chance) over double spikes (30% chance)
                    if spike_rng.random() < 0.7:
                        pattern = [(0, 0)]  # Single spike
                    else:
                        pattern = [(0, 0), (60, 0)]  # Double spike
                    
                    for offset_x, offset_y in pattern:
                        if spike_x + offset_x < level_width - 100:
                            spike_y = floor_y - 30 + offset_y  # Spikes on floor
                            spike_positions.append((spike_x + offset_x, spike_y))
                    
                    # After placing a spike group, ensure next placement is jumpable distance away
                    max_pattern_width = max([p[0] for p in pattern]) if pattern else 0
                    # Ensure minimum gap of 200px for jumpability (even wider gaps)
                    gap_size = max(200, max_pattern_width + 200)  # At least 200px gap after pattern
                else:
                    # No spikes here, normal gap
                    gap_size = 350 + spike_rng.randint(0, 250)  # Wider gaps between spike placements
                
                spike_x += gap_size
        
        # Ceiling spikes (hanging from ceiling above each floor) - match floor color, jumpable groupings
        for i, floor_y in enumerate(floor_ys):
            if i < num_floors - 1:  # Don't add ceiling spikes to top floor
                ceiling_y = floor_y - floor_spacing  # Position above this floor (bottom of ceiling)
                spike_x = spawn_safe_zone + 300
                
                while spike_x < level_width - 200:
                    # Place ceiling spikes with reduced frequency (20% chance, even less frequent)
                    if spike_rng.random() < 0.2:  # 20% chance to place spikes here
                        # Only single spikes on ceiling (easier to pass under)
                        cluster_size = 1  # Only single spikes on ceiling
                        for j in range(cluster_size):
                            if spike_x + (j * 50) < level_width - 100:
                                # Position so spike point is at ceiling_y (hanging down)
                                spike_positions.append((spike_x + (j * 50), ceiling_y - 4))
                        
                        # Ensure next placement is jumpable distance away
                        gap_size = max(200, 200)  # At least 200px gap after ceiling spike
                    else:
                        # No spikes here, normal gap
                        gap_size = 350 + spike_rng.randint(0, 250)  # Wider gaps
                    
                    spike_x += gap_size
        
        # Create all spike obstacles (will match floor color for Level 7)
        # Filter out any triple spike patterns that might have been created
        filtered_spike_positions = []
        spike_positions.sort(key=lambda pos: (pos[1], pos[0]))  # Sort by Y, then X
        
        # Group spikes by floor (Y position)
        spikes_by_floor = {}
        for x, y in spike_positions:
            if y not in spikes_by_floor:
                spikes_by_floor[y] = []
            spikes_by_floor[y].append(x)
        
        # Filter out triple spikes - ensure no 3 spikes within 150px
        for floor_y, spike_xs in spikes_by_floor.items():
            spike_xs.sort()
            filtered_floor_spikes = []
            i = 0
            
            while i < len(spike_xs):
                # Check if this spike is part of a triple pattern
                if i + 2 < len(spike_xs):
                    spike1 = spike_xs[i]
                    spike2 = spike_xs[i + 1]
                    spike3 = spike_xs[i + 2]
                    # If 3 spikes are within 150px, keep only first (remove middle and third)
                    if spike3 - spike1 <= 150:
                        # Keep first spike only, skip middle and third
                        filtered_floor_spikes.append(spike1)
                        i += 3  # Skip all three spikes
                        continue
                
                # Keep this spike (not part of triple pattern)
                filtered_floor_spikes.append(spike_xs[i])
                i += 1
            
            # Add filtered spikes for this floor
            for x in filtered_floor_spikes:
                filtered_spike_positions.append((x, floor_y))
        
        # Create obstacles from filtered positions
        for x, y in filtered_spike_positions:
            spike_obstacle = Obstacle(x, y, "spike")
            # Mark as Level 7 spike (will match floor color, not green)
            spike_obstacle.is_level7_spike = True
            self.obstacles.add(spike_obstacle)
            self.all_sprites.add(spike_obstacle)
        
        # Mark all existing spikes for Level 7 (in case any were created elsewhere)
        for obstacle in self.obstacles:
            if hasattr(obstacle, 'obstacle_type') and obstacle.obstacle_type == 'spike':
                obstacle.is_level7_spike = True
        
        # Add worm enemies distributed evenly across all floors - Level 7 specific
        enemy_rng = random.Random(8008 + self.current_level)
        enemy_count = 30  # Worm enemies for Level 7
        
        # Ensure worms spawn on all floors - distribute evenly
        worms_per_floor = enemy_count // num_floors  # 10 worms per floor
        extra_worms = enemy_count % num_floors  # 0 extra worms (30 / 3 = 10 exactly)
        
        enemies_added = 0
        
        # Spawn worms on each floor
        for floor_index in range(num_floors):
            floor_y = floor_ys[floor_index]
            
            # Calculate how many worms for this floor
            worms_for_this_floor = worms_per_floor
            if floor_index < extra_worms:  # Distribute extra worms to first floors
                worms_for_this_floor += 1
            
            # Find platforms on this floor to place enemies on
            floor_platforms = [p for p in platforms_list[floor_index] if p.rect.y == floor_y and p.rect.width >= 100]
            
            if not floor_platforms:
                # If no suitable platforms, try to find any platform near this floor
                floor_platforms = [p for p in platforms_list[floor_index] if p.rect.width >= 100]
            
            if floor_platforms:
                # Spawn worms on this floor
                for _ in range(worms_for_this_floor):
                    attempts = 0
                    max_attempts = 10
                    
                    while attempts < max_attempts:
                        attempts += 1
                        
                        # Choose a random platform on this floor
                        platform = enemy_rng.choice(floor_platforms)
                        
                        # Make sure platform is wide enough for worm (worms are 80px wide)
                        if platform.rect.width < 100:
                            continue
                        
                        x = enemy_rng.randint(platform.rect.left + 40, platform.rect.right - 40)
                        y = floor_y - 30  # Worms are low, closer to floor (24px tall)
                        
                        # Use worm enemy type for Level 7
                        enemy = Enemy(x, y, "worm", theme=self.theme)
                        
                        # Verify enemy is properly initialized
                        if hasattr(enemy, 'rect') and hasattr(enemy, 'update'):
                            self.enemies.add(enemy)
                            self.all_sprites.add(enemy)
                            enemies_added += 1
                            break
        
        # Store level properties for speedrun mechanics
        self.geometry_dash_mode = True
        self.spike_wall_x = 0
        self.spike_wall_speed = PLAYER_SPEED * 0.8  # Wall moves at 0.8x player speed
        self.player_speed_multiplier = 1.0  # Player moves at regular speed
        self.countdown_timer = 180
        self.countdown_active = True
        
        # Warning sign at spawn
        self.run_sign_x = 350
        self.run_sign_y = middle_floor_y - 100
        self.computer_warning_text = "RUN!"
        
        # Spawn position on middle floor
        self.geometry_dash_spawn_x = 150
        self.geometry_dash_spawn_y = middle_floor_y - 60  # On middle floor
        
        print(f"Level 7 (404: Floor Not Found) created: {level_width} pixels wide, {num_floors} floors, {enemy_count} enemies, player speed 1.0x, wall speed {self.spike_wall_speed}!")
    
    def _add_floor_gaps(self, level_def, gap_count=4):
        """Add gaps in the floor for Level 5 (Boo Who?)."""
        import random
        gap_rng = random.Random(4444 + self.current_level)
        level_width = level_def["width"]
        floor_y = level_def["height"] - 40  # Ground level
        
        # Get all ground platforms
        ground_platforms = [p for p in self.platforms if hasattr(p, 'platform_type') and p.platform_type == 'ground']
        if not ground_platforms:
            return
        
        # Sort by x position
        ground_platforms.sort(key=lambda p: p.rect.x)
        
        # Create gaps by removing platform segments
        # Don't create gaps at the very start or end
        safe_start = 400  # Keep first 400 pixels safe
        safe_end = 400    # Keep last 400 pixels safe
        
        gaps_created = 0
        attempts = 0
        max_attempts = 50
        
        while gaps_created < gap_count and attempts < max_attempts:
            attempts += 1
            
            # Find a random position in the safe zone
            gap_x = gap_rng.randint(safe_start, level_width - safe_end)
            
            # Find the ground platform that contains this x position
            platform_to_remove = None
            for platform in ground_platforms:
                if platform.rect.left <= gap_x <= platform.rect.right:
                    platform_to_remove = platform
                    break
            
            if platform_to_remove and platform_to_remove in self.platforms:
                # Remove this platform segment to create a gap
                self.platforms.remove(platform_to_remove)
                self.all_sprites.remove(platform_to_remove)
                ground_platforms.remove(platform_to_remove)
                gaps_created += 1
    
    def _ensure_platform_spacing(self, level_def):
        """Ensure all platforms have minimum spacing so player can fit between them.
        
        Player width is ~32 pixels (sprite), with 70% hitbox = ~22 pixels.
        Minimum safe gap: 32 + 20 buffer = 52 pixels, use 60 for safety.
        """
        MIN_GAP = 60  # Minimum horizontal gap between platforms
        PLATFORM_BUFFER = 10  # Extra buffer when adjusting platforms
        
        platforms_list = list(self.platforms)
        # Exclude ground platforms - they should be continuous with no gaps
        platforms_list = [p for p in platforms_list if not (hasattr(p, 'platform_type') and p.platform_type == 'ground')]
        # Sort by Y position, then X position for consistent processing
        platforms_list.sort(key=lambda p: (p.rect.y, p.rect.x))
        
        max_iterations = 3  # Limit iterations to prevent infinite loops
        for iteration in range(max_iterations):
            adjustments_made = False
            
            for i, p1 in enumerate(platforms_list):
                for j, p2 in enumerate(platforms_list[i+1:], i+1):
                    # Only check platforms at similar Y positions (within 50 pixels vertically)
                    if abs(p1.rect.y - p2.rect.y) > 50:
                        break  # Since sorted by Y, can break early
                    
                    # Check horizontal overlap or too-close spacing
                    if p1.rect.right <= p2.rect.left:
                        # p1 is to the left of p2
                        gap = p2.rect.left - p1.rect.right
                        if gap < MIN_GAP:
                            # Move p2 to the right to create minimum gap
                            move_distance = MIN_GAP - gap + PLATFORM_BUFFER
                            new_x = p2.rect.x + move_distance
                            # Keep within level bounds
                            if new_x + p2.rect.width <= level_def["width"]:
                                p2.rect.x = new_x
                                adjustments_made = True
                            elif p1.rect.x - move_distance >= 0:
                                # If can't move right, try moving p1 left instead
                                p1.rect.x = max(0, p1.rect.x - move_distance)
                                adjustments_made = True
                    elif p2.rect.right <= p1.rect.left:
                        # p2 is to the left of p1
                        gap = p1.rect.left - p2.rect.right
                        if gap < MIN_GAP:
                            # Move p1 to the right to create minimum gap
                            move_distance = MIN_GAP - gap + PLATFORM_BUFFER
                            new_x = p1.rect.x + move_distance
                            # Keep within level bounds
                            if new_x + p1.rect.width <= level_def["width"]:
                                p1.rect.x = new_x
                                adjustments_made = True
                            elif p2.rect.x - move_distance >= 0:
                                # If can't move right, try moving p2 left instead
                                p2.rect.x = max(0, p2.rect.x - move_distance)
                                adjustments_made = True
                    else:
                        # Platforms overlap horizontally - separate them
                        overlap = min(p1.rect.right, p2.rect.right) - max(p1.rect.left, p2.rect.left)
                        if overlap > 0:
                            # Move p2 to the right to create gap
                            move_distance = overlap + MIN_GAP + PLATFORM_BUFFER
                            new_x = p2.rect.x + move_distance
                            # Keep within level bounds
                            if new_x + p2.rect.width <= level_def["width"]:
                                p2.rect.x = new_x
                                adjustments_made = True
                            elif p1.rect.x - move_distance >= 0:
                                # If can't move right, try moving p1 left instead
                                p1.rect.x = max(0, p1.rect.x - move_distance)
                                adjustments_made = True
            
            # Re-sort after adjustments
            if adjustments_made:
                platforms_list.sort(key=lambda p: (p.rect.y, p.rect.x))
            else:
                break  # No more adjustments needed
    
    def _create_underwater_maze_v2(self):
        """Create an underwater maze level with swimming mechanics, walls, moving platforms, and spinning lasers.
        Level 8: Kraken Me Up - completely different from other levels."""
        import random
        import math
        level_def = self.levels[self.current_level]
        width = level_def["width"]
        height = level_def["height"]
        
        # Set underwater mode flag
        self.underwater_mode = True
        
        # Use level dimensions
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
        
        maze_rng = random.Random(8888 + self.current_level)
        spawn_safe_zone = 400
        
        # Create boundary walls to contain the maze
        wall_thickness = 40  # Thick boundary walls
        # Top wall
        top_wall = Platform(0, 0, width, wall_thickness, platform_type="normal", theme=self.theme)
        self.platforms.add(top_wall)
        self.all_sprites.add(top_wall)
        # Bottom wall
        bottom_wall = Platform(0, height - wall_thickness, width, wall_thickness, platform_type="normal", theme=self.theme)
        self.platforms.add(bottom_wall)
        self.all_sprites.add(bottom_wall)
        # Left wall
        left_wall = Platform(0, 0, wall_thickness, height, platform_type="normal", theme=self.theme)
        self.platforms.add(left_wall)
        self.all_sprites.add(left_wall)
        # Right wall
        right_wall = Platform(width - wall_thickness, 0, wall_thickness, height, platform_type="normal", theme=self.theme)
        self.platforms.add(right_wall)
        self.all_sprites.add(right_wall)
        
        # Create a guaranteed path from start to end
        # Path will be a series of connected open spaces
        path_segments = []
        segment_width = 200
        segment_height = 150
        num_segments = (width - spawn_safe_zone - 400) // segment_width
        
        # Create path waypoints
        waypoints = []
        for i in range(num_segments):
            waypoint_x = spawn_safe_zone + (i * segment_width) + segment_width // 2
            # Vary Y position but keep it navigable
            waypoint_y = height // 2 + maze_rng.randint(-100, 100)
            waypoint_y = max(150, min(height - 200, waypoint_y))  # Keep within bounds
            waypoints.append((waypoint_x, waypoint_y))
        
        # Add end waypoint
        end_x = width - 300
        end_y = height // 2
        waypoints.append((end_x, end_y))
        
        # Create walls around the path (but leave the path open)
        # Horizontal walls - MANY MORE for a proper dense maze
        horizontal_wall_count = 100 + level_def["difficulty"] * 10  # WAY more walls
        walls_placed = 0
        attempts = 0
        max_attempts = horizontal_wall_count * 3
        while walls_placed < horizontal_wall_count and attempts < max_attempts:
            attempts += 1
            x = maze_rng.randint(spawn_safe_zone + 200, width - 400)
            y = maze_rng.randint(150, height - 200)
            wall_width = maze_rng.randint(100, 400)  # Varied widths
            wall_height = 30  # Thick walls
            
            # Check if this wall would block the guaranteed path
            blocks_path = False
            for wx, wy in waypoints:
                # Check if wall overlaps with path waypoint area
                if (x < wx + segment_width//2 and x + wall_width > wx - segment_width//2 and
                    y < wy + segment_height//2 and y + wall_height > wy - segment_height//2):
                    blocks_path = True
                    break
            
            if not blocks_path:
                # Create horizontal wall platform
                wall = Platform(x, y, wall_width, wall_height, platform_type="normal", theme=self.theme)
                self.platforms.add(wall)
                self.all_sprites.add(wall)
                walls_placed += 1
        
        # Vertical walls - MANY MORE for a proper dense maze
        vertical_wall_count = 90 + level_def["difficulty"] * 10  # WAY more walls
        walls_placed = 0
        attempts = 0
        max_attempts = vertical_wall_count * 3
        while walls_placed < vertical_wall_count and attempts < max_attempts:
            attempts += 1
            x = maze_rng.randint(spawn_safe_zone + 200, width - 400)
            y = maze_rng.randint(150, height - 200)
            wall_width = 30  # Thick walls
            wall_height = maze_rng.randint(100, 300)  # Varied heights
            
            # Check if this wall would block the guaranteed path
            blocks_path = False
            for wx, wy in waypoints:
                # Check if wall overlaps with path waypoint area
                if (x < wx + segment_width//2 and x + wall_width > wx - segment_width//2 and
                    y < wy + segment_height//2 and y + wall_height > wy - segment_height//2):
                    blocks_path = True
                    break
            
            if not blocks_path:
                # Create vertical wall platform
                wall = Platform(x, y, wall_width, wall_height, platform_type="normal", theme=self.theme)
                self.platforms.add(wall)
                self.all_sprites.add(wall)
                walls_placed += 1
        
        # Add additional maze structure - create corridors and dead ends
        # Add some longer corridor walls
        corridor_count = 50 + level_def["difficulty"] * 5  # More corridors
        for _ in range(corridor_count):
            # Create longer walls for corridors
            if maze_rng.random() < 0.5:
                # Horizontal corridor
                x = maze_rng.randint(spawn_safe_zone + 200, width - 600)
                y = maze_rng.randint(150, height - 200)
                wall_width = maze_rng.randint(300, 500)  # Longer corridors
                wall_height = 30
                
                # Check if blocks path
                blocks_path = False
                for wx, wy in waypoints:
                    if (x < wx + segment_width//2 and x + wall_width > wx - segment_width//2 and
                        y < wy + segment_height//2 and y + wall_height > wy - segment_height//2):
                        blocks_path = True
                        break
                
                if not blocks_path:
                    wall = Platform(x, y, wall_width, wall_height, platform_type="normal", theme=self.theme)
                    self.platforms.add(wall)
                    self.all_sprites.add(wall)
            else:
                # Vertical corridor
                x = maze_rng.randint(spawn_safe_zone + 200, width - 400)
                y = maze_rng.randint(150, height - 300)
                wall_width = 30
                wall_height = maze_rng.randint(200, 350)  # Taller corridors
                
                # Check if blocks path
                blocks_path = False
                for wx, wy in waypoints:
                    if (x < wx + segment_width//2 and x + wall_width > wx - segment_width//2 and
                        y < wy + segment_height//2 and y + wall_height > wy - segment_height//2):
                        blocks_path = True
                        break
                
                if not blocks_path:
                    wall = Platform(x, y, wall_width, wall_height, platform_type="normal", theme=self.theme)
                    self.platforms.add(wall)
                    self.all_sprites.add(wall)
        
        # Add bubble walls - transparent bubble clusters (LOTS of them!)
        bubble_wall_count = 60 + level_def["difficulty"] * 10  # Many more bubble walls
        walls_placed = 0
        attempts = 0
        max_attempts = bubble_wall_count * 5
        while walls_placed < bubble_wall_count and attempts < max_attempts:
            attempts += 1
            x = maze_rng.randint(spawn_safe_zone + 200, width - 400)
            y = maze_rng.randint(150, height - 200)
            wall_width = maze_rng.randint(60, 180)
            wall_height = maze_rng.randint(60, 180)
            
            # Check if this bubble wall would block the guaranteed path
            blocks_path = False
            for wx, wy in waypoints:
                if (x < wx + segment_width//2 and x + wall_width > wx - segment_width//2 and
                    y < wy + segment_height//2 and y + wall_height > wy - segment_height//2):
                    blocks_path = True
                    break
            
            if not blocks_path:
                # Create bubble wall platform
                bubble_wall = Platform(x, y, wall_width, wall_height, platform_type="normal", theme=self.theme)
                bubble_wall.is_bubble_wall = True  # Mark as bubble wall
                self.platforms.add(bubble_wall)
                self.all_sprites.add(bubble_wall)
                walls_placed += 1
        
        # Add lots of moving platforms
        moving_platform_count = 20 + level_def["difficulty"] * 3
        for _ in range(moving_platform_count):
            x = maze_rng.randint(spawn_safe_zone + 200, width - 400)
            y = maze_rng.randint(100, height - 150)
            platform_width = maze_rng.randint(100, 180)
            platform_height = 20
            
            # Random movement type
            move_type = maze_rng.choice(["moving", "vertical_moving", "tetris_moving"])
            moving_platform = Platform(x, y, platform_width, platform_height, platform_type=move_type, theme=self.theme)
            moving_platform.original_x = x
            moving_platform.original_y = y
            moving_platform.move_offset = maze_rng.random() * 6.28  # Random starting phase
            self.platforms.add(moving_platform)
            self.all_sprites.add(moving_platform)
        
        # Add red static laser obstacles (no spinning) for Level 8
        laser_count = 8 + level_def["difficulty"]
        for _ in range(laser_count):
            x = maze_rng.randint(spawn_safe_zone + 300, width - 300)
            y = maze_rng.randint(150, height - 200)
            # Create static red laser obstacle (no rotation)
            laser = Obstacle(x, y, "spinning_laser")
            laser.rect.center = (x, y)  # Center on position (already set in __init__, but ensure it's correct)
            laser.draw_obstacle()  # Draw initial state
            self.obstacles.add(laser)
            self.all_sprites.add(laser)
        
        # Add coins throughout the maze for collection
        coin_count = 30 + level_def["difficulty"] * 5
        for _ in range(coin_count):
            x = maze_rng.randint(spawn_safe_zone + 100, width - 200)
            y = maze_rng.randint(100, height - 150)
            coin = Powerup(x, y, "coin")
            self.powerups.add(coin)
            self.all_sprites.add(coin)
        
        # Add underwater enemies: crabs, sharks, piranhas - MORE ENEMIES!
        enemy_rng = random.Random(9999 + self.current_level)
        enemy_count = 30 + level_def["difficulty"] * 5  # Many more enemies!
        
        # Distribute enemy types - place them throughout the maze
        enemies_placed = 0
        attempts = 0
        max_attempts = enemy_count * 15  # More attempts to place enemies
        while enemies_placed < enemy_count and attempts < max_attempts:
            attempts += 1
            x = enemy_rng.randint(spawn_safe_zone + 200, width - 300)
            y = enemy_rng.randint(150, height - 200)
            
            # Check if position is too close to spawn or waypoints
            too_close_to_path = False
            # Check spawn safe zone
            spawn_distance = ((x - spawn_safe_zone)**2 + (y - height//2)**2)**0.5
            if spawn_distance < 200:  # Keep enemies away from spawn
                too_close_to_path = True
            else:
                # Check waypoints
                for wx, wy in waypoints:
                    distance = ((x - wx)**2 + (y - wy)**2)**0.5
                    if distance < 100:  # Keep enemies away from path (reduced from 150)
                        too_close_to_path = True
                        break
            
            if not too_close_to_path:
                # Choose enemy type - more variety
                enemy_choice = enemies_placed % 6
                if enemy_choice < 2:
                    enemy_type = "crab"  # 2/6 = crabs
                elif enemy_choice < 4:
                    enemy_type = "shark"  # 2/6 = sharks
                else:
                    enemy_type = "piranha"  # 2/6 = piranhas
                
                enemy = Enemy(x, y, enemy_type, theme=self.theme)
                enemy.is_swimming = True  # Mark as swimming enemy
                # Initialize swimming behavior
                enemy.swim_timer = 0
                enemy.swim_direction = enemy_rng.choice([0, 1, 2, 3])
                enemy.swim_change_timer = enemy_rng.randint(0, 90)  # Random starting timer
                self.enemies.add(enemy)
                self.all_sprites.add(enemy)
                enemies_placed += 1
        
        # Add checkpoint at the end
        end_checkpoint = Checkpoint(width - 200, height // 2, theme=self.theme)
        self.checkpoints.add(end_checkpoint)
        self.all_sprites.add(end_checkpoint)
        
        # Safe spawn near start
        self.geometry_dash_spawn_x = spawn_safe_zone
        self.geometry_dash_spawn_y = height // 2
        
        # Initialize bubble wall of death for Level 8
        from constants import PLAYER_SPEED
        self.bubble_wall_mode = True
        self.bubble_wall_x = 0
        self.bubble_wall_speed = PLAYER_SPEED * 0.75  # Wall moves at 0.75x player speed (slightly slower than Level 7)
        self.bubble_wall_countdown_timer = 240  # 4 second countdown (60 FPS * 4)
        self.bubble_wall_countdown_active = True
        
        # Reset camera
        self.camera.x = 0
        self.camera.y = 0
        
        print(f"Underwater maze created: {width}x{height}, {enemies_placed} swimming enemies, {laser_count} spinning lasers, {len(self.platforms)} total platforms!")
    
    def _create_tetris_level(self):
        """Create a tetris-themed level with tetris wall of death, falling blocks, and tetris-colored platforms."""
        import random
        import math
        level_def = self.levels[self.current_level]
        width = level_def["width"]
        height = level_def["height"]
        
        # Use level dimensions
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
        
        from constants import PLAYER_SPEED, SAFE_JUMP_HEIGHT
        tetris_rng = random.Random(9999 + self.current_level)
        spawn_safe_zone = 400
        
        # Tetris colors for platforms
        tetris_colors = [
            (255, 0, 0),    # Red (I-piece)
            (0, 255, 0),    # Green (S-piece)
            (0, 0, 255),    # Blue (J-piece)
            (255, 255, 0),  # Yellow (O-piece)
            (255, 0, 255),  # Magenta (T-piece)
            (0, 255, 255),  # Cyan (Z-piece)
            (255, 165, 0),  # Orange (L-piece)
        ]
        
        # Create lots of tetris-colored platforms
        # Use smart level generator for accessible platforms
        generator = SmartLevelGenerator(width, height, level_def["difficulty"])
        platform_data = generator.generate_accessible_platforms()
        
        # Validate accessibility and add fixes if needed
        is_accessible = generator.validate_platform_accessibility()
        if not is_accessible:
            print(f"Level {self.current_level + 1}: Adding accessibility fixes...")
            generator.add_accessibility_fixes()
            generator.validate_platform_accessibility()
        
        # Get updated platform data after fixes
        platform_data = generator.platforms
        
        # Create platforms from generated data - all tetris-colored
        for platform_info in platform_data:
            # Choose random tetris color for each platform
            tetris_color = tetris_rng.choice(tetris_colors)
            platform = Platform(
                platform_info['x'], platform_info['y'], 
                platform_info['width'], platform_info['height'],
                platform_type=platform_info['type'], 
                theme=self.theme
            )
            # Mark platform as tetris-colored
            platform.tetris_color = tetris_color
            platform.is_tetris_platform = True
            self.platforms.add(platform)
            self.all_sprites.add(platform)
        
        # Add additional floating platforms for more interaction
        extra_platform_count = 30 + level_def["difficulty"] * 5
        for _ in range(extra_platform_count):
            x = tetris_rng.randint(spawn_safe_zone + 200, width - 400)
            y = tetris_rng.randint(100, height - 200)
            platform_width = tetris_rng.randint(120, 200)
            platform_height = 30
            tetris_color = tetris_rng.choice(tetris_colors)
            
            platform = Platform(x, y, platform_width, platform_height, platform_type="normal", theme=self.theme)
            platform.tetris_color = tetris_color
            platform.is_tetris_platform = True
            self.platforms.add(platform)
            self.all_sprites.add(platform)
        
        # Add falling tetris blocks from the sky
        falling_tetris_count = 20 + level_def["difficulty"] * 5
        for _ in range(falling_tetris_count):
            x = tetris_rng.randint(100, width - 100)
            y = tetris_rng.randint(-400, -50)  # Start above screen
            # Create falling tetris piece
            falling_tetris = Obstacle(x, y, "falling_tetris")
            falling_tetris.falling = True
            falling_tetris.fall_speed = 3.0 + tetris_rng.random() * 2.0
            falling_tetris.level_width = width  # Store level width for respawning
            self.obstacles.add(falling_tetris)
            self.all_sprites.add(falling_tetris)
        
        # Create evil tetris block enemies
        enemy_count = 15 + level_def["difficulty"] * 3
        for _ in range(enemy_count):
            x = tetris_rng.randint(spawn_safe_zone + 200, width - 300)
            y = tetris_rng.randint(150, height - 150)
            # Create tetris block enemy
            enemy = Enemy(x, y, "tetris_block", theme=self.theme)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)
        
        # Add checkpoints
        checkpoint_count = 3
        checkpoint_spacing = width // (checkpoint_count + 1)
        for i in range(1, checkpoint_count + 1):
            checkpoint_x = checkpoint_spacing * i
            checkpoint_y = height - 140
            checkpoint = Checkpoint(checkpoint_x, checkpoint_y, theme=self.theme)
            self.checkpoints.add(checkpoint)
            self.all_sprites.add(checkpoint)
        
        # Initialize tetris wall of death
        self.tetris_wall_mode = True
        self.tetris_wall_x = 0
        self.tetris_wall_speed = PLAYER_SPEED * 0.75  # Wall moves at 0.75x player speed
        self.tetris_wall_countdown_timer = 240  # 4 second countdown (60 FPS * 4)
        self.tetris_wall_countdown_active = True
        
        # Safe spawn position
        self.geometry_dash_spawn_x = spawn_safe_zone
        self.geometry_dash_spawn_y = height - 100
        
        # Reset camera
        self.camera.x = 0
        self.camera.y = 0
        
        print(f"Tetris level created: {width}x{height}, {enemy_count} tetris enemies, {falling_tetris_count} falling blocks, {len(self.platforms)} tetris platforms!")
    
    def _create_underwater_maze(self):
        """Create an underwater scrolling level (Level 8: Kraken Me Up, was Level 9)."""
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
        
        # Level 8 should have a rainbow star (bonus room on levels 1, 3, 5, 7, 9)
        if self.current_level == 7:  # Level 8 (0-indexed, was level 9)
            # Place one rainbow star
            star_cx = coin_rng.randint(3, 8) * segment - 100
            star_cy = coin_rng.randint(160, height - 220)
            rainbow_star = Powerup(star_cx, star_cy, "rainbow_star")
            self.powerups.add(rainbow_star)
            self.all_sprites.add(rainbow_star)
        
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
        
        # Level 9 should have a rainbow star (bonus room on levels 1, 3, 5, 7, 9)
        rainbow_star_placed = False
        if self.current_level == 8:  # Level 9 (0-indexed)
            # Place one rainbow star
            star_x = coin_rng.randint(200, 800)
            star_y = coin_rng.randint(150, 650)
            rainbow_star = Powerup(star_x, star_y, "rainbow_star")
            self.powerups.add(rainbow_star)
            self.all_sprites.add(rainbow_star)
            rainbow_star_placed = True
        
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
            jump_multiplier = 1.05 if self.current_level == 8 else 1.0
            # Use special spawn position for Geometry Dash level
            if hasattr(self, 'geometry_dash_spawn_x') and hasattr(self, 'geometry_dash_spawn_y'):
                spawn_x, spawn_y = self.geometry_dash_spawn_x, self.geometry_dash_spawn_y
            else:
                spawn_x, spawn_y = 100, 400
            self.player = Player(spawn_x, spawn_y, self.sound_manager, speed_multiplier, jump_multiplier, player_color=self.player_color)
            self.player._game = self  # Give player access to game state
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
        self.player = Player(spawn_x, spawn_y, self.sound_manager, speed_multiplier, jump_multiplier, player_color=self.player_color)
        self.all_sprites.add(self.player)
        self.camera.x = 0
        self.camera.y = 0
        self.state = GameState.PLAYING

    def restart_game(self):
        self.state = GameState.PLAYING
        self.lives = 3
        self.score = 0
        self.ros_stats_published = False  # Reset flag for new game
        # Reset victory-related attributes
        if hasattr(self, 'victory_points'):
            delattr(self, 'victory_points')
        if hasattr(self, 'final_score_with_victory'):
            delattr(self, 'final_score_with_victory')
        # Respect ROS start_level parameter if set
        if ROS_ENABLED:
            try:
                if rospy.has_param('start_level'):
                    self.current_level = rospy.get_param('start_level', 0)
                else:
                    self.current_level = 0
            except:
                self.current_level = 0
        else:
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
        self.player = Player(spawn_x, spawn_y, self.sound_manager, speed_multiplier, jump_multiplier, player_color=self.player_color)
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
                jump_multiplier = 1.05 if self.current_level == 8 else 1.0
                # Use special spawn position for Geometry Dash level
                if hasattr(self, 'geometry_dash_spawn_x') and hasattr(self, 'geometry_dash_spawn_y'):
                    spawn_x, spawn_y = self.geometry_dash_spawn_x, self.geometry_dash_spawn_y
                else:
                    spawn_x, spawn_y = 100, 400
                self.player = Player(spawn_x, spawn_y, self.sound_manager, speed_multiplier, jump_multiplier, player_color=self.player_color)
                self.player._game = self  # Give player access to game state
                self.all_sprites.add(self.player)
                self._needs_initial_load = False
                # If ROS enabled, go to Difficulty Select (will wait for user_name there)
                if ROS_ENABLED:
                    self.state = GameState.DIFFICULTY_SELECT
                else:
                    self.state = GameState.MENU
                return
        except Exception as e:
            print(f"Error during initial load: {e}")
            import traceback
            traceback.print_exc()
            self.state = GameState.MENU
            return
        
        # ROS Logic: Check if game is ready to start (difficulty and color selected)
        if ROS_ENABLED and self.state == GameState.DIFFICULTY_SELECT:
            try:
                # Check if ready_to_start_game is set (by difficulty_select_gui)
                if rospy.has_param('ready_to_start_game') and rospy.get_param('ready_to_start_game'):
                    if not hasattr(self, 'difficulty_selected'):
                        # Read difficulty from ROS parameter
                        difficulty = rospy.get_param('selected_difficulty', 'easy')
                        # Read start_level from parameter (set by game_node)
                        start_level = rospy.get_param('start_level', 0)
                        self.current_level = start_level
                        
                        # Store difficulty and level range
                        self.selected_difficulty = difficulty
                        if difficulty == "easy":
                            self.difficulty_start_level = 0
                            self.difficulty_end_level = 2
                        elif difficulty == "medium":
                            self.difficulty_start_level = 3
                            self.difficulty_end_level = 5
                        elif difficulty == "hard":
                            self.difficulty_start_level = 6
                            self.difficulty_end_level = 9
                        
                        self.difficulty_selected = True
                        # Start the game
                        self.start_game()
            except Exception as e:
                rospy.logwarn(f"Error checking ROS parameters: {e}")
                pass
        
        if self.state == GameState.PLAYING:
            self.camera.update(self.player)
            
            # Initialize result variable
            result = None
            
            # Handle bubble wall of death mechanics for Level 8
            if hasattr(self, 'bubble_wall_mode') and self.bubble_wall_mode:
                # Handle countdown timer
                if hasattr(self, 'bubble_wall_countdown_active') and self.bubble_wall_countdown_active:
                    self.bubble_wall_countdown_timer -= 1
                    if self.bubble_wall_countdown_timer <= 0:
                        self.bubble_wall_countdown_active = False
                        print("COUNTDOWN OVER! Bubble wall is now moving!")
                
                # Only move bubble wall after countdown is over
                if hasattr(self, 'bubble_wall_countdown_active') and not self.bubble_wall_countdown_active:
                    # Move bubble wall closer to player
                    self.bubble_wall_x += self.bubble_wall_speed
                    
                    # Check if bubble wall caught up to player
                    if self.bubble_wall_x >= self.player.rect.x - 50:
                        # Player is caught by bubble wall - death
                        result = "hit"
                    else:
                        result = self.player.update(self.platforms, self.enemies, self.powerups, self.obstacles, self.camera.x, self.camera.level_width)
                else:
                    # During countdown, normal player movement
                    result = self.player.update(self.platforms, self.enemies, self.powerups, self.obstacles, self.camera.x, self.camera.level_width)
            
            # Handle Geometry Dash spike wall mechanics
            elif hasattr(self, 'geometry_dash_mode') and self.geometry_dash_mode:
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
            elif hasattr(self, 'tetris_wall_mode') and self.tetris_wall_mode:
                # Tetris wall of death mechanics (Level 9)
                if hasattr(self, 'tetris_wall_countdown_active') and self.tetris_wall_countdown_active:
                    self.tetris_wall_countdown_timer -= 1
                    if self.tetris_wall_countdown_timer <= 0:
                        self.tetris_wall_countdown_active = False
                        print("COUNTDOWN OVER! Tetris wall is now moving!")
                
                # Only move tetris wall after countdown is over
                if hasattr(self, 'tetris_wall_countdown_active') and not self.tetris_wall_countdown_active:
                    # Move tetris wall closer to player
                    self.tetris_wall_x += self.tetris_wall_speed
                    
                    # Check if tetris wall caught up to player
                    if self.tetris_wall_x >= self.player.rect.x - 50:
                        # Player is caught by tetris wall - death
                        result = "hit"
                    else:
                        result = self.player.update(self.platforms, self.enemies, self.powerups, self.obstacles, self.camera.x, self.camera.level_width)
                else:
                    # During countdown, normal player movement
                    result = self.player.update(self.platforms, self.enemies, self.powerups, self.obstacles, self.camera.x, self.camera.level_width)
            else:
                result = self.player.update(self.platforms, self.enemies, self.powerups, self.obstacles, self.camera.x, self.camera.level_width)
            
            # Pass underwater_mode to player for swimming mechanics
            if hasattr(self, 'underwater_mode') and self.underwater_mode:
                self.player._game = self  # Give player access to game state
            
            # Check for checkpoint collisions
            checkpoint_collisions = pygame.sprite.spritecollide(self.player, self.checkpoints, False)
            for checkpoint in checkpoint_collisions:
                if not checkpoint.activated:
                    checkpoint.activate()
                    self.last_checkpoint = checkpoint
                    if self.sound_manager:
                        self.sound_manager.play('coin')  # Use coin sound for checkpoint activation
            
            # Check for regular powerup (coin) collisions
            powerup_collisions = pygame.sprite.spritecollide(self.player, self.powerups, True)
            if powerup_collisions:
                for powerup in powerup_collisions:
                    if hasattr(powerup, 'powerup_type'):
                        if powerup.powerup_type == "coin":
                            self.score += 100
                            if self.sound_manager:
                                self.sound_manager.play('coin')
                        elif powerup.powerup_type == "rainbow_star":
                            self.player.activate_star_powerup()
                            self.score += 500  # Bonus score for star powerup
            
            # Check for star powerup collisions (separate group)
            star_collisions = pygame.sprite.spritecollide(self.player, self.star_powerups, True)
            if star_collisions:
                self.player.activate_star_powerup()
                self.score += 500  # Bonus score for star powerup
            
            # Handle rainbow star collection (bonus room trigger)
            if result == "rainbow_star":
                # Rainbow star only transports to bonus room (no points)
                # Trigger bonus room only on levels 1, 3, 5, 7, 9 (0-indexed: 0, 2, 4, 6, 8)
                if self.current_level in [0, 2, 4, 6, 8] and self.current_level < len(self.levels):
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
                    
                    # Reset bubble wall mechanics on respawn
                    if hasattr(self, 'bubble_wall_mode') and self.bubble_wall_mode:
                        self.bubble_wall_x = 0  # Reset wall position
                        self.bubble_wall_countdown_timer = 240  # Reset countdown
                        self.bubble_wall_countdown_active = True  # Restart countdown
                        print("RESPAWN: Bubble wall reset, countdown restarted!")
                    # Reset Geometry Dash mechanics on respawn
                    elif hasattr(self, 'geometry_dash_mode') and self.geometry_dash_mode:
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
                # Check if we've completed the difficulty group
                if hasattr(self, 'selected_difficulty') and hasattr(self, 'difficulty_end_level'):
                    if self.current_level >= self.difficulty_end_level:
                        # Completed all levels in difficulty group - show victory!
                        self.state = GameState.VICTORY
                        # Calculate and add victory points
                        self._calculate_victory_points()
                    else:
                        self.state = GameState.LEVEL_COMPLETE
                else:
                    # No difficulty selected (normal mode), use old behavior
                    self.state = GameState.LEVEL_COMPLETE
            self.enemies.update(self.platforms)
            self.powerups.update()
            self.star_powerups.update()
            self.platforms.update()
            self.keys.update()
            # Update falling meatballs
            level_def = self.levels[self.current_level]
            for obstacle in self.obstacles:
                if hasattr(obstacle, 'update'):
                    obstacle.update(level_def["height"])
        
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
                    self.player = Player(400, 1100, self.sound_manager, player_color=self.player_color)
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
                jump_multiplier = 1.05 if self.current_level == 8 else 1.0
                # Use special spawn position for Geometry Dash level
                if hasattr(self, 'geometry_dash_spawn_x') and hasattr(self, 'geometry_dash_spawn_y'):
                    spawn_x, spawn_y = self.geometry_dash_spawn_x, self.geometry_dash_spawn_y
                else:
                    spawn_x, spawn_y = 100, 400
                self.player = Player(spawn_x, spawn_y, self.sound_manager, speed_multiplier, jump_multiplier, player_color=self.player_color)
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
        elif self.state == GameState.DIFFICULTY_SELECT:
            # When ROS is enabled, skip the built-in difficulty select screen
            # The separate difficulty_select_gui.py node handles this
            if not ROS_ENABLED:
                self.draw_difficulty_select()
            # When ROS is enabled, just show a blank screen (the separate GUI handles selection)
            # The game will start automatically when ready_to_start_game parameter is set
        elif self.state == GameState.VICTORY:
            self._draw_victory()
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
        
        # Draw bubble wall of death for Level 8
        if hasattr(self, 'bubble_wall_mode') and self.bubble_wall_mode:
            # Draw dramatic countdown timer
            if hasattr(self, 'bubble_wall_countdown_active') and self.bubble_wall_countdown_active:
                countdown_seconds = max(1, ((self.bubble_wall_countdown_timer - 1) // 60) + 1)
                frames_remaining = self.bubble_wall_countdown_timer % 60
                
                # Dramatic pulsing effect - larger and brighter as countdown approaches 0
                pulse_factor = 1.0 + 0.3 * abs(math.sin(frames_remaining * 0.2))
                if countdown_seconds <= 3:
                    size_multiplier = 1.0 + (0.5 * (4 - countdown_seconds) / 3)  # Gets bigger: 1.5x at 1, 1.33x at 2, 1.17x at 3
                else:
                    size_multiplier = 1.0
                
                # Dark overlay with blue tint for underwater
                overlay = pygame.Surface((self.screen_width, self.screen_height))
                overlay_alpha = 180 if countdown_seconds <= 3 else 120
                overlay.set_alpha(overlay_alpha)
                overlay.fill((0, 50, 100))  # Blue tint for underwater
                self.screen.blit(overlay, (0, 0))
                
                # Large dramatic countdown box with pulsing effect
                box_size = int(300 * size_multiplier * pulse_factor)
                countdown_rect = pygame.Rect(
                    self.screen_width // 2 - box_size // 2,
                    self.screen_height // 2 - box_size // 2,
                    box_size,
                    box_size
                )
                border_color_intensity = min(255, 100 + (countdown_seconds <= 3) * 155)
                border_width = 8 if countdown_seconds <= 3 else 5
                # Blue border for underwater theme
                pygame.draw.rect(self.screen, (0, border_color_intensity, 255), countdown_rect, border_width)
                
                # Inner glow effect for last 3 seconds
                if countdown_seconds <= 3:
                    inner_glow = pygame.Rect(
                        countdown_rect.x + 10, countdown_rect.y + 10,
                        countdown_rect.width - 20, countdown_rect.height - 20
                    )
                    glow_alpha = int(100 * (4 - countdown_seconds) / 3)
                    glow_surface = pygame.Surface((inner_glow.width, inner_glow.height))
                    glow_surface.set_alpha(glow_alpha)
                    glow_surface.fill((100, 200, 255))  # Light blue glow
                    self.screen.blit(glow_surface, inner_glow.topleft)
                
                # Dramatic countdown number - huge and pulsing
                from constants import ERROR_RED
                font_size = int(200 * size_multiplier * pulse_factor)
                font = pygame.font.Font(None, font_size)
                
                # Draw countdown number with custom color (red for urgency, cyan otherwise)
                countdown_color = ERROR_RED if countdown_seconds <= 3 else (0, 255, 255)  # Cyan for underwater
                number_text = str(countdown_seconds)
                number_surface = font.render(number_text, True, countdown_color)
                number_rect = number_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                
                # Outline for visibility
                outline_color = (0, 0, 0) if countdown_seconds <= 3 else (0, 100, 150)
                outline_surface = font.render(number_text, True, outline_color)
                outline_rect = outline_surface.get_rect(center=(self.screen_width // 2 + 2, self.screen_height // 2 + 2))
                self.screen.blit(outline_surface, outline_rect)
                self.screen.blit(number_surface, number_rect)
                
                # Warning text below countdown
                if countdown_seconds <= 3:
                    warning_text = "BUBBLE WALL INCOMING!"
                else:
                    warning_text = "PREPARE TO SWIM!"
                
                warning_font = pygame.font.Font(None, 48)
                warning_surface = warning_font.render(warning_text, True, (255, 255, 255))
                warning_rect = warning_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 150))
                self.screen.blit(warning_surface, warning_rect)
            else:
                # Countdown over - draw bubble wall
                bubble_wall_screen_x = self.bubble_wall_x - self.camera.x
                if -100 < bubble_wall_screen_x < self.screen_width + 100:
                    # Draw bubble wall - full height, blue bubbles
                    bubble_wall_rect = pygame.Rect(bubble_wall_screen_x, 0, 60, self.screen_height)
                    
                    # Base blue background
                    pygame.draw.rect(self.screen, (50, 150, 255), bubble_wall_rect)  # Deep blue
                    pygame.draw.rect(self.screen, (0, 100, 200), bubble_wall_rect, 3)  # Darker blue border
                    
                    # Draw bubbles across the wall
                    import random
                    bubble_rng = random.Random(8888)  # Fixed seed for consistent bubbles
                    for y in range(20, self.screen_height - 20, 40):
                        for x_offset in range(10, 50, 20):
                            bubble_x = bubble_wall_screen_x + x_offset
                            bubble_y = y + bubble_rng.randint(-10, 10)
                            bubble_size = bubble_rng.randint(8, 15)
                            
                            # Main bubble
                            pygame.draw.circle(self.screen, (100, 200, 255), (bubble_x, bubble_y), bubble_size)
                            pygame.draw.circle(self.screen, (50, 150, 255), (bubble_x, bubble_y), bubble_size, 2)
                            
                            # Bubble highlight
                            highlight_x = bubble_x - bubble_size // 3
                            highlight_y = bubble_y - bubble_size // 3
                            highlight_size = bubble_size // 3
                            pygame.draw.circle(self.screen, (200, 240, 255), (highlight_x, highlight_y), highlight_size)
                            
                            # Small bubbles around main bubble
                            for _ in range(2):
                                small_x = bubble_x + bubble_rng.randint(-bubble_size, bubble_size)
                                small_y = bubble_y + bubble_rng.randint(-bubble_size, bubble_size)
                                small_size = bubble_rng.randint(3, 6)
                                if 5 <= small_x - bubble_wall_screen_x < 55:
                                    pygame.draw.circle(self.screen, (100, 200, 255), (small_x, small_y), small_size)
                                    pygame.draw.circle(self.screen, (50, 150, 255), (small_x, small_y), small_size, 1)
                    
                    # Warning text on wall
                    warning_font = pygame.font.Font(None, 24)
                    warning_text = "!!!"
                    warning_surface = warning_font.render(warning_text, True, (255, 255, 255))
                    warning_rect = warning_surface.get_rect(center=(bubble_wall_screen_x + 30, self.screen_height // 2))
                    self.screen.blit(warning_surface, warning_rect)
        
        # Draw Tetris wall of death for Level 9
        elif hasattr(self, 'tetris_wall_mode') and self.tetris_wall_mode:
            # Draw dramatic countdown timer
            if hasattr(self, 'tetris_wall_countdown_active') and self.tetris_wall_countdown_active:
                countdown_seconds = max(1, ((self.tetris_wall_countdown_timer - 1) // 60) + 1)
                frames_remaining = self.tetris_wall_countdown_timer % 60
                
                # Dramatic pulsing effect
                pulse_factor = 1.0 + 0.3 * abs(math.sin(frames_remaining * 0.2))
                if countdown_seconds <= 3:
                    size_multiplier = 1.0 + (0.5 * (4 - countdown_seconds) / 3)
                else:
                    size_multiplier = 1.0
                
                # Dark overlay with tetris colors
                overlay = pygame.Surface((self.screen_width, self.screen_height))
                overlay_alpha = 180 if countdown_seconds <= 3 else 120
                overlay.set_alpha(overlay_alpha)
                overlay.fill((50, 0, 100))  # Purple tint for tetris theme
                self.screen.blit(overlay, (0, 0))
                
                # Large dramatic countdown box with pulsing effect
                box_size = int(300 * size_multiplier * pulse_factor)
                countdown_rect = pygame.Rect(
                    self.screen_width // 2 - box_size // 2,
                    self.screen_height // 2 - box_size // 2,
                    box_size,
                    box_size
                )
                border_color_intensity = min(255, 100 + (countdown_seconds <= 3) * 155)
                border_width = 8 if countdown_seconds <= 3 else 5
                # Tetris-colored border
                pygame.draw.rect(self.screen, (255, 0, 255), countdown_rect, border_width)
                
                # Inner glow effect for last 3 seconds
                if countdown_seconds <= 3:
                    inner_glow = pygame.Rect(
                        countdown_rect.x + 10, countdown_rect.y + 10,
                        countdown_rect.width - 20, countdown_rect.height - 20
                    )
                    glow_alpha = int(100 * (4 - countdown_seconds) / 3)
                    glow_surface = pygame.Surface((inner_glow.width, inner_glow.height))
                    glow_surface.set_alpha(glow_alpha)
                    glow_surface.fill((255, 0, 255))  # Magenta glow
                    self.screen.blit(glow_surface, inner_glow.topleft)
                
                # Dramatic countdown number
                from constants import ERROR_RED
                font_size = int(200 * size_multiplier * pulse_factor)
                font = pygame.font.Font(None, font_size)
                countdown_color = ERROR_RED if countdown_seconds <= 3 else (255, 0, 255)
                number_text = str(countdown_seconds)
                number_surface = font.render(number_text, True, countdown_color)
                number_rect = number_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                
                # Outline for visibility
                outline_color = (0, 0, 0) if countdown_seconds <= 3 else (100, 0, 150)
                outline_surface = font.render(number_text, True, outline_color)
                outline_rect = outline_surface.get_rect(center=(self.screen_width // 2 + 2, self.screen_height // 2 + 2))
                self.screen.blit(outline_surface, outline_rect)
                self.screen.blit(number_surface, number_rect)
                
                # Warning text below countdown
                if countdown_seconds <= 3:
                    warning_text = "TETRIS WALL INCOMING!"
                else:
                    warning_text = "PREPARE FOR TETRIS!"
                
                warning_font = pygame.font.Font(None, 48)
                warning_surface = warning_font.render(warning_text, True, (255, 255, 255))
                warning_rect = warning_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 150))
                self.screen.blit(warning_surface, warning_rect)
            else:
                # Countdown over - draw tetris wall
                tetris_wall_screen_x = self.tetris_wall_x - self.camera.x
                if -100 < tetris_wall_screen_x < self.screen_width + 100:
                    # Draw tetris wall - full height, made of tetris blocks
                    tetris_wall_rect = pygame.Rect(tetris_wall_screen_x, 0, 60, self.screen_height)
                    
                    # Tetris colors
                    tetris_colors = [
                        (255, 0, 0),    # Red
                        (0, 255, 0),    # Green
                        (0, 0, 255),    # Blue
                        (255, 255, 0),  # Yellow
                        (255, 0, 255),  # Magenta
                        (0, 255, 255),  # Cyan
                        (255, 165, 0),  # Orange
                    ]
                    
                    # Draw tetris blocks stacked in the wall
                    block_size = 30
                    import random
                    tetris_rng = random.Random(9999)  # Fixed seed for consistent pattern
                    for y in range(0, self.screen_height, block_size):
                        for x_offset in range(0, 60, block_size):
                            block_x = tetris_wall_screen_x + x_offset
                            block_y = y
                            block_color = tetris_colors[(y // block_size + x_offset // block_size) % len(tetris_colors)]
                            
                            # Draw tetris block
                            block_rect = pygame.Rect(block_x, block_y, block_size, block_size)
                            pygame.draw.rect(self.screen, block_color, block_rect)
                            pygame.draw.rect(self.screen, BLACK, block_rect, 2)
                            
                            # Grid lines inside block
                            pygame.draw.line(self.screen, BLACK, (block_x, block_y + block_size//2), (block_x + block_size, block_y + block_size//2), 1)
                            pygame.draw.line(self.screen, BLACK, (block_x + block_size//2, block_y), (block_x + block_size//2, block_y + block_size), 1)
                    
                    # Warning text on wall
                    warning_font = pygame.font.Font(None, 24)
                    warning_text = "!!!"
                    warning_surface = warning_font.render(warning_text, True, (255, 255, 255))
                    warning_rect = warning_surface.get_rect(center=(tetris_wall_screen_x + 30, self.screen_height // 2))
                    self.screen.blit(warning_surface, warning_rect)
        
        # Draw Geometry Dash mode elements
        elif hasattr(self, 'geometry_dash_mode') and self.geometry_dash_mode:
            # Draw dramatic countdown timer
            if hasattr(self, 'countdown_active') and self.countdown_active:
                countdown_seconds = max(1, ((self.countdown_timer - 1) // 60) + 1)
                frames_remaining = self.countdown_timer % 60
                
                # Dramatic pulsing effect - larger and brighter as countdown approaches 0
                pulse_factor = 1.0 + (0.3 * (1 - frames_remaining / 60))  # Pulse from 1.0 to 1.3
                size_multiplier = 1.0
                if countdown_seconds <= 3:
                    # Extra dramatic for last 3 seconds
                    size_multiplier = 1.0 + (0.5 * (4 - countdown_seconds) / 3)  # Gets bigger: 1.5x at 1, 1.33x at 2, 1.17x at 3
                
                # Create dramatic overlay - darken screen
                overlay = pygame.Surface((self.screen_width, self.screen_height))
                overlay_alpha = 180 if countdown_seconds <= 3 else 120
                overlay.set_alpha(overlay_alpha)
                overlay.fill((0, 0, 0))
                self.screen.blit(overlay, (0, 0))
                
                # Large dramatic countdown box with pulsing effect
                box_size = int(300 * size_multiplier * pulse_factor)
                countdown_rect = pygame.Rect(
                    self.screen_width//2 - box_size//2, 
                    self.screen_height//2 - box_size//2, 
                    box_size, 
                    box_size
                )
                
                # Pulsing green border - brighter when close to 0
                border_color_intensity = min(255, 100 + (countdown_seconds <= 3) * 155)
                border_width = 8 if countdown_seconds <= 3 else 5
                pygame.draw.rect(self.screen, (0, border_color_intensity, 0), countdown_rect, border_width)
                
                # Inner glow effect for last 3 seconds
                if countdown_seconds <= 3:
                    inner_rect = pygame.Rect(
                        countdown_rect.x + 10, countdown_rect.y + 10,
                        countdown_rect.width - 20, countdown_rect.height - 20
                    )
                    glow_surface = pygame.Surface((inner_rect.width, inner_rect.height))
                    glow_surface.set_alpha(100)
                    glow_surface.fill((0, 255, 0))
                    self.screen.blit(glow_surface, inner_rect.topleft)
                
                # Dramatic countdown number - huge and pulsing
                number_size = int(200 * size_multiplier * pulse_factor)
                from constants import ERROR_RED
                
                # Draw countdown number with custom color (red for urgency, green otherwise)
                countdown_color = ERROR_RED if countdown_seconds <= 3 else (0, 255, 0)
                font = pygame.font.Font(None, number_size)
                number_text = str(countdown_seconds)
                number_surface = font.render(number_text, True, countdown_color)
                number_rect = number_surface.get_rect(center=(self.screen_width//2, self.screen_height//2 - 20))
                
                # Add dramatic outline for visibility
                outline_color = (0, 0, 0) if countdown_seconds <= 3 else (0, 200, 0)
                for dx in (-3, -2, -1, 1, 2, 3):
                    for dy in (-3, -2, -1, 1, 2, 3):
                        outline_surface = font.render(number_text, True, outline_color)
                        self.screen.blit(outline_surface, (number_rect.x + dx, number_rect.y + dy))
                
                # Draw main number
                self.screen.blit(number_surface, number_rect)
                
                # Warning text below countdown
                if countdown_seconds <= 3:
                    warning_text = "WALL OF DEATH INCOMING!"
                    self.ui.draw_bubble_text(self.screen, warning_text, 
                                           self.screen_width//2, self.screen_height//2 + 150, 
                                           center=True, size=36)
                else:
                    warning_text = "PREPARE TO RUN!"
                    self.ui.draw_bubble_text(self.screen, warning_text, 
                                           self.screen_width//2, self.screen_height//2 + 150, 
                                           center=True, size=28)
                
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

    def _calculate_victory_points(self):
        """Calculate victory points based on difficulty completed."""
        if not hasattr(self, 'selected_difficulty'):
            return
        
        # Base victory points by difficulty
        if self.selected_difficulty == "easy":
            victory_points = 500
        elif self.selected_difficulty == "medium":
            victory_points = 1000
        elif self.selected_difficulty == "hard":
            victory_points = 2000
        else:
            victory_points = 0
        
        # Store victory points (will be added to score)
        self.victory_points = victory_points
        self.final_score_with_victory = self.score + victory_points
        
        rospy.loginfo(f"Victory! Difficulty: {self.selected_difficulty}, Base Score: {self.score}, Victory Points: {victory_points}, Final: {self.final_score_with_victory}")

    def _publish_victory_stats(self):
        """Publish victory stats to ROS."""
        if ROS_ENABLED and hasattr(self, 'ros_pub_stats') and hasattr(self, 'final_score_with_victory'):
            msg = Int64()
            msg.data = self.final_score_with_victory
            try:
                self.ros_pub_stats.publish(msg)
                rospy.loginfo(f"ROS: Published victory score {self.final_score_with_victory}")
                self.ros_stats_published = True
                # Also update the score for display
                self.score = self.final_score_with_victory
            except Exception as e:
                rospy.logerr(f"Failed to publish victory stats: {e}")

    def _draw_victory(self):
        """Draw victory screen after completing difficulty group."""
        # Publish stats immediately when victory screen is shown (only once)
        if ROS_ENABLED and not self.ros_stats_published and hasattr(self, 'ros_pub_stats') and hasattr(self, 'final_score_with_victory'):
            msg = Int64()
            msg.data = self.final_score_with_victory
            try:
                self.ros_pub_stats.publish(msg)
                rospy.loginfo(f"ROS: Published victory score {self.final_score_with_victory}")
                self.ros_stats_published = True
                # Also update the score for display
                self.score = self.final_score_with_victory
            except Exception as e:
                rospy.logerr(f"Failed to publish victory stats: {e}")
        
        self.bg.draw(self.screen, self.current_level, is_bonus_room=False)
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(140)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Victory title
        difficulty_name = self.selected_difficulty.capitalize() if hasattr(self, 'selected_difficulty') else "Difficulty"
        self.ui.draw_cheese_title(self.screen, f"{difficulty_name} Difficulty", self.screen_width//2, 80, center=True, size=64)
        self.ui.draw_cheese_title(self.screen, "COMPLETED!", self.screen_width//2, 150, center=True, size=96)
        
        # Show stats
        if hasattr(self, 'victory_points'):
            self.ui.draw_bubble_text(self.screen, f"Base Score: {self.score:,}", self.screen_width//2, 280, center=True, size=40)
            self.ui.draw_bubble_text(self.screen, f"Victory Bonus: +{self.victory_points:,}", self.screen_width//2, 330, center=True, size=36, color=MINT_GREEN)
            self.ui.draw_bubble_text(self.screen, f"Final Score: {self.final_score_with_victory:,}", self.screen_width//2, 390, center=True, size=48, color=SOFT_YELLOW)
        
        # Show completed levels
        if hasattr(self, 'difficulty_start_level') and hasattr(self, 'difficulty_end_level'):
            start = self.difficulty_start_level + 1
            end = self.difficulty_end_level + 1
            self.ui.draw_bubble_text(self.screen, f"Levels {start}-{end} Completed!", self.screen_width//2, 450, center=True, size=32)
        
        # Continue button
        self.ui.draw_cheese_button(self.screen, "Press SPACE/ENTER to Continue", self.screen_width//2, self.screen_height - 100, width=500)
        
        # Update high score
        if hasattr(self, 'final_score_with_victory'):
            if self.final_score_with_victory > self.high_score:
                self.high_score = self.final_score_with_victory
                self.save_high_score()

    def _draw_game_over(self):
        # ROS Logic: Publish stats if not already done
        if ROS_ENABLED and not self.ros_stats_published and hasattr(self, 'ros_pub_stats'):
            msg = Int64()
            msg.data = self.score
            try:
                self.ros_pub_stats.publish(msg)
                rospy.loginfo(f"ROS: Published final score {self.score}")
                self.ros_stats_published = True
            except Exception as e:
                rospy.logerr(f"Failed to publish stats: {e}")
        
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

    def set_difficulty(self, difficulty):
        """Set game difficulty via ROS service and start game."""
        # Call ROS service
        if ROS_ENABLED:
            rospy.wait_for_service('difficulty')
            try:
                set_diff = rospy.ServiceProxy('difficulty', SetGameDifficulty)
                resp = set_diff(difficulty)
                if resp.success:
                    rospy.loginfo(f"Difficulty set to {difficulty}")
                    
                    # Read start_level from parameter (set by game_node)
                    try:
                        start_level = rospy.get_param('start_level', 0)
                        self.current_level = start_level
                    except:
                        # Fallback mapping
                        if difficulty == "easy":
                            self.current_level = 0
                        elif difficulty == "medium":
                            self.current_level = 3
                        elif difficulty == "hard":
                            self.current_level = 6
                    
                    self.difficulty_selected = True
                    # Store difficulty and level range
                    self.selected_difficulty = difficulty
                    if difficulty == "easy":
                        self.difficulty_start_level = 0
                        self.difficulty_end_level = 2  # Levels 1-3 (indices 0-2)
                    elif difficulty == "medium":
                        self.difficulty_start_level = 3
                        self.difficulty_end_level = 5  # Levels 4-6 (indices 3-5)
                    elif difficulty == "hard":
                        self.difficulty_start_level = 6
                        self.difficulty_end_level = 9  # Levels 7-10 (indices 6-9)
                    self.start_game()
                else:
                    rospy.logwarn(f"Failed to set difficulty: {resp.message}")
            except Exception as e:
                rospy.logerr(f"Service call failed: {e}")
        else:
            # Fallback if ROS not enabled (testing)
            if difficulty == "easy":
                self.current_level = 0
                self.difficulty_start_level = 0
                self.difficulty_end_level = 2
            elif difficulty == "medium":
                self.current_level = 3
                self.difficulty_start_level = 3
                self.difficulty_end_level = 5
            elif difficulty == "hard":
                self.current_level = 6
                self.difficulty_start_level = 6
                self.difficulty_end_level = 9
            self.selected_difficulty = difficulty
            self.start_game()

    def ros_keyboard_callback(self, msg):
        """Handle keyboard messages from ROS control_node."""
        if not ROS_ENABLED:
            return
        
        direction = msg.data
        rospy.loginfo(f"GUI Game: Received keyboard message from ROS: {direction}")
        
        # Process keyboard input for all states (but player only uses it when playing)
        if direction in ["LEFT", "RIGHT", "UP", "DOWN"]:
            # Set the direction to True (key pressed)
            # Keep it True for a few frames so player.update() can read it
            self.ros_keyboard_state[direction] = True
            if self.state == GameState.PLAYING:
                rospy.loginfo(f"GUI Game: Processing ROS keyboard input: {direction} (game is playing)")
            else:
                rospy.logdebug(f"GUI Game: Received ROS keyboard '{direction}' but game state is {self.state} (will be used when playing)")
        else:
            rospy.logwarn(f"GUI Game: Received unknown keyboard direction: {direction}")
        # Note: We don't filter out messages from ourselves because
        # the control_node and game can both publish, and game_node subscribes to all
    
    def set_player_color(self, color):
        """Set player color and update ROS parameter."""
        # color: 1 = Red, 2 = Purple, 3 = Blue
        if color in [1, 2, 3]:
            self.player_color = color
            if ROS_ENABLED:
                try:
                    rospy.set_param('change_player_color', color)
                    rospy.loginfo(f"Player color set to {color}")
                except:
                    pass
            # Update player color if player exists
            if hasattr(self, 'player') and self.player:
                self.player.player_color = color
                # Update sprite animator to load correct colored sprites
                self.player.update_sprite_animator_color()
                self.player.draw_character()

    def draw_difficulty_select(self):
        """Draw difficulty selection screen."""
        # Draw background
        self.bg.draw(self.screen, 0, is_bonus_room=False)
        
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Check if we have user name
        user_name = None
        if ROS_ENABLED:
            try:
                if rospy.has_param('user_name'):
                    user_name = rospy.get_param('user_name')
            except:
                pass
        
        if user_name:
            self.ui.draw_cheese_title(self.screen, f"Hello, {user_name}!", self.screen_width//2, 60, center=True, size=64)
            self.ui.draw_bubble_text(self.screen, "Select Difficulty:", self.screen_width//2, 130, center=True, size=48)
            
            # Buttons
            y = 200
            self.ui.draw_cheese_button(self.screen, "1. Easy (Levels 1-3)", self.screen_width//2, y, width=400)
            self.ui.draw_cheese_button(self.screen, "2. Medium (Levels 4-6)", self.screen_width//2, y + 70, width=400)
            self.ui.draw_cheese_button(self.screen, "3. Hard (Levels 7-10)", self.screen_width//2, y + 140, width=400)
            
            # Color selection
            color_y = y + 220
            self.ui.draw_bubble_text(self.screen, "Select Character Color:", self.screen_width//2, color_y, center=True, size=40)
            
            # Color buttons
            color_btn_y = color_y + 50
            color_btn_width = 200
            color_spacing = 50
            
            # Red button
            red_selected = "✓ " if self.player_color == 1 else ""
            self.ui.draw_cheese_button(self.screen, f"{red_selected}R - Red", self.screen_width//2 - color_btn_width - color_spacing, color_btn_y, width=color_btn_width)
            
            # Purple button (default)
            purple_selected = "✓ " if self.player_color == 2 else ""
            self.ui.draw_cheese_button(self.screen, f"{purple_selected}P - Purple", self.screen_width//2, color_btn_y, width=color_btn_width)
            
            # Blue button
            blue_selected = "✓ " if self.player_color == 3 else ""
            self.ui.draw_cheese_button(self.screen, f"{blue_selected}B - Blue", self.screen_width//2 + color_btn_width + color_spacing, color_btn_y, width=color_btn_width)
            
            # Character preview
            preview_y = color_btn_y + 100
            self.ui.draw_bubble_text(self.screen, "Preview:", self.screen_width//2, preview_y, center=True, size=32)
            
            # Draw character preview with selected color
            if not hasattr(self, 'preview_player') or not self.preview_player:
                from entities import Player
                # Create preview player at origin (we'll position it manually when drawing)
                self.preview_player = Player(0, 0, None, 1.0, 1.0, player_color=self.player_color)
                self.preview_player.sprite_animator.set_animation("idle", True)
            
            # Update preview player color if changed
            if self.preview_player.player_color != self.player_color:
                self.preview_player.player_color = self.player_color
                self.preview_player.draw_character()
            
            # Update preview animation
            self.preview_player.sprite_animator.update()
            self.preview_player.draw_character()
            
            # Draw preview character centered
            preview_sprite = self.preview_player.image
            preview_rect = preview_sprite.get_rect(center=(self.screen_width//2, preview_y + 100))
            self.screen.blit(preview_sprite, preview_rect)
            
            self.ui.draw_bubble_text(self.screen, "Press 1, 2, or 3 to select difficulty", self.screen_width//2, preview_y + 150, center=True, size=28)
        else:
            self.ui.draw_cheese_title(self.screen, "Welcome!", self.screen_width//2, 100, center=True, size=72)
            self.ui.draw_bubble_text(self.screen, "Please enter your details", self.screen_width//2, 200, center=True, size=48)
            self.ui.draw_bubble_text(self.screen, "in the terminal window...", self.screen_width//2, 250, center=True, size=48)


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
