import pygame
import sys
import random
from enum import Enum

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Pastel Color Scheme
WHITE = (255, 255, 255)
BLACK = (50, 50, 50)  # Softer black
CREAM = (255, 253, 240)
SOFT_BLUE = (173, 216, 230)
SKY_BLUE = (135, 206, 235)
LAVENDER = (230, 230, 250)
SOFT_PURPLE = (221, 160, 221)
LIGHT_PURPLE = (238, 203, 238)
PASTEL_GREEN = (152, 251, 152)
SAGE_GREEN = (159, 197, 159)
MINT_GREEN = (189, 252, 201)
SOFT_YELLOW = (255, 255, 224)
PEACH = (255, 218, 185)
CORAL = (255, 183, 178)
SOFT_PINK = (255, 182, 193)
DUSTY_ROSE = (188, 143, 143)
BEIGE = (245, 245, 220)
LIGHT_BROWN = (205, 183, 158)
MOUNTAIN_PURPLE = (176, 196, 222)
MOUNTAIN_BLUE = (119, 136, 153)

# Physics
GRAVITY = 0.8
JUMP_STRENGTH = -15
PLAYER_SPEED = 5
ENEMY_SPEED = 2

# Level dimensions
LEVEL_WIDTH = 3200
LEVEL_HEIGHT = 600

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    PAUSED = 4
    LEVEL_COMPLETE = 5

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.enabled = False
        self.volume = 0.3  # Default volume (30%)
        
        # Try to enable sound system and create sounds
        try:
            # Set mixer volume
            pygame.mixer.set_num_channels(8)
            
            # Create simple sound effects
            self.create_sound_effects()
            self.enabled = True
            print("Sound system enabled")
        except Exception as e:
            print(f"Sound system disabled: {e}")
            self.enabled = False
    
    def create_sound_effects(self):
        """Create simple sound effects using basic waveforms"""
        try:
            # Create simple placeholder sounds with different frequencies
            # These will be very quiet and simple
            
            # Create basic sounds using simple buffers
            self.sounds['coin'] = self.create_simple_sound(800, 0.1)
            self.sounds['enemy_kill'] = self.create_simple_sound(400, 0.15)
            self.sounds['jump'] = self.create_simple_sound(600, 0.08)
            self.sounds['hit'] = self.create_simple_sound(200, 0.2)
            
            # Set volumes
            for sound in self.sounds.values():
                sound.set_volume(self.volume * 0.3)  # Very quiet
            
        except Exception as e:
            print(f"Could not create sound effects: {e}")
            self.enabled = False
    
    def create_simple_sound(self, frequency, duration):
        """Create a very simple sound"""
        try:
            # Create a simple buffer with basic wave
            sample_rate = 22050
            frames = int(duration * sample_rate)
            
            # Create simple sine wave as bytes
            import math
            wave_data = []
            for i in range(frames):
                t = float(i) / sample_rate
                # Simple sine wave with envelope
                wave = math.sin(2 * math.pi * frequency * t)
                envelope = max(0, 1 - (i / frames))  # Fade out
                sample = int(wave * envelope * 8000)  # Very quiet
                # Convert to bytes (16-bit signed)
                wave_data.extend([sample & 0xFF, (sample >> 8) & 0xFF])
            
            # Create sound from buffer
            buffer = bytes(wave_data)
            return pygame.mixer.Sound(buffer=buffer)
            
        except Exception as e:
            print(f"Could not create simple sound: {e}")
            # Return silent sound
            return pygame.mixer.Sound(buffer=b'\x00\x00' * 1000)
    
    
    def set_volume(self, volume):
        """Set master volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
    
    def play(self, sound_name):
        """Play a sound effect"""
        if self.enabled and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"Could not play sound {sound_name}: {e}")

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, sound_manager=None):
        super().__init__()
        self.image = pygame.Surface((32, 48), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Physics
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.jump_count = 0
        self.max_jumps = 1
        
        # Animation
        self.facing_right = True
        
        # Sound
        self.sound_manager = sound_manager
        
        # Draw the character
        self.draw_character()
    
    def draw_character(self):
        self.image.fill((0, 0, 0, 0))  # Clear with transparency
        
        # Body (soft purple rounded rectangle)
        pygame.draw.ellipse(self.image, SOFT_PURPLE, (4, 12, 24, 32))
        pygame.draw.ellipse(self.image, DUSTY_ROSE, (4, 12, 24, 32), 2)
        
        # Head (soft purple circle)
        pygame.draw.circle(self.image, SOFT_PURPLE, (16, 16), 12)
        pygame.draw.circle(self.image, DUSTY_ROSE, (16, 16), 12, 2)
        
        # Animal ears (triangular)
        if self.facing_right:
            # Right-facing ears
            pygame.draw.polygon(self.image, LIGHT_PURPLE, [(8, 8), (12, 4), (16, 8)])
            pygame.draw.polygon(self.image, SOFT_PINK, [(9, 7), (12, 5), (15, 7)])
            pygame.draw.polygon(self.image, LIGHT_PURPLE, [(16, 8), (20, 4), (24, 8)])
            pygame.draw.polygon(self.image, SOFT_PINK, [(17, 7), (20, 5), (23, 7)])
        else:
            # Left-facing ears
            pygame.draw.polygon(self.image, LIGHT_PURPLE, [(8, 8), (12, 4), (16, 8)])
            pygame.draw.polygon(self.image, SOFT_PINK, [(9, 7), (12, 5), (15, 7)])
            pygame.draw.polygon(self.image, LIGHT_PURPLE, [(16, 8), (20, 4), (24, 8)])
            pygame.draw.polygon(self.image, SOFT_PINK, [(17, 7), (20, 5), (23, 7)])
        
        # Eyes (larger and more expressive)
        if self.facing_right:
            # Right-facing eyes
            pygame.draw.circle(self.image, WHITE, (12, 12), 4)
            pygame.draw.circle(self.image, WHITE, (20, 12), 4)
            pygame.draw.circle(self.image, BLACK, (14, 12), 2)
            pygame.draw.circle(self.image, BLACK, (22, 12), 2)
            # Eye shine
            pygame.draw.circle(self.image, WHITE, (15, 11), 1)
            pygame.draw.circle(self.image, WHITE, (23, 11), 1)
        else:
            # Left-facing eyes
            pygame.draw.circle(self.image, WHITE, (12, 12), 4)
            pygame.draw.circle(self.image, WHITE, (20, 12), 4)
            pygame.draw.circle(self.image, BLACK, (10, 12), 2)
            pygame.draw.circle(self.image, BLACK, (18, 12), 2)
            # Eye shine
            pygame.draw.circle(self.image, WHITE, (9, 11), 1)
            pygame.draw.circle(self.image, WHITE, (17, 11), 1)
        
        # Nose (small pink triangle)
        pygame.draw.polygon(self.image, SOFT_PINK, [(16, 16), (14, 18), (18, 18)])
        
        # Mouth (small smile)
        pygame.draw.arc(self.image, BLACK, (12, 18, 8, 4), 0, 3.14159, 2)
        
        # Arms (more rounded)
        pygame.draw.circle(self.image, LIGHT_PURPLE, (2, 20), 4)
        pygame.draw.circle(self.image, LIGHT_PURPLE, (30, 20), 4)
        
        # Feet (more paw-like)
        pygame.draw.ellipse(self.image, DUSTY_ROSE, (6, 42, 8, 6))
        pygame.draw.ellipse(self.image, DUSTY_ROSE, (18, 42, 8, 6))
        # Paw pads
        pygame.draw.circle(self.image, SOFT_PINK, (10, 44), 1)
        pygame.draw.circle(self.image, SOFT_PINK, (22, 44), 1)
        
    def update(self, platforms, enemies, powerups, obstacles, camera_x):
        keys = pygame.key.get_pressed()
        
        # Horizontal movement
        self.vel_x = 0
        old_facing = self.facing_right
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True
            
        # Redraw character if facing direction changed
        if old_facing != self.facing_right:
            self.draw_character()
            
        # Jumping (only when on ground)
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False
            if self.sound_manager:
                self.sound_manager.play('jump')
        
        # Apply gravity
        self.vel_y += GRAVITY
        
        # Move horizontally
        self.rect.x += self.vel_x
        
        # Check horizontal collisions with platforms
        collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collisions:
            if self.vel_x > 0:  # Moving right
                self.rect.right = platform.rect.left
            elif self.vel_x < 0:  # Moving left
                self.rect.left = platform.rect.right
        
        # Move vertically
        self.rect.y += int(self.vel_y)
        
        # Check vertical collisions with platforms
        self.on_ground = False
        collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collisions:
            if self.vel_y > 0:  # Falling
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
                self.on_ground = True
                self.jump_count = 0
            elif self.vel_y < 0:  # Jumping up
                self.rect.top = platform.rect.bottom
                self.vel_y = 0
        
        # Keep player in level bounds
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > LEVEL_WIDTH:
            self.rect.right = LEVEL_WIDTH
            
        # Check if player fell off the level
        if self.rect.top > LEVEL_HEIGHT:
            return "death"
            
        # Check enemy collisions
        enemy_collisions = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in enemy_collisions:
            # Check if player is jumping on enemy (player's bottom is above enemy's center)
            if self.vel_y > 0 and self.rect.bottom < enemy.rect.centery:
                enemy.kill()
                # Slightly higher bounce on enemy stomp
                self.vel_y = int(JUMP_STRENGTH * 1.15)
                if self.sound_manager:
                    self.sound_manager.play('enemy_kill')
                return "enemy_killed"
            else:
                # Player got hit by enemy
                if self.sound_manager:
                    self.sound_manager.play('hit')
                return "hit"
        
        # Check powerup collisions
        powerup_collisions = pygame.sprite.spritecollide(self, powerups, True)
        if powerup_collisions:
            if self.sound_manager:
                self.sound_manager.play('coin')
            return "powerup"
            
        # Check obstacle collisions
        obstacle_collisions = pygame.sprite.spritecollide(self, obstacles, False)
        if obstacle_collisions:
            if self.sound_manager:
                self.sound_manager.play('hit')
            return "hit"
            
        return None

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type="basic"):
        super().__init__()
        self.enemy_type = enemy_type
        
        # Different sizes for different types
        if enemy_type == "basic":
            self.image = pygame.Surface((36, 36), pygame.SRCALPHA)
            self.speed = ENEMY_SPEED
        elif enemy_type == "fast":
            self.image = pygame.Surface((28, 28), pygame.SRCALPHA)
            self.speed = ENEMY_SPEED * 1.5
        elif enemy_type == "big":
            self.image = pygame.Surface((48, 48), pygame.SRCALPHA)
            self.speed = ENEMY_SPEED * 0.7
        else:  # jumper
            self.image = pygame.Surface((32, 40), pygame.SRCALPHA)
            self.speed = ENEMY_SPEED
            
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.vel_x = random.choice([-self.speed, self.speed])
        self.vel_y = 0
        
        # Jumper specific
        self.jump_timer = 0
        self.jump_cooldown = random.randint(60, 120)  # frames
        
        # Draw the enemy
        self.draw_enemy()
    
    def draw_enemy(self):
        self.image.fill((0, 0, 0, 0))  # Clear with transparency
        
        w, h = self.image.get_size()
        
        if self.enemy_type == "basic":
            # Basic spiky enemy (coral)
            pygame.draw.ellipse(self.image, CORAL, (3, 12, 30, 24))
            pygame.draw.ellipse(self.image, DUSTY_ROSE, (3, 12, 30, 24), 2)
            
            # Spikes on top
            spike_points = [
                [(8, 12), (12, 3), (16, 12)],
                [(14, 12), (18, 1), (22, 12)],
                [(20, 12), (24, 3), (28, 12)]
            ]
            for spike in spike_points:
                pygame.draw.polygon(self.image, DUSTY_ROSE, spike)
                pygame.draw.polygon(self.image, BLACK, spike, 1)
            
            # Eyes and features
            pygame.draw.circle(self.image, SOFT_PINK, (12, 18), 3)
            pygame.draw.circle(self.image, SOFT_PINK, (24, 18), 3)
            pygame.draw.circle(self.image, BLACK, (11, 17), 2)
            pygame.draw.circle(self.image, BLACK, (23, 17), 2)
            pygame.draw.line(self.image, BLACK, (15, 24), (21, 24), 3)
            
        elif self.enemy_type == "fast":
            # Fast enemy (smaller, more streamlined)
            pygame.draw.ellipse(self.image, SOFT_PINK, (2, 8, 24, 16))
            pygame.draw.ellipse(self.image, CORAL, (2, 8, 24, 16), 2)
            
            # Small spikes
            pygame.draw.polygon(self.image, CORAL, [(8, 8), (10, 4), (12, 8)])
            pygame.draw.polygon(self.image, CORAL, [(16, 8), (18, 4), (20, 8)])
            
            # Eyes
            pygame.draw.circle(self.image, BLACK, (9, 14), 1)
            pygame.draw.circle(self.image, BLACK, (19, 14), 1)
            
        elif self.enemy_type == "big":
            # Big enemy (larger, more intimidating)
            pygame.draw.ellipse(self.image, DUSTY_ROSE, (4, 16, 40, 32))
            pygame.draw.ellipse(self.image, CORAL, (4, 16, 40, 32), 3)
            
            # Large spikes
            spike_points = [
                [(10, 16), (16, 4), (22, 16)],
                [(18, 16), (24, 2), (30, 16)],
                [(26, 16), (32, 4), (38, 16)]
            ]
            for spike in spike_points:
                pygame.draw.polygon(self.image, CORAL, spike)
                pygame.draw.polygon(self.image, BLACK, spike, 2)
            
            # Large eyes
            pygame.draw.circle(self.image, SOFT_PINK, (16, 24), 4)
            pygame.draw.circle(self.image, SOFT_PINK, (32, 24), 4)
            pygame.draw.circle(self.image, BLACK, (15, 23), 3)
            pygame.draw.circle(self.image, BLACK, (31, 23), 3)
            
        else:  # jumper
            # Jumper enemy (spring-like)
            pygame.draw.ellipse(self.image, PEACH, (4, 20, 24, 20))
            pygame.draw.ellipse(self.image, CORAL, (4, 20, 24, 20), 2)
            
            # Spring coil effect
            for i in range(3):
                y = 15 + i * 4
                pygame.draw.ellipse(self.image, DUSTY_ROSE, (6, y, 20, 3))
            
            # Eyes
            pygame.draw.circle(self.image, WHITE, (12, 12), 3)
            pygame.draw.circle(self.image, WHITE, (20, 12), 3)
            pygame.draw.circle(self.image, BLACK, (12, 12), 2)
            pygame.draw.circle(self.image, BLACK, (20, 12), 2)
        
        # Common feet for all types
        foot_y = h - 6
        pygame.draw.ellipse(self.image, BLACK, (w//4, foot_y, w//6, 4))
        pygame.draw.ellipse(self.image, BLACK, (3*w//4 - w//6, foot_y, w//6, 4))
        
    def update(self, platforms):
        # Apply gravity
        self.vel_y += GRAVITY
        
        # Special behavior for jumper enemies
        if self.enemy_type == "jumper":
            self.jump_timer += 1
            if self.jump_timer >= self.jump_cooldown and self.vel_y == 0:
                self.vel_y = JUMP_STRENGTH * 0.7  # Smaller jump than player
                self.jump_timer = 0
                self.jump_cooldown = random.randint(60, 120)
        
        # Move horizontally
        self.rect.x += int(self.vel_x)
        
        # Check horizontal collisions
        collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collisions:
            if self.vel_x > 0:
                self.rect.right = platform.rect.left
                self.vel_x = -self.speed
            elif self.vel_x < 0:
                self.rect.left = platform.rect.right
                self.vel_x = self.speed
        
        # Move vertically
        self.rect.y += int(self.vel_y)
        
        # Check vertical collisions
        collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collisions:
            if self.vel_y > 0:
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
            elif self.vel_y < 0:
                self.rect.top = platform.rect.bottom
                self.vel_y = 0
        
        # Reverse direction at edges or if no ground ahead
        if self.rect.left < 0 or self.rect.right > LEVEL_WIDTH:
            self.vel_x *= -1
            
        # Remove if fallen off level
        if self.rect.top > LEVEL_HEIGHT:
            self.kill()

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, platform_type="normal"):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.rect = pygame.Rect(x, y, width, height)
        self.platform_type = platform_type
        self.original_x = x
        self.move_offset = 0
        
        # Draw intricate platform
        self.draw_platform(width, height)
    
    def draw_platform(self, width, height):
        if self.platform_type == "cloud":
            # Cloud platform
            self.image.fill((0, 0, 0, 0))  # Transparent background
            # Main cloud body
            pygame.draw.ellipse(self.image, WHITE, (0, height//3, width, height//2))
            # Cloud puffs
            for i in range(0, width, width//4):
                pygame.draw.circle(self.image, WHITE, (i + width//8, height//2), height//3)
            # Soft shadow
            pygame.draw.ellipse(self.image, LAVENDER, (2, height//3 + 2, width-4, height//2 - 4))
        
        elif self.platform_type == "ice":
            # Ice platform
            self.image.fill(SOFT_BLUE)
            # Ice crystals
            for x in range(0, width, 20):
                for y in range(0, height, 10):
                    if random.random() < 0.3:
                        pygame.draw.circle(self.image, WHITE, (x + random.randint(0, 15), y + random.randint(0, 8)), 1)
            # Highlight
            pygame.draw.line(self.image, WHITE, (0, 0), (width, 0), 2)
            # Shadow
            pygame.draw.line(self.image, MOUNTAIN_BLUE, (0, height-1), (width, height-1), 1)
        
        else:  # normal platform
            # Base platform color (soft earthy tones)
            self.image.fill(LIGHT_BROWN)
            
            # Top grass layer
            grass_height = min(8, height // 3)
            pygame.draw.rect(self.image, SAGE_GREEN, (0, 0, width, grass_height))
            
            # Grass texture (small vertical lines)
            for x in range(0, width, 4):
                grass_x = x + random.randint(-1, 1)
                if 0 <= grass_x < width:
                    pygame.draw.line(self.image, PASTEL_GREEN, (grass_x, 0), (grass_x, grass_height - 1))
            
            # Stone/dirt texture with pastel colors
            for y in range(grass_height, height, 8):
                for x in range(0, width, 12):
                    # Add some stone blocks
                    block_width = min(10, width - x)
                    block_height = min(6, height - y)
                    if block_width > 0 and block_height > 0:
                        # Pastel earth tones
                        shade = random.choice([BEIGE, LIGHT_BROWN, PEACH])
                        pygame.draw.rect(self.image, shade, (x, y, block_width, block_height))
                        # Add soft border
                        pygame.draw.rect(self.image, DUSTY_ROSE, (x, y, block_width, block_height), 1)
            
            # Top border highlight
            pygame.draw.line(self.image, MINT_GREEN, (0, grass_height), (width, grass_height), 1)
            
            # Bottom shadow
            if height > 4:
                pygame.draw.line(self.image, DUSTY_ROSE, (0, height-1), (width, height-1), 1)
    
    def update(self):
        if self.platform_type == "moving":
            # Moving platform logic
            self.move_offset += 0.02
            self.rect.x = self.original_x + int(50 * pygame.math.Vector2(1, 0).rotate(self.move_offset * 180 / 3.14159).x)

class Powerup(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Animation
        self.float_offset = 0
        self.original_y = y
        self.spin_angle = 0
        
        # Draw the coin
        self.draw_coin()
        
    def draw_coin(self):
        self.image.fill((0, 0, 0, 0))  # Clear with transparency
        
        # Coin body (soft golden circle)
        pygame.draw.circle(self.image, SOFT_YELLOW, (12, 12), 10)
        pygame.draw.circle(self.image, PEACH, (12, 12), 10, 2)
        
        # Inner circle for depth
        pygame.draw.circle(self.image, CREAM, (12, 12), 7)
        pygame.draw.circle(self.image, PEACH, (12, 12), 7, 1)
        
        # Draw simplified star/sparkle with softer colors
        pygame.draw.line(self.image, WHITE, (12, 8), (12, 16), 2)
        pygame.draw.line(self.image, WHITE, (8, 12), (16, 12), 2)
        pygame.draw.line(self.image, CREAM, (9, 9), (15, 15), 1)
        pygame.draw.line(self.image, CREAM, (15, 9), (9, 15), 1)
        
        # Highlight for shine effect
        pygame.draw.circle(self.image, WHITE, (9, 9), 2)
        
    def update(self):
        # Floating animation
        self.float_offset += 0.15
        float_y = int(3 * pygame.math.Vector2(0, 1).rotate(self.float_offset * 180 / 3.14159).y)
        self.rect.y = self.original_y + float_y
        
        # Spinning animation (redraw coin with different perspective)
        self.spin_angle += 5
        if self.spin_angle >= 360:
            self.spin_angle = 0

class Plant(pygame.sprite.Sprite):
    def __init__(self, x, y, plant_type="small"):
        super().__init__()
        self.plant_type = plant_type
        
        if plant_type == "small":
            self.image = pygame.Surface((24, 36), pygame.SRCALPHA)  # Made bigger
        elif plant_type == "large":
            self.image = pygame.Surface((36, 54), pygame.SRCALPHA)  # Made bigger
        else:  # flower
            self.image = pygame.Surface((20, 32), pygame.SRCALPHA)
            
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Draw the plant
        self.draw_plant()
        
    def draw_plant(self):
        self.image.fill((0, 0, 0, 0))  # Clear with transparency
        
        if self.plant_type == "small":
            # Small bush/grass (bigger)
            # Stem
            pygame.draw.line(self.image, SAGE_GREEN, (12, 28), (12, 36), 4)
            
            # Main leaves
            pygame.draw.circle(self.image, PASTEL_GREEN, (12, 22), 8)
            pygame.draw.circle(self.image, SAGE_GREEN, (12, 22), 8, 1)
            
            # Side leaves
            pygame.draw.circle(self.image, MINT_GREEN, (6, 26), 5)
            pygame.draw.circle(self.image, MINT_GREEN, (18, 26), 5)
            
            # Additional small leaves
            pygame.draw.circle(self.image, PASTEL_GREEN, (4, 20), 3)
            pygame.draw.circle(self.image, PASTEL_GREEN, (20, 20), 3)
            
            # Highlights
            pygame.draw.circle(self.image, WHITE, (9, 19), 1)
            pygame.draw.circle(self.image, WHITE, (15, 19), 1)
            
        elif self.plant_type == "large":
            # Large tree/bush (bigger)
            # Trunk
            pygame.draw.rect(self.image, LIGHT_BROWN, (15, 42, 6, 12))
            
            # Main foliage
            pygame.draw.circle(self.image, PASTEL_GREEN, (18, 30), 14)
            pygame.draw.circle(self.image, SAGE_GREEN, (18, 30), 14, 2)
            
            # Additional leaf clusters
            pygame.draw.circle(self.image, MINT_GREEN, (8, 28), 8)
            pygame.draw.circle(self.image, MINT_GREEN, (28, 28), 8)
            pygame.draw.circle(self.image, PASTEL_GREEN, (18, 18), 10)
            
            # Small detail leaves
            pygame.draw.circle(self.image, SAGE_GREEN, (12, 35), 4)
            pygame.draw.circle(self.image, SAGE_GREEN, (24, 35), 4)
            
            # Highlights
            pygame.draw.circle(self.image, WHITE, (12, 24), 1)
            pygame.draw.circle(self.image, WHITE, (24, 24), 1)
            pygame.draw.circle(self.image, WHITE, (18, 15), 2)
            
        else:  # flower
            # Flower plant
            # Stem
            pygame.draw.line(self.image, SAGE_GREEN, (10, 24), (10, 32), 3)
            
            # Leaves
            pygame.draw.ellipse(self.image, PASTEL_GREEN, (6, 20, 8, 4))
            pygame.draw.ellipse(self.image, PASTEL_GREEN, (6, 24, 8, 4))
            
            # Flower petals
            petal_colors = [SOFT_PINK, CORAL, PEACH]
            petal_color = random.choice(petal_colors)
            
            # Draw petals around center
            for angle in range(0, 360, 45):
                x = 10 + int(4 * pygame.math.Vector2(1, 0).rotate(angle).x)
                y = 16 + int(4 * pygame.math.Vector2(1, 0).rotate(angle).y)
                pygame.draw.circle(self.image, petal_color, (x, y), 3)
            
            # Flower center
            pygame.draw.circle(self.image, SOFT_YELLOW, (10, 16), 3)
            pygame.draw.circle(self.image, PEACH, (10, 16), 3, 1)

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, obstacle_type="spike"):
        super().__init__()
        self.obstacle_type = obstacle_type
        
        if obstacle_type == "spike":
            self.image = pygame.Surface((20, 24), pygame.SRCALPHA)
        else:  # pit
            self.image = pygame.Surface((40, 20), pygame.SRCALPHA)
            
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Draw the obstacle
        self.draw_obstacle()
        
    def draw_obstacle(self):
        self.image.fill((0, 0, 0, 0))  # Clear with transparency
        
        if self.obstacle_type == "spike":
            # Ground spikes
            spike_points = [
                [(2, 24), (10, 4), (18, 24)],
                [(0, 24), (6, 12), (12, 24)],
                [(8, 24), (14, 8), (20, 24)]
            ]
            for spike in spike_points:
                pygame.draw.polygon(self.image, DUSTY_ROSE, spike)
                pygame.draw.polygon(self.image, BLACK, spike, 1)

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        
    def update(self, target):
        # Follow the player with some offset
        self.x = target.rect.centerx - SCREEN_WIDTH // 2
        
        # Keep camera within level bounds
        if self.x < 0:
            self.x = 0
        if self.x > LEVEL_WIDTH - SCREEN_WIDTH:
            self.x = LEVEL_WIDTH - SCREEN_WIDTH

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mario-Style Platformer")
        self.clock = pygame.time.Clock()
        
        # Initialize sound manager
        self.sound_manager = SoundManager()
        
        self.state = GameState.MENU
        self.lives = 3
        self.score = 0
        self.level_progress = 0  # For progressive difficulty
        self.current_level = 0
        self.levels = self.generate_levels()
        self.theme = self.levels[self.current_level]["theme"]
        
        # Create sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.plants = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        
        # Create camera
        self.camera = Camera()
        
        # Background cache
        self._bg_cache = None
        self._bg_blobs = []

        # Create level
        self.create_level()
        
        # Create player
        self.player = Player(100, 400, self.sound_manager)
        self.all_sprites.add(self.player)
        
        # Font for UI
        self.font = pygame.font.Font(None, 36)
        
    def set_level_dimensions(self, width, height):
        global LEVEL_WIDTH, LEVEL_HEIGHT
        LEVEL_WIDTH = width
        LEVEL_HEIGHT = height

    def generate_levels(self):
        # Define 10 themed levels with growing width/difficulty and distinct colors
        themes = [
            {"sky_top": LAVENDER, "sky_bottom": SKY_BLUE, "mountain_back": MOUNTAIN_PURPLE, "mountain_front": MOUNTAIN_BLUE},
            {"sky_top": SOFT_BLUE, "sky_bottom": SAGE_GREEN, "mountain_back": LIGHT_PURPLE, "mountain_front": SOFT_PURPLE},
            {"sky_top": PEACH, "sky_bottom": SOFT_YELLOW, "mountain_back": BEIGE, "mountain_front": LIGHT_BROWN},
            {"sky_top": SOFT_PINK, "sky_bottom": CORAL, "mountain_back": DUSTY_ROSE, "mountain_front": PEACH},
            {"sky_top": MINT_GREEN, "sky_bottom": PASTEL_GREEN, "mountain_back": SAGE_GREEN, "mountain_front": MINT_GREEN},
            {"sky_top": LIGHT_PURPLE, "sky_bottom": SOFT_PURPLE, "mountain_back": LAVENDER, "mountain_front": LIGHT_PURPLE},
            {"sky_top": CREAM, "sky_bottom": SOFT_YELLOW, "mountain_back": PEACH, "mountain_front": CORAL},
            {"sky_top": SKY_BLUE, "sky_bottom": SOFT_BLUE, "mountain_back": MOUNTAIN_BLUE, "mountain_front": BLACK},
            {"sky_top": SOFT_YELLOW, "sky_bottom": PEACH, "mountain_back": LIGHT_BROWN, "mountain_front": DUSTY_ROSE},
            {"sky_top": SOFT_PURPLE, "sky_bottom": LIGHT_PURPLE, "mountain_back": LAVENDER, "mountain_front": MOUNTAIN_BLUE},
        ]
        levels = []
        for i in range(10):
            width = 2800 + i * 400
            difficulty = i  # increases with level index
            levels.append({
                "width": width,
                "height": 600,
                "difficulty": difficulty,
                "theme": themes[i % len(themes)]
            })
        return levels

    def create_level(self):
        # Configure dimensions and theme for current level
        level_def = self.levels[self.current_level]
        self.set_level_dimensions(level_def["width"], level_def["height"])
        self.theme = level_def["theme"]
        # Ground platforms
        for x in range(0, LEVEL_WIDTH, 200):
            platform = Platform(x, LEVEL_HEIGHT - 40, 200, 40)
            self.platforms.add(platform)
            self.all_sprites.add(platform)
        
        # Floating platforms with different types
        # Procedurally create floating platforms based on level width and difficulty
        platforms_data = []
        segment = LEVEL_WIDTH // 8
        rng = random.Random(1337 + self.current_level)
        for s in range(1, 8):
            base_x = s * segment
            count = 1 + (level_def["difficulty"] // 2)
            for c in range(count):
                x = base_x - rng.randint(80, 180)
                y = rng.randint(220, 480)
                w = rng.choice([100, 120, 150])
                h = 20
                ptype = rng.choice(["normal", "cloud", "ice", "moving"]) if s % 2 == 0 else rng.choice(["normal", "cloud", "ice"])
                platforms_data.append((x, y, w, h, ptype))
        
        for x, y, w, h, ptype in platforms_data:
            platform = Platform(x, y, w, h, ptype)
            self.platforms.add(platform)
            self.all_sprites.add(platform)
        
        # Create enemies with progressive difficulty
        # Enemies scale with difficulty
        enemy_data = []
        enemy_kinds = ["basic", "fast", "jumper", "big"]
        enemy_count = 8 + level_def["difficulty"] * 2
        rng = random.Random(9000 + self.current_level)
        for _ in range(enemy_count):
            x = rng.randint(300, LEVEL_WIDTH - 300)
            y = rng.randint(240, 460)
            etype = rng.choices(enemy_kinds, weights=[4, 3 + level_def["difficulty"], 3, 1 + level_def["difficulty"]//2])[0]
            enemy_data.append((x, y, etype))
        
        # Add more enemies based on level progress
        if self.level_progress > 0:
            enemy_data.extend([
                (500, 400, "fast"), (1100, 350, "big"), (1700, 400, "jumper"),
                (2300, 350, "fast"), (2900, 350, "big")
            ])
        
        if self.level_progress > 1:
            enemy_data.extend([
                (600, 400, "jumper"), (1400, 250, "big"), (2000, 300, "fast"),
                (2600, 200, "jumper")
            ])
        
        for x, y, etype in enemy_data:
            enemy = Enemy(x, y, etype)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)
        
        # Create powerups
        powerup_positions = []
        rng = random.Random(777 + self.current_level)
        for s in range(2, 9):
            x = s * (LEVEL_WIDTH // 10) + rng.randint(-60, 60)
            y = rng.randint(260, 420)
            powerup_positions.append((x, y))
        
        for x, y in powerup_positions:
            powerup = Powerup(x, y)
            self.powerups.add(powerup)
            self.all_sprites.add(powerup)
        
        # Create decorative plants with more variety
        plant_data = []
        rng = random.Random(4242 + self.current_level)
        for x in range(130, LEVEL_WIDTH, 300):
            plant_type = rng.choice(["small", "large", "flower", "small", "flower"])
            plant_data.append((x, LEVEL_HEIGHT - 76, plant_type))
        
        for x, y, ptype in plant_data:
            plant = Plant(x, y, ptype)
            self.plants.add(plant)
            self.all_sprites.add(plant)
            
        # Create obstacles
        obstacle_positions = []
        rng = random.Random(555 + self.current_level)
        spike_count = 3 + level_def["difficulty"]
        for _ in range(spike_count):
            obstacle_positions.append((rng.randint(600, LEVEL_WIDTH - 400), LEVEL_HEIGHT - 64, "spike"))
        
        for x, y, otype in obstacle_positions:
            obstacle = Obstacle(x, y, otype)
            self.obstacles.add(obstacle)
            self.all_sprites.add(obstacle)
    
    def _ensure_background_cache(self):
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

            # Create a few slow-moving abstract blobs on their own surface
            self._bg_blobs = []
            rng = random.Random(101 + self.current_level)
            for _ in range(5):
                blob = {
                    "x": rng.randint(-100, SCREEN_WIDTH + 100),
                    "y": rng.randint(40, SCREEN_HEIGHT - 120),
                    "r": rng.randint(40, 90),
                    "vx": rng.choice([-0.1, 0.08, 0.12, -0.08]),
                    "color": (
                        int((self.theme["sky_top"][0] + self.theme["sky_bottom"][0]) / 2),
                        int((self.theme["sky_top"][1] + self.theme["sky_bottom"][1]) / 2),
                        int((self.theme["sky_top"][2] + self.theme["sky_bottom"][2]) / 2),
                    ),
                }
                self._bg_blobs.append(blob)

    def draw_background(self):
        # Cached gradient background with subtle blobs; no text, no trails
        self._ensure_background_cache()
        self.screen.blit(self._bg_cache, (0, 0))

        # Draw and update blobs on a temporary surface to avoid trails
        blob_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for blob in self._bg_blobs:
            pygame.draw.circle(blob_surface, (*blob["color"], 50), (int(blob["x"]), int(blob["y"])), blob["r"])
            blob["x"] += blob["vx"]
            if blob["x"] < -120:
                blob["x"] = SCREEN_WIDTH + 100
            elif blob["x"] > SCREEN_WIDTH + 120:
                blob["x"] = -100
        self.screen.blit(blob_surface, (0, 0))
    
    def draw_mountains_and_clouds(self):
        # Intentionally no-op; mountain/cloud layers removed to simplify and avoid artifacts
        pass
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.start_game()
                elif self.state == GameState.LEVEL_COMPLETE:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.continue_to_next_level()
                    elif event.key == pygame.K_m:
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
    
    def start_game(self):
        """Start a new game"""
        self.state = GameState.PLAYING
        self.lives = 3
        self.score = 0
        self.level_progress = 0
        self.current_level = 0
        self.theme = self.levels[self.current_level]["theme"]
        
        # Clear and recreate everything
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
    
    def add_difficulty_enemies(self):
        """Add more enemies as difficulty increases"""
        # Limit total enemies to prevent performance issues
        if len(self.enemies) >= 25:
            return
            
        new_enemies = [
            (random.randint(200, LEVEL_WIDTH - 200), random.randint(300, 500), "fast"),
            (random.randint(200, LEVEL_WIDTH - 200), random.randint(300, 500), "jumper"),
        ]
        
        if self.level_progress > 2:
            new_enemies.append((random.randint(200, LEVEL_WIDTH - 200), random.randint(300, 500), "big"))
        
        for x, y, etype in new_enemies:
            if len(self.enemies) < 25:  # Double check
                enemy = Enemy(x, y, etype)
                self.enemies.add(enemy)
                self.all_sprites.add(enemy)
    
    def update(self):
        if self.state == GameState.PLAYING:
            # Update camera
            self.camera.update(self.player)
            
            # Update player
            result = self.player.update(self.platforms, self.enemies, self.powerups, self.obstacles, self.camera.x)
            
            if result == "death" or result == "hit":
                self.lives -= 1
                if self.lives <= 0:
                    self.state = GameState.GAME_OVER
                else:
                    # Respawn player
                    self.player.rect.x = 100
                    self.player.rect.y = 400
                    self.player.vel_x = 0
                    self.player.vel_y = 0
            elif result == "enemy_killed":
                self.score += 100
                # Check for level progression
                if self.score > 0 and self.score % 1000 == 0:
                    self.level_progress += 1
                    # Add more enemies for increased difficulty
                    self.add_difficulty_enemies()
            elif result == "powerup":
                self.lives += 1
                self.score += 200
            
            # Detect end of level: when player reaches (or exceeds) level width
            if self.player.rect.right >= LEVEL_WIDTH - 5:
                self.state = GameState.LEVEL_COMPLETE
            
            # Update enemies
            self.enemies.update(self.platforms)
            
            # Update powerups
            self.powerups.update()
            
            # Update platforms (for moving platforms)
            self.platforms.update()
    
    def draw(self):
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        elif self.state == GameState.LEVEL_COMPLETE:
            self.draw_level_complete()
        
        pygame.display.flip()
    
    def draw_menu(self):
        # Draw scenic background
        self.draw_background()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(64)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Title with shadow effect
        title_font = pygame.font.Font(None, 84)
        
        # Shadow
        shadow_text = title_font.render("Animal Platformer", True, BLACK)
        shadow_rect = shadow_text.get_rect(center=(SCREEN_WIDTH//2 + 3, SCREEN_HEIGHT//4 + 3))
        self.screen.blit(shadow_text, shadow_rect)
        
        # Main title
        title_text = title_font.render("Animal Platformer", True, SOFT_PURPLE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
        self.screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle_font = pygame.font.Font(None, 36)
        subtitle_text = subtitle_font.render("A Mario-inspired Adventure", True, LIGHT_PURPLE)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4 + 60))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Instructions with button styling
        instruction_font = pygame.font.Font(None, 32)
        instructions = [
            ("Press SPACE or ENTER to Start", MINT_GREEN),
            ("Arrow Keys or WASD to Move", SOFT_YELLOW),
            ("SPACE to Jump", PEACH),
            ("ESC to Quit", CORAL)
        ]
        
        start_y = SCREEN_HEIGHT//2 + 40
        for i, (instruction, color) in enumerate(instructions):
            # Button-like background
            button_width = 350
            button_height = 35
            button_rect = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, 
                                    start_y + i * 50, 
                                    button_width, button_height)
            pygame.draw.rect(self.screen, color, button_rect)
            pygame.draw.rect(self.screen, BLACK, button_rect, 2)
            
            # Text
            text = instruction_font.render(instruction, True, BLACK)
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
        
        # Add volume control hint
        volume_font = pygame.font.Font(None, 24)
        volume_text = volume_font.render("Sound effects enabled", True, WHITE)
        volume_rect = volume_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
        self.screen.blit(volume_text, volume_rect)
    
    def draw_game(self):
        # Draw scenic background
        self.draw_background()
        
        # Draw all sprites with camera offset (with culling for performance)
        for sprite in self.all_sprites:
            screen_x = sprite.rect.x - self.camera.x
            screen_y = sprite.rect.y - self.camera.y
            
            # Only draw sprites that are visible on screen (culling)
            if (-sprite.rect.width < screen_x < SCREEN_WIDTH and 
                -sprite.rect.height < screen_y < SCREEN_HEIGHT):
                self.screen.blit(sprite.image, (screen_x, screen_y))
        
        # Draw UI
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        level_text = self.font.render(f"Level: {self.current_level + 1}/{len(self.levels)}", True, WHITE)
        self.screen.blit(lives_text, (10, 10))
        self.screen.blit(score_text, (10, 50))
        self.screen.blit(level_text, (10, 90))

    def draw_level_complete(self):
        # Background
        self.draw_background()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.Font(None, 84)
        title_text = title_font.render(f"Level {self.current_level + 1} Complete!", True, SOFT_YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
        self.screen.blit(title_text, title_rect)

        info_font = pygame.font.Font(None, 36)
        if self.current_level < len(self.levels) - 1:
            info = "Press SPACE/ENTER to Continue"
        else:
            info = "All levels complete! Press M for Menu"
        info_text = info_font.render(info, True, WHITE)
        info_rect = info_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(info_text, info_rect)

        small = pygame.font.Font(None, 28)
        small_text = small.render("Press M for Menu", True, WHITE)
        small_rect = small_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(small_text, small_rect)

    def continue_to_next_level(self):
        if self.current_level < len(self.levels) - 1:
            self.current_level += 1
            self.theme = self.levels[self.current_level]["theme"]
            # Reset and load next level
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
            # Finished all levels
            self.state = GameState.MENU
    
    def draw_game_over(self):
        # Draw scenic background
        self.draw_background()
        
        # Semi-transparent overlay for better text readability
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Game Over title with shadow effect
        game_over_font = pygame.font.Font(None, 84)
        
        # Shadow
        shadow_text = game_over_font.render("GAME OVER", True, BLACK)
        shadow_rect = shadow_text.get_rect(center=(SCREEN_WIDTH//2 + 3, SCREEN_HEIGHT//3 + 3))
        self.screen.blit(shadow_text, shadow_rect)
        
        # Main text
        game_over_text = game_over_font.render("GAME OVER", True, CORAL)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Stats panel background
        panel_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 60, 400, 120)
        pygame.draw.rect(self.screen, LIGHT_PURPLE, panel_rect)
        pygame.draw.rect(self.screen, DUSTY_ROSE, panel_rect, 3)
        
        # Final score with better formatting
        score_font = pygame.font.Font(None, 52)
        final_score_text = score_font.render(f"Final Score: {self.score}", True, BLACK)
        score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20))
        self.screen.blit(final_score_text, score_rect)
        
        # Level reached
        level_font = pygame.font.Font(None, 36)
        level_text = level_font.render(f"Level Reached: {self.level_progress + 1}", True, BLACK)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
        self.screen.blit(level_text, level_rect)
        
        # Instructions with better styling
        instruction_font = pygame.font.Font(None, 32)
        instructions = [
            ("Press R or SPACE to Restart", SOFT_YELLOW),
            ("Press M for Main Menu", MINT_GREEN),
            ("Press ESC to Quit", CORAL)
        ]
        
        for i, (instruction, color) in enumerate(instructions):
            # Button-like background
            button_width = 300
            button_height = 35
            button_rect = pygame.Rect(SCREEN_WIDTH//2 - button_width//2, 
                                    SCREEN_HEIGHT//2 + 120 + i * 50, 
                                    button_width, button_height)
            pygame.draw.rect(self.screen, color, button_rect)
            pygame.draw.rect(self.screen, BLACK, button_rect, 2)
            
            # Text
            text = instruction_font.render(instruction, True, BLACK)
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
    
    def restart_game(self):
        self.state = GameState.PLAYING
        self.lives = 3
        self.score = 0
        self.current_level = 0
        
        # Clear all sprites
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()
        self.powerups.empty()
        self.plants.empty()
        self.obstacles.empty()
        
        # Recreate level and player
        self.theme = self.levels[self.current_level]["theme"]
        self.create_level()
        self.player = Player(100, 400, self.sound_manager)
        self.all_sprites.add(self.player)
        
        # Reset camera
        self.camera.x = 0
        self.camera.y = 0
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
