"""Entity and rendering logic for Rat Race.

Defines sprite classes and gameplay primitives:
- Player: input handling, physics, collisions, animation
- Enemy: archetypes (basic/fast/big/jumper/air/etc.) with behaviors
- Platform: themed tiles and moving variants, including fading/spiky
- Powerup, Plant, Obstacle: collectible and environmental items

Used by `game.py` to build each level.
"""

import random
import math
import pygame
from constants import GRAVITY, JUMP_STRENGTH, PLAYER_SPEED, ENEMY_SPEED, LEVEL_WIDTH, LEVEL_HEIGHT, WHITE, BLACK, SOFT_PURPLE, LIGHT_PURPLE, SOFT_PINK, DUSTY_ROSE, PEACH, CORAL, MOUNTAIN_BLUE, BEIGE, LIGHT_BROWN, SAGE_GREEN, PASTEL_GREEN, MINT_GREEN, SOFT_YELLOW, SOFT_BLUE, CREAM, CHEESE_YELLOW, MELTED_CHEESE, BURNT_ORANGE, SOOT_GREY, MOSS_GREEN, DARK_BROWN, WET_ROCK_GREY, STEEL_GREY, DARK_GREY, SILVER, MOLTEN_ORANGE, ICE_BLUE, SNOW_WHITE, ECTOPLASM_GREEN, GHOSTLY_WHITE, SHADOW_GREY, GLITCH_GREEN, ERROR_RED, MOZZARELLA_WHITE, TOMATO_RED, BASIL_GREEN, CONCRETE_GREY, IVY_GREEN, DEEP_SEA_BLUE, DARK_BLUE, SEAWEED_GREEN, SKY_BLUE, PARMESAN_YELLOW, MARINARA_RED, STATIC_WHITE, NEON_MAGENTA, NEON_CYAN, NEON_YELLOW, NEON_GREEN, NEON_RED, NEON_WHITE, NEON_PURPLE

# Additional colors for new enemies
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
from sprite_animator import SpriteAnimator


class Player(pygame.sprite.Sprite):
    """Controllable character handling input, physics, and collisions.

    The visible sprite can be larger than the collision hitbox for more
    forgiving gameplay. Animation frames are provided by `SpriteAnimator`.
    """
    def __init__(self, x, y, sound_manager=None, speed_multiplier=1.0, jump_multiplier=1.0):
        super().__init__()
        
        # Initialize sprite animator
        self.sprite_animator = SpriteAnimator()
        self.speed_multiplier = speed_multiplier
        self.jump_multiplier = jump_multiplier
        
        # Get initial sprite and set up rect
        self.image = self.sprite_animator.get_current_sprite()
        # Create a smaller hitbox (70% of sprite size for more forgiving collisions)
        sprite_rect = self.image.get_rect()
        hitbox_width = int(sprite_rect.width * 0.7)
        hitbox_height = int(sprite_rect.height * 0.7)
        self.rect = pygame.Rect(x, y, hitbox_width, hitbox_height)
        # Store offset to center the sprite on the hitbox
        self.sprite_offset_x = (sprite_rect.width - hitbox_width) // 2
        self.sprite_offset_y = (sprite_rect.height - hitbox_height) // 2
        
        # Physics
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.jump_count = 0
        self.max_jumps = 1
        self.facing_right = True
        self.sound_manager = sound_manager
        
        # Variable jump height tracking
        self.jump_hold_time = 1
        self.max_jump_hold = 15  # Maximum frames to hold jump for bonus (15 frames = 0.25 seconds at 60 FPS)
        
        # Animation state
        self.animation_state = "idle"
        self.is_dying = False
        self.death_timer = 0
        
        # Star powerup state
        self.star_active = False
        self.star_timer = 0
        self.star_duration = 600  # 10 seconds at 60 FPS
        self.glow_pulse = 0
        
        # Cheese globs now work like rocks - no stuck timer needed
        
        # Set initial animation
        self.sprite_animator.set_animation("idle", self.facing_right)
    
    def respawn(self, x, y):
        """Reset player state for respawning."""
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.jump_count = 0
        self.is_dying = False
        self.death_timer = 0
        self.animation_state = "idle"
        self.sprite_animator.set_animation("idle", self.facing_right)
        self.jump_hold_time = 0  # Reset jump hold time
        # Keep star powerup active through respawn
    
    def activate_star_powerup(self):
        """Activate the star powerup effect."""
        self.star_active = True
        self.star_timer = self.star_duration
        if self.sound_manager:
            self.sound_manager.play('coin')  # Use coin sound for powerup

    def draw_character(self):
        """Rebuild the current frame for the player sprite image.

        Does not modify the collision rect size, only updates the
        visible `self.image` (with glow when a star is active).
        """
        """Update the character sprite using the sprite animator."""
        # Update the sprite animator
        self.sprite_animator.update()
        
        # Get the current sprite
        base_sprite = self.sprite_animator.get_current_sprite()
        
        # If star is active, add glow effect
        if self.star_active:
            # Create a larger surface for the glow
            glow_size = 20
            glow_surface = pygame.Surface((base_sprite.get_width() + glow_size * 2, 
                                          base_sprite.get_height() + glow_size * 2), 
                                         pygame.SRCALPHA)
            
            # Draw multiple glow layers
            self.glow_pulse += 0.2
            pulse_intensity = abs(math.sin(self.glow_pulse))
            
            for i in range(5, 0, -1):
                glow_layer = pygame.Surface((base_sprite.get_width() + i * 4, 
                                            base_sprite.get_height() + i * 4), 
                                           pygame.SRCALPHA)
                alpha = int(30 * pulse_intensity * (i / 5))
                # Draw glow in soft yellow
                pygame.draw.rect(glow_layer, (*SOFT_YELLOW[:3], alpha), glow_layer.get_rect(), border_radius=10)
                glow_surface.blit(glow_layer, (glow_size - i * 2, glow_size - i * 2))
            
            # Draw the base sprite on top of the glow
            glow_surface.blit(base_sprite, (glow_size, glow_size))
            
            # Add sparkles around the character
            for _ in range(3):
                sparkle_x = glow_size + random.randint(0, base_sprite.get_width())
                sparkle_y = glow_size + random.randint(0, base_sprite.get_height())
                sparkle_size = random.randint(2, 4)
                pygame.draw.circle(glow_surface, WHITE, (sparkle_x, sparkle_y), sparkle_size)
            
            self.image = glow_surface
            # Keep the smaller hitbox rect (don't resize to match image)
        else:
            # Normal sprite without glow
            self.image = base_sprite
            # Keep the smaller hitbox rect (don't resize to match image)
    

    def update(self, platforms, enemies, powerups, obstacles, camera_x, level_width=None):
        """Advance the player by one frame and handle interactions.

        Returns an event string when something noteworthy happens.
        """
        # Update star powerup timer
        if self.star_active:
            self.star_timer -= 1
            if self.star_timer <= 0:
                self.star_active = False
                self.star_timer = 0
        
        # Handle death animation
        if self.is_dying:
            self.death_timer += 1
            if self.death_timer > 60:  # 1 second death animation
                return "death"
            # Keep showing dying animation
            self.sprite_animator.set_animation("dying", self.facing_right)
            self.draw_character()
            return None
        
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        old_facing = self.facing_right
        
        # Calculate speed and jump based on star powerup and speed multiplier
        base_speed = PLAYER_SPEED * self.speed_multiplier
        current_speed = base_speed * 1.5 if self.star_active else base_speed
        base_jump = JUMP_STRENGTH * self.jump_multiplier
        current_jump = base_jump * 1.3 if self.star_active else base_jump
        
        # Determine animation state based on movement and physics
        if self.vel_y < -2:  # Jumping up
            self.animation_state = "jumping"
        elif self.vel_y > 2:  # Falling
            self.animation_state = "falling"
        elif abs(self.vel_x) > 0:  # Moving horizontally
            self.animation_state = "walking"
        else:
            self.animation_state = "idle"
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -current_speed
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = current_speed
            self.facing_right = True
        
        # Update sprite animator with current state
        self.sprite_animator.set_animation(self.animation_state, self.facing_right)
        
        # Variable jump height implementation
        jump_pressed = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        
        if jump_pressed and self.on_ground:
            # Track how long jump button is held
            self.jump_hold_time += 1
            if self.jump_hold_time <= self.max_jump_hold:
                # Apply 10% bonus for holding jump button longer
                jump_bonus = 1.0 + (self.jump_hold_time / self.max_jump_hold) * 0.1  # Up to 10% bonus
                self.vel_y = current_jump * jump_bonus
            else:
                # Maximum bonus reached
                self.vel_y = current_jump * 1.1
            self.on_ground = False
            self.animation_state = "jumping"
            self.sprite_animator.set_animation("jumping", self.facing_right)
            if self.sound_manager:
                self.sound_manager.play('jump')
        elif not jump_pressed:
            # Reset jump hold time when button is released
            self.jump_hold_time = 0
        
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
            # Skip collision with space rocks (visual only)
            if hasattr(platform, 'platform_type') and platform.platform_type in ["space_rock"]:
                continue
            # Spiky platforms kill the player on contact
            if hasattr(platform, 'platform_type') and platform.platform_type == "spiky_platform":
                return "hit"  # Player dies when touching spiky platform
            if self.vel_y > 0:
                # Check if platform is solid (for fading platforms)
                if hasattr(platform, 'is_solid') and not platform.is_solid:
                    continue  # Skip collision with faded platforms
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
                self.on_ground = True
                self.jump_count = 0
                # Platform landing logic (for future use)
                pass
            elif self.vel_y < 0:
                # Check if platform is solid (for fading platforms)
                if hasattr(platform, 'is_solid') and not platform.is_solid:
                    continue  # Skip collision with faded platforms
                self.rect.top = platform.rect.bottom
                self.vel_y = 0
        if self.rect.left < 0:
            self.rect.left = 0
        # Use passed level_width if provided, otherwise fall back to global
        max_width = level_width if level_width is not None else LEVEL_WIDTH
        if self.rect.right > max_width:
            self.rect.right = max_width
        if self.rect.top > LEVEL_HEIGHT:
            self.is_dying = True
            self.animation_state = "dying"
            self.sprite_animator.set_animation("dying", self.facing_right)
            return None
        enemy_collisions = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in enemy_collisions:
            # If star is active, kill enemies on any touch
            if self.star_active:
                enemy.kill()
                if self.sound_manager:
                    self.sound_manager.play('enemy_kill')
                return "enemy_killed"
            # Check if player is jumping on enemy (player's bottom is above enemy's center)
            elif self.vel_y > 0 and self.rect.bottom < enemy.rect.centery:
                # Handle different enemy types
                if enemy.enemy_type in ["double_hit", "air_dragon"] and enemy.health > 1:
                    # Multi-hit enemy - damage but don't kill
                    enemy.take_damage()
                    self.vel_y = int(current_jump * 1.15)
                    self.animation_state = "stomping"
                    self.sprite_animator.set_animation("stomping", self.facing_right)
                    if self.sound_manager:
                        self.sound_manager.play('enemy_kill')
                    return "enemy_damaged"
                else:
                    # Single-hit enemy or final hit on multi-hit enemy
                    enemy.kill()
                    self.vel_y = int(current_jump * 1.15)
                    self.animation_state = "stomping"
                    self.sprite_animator.set_animation("stomping", self.facing_right)
                    if self.sound_manager:
                        self.sound_manager.play('enemy_kill')
                    return "enemy_killed"
            else:
                # Player got hit by enemy (only if star is not active)
                self.is_dying = True
                self.animation_state = "dying"
                self.sprite_animator.set_animation("dying", self.facing_right)
                if self.sound_manager:
                    self.sound_manager.play('hit')
                return "hit"
            # Check if this was a key enemy
            if hasattr(enemy, 'enemy_type') and enemy.enemy_type == "key_enemy":
                return "key_enemy_killed"
        powerup_collisions = pygame.sprite.spritecollide(self, powerups, False)
        if powerup_collisions:
            # Check powerup type before removing it
            powerup = powerup_collisions[0]
            powerup_type = getattr(powerup, 'powerup_type', 'coin')
            
            # Remove the powerup
            powerup.kill()
            
            if self.sound_manager:
                self.sound_manager.play('coin')
            
            # Return the powerup type
            if powerup_type == "rainbow_star":
                return "rainbow_star"
            elif powerup_type == "blue_star":
                return "blue_star"
            else:
                return "powerup"
        # Cheese now works like rocks - no stuck timer needed
        
        obstacle_collisions = pygame.sprite.spritecollide(self, obstacles, False)
        if obstacle_collisions and not self.star_active:
            hit = obstacle_collisions[0]
            if getattr(hit, 'obstacle_type', '') in ('jungle_plant', 'rock', 'cheese_glob'):
                # Jungle plant or rock: block movement without damage
                if self.vel_x > 0:
                    self.rect.right = hit.rect.left
                elif self.vel_x < 0:
                    self.rect.left = hit.rect.right
                self.vel_x = 0
                self.draw_character()
                return None
            elif getattr(hit, 'obstacle_type', '') == 'lava_pit':
                # Lava pit: instant damage
                self.is_dying = True
                self.animation_state = "dying"
                self.sprite_animator.set_animation("dying", self.facing_right)
                if self.sound_manager:
                    self.sound_manager.play('hit')
                return "hit"
            else:
                # Only take damage from other obstacles if star is not active
                self.is_dying = True
                self.animation_state = "dying"
                self.sprite_animator.set_animation("dying", self.facing_right)
                if self.sound_manager:
                    self.sound_manager.play('hit')
                return "hit"
        
        # Update character drawing with current animation state
        self.draw_character()
        return None


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type="basic", theme=None):
        """Initialize an enemy of a given type at (x, y)."""
        super().__init__()
        self.enemy_type = enemy_type
        self.theme = theme or {}
        
        # Enemy health and state
        self.health = 1
        self.max_health = 1
        self.is_air_enemy = False
        
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
        elif enemy_type == "double_hit":
            self.image = pygame.Surface((64, 64), pygame.SRCALPHA)
            self.speed = ENEMY_SPEED * 0.8
            self.health = 2
            self.max_health = 2
        elif enemy_type == "air_bat":
            self.image = pygame.Surface((48, 32), pygame.SRCALPHA)
            self.speed = ENEMY_SPEED * 1.2
            self.is_air_enemy = True
        elif enemy_type == "air_dragon":
            self.image = pygame.Surface((60, 40), pygame.SRCALPHA)
            self.speed = ENEMY_SPEED * 0.9
            self.is_air_enemy = True
            self.health = 2
            self.max_health = 2
        else:  # jumper
            self.image = pygame.Surface((52, 62), pygame.SRCALPHA)
            self.speed = ENEMY_SPEED
            
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = random.choice([-self.speed, self.speed])
        self.vel_y = 0
        self.jump_timer = 0
        self.jump_cooldown = random.randint(60, 120)
        
        # Air enemy specific properties
        if self.is_air_enemy:
            self.flight_pattern = random.choice(["horizontal", "circular", "zigzag"])
            self.flight_timer = 0
            self.base_y = y  # For circular and zigzag patterns
            
        self.draw_enemy()

    def draw_enemy(self):
        self.image.fill((0, 0, 0, 0))
        w, h = self.image.get_size()
        colors = self.theme.get('enemy_palette', [CORAL, SOFT_PINK, DUSTY_ROSE])
        
        # Scale down if damaged (double-hit enemies)
        if self.enemy_type in ["double_hit", "air_dragon"] and self.health < self.max_health:
            scale_factor = 0.7
            w = int(w * scale_factor)
            h = int(h * scale_factor)
            # Center the smaller enemy
            offset_x = (self.image.get_width() - w) // 2
            offset_y = (self.image.get_height() - h) // 2
        else:
            offset_x = 0
            offset_y = 0
            
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
        elif self.enemy_type == "double_hit":
            # Double-hit enemy - armored look
            base_c = colors[0]
            sec_c = colors[1] if len(colors) > 1 else DUSTY_ROSE
            # Main body
            pygame.draw.ellipse(self.image, base_c, (6 + offset_x, 20 + offset_y, w-12, h-32))
            pygame.draw.ellipse(self.image, sec_c, (6 + offset_x, 20 + offset_y, w-12, h-32), 4)
            # Armor plates
            pygame.draw.rect(self.image, DARK_GREY, (8 + offset_x, 15 + offset_y, w-16, 8))
            pygame.draw.rect(self.image, DARK_GREY, (8 + offset_x, 35 + offset_y, w-16, 6))
            # Eyes
            pygame.draw.circle(self.image, colors[2%len(colors)], (w//3 + offset_x, h//2 + offset_y), 8)
            pygame.draw.circle(self.image, colors[2%len(colors)], (2*w//3 + offset_x, h//2 + offset_y), 8)
            pygame.draw.circle(self.image, BLACK, (w//3 + offset_x, h//2 + offset_y), 4)
            pygame.draw.circle(self.image, BLACK, (2*w//3 + offset_x, h//2 + offset_y), 4)
            # Angry mouth
            pygame.draw.line(self.image, BLACK, (w//2 - 10 + offset_x, h//2 + 20 + offset_y), (w//2 + 10 + offset_x, h//2 + 20 + offset_y), 4)
        elif self.enemy_type == "air_bat":
            # Flying bat - dark and menacing
            base_c = DARK_GREY
            wing_c = BLACK
            # Body
            pygame.draw.ellipse(self.image, base_c, (w//2 - 4 + offset_x, h//2 - 4 + offset_y, 8, 12))
            # Wings
            pygame.draw.ellipse(self.image, wing_c, (2 + offset_x, h//2 - 8 + offset_y, w//2, 16))
            pygame.draw.ellipse(self.image, wing_c, (w//2 + offset_x, h//2 - 8 + offset_y, w//2, 16))
            # Eyes
            pygame.draw.circle(self.image, RED, (w//2 - 2 + offset_x, h//2 - 2 + offset_y), 2)
            pygame.draw.circle(self.image, RED, (w//2 + 2 + offset_x, h//2 - 2 + offset_y), 2)
        elif self.enemy_type == "air_dragon":
            # Flying dragon - more elaborate
            base_c = colors[0]
            wing_c = colors[1] if len(colors) > 1 else SOFT_PINK
            # Body
            pygame.draw.ellipse(self.image, base_c, (8 + offset_x, h//2 - 6 + offset_y, w-16, 12))
            # Wings
            pygame.draw.ellipse(self.image, wing_c, (4 + offset_x, h//2 - 10 + offset_y, w//2, 20))
            pygame.draw.ellipse(self.image, wing_c, (w//2 + offset_x, h//2 - 10 + offset_y, w//2, 20))
            # Head
            pygame.draw.circle(self.image, base_c, (w//2 + offset_x, h//2 - 8 + offset_y), 6)
            # Eyes
            pygame.draw.circle(self.image, YELLOW, (w//2 - 2 + offset_x, h//2 - 10 + offset_y), 2)
            pygame.draw.circle(self.image, YELLOW, (w//2 + 2 + offset_x, h//2 - 10 + offset_y), 2)
            # Tail
            pygame.draw.line(self.image, base_c, (w//2 + offset_x, h//2 + 6 + offset_y), (w//2 + offset_x, h//2 + 12 + offset_y), 3)
        elif self.enemy_type == "key_enemy":
            # Computer virus worm
            # Worm body (segmented)
            segments = 6
            segment_width = w // segments
            for i in range(segments):
                seg_x = i * segment_width + offset_x
                seg_y = h//2 - 6 + offset_y + int(3 * math.sin(i * 0.5))
                # Alternating colors for worm segments
                if i % 2 == 0:
                    seg_color = GLITCH_GREEN
                else:
                    seg_color = (0, 255, 0)  # Bright green
                pygame.draw.ellipse(self.image, seg_color, (seg_x, seg_y, segment_width-2, 12))
                pygame.draw.ellipse(self.image, BLACK, (seg_x, seg_y, segment_width-2, 12), 1)
            
            # Worm head
            head_x = w//2 - 8 + offset_x
            head_y = h//2 - 8 + offset_y
            pygame.draw.circle(self.image, GLITCH_GREEN, (head_x, head_y), 8)
            pygame.draw.circle(self.image, BLACK, (head_x, head_y), 8, 2)
            
            # Eyes
            pygame.draw.circle(self.image, ERROR_RED, (head_x - 3, head_y - 2), 2)
            pygame.draw.circle(self.image, ERROR_RED, (head_x + 3, head_y - 2), 2)
            
            # Virus spikes
            for i in range(4):
                spike_x = head_x + int(6 * math.cos(i * math.pi / 2))
                spike_y = head_y + int(6 * math.sin(i * math.pi / 2))
                pygame.draw.circle(self.image, ERROR_RED, (spike_x, spike_y), 2)
            
            # Key indicator (if this enemy has a key)
            if hasattr(self, 'key_color'):
                key_x = w//2 + offset_x
                key_y = h - 10 + offset_y
                if self.key_color == "red":
                    key_color = ERROR_RED
                else:
                    key_color = (0, 0, 255)  # Blue
                pygame.draw.circle(self.image, key_color, (key_x, key_y), 4)
                pygame.draw.circle(self.image, BLACK, (key_x, key_y), 4, 1)
        elif self.enemy_type == "bonus_animal":
            # Special animal enemies for bonus room
            # Draw a cute but dangerous animal
            center_x, center_y = w//2 + offset_x, h//2 + offset_y
            
            # Animal body
            pygame.draw.ellipse(self.image, (139, 69, 19), (center_x - 12, center_y - 8, 24, 16))  # Brown body
            pygame.draw.ellipse(self.image, BLACK, (center_x - 12, center_y - 8, 24, 16), 2)
            
            # Animal head
            pygame.draw.circle(self.image, (160, 82, 45), (center_x - 8, center_y - 2), 8)  # Lighter brown head
            pygame.draw.circle(self.image, BLACK, (center_x - 8, center_y - 2), 8, 2)
            
            # Ears
            pygame.draw.circle(self.image, (139, 69, 19), (center_x - 12, center_y - 6), 4)
            pygame.draw.circle(self.image, (139, 69, 19), (center_x - 4, center_y - 6), 4)
            pygame.draw.circle(self.image, BLACK, (center_x - 12, center_y - 6), 4, 1)
            pygame.draw.circle(self.image, BLACK, (center_x - 4, center_y - 6), 4, 1)
            
            # Eyes
            pygame.draw.circle(self.image, YELLOW, (center_x - 10, center_y - 4), 2)
            pygame.draw.circle(self.image, YELLOW, (center_x - 6, center_y - 4), 2)
            pygame.draw.circle(self.image, BLACK, (center_x - 10, center_y - 4), 2, 1)
            pygame.draw.circle(self.image, BLACK, (center_x - 6, center_y - 4), 2, 1)
            
            # Snout
            pygame.draw.circle(self.image, (139, 69, 19), (center_x - 4, center_y + 1), 3)
            pygame.draw.circle(self.image, BLACK, (center_x - 4, center_y + 1), 3, 1)
            
            # Tail
            pygame.draw.ellipse(self.image, (139, 69, 19), (center_x + 8, center_y - 2, 8, 4))
            pygame.draw.ellipse(self.image, BLACK, (center_x + 8, center_y - 2, 8, 4), 1)
            
            # Special sparkles (magical bonus animal)
            for i in range(3):
                sparkle_x = center_x + random.randint(-15, 15)
                sparkle_y = center_y + random.randint(-10, 10)
                pygame.draw.circle(self.image, (255, 215, 0), (sparkle_x, sparkle_y), 1)  # Gold sparkles
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
        """Update enemy movement, gravity, and platform collisions."""
        # Handle air enemies differently
        if self.is_air_enemy:
            self.update_air_enemy()
        else:
            # Ground enemies follow normal physics
            self.vel_y += GRAVITY
        if self.enemy_type == "jumper":
            self.jump_timer += 1
            if self.jump_timer >= self.jump_cooldown and self.vel_y == 0:
                self.vel_y = JUMP_STRENGTH * 0.7
                self.jump_timer = 0
                self.jump_cooldown = random.randint(60, 120)
            
            # Horizontal movement
        self.rect.x += int(self.vel_x)
        collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collisions:
            if self.vel_x > 0:
                self.rect.right = platform.rect.left
                self.vel_x = -self.speed
            elif self.vel_x < 0:
                self.rect.left = platform.rect.right
                self.vel_x = self.speed
            
            # Vertical movement
        self.rect.y += int(self.vel_y)
        collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in collisions:
            if self.vel_y > 0:
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
            elif self.vel_y < 0:
                self.rect.top = platform.rect.bottom
                self.vel_y = 0
            
            # Boundary checks
        if self.rect.left < 0 or self.rect.right > LEVEL_WIDTH:
            self.vel_x *= -1
        if self.rect.top > LEVEL_HEIGHT:
            self.kill()
    
    def update_air_enemy(self):
        """Update air enemies with flight patterns."""
        self.flight_timer += 1
        
        if self.flight_pattern == "horizontal":
            # Simple horizontal movement
            self.rect.x += int(self.vel_x)
            if self.rect.left < 0 or self.rect.right > LEVEL_WIDTH:
                self.vel_x *= -1
                
        elif self.flight_pattern == "circular":
            # Circular flight pattern
            radius = 50
            angle = self.flight_timer * 0.05
            self.rect.x = self.base_y + int(radius * math.cos(angle))
            self.rect.y = self.base_y + int(radius * math.sin(angle))
            
        elif self.flight_pattern == "zigzag":
            # Zigzag pattern
            self.rect.x += int(self.vel_x)
            self.rect.y = self.base_y + int(20 * math.sin(self.flight_timer * 0.1))
            if self.rect.left < 0 or self.rect.right > LEVEL_WIDTH:
                self.vel_x *= -1
        
        # Keep air enemies within bounds
        if self.rect.left < 0:
            self.rect.left = 0
            self.vel_x = abs(self.vel_x)
        if self.rect.right > LEVEL_WIDTH:
            self.rect.right = LEVEL_WIDTH
            self.vel_x = -abs(self.vel_x)
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > LEVEL_HEIGHT:
            self.rect.bottom = LEVEL_HEIGHT
    
    def take_damage(self):
        """Handle enemy taking damage."""
        if self.health > 1:
            self.health -= 1
            # Redraw enemy at smaller size
            self.draw_enemy()
            return False  # Not dead yet
        else:
            self.kill()
            return True  # Enemy died


class Checkpoint(pygame.sprite.Sprite):
    def __init__(self, x, y, theme=None):
        super().__init__()
        self.theme = theme or {}
        self.image = pygame.Surface((80, 100), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.activated = False
        self.draw_house()
    
    def draw_house(self):
        """Draw checkpoint. If theme is cheese, draw a cheese wheel."""
        self.image.fill((0, 0, 0, 0))
        w, h = self.image.get_size()
        theme_name = self.theme.get('name', '')
        if theme_name == "The Big Melt-down":
            # Draw a cheese wheel checkpoint with slightly different color
            cx, cy = w//2, h//2 + 10
            radius = min(w, h)//2 - 10
            body = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.circle(body, MELTED_CHEESE, (cx, cy), radius)
            pygame.draw.circle(body, BURNT_ORANGE, (cx, cy), radius, 4)
            # Wedge cut
            pygame.draw.polygon(body, (0,0,0,0), [(cx, cy), (cx+radius, cy-10), (cx+radius, cy+10)])
            # Cheese holes
            for _ in range(8):
                r = random.randint(4, 8)
                ox = random.randint(cx - radius + 10, cx + radius - 10)
                oy = random.randint(cy - radius + 10, cy + radius - 10)
                pygame.draw.circle(body, SOOT_GREY, (ox, oy), r)
            self.image.blit(body, (0,0))
            # Small flag to indicate activation
            if self.activated:
                pygame.draw.rect(self.image, RED, (cx-2, cy - radius - 12, 4, 12))
                pygame.draw.polygon(self.image, SOFT_YELLOW, [(cx+2, cy - radius - 12), (cx+18, cy - radius - 6), (cx+2, cy - radius)])
                pygame.draw.rect(self.image, BLACK, (cx-2, cy - radius - 12, 4, 12), 1)
        elif theme_name == "Moss-t Be Joking":
            # Draw a palm tree checkpoint
            trunk_x = w//2 - 6
            pygame.draw.rect(self.image, DARK_BROWN, (trunk_x, h-60, 12, 60))
            pygame.draw.rect(self.image, BLACK, (trunk_x, h-60, 12, 60), 1)
            # Leaves (big palm fronds)
            center = (w//2, h-60)
            for angle in (-50, -20, 10, 40, 70):
                leaf = pygame.Surface((60, 28), pygame.SRCALPHA)
                pygame.draw.ellipse(leaf, SAGE_GREEN, (0, 0, 60, 28))
                pygame.draw.ellipse(leaf, MOSS_GREEN, (0, 0, 60, 28), 3)
                rot = pygame.transform.rotate(leaf, angle)
                self.image.blit(rot, (center[0] - rot.get_width()//2, center[1] - rot.get_height()//2))
            # Activation coconuts
            if self.activated:
                pygame.draw.circle(self.image, DARK_BROWN, (w//2 - 10, h-50), 5)
                pygame.draw.circle(self.image, DARK_BROWN, (w//2 + 10, h-48), 5)
        elif theme_name == "Smelted Dreams":
            # Draw a candelabra/lantern checkpoint
            candelabra = pygame.Surface((w, h), pygame.SRCALPHA)
            
            # Base (stone pedestal)
            base_rect = pygame.Rect(15, h-35, w-30, 25)
            pygame.draw.rect(candelabra, DARK_GREY, base_rect)
            pygame.draw.rect(candelabra, BLACK, base_rect, 2)
            
            # Main pillar
            pillar_rect = pygame.Rect(w//2-4, h-60, 8, 30)
            pygame.draw.rect(candelabra, STEEL_GREY, pillar_rect)
            pygame.draw.rect(candelabra, BLACK, pillar_rect, 1)
            
            # Candelabra arms (3 arms)
            arm_positions = [w//2-12, w//2, w//2+12]
            for i, arm_x in enumerate(arm_positions):
                # Arm extending from pillar
                arm_y = h-50
                pygame.draw.line(candelabra, STEEL_GREY, (w//2, arm_y), (arm_x, arm_y-15), 3)
                pygame.draw.line(candelabra, BLACK, (w//2, arm_y), (arm_x, arm_y-15), 1)
                
                # Candle holder
                pygame.draw.circle(candelabra, DARK_GREY, (arm_x, arm_y-15), 4)
                pygame.draw.circle(candelabra, BLACK, (arm_x, arm_y-15), 4, 1)
                
                # Candle
                pygame.draw.rect(candelabra, CREAM, (arm_x-2, arm_y-25, 4, 10))
                pygame.draw.rect(candelabra, BLACK, (arm_x-2, arm_y-25, 4, 10), 1)
                
                # Flame
                flame_points = [
                    (arm_x, arm_y-25),  # Bottom of flame
                    (arm_x-2, arm_y-30),  # Left tip
                    (arm_x, arm_y-32),  # Top tip
                    (arm_x+2, arm_y-30),  # Right tip
                ]
                pygame.draw.polygon(candelabra, (255, 150, 0), flame_points)
                pygame.draw.polygon(candelabra, (255, 200, 60), flame_points[1:])  # Inner flame
            
            self.image.blit(candelabra, (0, 0))
            
            # Activation effect - make flames brighter
            if self.activated:
                for arm_x in arm_positions:
                    # Brighter flames when activated
                    flame_points = [
                        (arm_x, arm_y-25),  # Bottom of flame
                        (arm_x-3, arm_y-32),  # Left tip (bigger)
                        (arm_x, arm_y-35),  # Top tip (bigger)
                        (arm_x+3, arm_y-32),  # Right tip (bigger)
                    ]
                    pygame.draw.polygon(self.image, (255, 100, 0), flame_points)
                    pygame.draw.polygon(self.image, (255, 250, 100), flame_points[1:])  # Brighter inner flame
        elif theme_name == "Frost and Furious":
            # Draw an igloo checkpoint
            igloo = pygame.Surface((w, h), pygame.SRCALPHA)
            cx, cy = w//2, h-30
            radius = 34
            # Dome
            pygame.draw.circle(igloo, ICE_BLUE, (cx, cy), radius)
            pygame.draw.circle(igloo, SNOW_WHITE, (cx, cy), radius, 3)
            pygame.draw.rect(igloo, (0,0,0,0), (0, cy, w, h-cy))  # cut the bottom
            # Entrance
            pygame.draw.ellipse(igloo, DARK_BLUE, (cx-14, cy-6, 28, 22))
            pygame.draw.ellipse(igloo, BLACK, (cx-14, cy-6, 28, 22), 2)
            # Ice bricks lines
            for yline in range(cy-24, cy+2, 8):
                pygame.draw.line(igloo, SNOW_WHITE, (cx-24, yline), (cx+24, yline), 2)
            self.image.blit(igloo, (0, 0))
            if self.activated:
                # Snow sparkle on top when activated
                pygame.draw.circle(self.image, SNOW_WHITE, (cx, cy - radius - 2), 4)
        elif theme_name == "Boo Who?":
            # Draw a spaceship checkpoint
            spaceship = pygame.Surface((w, h), pygame.SRCALPHA)
            
            # Spaceship body (sleek oval shape)
            ship_center_x, ship_center_y = w//2, h-40
            ship_width, ship_height = 50, 25
            pygame.draw.ellipse(spaceship, STEEL_GREY, (ship_center_x - ship_width//2, ship_center_y - ship_height//2, ship_width, ship_height))
            pygame.draw.ellipse(spaceship, BLACK, (ship_center_x - ship_width//2, ship_center_y - ship_height//2, ship_width, ship_height), 2)
            
            # Spaceship nose (pointed front)
            nose_points = [
                (ship_center_x + ship_width//2, ship_center_y),  # Front center
                (ship_center_x + ship_width//2 + 15, ship_center_y - 8),  # Top point
                (ship_center_x + ship_width//2 + 15, ship_center_y + 8),  # Bottom point
            ]
            pygame.draw.polygon(spaceship, STEEL_GREY, nose_points)
            pygame.draw.polygon(spaceship, BLACK, nose_points, 2)
            
            # Cockpit window
            pygame.draw.ellipse(spaceship, ECTOPLASM_GREEN, (ship_center_x - 8, ship_center_y - 6, 16, 12))
            pygame.draw.ellipse(spaceship, BLACK, (ship_center_x - 8, ship_center_y - 6, 16, 12), 1)
            
            # Engine exhausts
            for offset in [-12, -4, 4, 12]:
                exhaust_x = ship_center_x + offset
                exhaust_y = ship_center_y + ship_height//2 + 5
                pygame.draw.rect(spaceship, DARK_GREY, (exhaust_x - 2, exhaust_y, 4, 8))
                pygame.draw.rect(spaceship, BLACK, (exhaust_x - 2, exhaust_y, 4, 8), 1)
            
            # Landing gear/stand
            stand_rect = pygame.Rect(w//2 - 15, h-25, 30, 15)
            pygame.draw.rect(spaceship, DARK_GREY, stand_rect)
            pygame.draw.rect(spaceship, BLACK, stand_rect, 2)
            
            self.image.blit(spaceship, (0, 0))
            
            # Activation effect - glowing lights
            if self.activated:
                # Glowing navigation lights
                pygame.draw.circle(self.image, (0, 255, 0), (ship_center_x - 20, ship_center_y - 10), 3)  # Green light
                pygame.draw.circle(self.image, (255, 0, 0), (ship_center_x + 20, ship_center_y - 10), 3)  # Red light
                pygame.draw.circle(self.image, (0, 0, 255), (ship_center_x, ship_center_y - 15), 3)  # Blue light
                
                # Glowing engine exhausts
                for offset in [-12, -4, 4, 12]:
                    exhaust_x = ship_center_x + offset
                    exhaust_y = ship_center_y + ship_height//2 + 8
                    pygame.draw.circle(self.image, (255, 150, 0), (exhaust_x, exhaust_y), 2)  # Glowing exhaust
        elif theme_name == "404: Floor Not Found":
            # Draw a computer checkpoint
            computer = pygame.Surface((w, h), pygame.SRCALPHA)
            
            # Monitor screen
            screen_rect = pygame.Rect(10, 10, w-20, h-30)
            pygame.draw.rect(computer, BLACK, screen_rect)
            pygame.draw.rect(computer, GLITCH_GREEN, screen_rect, 2)
            
            # Screen content (code-like)
            for i in range(0, h-40, 8):
                code_chars = []
                for _ in range(8):
                    code_chars.append(random.choice(["0", "1", "A", "B", "C", "D", "E", "F"]))
                code_line = "".join(code_chars)
                font_size = 8
                for j, char in enumerate(code_line[:6]):  # Limit to fit screen
                    char_x = 15 + j * 8
                    char_y = 15 + i
                    if char_x < w-10 and char_y < h-20:
                        pygame.draw.rect(computer, GLITCH_GREEN, (char_x, char_y, 6, 6))
            
            # Monitor stand
            stand_rect = pygame.Rect(w//2 - 10, h-25, 20, 15)
            pygame.draw.rect(computer, STEEL_GREY, stand_rect)
            pygame.draw.rect(computer, BLACK, stand_rect, 2)
            
            # Keyboard (below monitor)
            keyboard_rect = pygame.Rect(5, h-20, w-10, 10)
            pygame.draw.rect(computer, DARK_GREY, keyboard_rect)
            pygame.draw.rect(computer, BLACK, keyboard_rect, 1)
            
            # Key indicators
            for i in range(0, w-15, 8):
                key_x = 8 + i
                if key_x < w-8:
                    pygame.draw.rect(computer, GLITCH_GREEN, (key_x, h-18, 6, 6), 1)
            
            self.image.blit(computer, (0, 0))
            
            # Activation effect - screen glitch
            if self.activated:
                # Glitch effect overlay
                for _ in range(10):
                    glitch_x = random.randint(10, w-20)
                    glitch_y = random.randint(10, h-30)
                    glitch_width = random.randint(2, 8)
                    glitch_height = random.randint(1, 3)
                    pygame.draw.rect(self.image, ERROR_RED, (glitch_x, glitch_y, glitch_width, glitch_height))
        else:
            
            # House colors
            house_colors = self.theme.get('checkpoint_palette', [BEIGE, DARK_BROWN, SOFT_YELLOW])
            roof_color = house_colors[1] if len(house_colors) > 1 else DARK_BROWN
            wall_color = house_colors[0] if len(house_colors) > 0 else BEIGE
            window_color = house_colors[2] if len(house_colors) > 2 else SOFT_YELLOW
            
            # House base (rectangle)
            pygame.draw.rect(self.image, wall_color, (10, 40, w-20, h-50))
            pygame.draw.rect(self.image, BLACK, (10, 40, w-20, h-50), 2)
            
            # Roof (triangle)
            roof_points = [(5, 40), (w//2, 10), (w-5, 40)]
            pygame.draw.polygon(self.image, roof_color, roof_points)
            pygame.draw.polygon(self.image, BLACK, roof_points, 2)
            
            # Door
            pygame.draw.rect(self.image, DARK_BROWN, (w//2-8, h-30, 16, 30))
            pygame.draw.rect(self.image, BLACK, (w//2-8, h-30, 16, 30), 2)
            
            # Windows
            pygame.draw.rect(self.image, window_color, (w//4-6, 50, 12, 12))
            pygame.draw.rect(self.image, BLACK, (w//4-6, 50, 12, 12), 1)
            pygame.draw.rect(self.image, window_color, (3*w//4-6, 50, 12, 12))
            pygame.draw.rect(self.image, BLACK, (3*w//4-6, 50, 12, 12), 1)
            
            # Chimney
            pygame.draw.rect(self.image, DARK_BROWN, (w-15, 20, 8, 25))
            pygame.draw.rect(self.image, BLACK, (w-15, 20, 8, 25), 1)
            
            # Flag on top (indicates if activated)
            if self.activated:
                pygame.draw.rect(self.image, RED, (w//2-2, 5, 4, 15))
                pygame.draw.rect(self.image, BLACK, (w//2-2, 5, 4, 15), 1)
    
    def activate(self):
        """Activate the checkpoint."""
        self.activated = True
        self.draw_house()  # Redraw with flag


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, platform_type="normal", theme=None):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = pygame.Rect(x, y, width, height)
        self.platform_type = platform_type
        self.original_x = x
        self.original_y = y
        self.move_offset = 0
        self.theme = theme or {}
        # Removed falling cloud variables - now using regular moving platforms
        self.draw_platform(width, height)

    def draw_platform(self, width, height):
        # Check for specific platform types first
        if self.platform_type == "tree_block":
            self.draw_tree_block(width, height)
        elif self.platform_type == "rock_block":
            self.draw_rock_block(width, height)
        elif self.platform_type == "ice_shard":
            self.draw_ice_shard(width, height)
        # Removed falling_cloud case - now using regular moving platforms
        elif self.platform_type == "space_rock":
            self.draw_space_rock(width, height)
        elif self.platform_type == "tetris_moving":
            self.draw_tetris_platform(width, height)
        elif self.platform_type == "fading_platform":
            self.draw_fading_platform(width, height)
        elif self.platform_type == "golden_platform":
            self.draw_golden_platform(width, height)
        elif self.platform_type == "rainbow_platform":
            self.draw_rainbow_platform(width, height)
        elif self.platform_type == "pasta_slide":
            self.draw_pasta_slide(width, height)
        elif self.platform_type == "pasta_moving":
            self.draw_pasta_moving(width, height)
        elif self.platform_type == "concrete_platform":
            self.draw_concrete_platform(width, height)
        elif self.platform_type == "fire_escape":
            self.draw_fire_escape(width, height)
        elif self.platform_type == "neon_platform":
            self.draw_neon_platform(width, height)
        elif self.platform_type == "spiky_platform":
            self.draw_spiky_platform(width, height)
        elif self.platform_type == "vertical_moving":
            self.draw_vertical_moving_platform(width, height)
        else:
            # Use theme-based styling for regular platforms
            theme_name = self.theme.get('name', 'default')
            
            if theme_name == "The Big Melt-down":
                self.draw_cheese_platform(width, height)
            elif theme_name == "Moss-t Be Joking":
                self.draw_mossy_platform(width, height)
            elif theme_name == "Smelted Dreams":
                self.draw_metal_platform(width, height)
                # Chance to overlay flames to indicate 'on fire'
                import random
                if random.random() < 0.35:
                    self._overlay_flames(width, height)
            elif theme_name == "Frost and Furious":
                self.draw_ice_platform(width, height)
            elif theme_name == "Boo Who?":
                self.draw_ghost_platform(width, height)
            elif theme_name == "404: Floor Not Found":
                self.draw_digital_platform(width, height)
            elif theme_name == "Pasta La Vista":
                self.draw_pasta_platform(width, height)
            elif theme_name == "Concrete Jungle":
                self.draw_concrete_platform(width, height)
            elif theme_name == "Kraken Me Up":
                self.draw_underwater_platform(width, height)
            elif theme_name == "Neon Night":
                self.draw_neon_platform(width, height)
            else:
                # Default platform styling
                self.draw_default_platform(width, height)
    
    def draw_cheese_platform(self, width, height):
        # Melted cheese theme with slightly different color
        self.image.fill(MELTED_CHEESE)
        pygame.draw.rect(self.image, BURNT_ORANGE, (0, 0, width, height), 2)
        # Cheese holes
        for i in range(width // 20):
            hole_x = random.randint(5, width - 10)
            hole_y = random.randint(5, height - 10)
            pygame.draw.circle(self.image, SOOT_GREY, (hole_x, hole_y), 3)
        # Melted edges
        for x in range(0, width, 15):
            pygame.draw.arc(self.image, BURNT_ORANGE, (x, height-8, 15, 12), 0, 3.14, 2)
    
    def draw_tree_block(self, width, height):
        """Draw a tree block platform for Level 2."""
        # Tree trunk
        self.image.fill(DARK_BROWN)
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 2)
        
        # Tree bark texture
        for x in range(0, width, 8):
            for y in range(0, height, 6):
                if random.random() < 0.4:
                    pygame.draw.circle(self.image, (101, 67, 33), (x + 4, y + 3), 2)
        
        # Tree canopy (leaves on top)
        leaf_height = min(12, height // 2)
        pygame.draw.rect(self.image, MOSS_GREEN, (0, 0, width, leaf_height))
        pygame.draw.rect(self.image, BLACK, (0, 0, width, leaf_height), 1)
        
        # Leaf texture
        for i in range(width // 4):
            leaf_x = random.randint(2, width - 6)
            leaf_y = random.randint(2, leaf_height - 4)
            pygame.draw.ellipse(self.image, SAGE_GREEN, (leaf_x, leaf_y, 4, 3))
    
    def draw_rock_block(self, width, height):
        """Draw a rock block platform for Level 2."""
        # Rock base
        self.image.fill(WET_ROCK_GREY)
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 2)
        
        # Rock texture with moss patches
        for x in range(0, width, 6):
            for y in range(0, height, 4):
                if random.random() < 0.3:
                    # Rock texture
                    pygame.draw.circle(self.image, DARK_BROWN, (x + 3, y + 2), 1)
                elif random.random() < 0.15:
                    # Moss patches
                    pygame.draw.circle(self.image, MOSS_GREEN, (x + 3, y + 2), 2)
        
        # Moss on edges
        pygame.draw.line(self.image, MOSS_GREEN, (0, 0), (width, 0), 2)
        pygame.draw.line(self.image, SAGE_GREEN, (2, 2), (width-2, 2), 1)
    
    def draw_ice_shard(self, width, height):
        """Draw an ice shard platform for Level 4."""
        # Ice shard base
        self.image.fill(ICE_BLUE)
        pygame.draw.rect(self.image, SNOW_WHITE, (0, 0, width, height), 2)
        
        # Ice crystal texture
        for x in range(0, width, 8):
            for y in range(0, height, 6):
                if random.random() < 0.6:
                    # Crystal sparkles
                    pygame.draw.circle(self.image, SNOW_WHITE, (x + 4, y + 3), 1)
        
        # Sharp ice edges
        pygame.draw.line(self.image, SNOW_WHITE, (0, 0), (width, 0), 3)
        pygame.draw.line(self.image, ICE_BLUE, (0, height-1), (width, height-1), 1)
        
        # Ice shard points on top
        for x in range(0, width, 12):
            pygame.draw.polygon(self.image, SNOW_WHITE, [(x, height), (x+6, height-8), (x+12, height)])
    
    def draw_falling_cloud(self, width, height):
        """Draw a falling cloud platform for Level 5."""
        # Cloud base (fluffy white cloud)
        self.image.fill(WHITE)
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 2)
        
        # Cloud puffs
        for i in range(0, width, 20):
            puff_size = random.randint(8, 16)
            puff_x = i + random.randint(-5, 5)
            puff_y = random.randint(height//4, height*3//4)
            pygame.draw.circle(self.image, (240, 240, 240), (puff_x, puff_y), puff_size)
            pygame.draw.circle(self.image, BLACK, (puff_x, puff_y), puff_size, 1)
        
        # Warning effect - make it look unstable
        for x in range(0, width, 15):
            pygame.draw.line(self.image, (255, 200, 200), (x, 2), (x+10, 2), 1)
            pygame.draw.line(self.image, (255, 200, 200), (x, height-3), (x+10, height-3), 1)
    
    def draw_space_rock(self, width, height):
        """Draw a large space rock for Level 5."""
        # Rock base (dark grey/black space rock)
        self.image.fill(DARK_GREY)
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 3)
        
        # Space rock texture with craters
        for x in range(0, width, 12):
            for y in range(0, height, 8):
                if random.random() < 0.4:
                    # Rock texture
                    pygame.draw.circle(self.image, (40, 40, 40), (x + 6, y + 4), random.randint(1, 3))
                elif random.random() < 0.15:
                    # Craters
                    crater_size = random.randint(3, 6)
                    pygame.draw.circle(self.image, BLACK, (x + 6, y + 4), crater_size)
                    pygame.draw.circle(self.image, (20, 20, 20), (x + 6, y + 4), crater_size-1)
        
        # Space weathering effects
        for x in range(0, width, 8):
            for y in range(0, height, 6):
                if random.random() < 0.1:
                    # Glowing mineral deposits
                    pygame.draw.circle(self.image, (100, 100, 150), (x + 4, y + 3), 1)
        
        # Sharp edges
        pygame.draw.line(self.image, BLACK, (0, 0), (width, 0), 2)
        pygame.draw.line(self.image, BLACK, (0, height-1), (width, height-1), 2)
    
    def draw_tetris_platform(self, width, height):
        """Draw a Tetris-like moving platform for Level 6."""
        # Neon colors for computer theme
        neon_colors = [NEON_CYAN, NEON_MAGENTA, NEON_GREEN, NEON_YELLOW, NEON_RED]
        base_color = random.choice(neon_colors)
        
        # Platform base
        self.image.fill(base_color)
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 3)
        
        # Tetris block pattern
        block_size = 20
        for x in range(0, width, block_size):
            for y in range(0, height, block_size):
                # Create pixelated block effect
                if (x // block_size + y // block_size) % 2 == 0:
                    pygame.draw.rect(self.image, (255, 255, 255), (x, y, block_size, block_size), 1)
        
        # Neon glow effect
        pygame.draw.rect(self.image, base_color, (2, 2, width-4, height-4), 2)
        
        # Grid lines for Tetris effect
        for x in range(0, width, block_size):
            pygame.draw.line(self.image, BLACK, (x, 0), (x, height), 1)
        for y in range(0, height, block_size):
            pygame.draw.line(self.image, BLACK, (0, y), (width, y), 1)
    
    def draw_fading_platform(self, width, height):
        """Draw a fading platform for Level 6."""
        # Initialize fade properties if not set
        if not hasattr(self, 'fade_timer'):
            self.fade_timer = 0
        if not hasattr(self, 'is_solid'):
            self.is_solid = True
        
        # Neon blue color
        base_color = (0, 100, 255)
        
        # Calculate alpha based on fade timer
        fade_cycle = 120  # 2 seconds at 60 FPS
        fade_phase = (self.fade_timer % fade_cycle) / fade_cycle
        
        if fade_phase < 0.5:
            # Fade out
            alpha = int(255 * (1 - fade_phase * 2))
            self.is_solid = False
        else:
            # Fade in
            alpha = int(255 * ((fade_phase - 0.5) * 2))
            self.is_solid = True
        
        # Create surface with alpha
        self.image.fill((0, 0, 0, 0))  # Transparent background
        temp_surface = pygame.Surface((width, height))
        temp_surface.fill(base_color)
        temp_surface.set_alpha(alpha)
        
        # Draw platform with alpha
        pygame.draw.rect(temp_surface, base_color, (0, 0, width, height))
        pygame.draw.rect(temp_surface, BLACK, (0, 0, width, height), 2)
        
        # Grid pattern
        for x in range(0, width, 10):
            pygame.draw.line(temp_surface, BLACK, (x, 0), (x, height), 1)
        for y in range(0, height, 10):
            pygame.draw.line(temp_surface, BLACK, (0, y), (width, y), 1)
        
        self.image.blit(temp_surface, (0, 0))
        
        # Update fade timer
        self.fade_timer += 1
    
    def draw_golden_platform(self, width, height):
        """Draw a golden platform for bonus room."""
        # Gold base
        self.image.fill((255, 215, 0))  # Gold color
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 3)
        
        # Golden shine effect
        pygame.draw.rect(self.image, (255, 255, 150), (2, 2, width-4, height-4), 1)
        pygame.draw.rect(self.image, (255, 255, 200), (4, 4, width-8, height-8), 1)
        
        # Gem-like decorations
        for i in range(0, width, 20):
            gem_x = i + 10
            gem_y = height // 2
            pygame.draw.circle(self.image, (255, 255, 255), (gem_x, gem_y), 3)
            pygame.draw.circle(self.image, BLACK, (gem_x, gem_y), 3, 1)
    
    def draw_rainbow_platform(self, width, height):
        """Draw a rainbow platform for bonus room."""
        # Rainbow stripes
        stripe_height = height // 7
        colors = [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), 
                 (0, 0, 255), (75, 0, 130), (148, 0, 211)]
        
        for i, color in enumerate(colors):
            stripe_y = i * stripe_height
            pygame.draw.rect(self.image, color, (0, stripe_y, width, stripe_height))
        
        # Border
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 3)
        
        # Sparkle effects
        for _ in range(5):
            sparkle_x = random.randint(5, width - 5)
            sparkle_y = random.randint(5, height - 5)
            pygame.draw.circle(self.image, WHITE, (sparkle_x, sparkle_y), 2)
    
    def draw_pasta_slide(self, width, height):
        """Draw a pasta slide platform for Level 7."""
        # Pasta colors
        pasta_color = PARMESAN_YELLOW
        sauce_color = (200, 50, 50)  # Red sauce
        
        # Create sloped pasta shape
        self.image.fill(pasta_color)
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 3)
        
        # Draw pasta strands
        for i in range(0, width, 15):
            strand_x = i
            strand_height = height - (i // 3)  # Sloped effect
            pygame.draw.rect(self.image, (255, 255, 255), (strand_x, height - strand_height, 10, strand_height), 1)
        
        # Add sauce drips
        for i in range(0, width, 20):
            drip_x = i + 10
            pygame.draw.circle(self.image, sauce_color, (drip_x, height - 5), 3)
            pygame.draw.circle(self.image, BLACK, (drip_x, height - 5), 3, 1)
    
    def draw_pasta_moving(self, width, height):
        """Draw a moving pasta platform for Level 7."""
        # Pasta colors
        pasta_color = PARMESAN_YELLOW
        meat_color = (150, 100, 80)  # Meatball color
        
        # Platform base
        self.image.fill(pasta_color)
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 3)
        
        # Draw meatball chunks on platform
        for i in range(0, width, 25):
            chunk_x = i + 12
            chunk_y = height // 2
            pygame.draw.circle(self.image, meat_color, (chunk_x, chunk_y), 6)
            pygame.draw.circle(self.image, BLACK, (chunk_x, chunk_y), 6, 1)
        
        # Pasta texture
        for i in range(0, width, 8):
            pygame.draw.line(self.image, (255, 255, 255), (i, 0), (i, height), 1)
    
    def draw_concrete_platform(self, width, height):
        """Draw a concrete building ledge for Level 8."""
        # Concrete colors
        concrete_color = CONCRETE_GREY
        rebar_color = (100, 100, 100)
        
        # Concrete base
        self.image.fill(concrete_color)
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 3)
        
        # Concrete texture lines
        for i in range(0, width, 15):
            pygame.draw.line(self.image, (200, 200, 200), (i, 0), (i, height), 1)
        
        # Rebar (steel reinforcement)
        pygame.draw.rect(self.image, rebar_color, (5, height//2-2, width-10, 4))
        pygame.draw.rect(self.image, BLACK, (5, height//2-2, width-10, 4), 1)
        
        # Rust spots
        for _ in range(3):
            rust_x = random.randint(10, width-10)
            rust_y = random.randint(5, height-5)
            pygame.draw.circle(self.image, (150, 100, 50), (rust_x, rust_y), 2)
    
    def draw_fire_escape(self, width, height):
        """Draw a fire escape platform for Level 8."""
        # Metal colors
        metal_color = STEEL_GREY
        rust_color = (150, 100, 50)
        
        # Metal platform
        self.image.fill(metal_color)
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 2)
        
        # Metal grating pattern
        for i in range(0, width, 8):
            pygame.draw.line(self.image, BLACK, (i, 0), (i, height), 1)
        for i in range(0, height, 8):
            pygame.draw.line(self.image, BLACK, (0, i), (width, i), 1)
        
        # Rust spots
        for _ in range(4):
            rust_x = random.randint(5, width-5)
            rust_y = random.randint(5, height-5)
            pygame.draw.circle(self.image, rust_color, (rust_x, rust_y), 1)
        
        # Bolts
        pygame.draw.circle(self.image, BLACK, (5, 5), 2)
        pygame.draw.circle(self.image, BLACK, (width-5, 5), 2)
        pygame.draw.circle(self.image, BLACK, (5, height-5), 2)
        pygame.draw.circle(self.image, BLACK, (width-5, height-5), 2)
    
    def draw_neon_platform(self, width, height):
        """Draw a glowing neon platform for Level 10."""
        # Neon colors
        neon_colors = [NEON_MAGENTA, NEON_CYAN, NEON_YELLOW, NEON_GREEN, NEON_RED]
        base_color = random.choice(neon_colors)
        
        # Platform base
        self.image.fill(base_color)
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 3)
        
        # Neon glow effect
        pygame.draw.rect(self.image, NEON_WHITE, (2, 2, width-4, height-4), 1)
        
        # Circuit pattern
        for x in range(0, width, 10):
            for y in range(0, height, 10):
                if (x // 10 + y // 10) % 2 == 0:
                    pygame.draw.circle(self.image, NEON_WHITE, (x + 5, y + 5), 1)
        
        # Glowing edges
        pygame.draw.line(self.image, NEON_WHITE, (0, 0), (width, 0), 2)
        pygame.draw.line(self.image, NEON_WHITE, (0, height-1), (width, height-1), 2)
    
    def draw_spiky_platform(self, width, height):
        """Draw a spiky platform that kills the player on contact."""
        # Platform base (dark red to indicate danger)
        self.image.fill((100, 0, 0))
        pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 3)
        
        # Spikes covering the entire platform
        spike_height = height // 2
        for x in range(0, width, 8):
            spike_points = [
                (x, height),
                (x + 4, height - spike_height),
                (x + 8, height)
            ]
            pygame.draw.polygon(self.image, (150, 0, 0), spike_points)
            pygame.draw.polygon(self.image, BLACK, spike_points, 1)
        
        # Warning effect - pulsing red
        for x in range(0, width, 12):
            pygame.draw.line(self.image, (255, 100, 100), (x, 2), (x+8, 2), 1)
            pygame.draw.line(self.image, (255, 100, 100), (x, height-3), (x+8, height-3), 1)
    
    def draw_vertical_moving_platform(self, width, height):
        """Draw a vertically moving platform that matches the level theme when possible, cloud otherwise."""
        theme_name = self.theme.get('name', 'default')
        
        try:
            if theme_name == "The Big Melt-down":
                # Cheese theme - yellow platform with holes
                self.image.fill((255, 215, 0))  # Gold
                pygame.draw.rect(self.image, (139, 69, 19), (0, 0, width, height), 2)
                # Cheese holes
                for i in range(3):
                    x = (i + 1) * width // 4
                    y = height // 2
                    pygame.draw.circle(self.image, (255, 255, 255), (x, y), 4)
                    
            elif theme_name == "Moss-t Be Joking":
                # Jungle theme - green platform with leaves
                self.image.fill((34, 139, 34))  # Forest Green
                pygame.draw.rect(self.image, (0, 100, 0), (0, 0, width, height), 2)
                # Jungle leaves
                for x in range(0, width, 15):
                    pygame.draw.ellipse(self.image, (0, 150, 0), (x, 2, 8, 6))
                    
            elif theme_name == "Smelted Dreams":
                # Metal theme - silver platform with rivets
                self.image.fill((192, 192, 192))  # Silver
                pygame.draw.rect(self.image, (105, 105, 105), (0, 0, width, height), 2)
                # Metal rivets
                for x in range(width//6, width, width//3):
                    pygame.draw.circle(self.image, (169, 169, 169), (x, height//2), 2)
                    
            elif theme_name == "Frost and Furious":
                # Ice theme - blue/white platform with crystals
                self.image.fill((173, 216, 230))  # Light Blue
                pygame.draw.rect(self.image, (135, 206, 235), (0, 0, width, height), 2)
                # Ice crystals
                for x in range(0, width, 12):
                    pygame.draw.polygon(self.image, (255, 255, 255), 
                                      [(x, height//2), (x+3, height//2-3), (x+6, height//2)])
                    
            elif theme_name == "Boo Who?":
                # Ghost theme - ghostly blue platform
                self.image.fill((150, 150, 255))
                pygame.draw.rect(self.image, (0, 0, 0), (0, 0, width, height), 2)
                # Ghostly effect
                pygame.draw.rect(self.image, (200, 200, 255), (1, 1, width-2, height-2), 1)
                # Ethereal glow effect
                for x in range(0, width, 8):
                    pygame.draw.line(self.image, (255, 255, 255), (x, 1), (x+4, 1), 1)
                    pygame.draw.line(self.image, (255, 255, 255), (x, height-2), (x+4, height-2), 1)
                    
            elif theme_name == "404: Floor Not Found":
                # Digital theme - neon green platform
                self.image.fill((0, 255, 0))  # Neon Green
                pygame.draw.rect(self.image, (0, 200, 0), (0, 0, width, height), 2)
                # Digital pattern
                for x in range(0, width, 8):
                    for y in range(0, height, 8):
                        if (x // 8 + y // 8) % 2 == 0:
                            pygame.draw.rect(self.image, (0, 180, 0), (x, y, 4, 4))
                            
            elif theme_name == "Pasta La Vista":
                # Pasta theme - orange platform with strands
                self.image.fill((255, 165, 0))  # Orange
                pygame.draw.rect(self.image, (255, 140, 0), (0, 0, width, height), 2)
                # Pasta strands
                for i in range(3):
                    y = height//4 + i * height//6
                    pygame.draw.line(self.image, (255, 255, 255), (0, y), (width, y), 2)
                    
            elif theme_name == "Concrete Jungle":
                # Concrete theme - gray platform with texture
                self.image.fill((128, 128, 128))  # Gray
                pygame.draw.rect(self.image, (105, 105, 105), (0, 0, width, height), 2)
                # Concrete texture
                for x in range(0, width, 6):
                    pygame.draw.line(self.image, (169, 169, 169), (x, 0), (x, height), 1)
                    
            elif theme_name == "Kraken Me Up":
                # Underwater theme - blue-green platform with bubbles
                self.image.fill((0, 139, 139))  # Dark Cyan
                pygame.draw.rect(self.image, (0, 100, 100), (0, 0, width, height), 2)
                # Bubbles
                for i in range(4):
                    x = (i + 1) * width // 5
                    pygame.draw.circle(self.image, (173, 216, 230), (x, height//3), 2)
                    
            elif theme_name == "Neon Night":
                # Neon theme - bright purple platform with glow
                self.image.fill(NEON_PURPLE)  # Blue Violet
                pygame.draw.rect(self.image, (75, 0, 130), (0, 0, width, height), 2)
                # Neon glow
                pygame.draw.rect(self.image, NEON_WHITE, (1, 1, width-2, height-2), 1)
                
            else:
                # Fallback to cloud theme for unknown themes
                raise ValueError("Unknown theme, using cloud fallback")
                
        except:
            # Fallback to cloud styling if theme matching fails
            self.image.fill((255, 255, 255))
            # Cloud shape - rounded and fluffy
            pygame.draw.ellipse(self.image, (240, 240, 240), (0, height//4, width, height//2))
            
            # Cloud bumps for fluffy effect
            bump_size = height//3
            for i in range(3):
                x = i * width//3 + width//6
                pygame.draw.circle(self.image, (250, 250, 250), (x, height//2), bump_size)
            
            # Soft shadow/border
            pygame.draw.ellipse(self.image, (220, 220, 220), (0, height//4, width, height//2), 1)
            
            # Cloud texture - subtle dots
            for x in range(0, width, 8):
                for y in range(height//4, 3*height//4, 6):
                    if (x + y) % 12 == 0:
                        pygame.draw.circle(self.image, (235, 235, 235), (x, y), 1)
        
        # Add up/down arrows to indicate vertical movement (common to all themes)
        arrow_size = min(width//8, height//6, 4)
        # Up arrow
        up_arrow_x = width//4
        up_arrow_y = height//3
        up_arrow_points = [
            (up_arrow_x, up_arrow_y + arrow_size),
            (up_arrow_x - arrow_size//2, up_arrow_y),
            (up_arrow_x + arrow_size//2, up_arrow_y)
        ]
        pygame.draw.polygon(self.image, (100, 100, 100), up_arrow_points)
        pygame.draw.polygon(self.image, (50, 50, 50), up_arrow_points, 1)
        
        # Down arrow
        down_arrow_x = 3*width//4
        down_arrow_y = 2*height//3
        down_arrow_points = [
            (down_arrow_x, down_arrow_y - arrow_size),
            (down_arrow_x - arrow_size//2, down_arrow_y),
            (down_arrow_x + arrow_size//2, down_arrow_y)
        ]
        pygame.draw.polygon(self.image, (100, 100, 100), down_arrow_points)
        pygame.draw.polygon(self.image, (50, 50, 50), down_arrow_points, 1)
    
    def update(self):
        """Update platform behavior (for moving and falling platforms)."""
        if self.platform_type == "moving":
            # Moving platform logic
            self.move_offset += 0.02
            self.rect.x = self.original_x + int(50 * pygame.math.Vector2(1, 0).rotate(self.move_offset * 180 / 3.14159).x)
        # Removed falling cloud behavior - now using regular moving platforms
        elif self.platform_type == "tetris_moving":
            # Tetris platform movement - up/down and side to side
            self.move_offset += 0.03
            # Horizontal movement
            self.rect.x = self.original_x + int(60 * math.sin(self.move_offset))
            # Vertical movement (different phase)
            self.rect.y = self.original_y + int(40 * math.cos(self.move_offset * 0.7))
        elif self.platform_type == "fading_platform":
            # Fading platform updates its visual state
            self.draw_fading_platform(self.rect.width, self.rect.height)
        elif self.platform_type == "golden_platform":
            # Golden platforms can move vertically
            self.move_offset += 0.02
            self.rect.y = self.original_y + int(30 * math.sin(self.move_offset))
        elif self.platform_type == "rainbow_platform":
            # Rainbow platforms can move horizontally
            self.move_offset += 0.025
            self.rect.x = self.original_x + int(40 * math.cos(self.move_offset))
        elif self.platform_type == "pasta_moving":
            # Pasta moving platforms move vertically to help escape meatballs
            self.move_offset += 0.03
            self.rect.y = self.original_y + int(50 * math.sin(self.move_offset))
        elif self.platform_type == "vertical_moving":
            # Vertical moving platforms for Level 5 (Boo Who?)
            self.move_offset += 0.025
            import math
            self.rect.y = self.original_y + int(60 * math.sin(self.move_offset))
    
    # Removed trigger_fall method - no longer using falling clouds
    
    def draw_mossy_platform(self, width, height):
        # Mossy boulder theme
        self.image.fill(MOSS_GREEN)
        pygame.draw.rect(self.image, DARK_BROWN, (0, 0, width, height), 2)
        # Moss patches
        for i in range(width // 15):
            moss_x = random.randint(2, width - 8)
            moss_y = random.randint(2, height - 8)
            pygame.draw.ellipse(self.image, SAGE_GREEN, (moss_x, moss_y, 6, 4))
        # Rock texture
        for x in range(0, width, 8):
            for y in range(0, height, 6):
                if random.random() < 0.3:
                    pygame.draw.circle(self.image, WET_ROCK_GREY, (x + 4, y + 3), 2)
    
    def draw_metal_platform(self, width, height):
        # Metal beam theme
        self.image.fill(STEEL_GREY)
        pygame.draw.rect(self.image, DARK_GREY, (0, 0, width, height), 2)
        # Metal rivets
        for x in range(10, width, 20):
            pygame.draw.circle(self.image, SILVER, (x, height//2), 3)
            pygame.draw.circle(self.image, BLACK, (x, height//2), 1)
        # Weld marks
        for i in range(width // 25):
            weld_x = random.randint(5, width - 5)
            pygame.draw.line(self.image, MOLTEN_ORANGE, (weld_x, 0), (weld_x, height), 2)

    def _overlay_flames(self, width, height):
        # Simple flame triangles along the top of platform
        import random
        for x in range(0, width, 12):
            flame_h = random.randint(6, max(7, height//2))
            points = [(x, 0), (x+6, flame_h), (x+12, 0)]
            pygame.draw.polygon(self.image, (255, 120, 0), points)
            pygame.draw.polygon(self.image, (255, 200, 60), [(x+3, 0), (x+6, flame_h-3), (x+9, 0)])
    
    def draw_ice_platform(self, width, height):
        # Ice platform theme
        self.image.fill(ICE_BLUE)
        pygame.draw.rect(self.image, SNOW_WHITE, (0, 0, width, height), 2)
        # Ice crystals
        for x in range(0, width, 12):
            for y in range(0, height, 8):
                if random.random() < 0.4:
                    pygame.draw.circle(self.image, SNOW_WHITE, (x + 6, y + 4), 2)
        # Frost lines
        for i in range(width // 15):
            frost_x = random.randint(0, width)
            pygame.draw.line(self.image, SNOW_WHITE, (frost_x, 0), (frost_x + random.randint(-3, 3), height), 1)
    
    def draw_ghost_platform(self, width, height):
        # Spectral platform theme
        self.image.fill((0, 0, 0, 0))  # Transparent
        pygame.draw.ellipse(self.image, ECTOPLASM_GREEN, (0, height//3, width, height//2))
        # Ghostly glow
        for x in range(0, width, width//4):
            pygame.draw.circle(self.image, GHOSTLY_WHITE, (x + width//8, height//2), height//3)
        pygame.draw.ellipse(self.image, SHADOW_GREY, (2, height//3 + 2, width-4, height//2 - 4))
    
    def draw_digital_platform(self, width, height):
        # Digital/glitch theme
        self.image.fill(BLACK)
        pygame.draw.rect(self.image, GLITCH_GREEN, (0, 0, width, height), 2)
        # Digital grid
        for x in range(0, width, 8):
            pygame.draw.line(self.image, GLITCH_GREEN, (x, 0), (x, height), 1)
        for y in range(0, height, 8):
            pygame.draw.line(self.image, GLITCH_GREEN, (0, y), (width, y), 1)
        # Glitch effects
        for i in range(width // 20):
            glitch_x = random.randint(0, width - 5)
            glitch_y = random.randint(0, height - 5)
            pygame.draw.rect(self.image, ERROR_RED, (glitch_x, glitch_y, 4, 4))
    
    def draw_pasta_platform(self, width, height):
        # Pasta theme
        self.image.fill(MOZZARELLA_WHITE)
        pygame.draw.rect(self.image, TOMATO_RED, (0, 0, width, height), 2)
        # Pasta strands
        for i in range(width // 10):
            strand_x = random.randint(0, width)
            strand_y = random.randint(0, height)
            pygame.draw.line(self.image, BASIL_GREEN, (strand_x, strand_y), (strand_x + random.randint(-5, 5), strand_y + random.randint(-3, 3)), 2)
        # Meatball
        if width > 30:
            pygame.draw.circle(self.image, TOMATO_RED, (width//2, height//2), 8)
    
    def draw_concrete_platform(self, width, height):
        # Concrete with vines theme
        self.image.fill(CONCRETE_GREY)
        pygame.draw.rect(self.image, DARK_GREY, (0, 0, width, height), 2)
        # Cracks
        for i in range(width // 20):
            crack_x = random.randint(0, width)
            pygame.draw.line(self.image, DARK_GREY, (crack_x, 0), (crack_x + random.randint(-2, 2), height), 1)
        # Ivy vines
        for x in range(0, width, 15):
            pygame.draw.line(self.image, IVY_GREEN, (x, 0), (x + random.randint(-3, 3), height), 3)
    
    def draw_underwater_platform(self, width, height):
        # Underwater/sunken ship theme
        self.image.fill(DEEP_SEA_BLUE)
        pygame.draw.rect(self.image, DARK_BLUE, (0, 0, width, height), 2)
        # Barnacles
        for i in range(width // 12):
            barnacle_x = random.randint(2, width - 6)
            barnacle_y = random.randint(2, height - 6)
            pygame.draw.circle(self.image, DARK_BROWN, (barnacle_x, barnacle_y), 3)
        # Seaweed
        for x in range(0, width, 20):
            pygame.draw.line(self.image, SEAWEED_GREEN, (x, height), (x + random.randint(-2, 2), height - random.randint(5, 15)), 2)
    
    def draw_default_platform(self, width, height):
        # Original default platform styling
        style = self.platform_type
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
        elif self.platform_type == "vertical_moving":
            # Vertical moving platforms for Level 5 (Boo Who?)
            self.move_offset += 0.025
            import math
            self.rect.y = self.original_y + int(60 * math.sin(self.move_offset))


class Powerup(pygame.sprite.Sprite):
    def __init__(self, x, y, powerup_type="coin"):
        """Create a powerup at (x, y). Type controls visuals and effect."""
        super().__init__()
        self.powerup_type = powerup_type
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.float_offset = 0
        self.original_y = y
        self.spin_angle = 0
        if powerup_type == "bonus_coin":
            self.draw_bonus_coin()
        elif powerup_type == "rainbow_star":
            self.draw_rainbow_star()
        elif powerup_type == "blue_star":
            self.draw_blue_star()
        else:
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
    
    def draw_bonus_coin(self):
        """Draw a special bonus coin that gives lives and points."""
        self.image.fill((0, 0, 0, 0))
        # Larger bonus coin body with rainbow colors
        pygame.draw.circle(self.image, (255, 215, 0), (12, 12), 12)  # Gold base
        pygame.draw.circle(self.image, (255, 255, 255), (12, 12), 10)  # White center
        
        # Rainbow border
        colors = [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (75, 0, 130)]
        for i, color in enumerate(colors):
            angle = i * 60 * 3.14159 / 180
            x = 12 + int(9 * math.cos(angle))
            y = 12 + int(9 * math.sin(angle))
            pygame.draw.circle(self.image, color, (x, y), 2)
        
        # Sparkle effects
        pygame.draw.circle(self.image, (255, 255, 255), (8, 6), 2)
        pygame.draw.circle(self.image, (255, 255, 255), (16, 18), 2)
        pygame.draw.circle(self.image, (255, 255, 255), (6, 16), 1)
        pygame.draw.circle(self.image, (255, 255, 255), (18, 8), 1)
    
    def draw_rainbow_star(self):
        """Draw a rainbow star powerup."""
        self.image.fill((0, 0, 0, 0))
        
        # Rainbow colors
        rainbow_colors = [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), 
                         (0, 0, 255), (75, 0, 130), (148, 0, 211)]
        
        center_x, center_y = 12, 12
        
        # Draw rainbow star
        star_points = []
        for i in range(10):  # 5-pointed star
            angle = i * 36 * 3.14159 / 180
            if i % 2 == 0:
                radius = 10  # Outer points
            else:
                radius = 5   # Inner points
            x = center_x + int(radius * math.cos(angle))
            y = center_y + int(radius * math.sin(angle))
            star_points.append((x, y))
        
        # Draw star with rainbow colors
        for i, point in enumerate(star_points):
            color = rainbow_colors[i % len(rainbow_colors)]
            pygame.draw.circle(self.image, color, point, 2)
        
        # Draw main star outline
        pygame.draw.polygon(self.image, (255, 255, 255), star_points)
        pygame.draw.polygon(self.image, (0, 0, 0), star_points, 1)

    def draw_blue_star(self):
        """Draw a blue star powerup."""
        self.image.fill((0, 0, 0, 0))
        
        # Blue color scheme
        blue_colors = [(100, 149, 237), (65, 105, 225), (30, 144, 255), (0, 191, 255)]
        
        center_x, center_y = 12, 12
        
        # Draw blue star
        star_points = []
        for i in range(10):  # 5-pointed star
            angle = i * 36 * 3.14159 / 180
            if i % 2 == 0:
                radius = 10  # Outer points
            else:
                radius = 5   # Inner points
            x = center_x + int(radius * math.cos(angle))
            y = center_y + int(radius * math.sin(angle))
            star_points.append((x, y))
        
        # Draw star with blue colors
        for i, point in enumerate(star_points):
            color = blue_colors[i % len(blue_colors)]
            pygame.draw.circle(self.image, color, point, 2)
        
        # Draw main star outline in bright blue
        pygame.draw.polygon(self.image, (135, 206, 235), star_points)  # Sky blue
        pygame.draw.polygon(self.image, (0, 0, 139), star_points, 1)  # Dark blue outline
        
        # Sparkle effects
        sparkle_positions = [(6, 6), (18, 6), (6, 18), (18, 18), (12, 3), (12, 21)]
        for pos in sparkle_positions:
            pygame.draw.circle(self.image, (255, 255, 255), pos, 1)

    def update(self):
        self.float_offset += 0.15
        float_y = int(3 * pygame.math.Vector2(0, 1).rotate(self.float_offset * 180 / 3.14159).y)
        self.rect.y = self.original_y + float_y
        self.spin_angle += 5
        if self.spin_angle >= 360:
            self.spin_angle = 0


class StarPowerup(pygame.sprite.Sprite):
    """Special star-shaped powerup that gives temporary invincibility and power boost."""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.float_offset = 0
        self.original_y = y
        self.spin_angle = 0
        self.pulse_offset = 0
        self.draw_star()

    def draw_star(self):
        """Draw a glowing star shape."""
        self.image.fill((0, 0, 0, 0))
        center_x, center_y = 20, 20
        
        # Calculate star points (5-pointed star)
        outer_radius = 16 + int(2 * math.sin(self.pulse_offset))
        inner_radius = 7 + int(1 * math.sin(self.pulse_offset))
        
        points = []
        for i in range(10):
            angle = (i * 36 - 90 + self.spin_angle) * math.pi / 180
            if i % 2 == 0:
                # Outer point
                x = center_x + outer_radius * math.cos(angle)
                y = center_y + outer_radius * math.sin(angle)
            else:
                # Inner point
                x = center_x + inner_radius * math.cos(angle)
                y = center_y + inner_radius * math.sin(angle)
            points.append((x, y))
        
        # Draw glow effect (multiple layers)
        for glow_size in [6, 4, 2]:
            glow_surface = pygame.Surface((40, 40), pygame.SRCALPHA)
            glow_points = []
            for i in range(10):
                angle = (i * 36 - 90 + self.spin_angle) * math.pi / 180
                if i % 2 == 0:
                    radius = outer_radius + glow_size
                else:
                    radius = inner_radius + glow_size
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                glow_points.append((x, y))
            
            alpha = 50 - (glow_size * 8)
            glow_color = (*SOFT_YELLOW[:3], alpha)
            pygame.draw.polygon(glow_surface, glow_color, glow_points)
            self.image.blit(glow_surface, (0, 0))
        
        # Draw main star
        pygame.draw.polygon(self.image, SOFT_YELLOW, points)
        pygame.draw.polygon(self.image, WHITE, points, 2)
        
        # Add sparkle in center
        pygame.draw.circle(self.image, WHITE, (center_x, center_y), 4)
        pygame.draw.circle(self.image, SOFT_YELLOW, (center_x, center_y), 2)

    def update(self):
        """Animate the star powerup with floating, spinning, and pulsing."""
        self.float_offset += 0.1
        float_y = int(5 * math.sin(self.float_offset))
        self.rect.y = self.original_y + float_y
        
        self.spin_angle += 3
        if self.spin_angle >= 360:
            self.spin_angle = 0
        
        self.pulse_offset += 0.15
        
        # Redraw star with new animation state
        self.draw_star()


class HiddenDoor(pygame.sprite.Sprite):
    """Secret door that requires star powerup to reach."""
    def __init__(self, x, y, accessed=False):
        super().__init__()
        self.image = pygame.Surface((48, 64), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.pulse_offset = 0
        self.accessed = accessed
        self.draw_door()
    
    def draw_door(self):
        """Draw a mysterious glowing door."""
        self.image.fill((0, 0, 0, 0))
        w, h = self.image.get_size()
        
        # If accessed, draw a closed/disappeared door
        if self.accessed:
            # Draw a simple closed door (darker, no glow)
            pygame.draw.rect(self.image, (60, 40, 80), (4, 8, w-8, h-16), border_radius=8)
            pygame.draw.rect(self.image, (100, 80, 120), (4, 8, w-8, h-16), 3, border_radius=8)
            
            # Draw a simple "X" to indicate it's closed
            font = pygame.font.Font(None, 36)
            text = font.render("X", True, (150, 150, 150))
            text_rect = text.get_rect(center=(w//2, h//2))
            self.image.blit(text, text_rect)
        else:
            # Original glowing door
            # Door frame
            pygame.draw.rect(self.image, (80, 60, 100), (4, 8, w-8, h-16), border_radius=8)
            pygame.draw.rect(self.image, (120, 100, 140), (4, 8, w-8, h-16), 3, border_radius=8)
            
            # Inner glow with pulse
            pulse_intensity = abs(math.sin(self.pulse_offset))
            glow_color = (150 + int(50 * pulse_intensity), 120 + int(30 * pulse_intensity), 200)
            pygame.draw.rect(self.image, glow_color, (10, 14, w-20, h-28), border_radius=6)
            
            # Mystery symbol (question mark)
            font = pygame.font.Font(None, 48)
            text = font.render("?", True, WHITE)
            text_rect = text.get_rect(center=(w//2, h//2))
            self.image.blit(text, text_rect)
    
    def update(self):
        """Animate the door pulse."""
        self.pulse_offset += 0.1
        self.draw_door()


class BigCoin(pygame.sprite.Sprite):
    """Large coin that gives many points and hearts."""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.float_offset = 0
        self.original_y = y
        self.spin_angle = 0
        self.draw_coin()
    
    def draw_coin(self):
        """Draw a big golden coin."""
        self.image.fill((0, 0, 0, 0))
        center = 30
        
        # Outer glow
        for r in range(32, 26, -2):
            alpha = 60 - (32 - r) * 10
            pygame.draw.circle(self.image, (*SOFT_YELLOW[:3], alpha), (center, center), r)
        
        # Main coin body
        pygame.draw.circle(self.image, CHEESE_YELLOW, (center, center), 26)
        pygame.draw.circle(self.image, (200, 160, 0), (center, center), 26, 3)
        
        # Inner circle
        pygame.draw.circle(self.image, SOFT_YELLOW, (center, center), 20)
        pygame.draw.circle(self.image, (200, 160, 0), (center, center), 20, 2)
        
        # Dollar sign
        font = pygame.font.Font(None, 36)
        text = font.render("$", True, (180, 140, 0))
        text_rect = text.get_rect(center=(center, center))
        self.image.blit(text, text_rect)
        
        # Sparkles
        for _ in range(4):
            angle = self.spin_angle + _ * 90
            rad = math.radians(angle)
            sx = center + int(18 * math.cos(rad))
            sy = center + int(18 * math.sin(rad))
            pygame.draw.circle(self.image, WHITE, (sx, sy), 3)
    
    def update(self):
        """Animate the big coin."""
        self.float_offset += 0.08
        float_y = int(8 * math.sin(self.float_offset))
        self.rect.y = self.original_y + float_y
        
        self.spin_angle += 4
        if self.spin_angle >= 360:
            self.spin_angle = 0
        self.draw_coin()


class BonusNPC(pygame.sprite.Sprite):
    """NPC that gives rewards in bonus room."""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 56), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.bounce_offset = 0
        self.draw_npc()
    
    def draw_npc(self):
        """Draw a friendly cheese character."""
        self.image.fill((0, 0, 0, 0))
        w, h = self.image.get_size()
        
        # Cheese body
        pygame.draw.ellipse(self.image, CHEESE_YELLOW, (4, 14, 32, 36))
        pygame.draw.ellipse(self.image, BURNT_ORANGE, (4, 14, 32, 36), 2)
        
        # Cheese holes
        pygame.draw.circle(self.image, (200, 180, 140), (12, 26), 4)
        pygame.draw.circle(self.image, (200, 180, 140), (26, 32), 5)
        
        # Happy face
        pygame.draw.circle(self.image, BLACK, (14, 22), 3)
        pygame.draw.circle(self.image, BLACK, (26, 22), 3)
        pygame.draw.arc(self.image, BLACK, (12, 28, 16, 12), 0, 3.14, 2)
        
        # Crown
        for i in range(3):
            x = 10 + i * 8
            pygame.draw.polygon(self.image, SOFT_YELLOW, [(x, 14), (x+4, 8), (x+8, 14)])
    
    def update(self):
        """Animate NPC bounce."""
        self.bounce_offset += 0.15
        bounce = int(4 * abs(math.sin(self.bounce_offset)))
        self.rect.y = self.rect.y - bounce + int(4 * abs(math.sin(self.bounce_offset - 0.15)))


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, obstacle_type="spike"):
        """Construct an obstacle (spike, coral, firewall, etc.) at (x, y)."""
        super().__init__()
        self.obstacle_type = obstacle_type
        if obstacle_type == "spike":
            self.image = pygame.Surface((20, 24), pygame.SRCALPHA)
        elif obstacle_type == "ice_spike":
            self.image = pygame.Surface((20, 26), pygame.SRCALPHA)
        elif obstacle_type == "jungle_plant":
            self.image = pygame.Surface((28, 46), pygame.SRCALPHA)
        elif obstacle_type == "rock":
            self.image = pygame.Surface((36, 26), pygame.SRCALPHA)
        elif obstacle_type == "cheese_glob":
            self.image = pygame.Surface((36, 20), pygame.SRCALPHA)
        elif obstacle_type == "lava_pit":
            self.image = pygame.Surface((80, 16), pygame.SRCALPHA)
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
        elif self.obstacle_type == "ice_spike":
            # Taller, blueish spikes for ice
            spike_points = [
                [(2, 26), (10, 2), (18, 26)],
                [(0, 26), (6, 10), (12, 26)],
                [(8, 26), (14, 6), (20, 26)]
            ]
            for spike in spike_points:
                pygame.draw.polygon(self.image, ICE_BLUE, spike)
                pygame.draw.polygon(self.image, SNOW_WHITE, spike, 1)
        elif self.obstacle_type == "jungle_plant":
            # Tall leafy plant blocking path
            pygame.draw.ellipse(self.image, MOSS_GREEN, (4, 12, 20, 28))
            pygame.draw.ellipse(self.image, DARK_BROWN, (4, 12, 20, 28), 3)
            # Leaves
            pygame.draw.ellipse(self.image, SAGE_GREEN, (0, 0, 18, 18))
            pygame.draw.ellipse(self.image, SAGE_GREEN, (10, 0, 18, 18))
            pygame.draw.line(self.image, DARK_BROWN, (14, 40), (14, 46), 3)
        elif self.obstacle_type == "rock":
            # Ground rock
            pygame.draw.ellipse(self.image, WET_ROCK_GREY, (0, 6, 36, 20))
            pygame.draw.ellipse(self.image, DARK_BROWN, (0, 6, 36, 20), 2)
        elif self.obstacle_type == "cheese_glob":
            # Draw a bigger cheese glob that works like rocks
            pygame.draw.ellipse(self.image, MELTED_CHEESE, (0, 0, 48, 32))  # Much bigger cheese glob
            pygame.draw.ellipse(self.image, BURNT_ORANGE, (0, 0, 48, 32), 3)
            # Holes
            for _ in range(6):  # More holes for larger cheese
                r = random.randint(2, 5)
                x = random.randint(8, 40)
                y = random.randint(6, 26)
                pygame.draw.circle(self.image, SOOT_GREY, (x, y), r)
        elif self.obstacle_type == "lava_pit":
            # Draw a realistic lava pit with flames
            w, h = self.image.get_width(), self.image.get_height()
            
            # Lava base (molten rock)
            pygame.draw.rect(self.image, (60, 15, 5), (0, 0, w, h))
            pygame.draw.rect(self.image, (90, 25, 8), (0, 0, w, h//2))
            
            # Molten lava surface with bubbling effect
            for i in range(0, w, 6):
                for j in range(0, h//2, 4):
                    if random.random() < 0.7:
                        # Lava bubbles
                        bubble_color = random.choice([(255, 80, 0), (255, 120, 20), (255, 60, 0)])
                        pygame.draw.circle(self.image, bubble_color, (i + 3, j + 2), random.randint(1, 3))
            
            # Flames rising from lava
            for i in range(0, w, 8):
                flame_height = random.randint(8, 16)
                # Multiple flame layers for realistic effect
                for layer in range(3):
                    flame_color = [(255, 150, 0), (255, 100, 0), (255, 50, 0)][layer]
                    flame_width = 4 - layer
                    flame_x = i + random.randint(-1, 1)
                    
                    # Draw flame shape
                    flame_points = [
                        (flame_x, h),  # Bottom center
                        (flame_x - flame_width//2, h - flame_height//2),  # Left middle
                        (flame_x, 0),  # Top center
                        (flame_x + flame_width//2, h - flame_height//2),  # Right middle
                    ]
                    pygame.draw.polygon(self.image, flame_color, flame_points)
            
            # Hot embers floating around
            for _ in range(random.randint(2, 4)):
                ember_x = random.randint(0, w)
                ember_y = random.randint(0, h//2)
                ember_color = random.choice([(255, 200, 50), (255, 150, 30), (255, 100, 20)])
                pygame.draw.circle(self.image, ember_color, (ember_x, ember_y), 1)
        elif self.obstacle_type.startswith("firewall_"):
            # Draw computer firewalls
            firewall_color = self.obstacle_type.split("_")[1]  # "red" or "blue"
            w, h = self.image.get_width(), self.image.get_height()
            
            # Wall base
            if firewall_color == "red":
                base_color = (150, 0, 0)
                glow_color = (255, 0, 0)
                border_color = (200, 50, 50)
            else:  # blue
                base_color = (0, 0, 150)
                glow_color = (0, 0, 255)
                border_color = (50, 50, 200)
            
            # Firewall body
            pygame.draw.rect(self.image, base_color, (0, 0, w, h))
            pygame.draw.rect(self.image, border_color, (0, 0, w, h), 3)
            
            # Glowing effect
            pygame.draw.rect(self.image, glow_color, (2, 2, w-4, h-4), 1)
            
            # Circuit pattern
            for x in range(0, w, 8):
                for y in range(0, h, 8):
                    if (x // 8 + y // 8) % 2 == 0:
                        pygame.draw.circle(self.image, glow_color, (x + 4, y + 4), 1)
            
            # Lock symbol
            lock_x, lock_y = w//2, h//2
            pygame.draw.rect(self.image, BLACK, (lock_x - 8, lock_y - 6, 16, 12))
            pygame.draw.rect(self.image, glow_color, (lock_x - 6, lock_y - 4, 12, 8))
            pygame.draw.rect(self.image, BLACK, (lock_x - 4, lock_y - 8, 8, 6))
            
            # "FIREWALL" text effect
            text_y = h - 15
            for i, char in enumerate("FIREWALL"):
                char_x = 5 + i * 6
                if char_x < w - 5:
                    pygame.draw.rect(self.image, glow_color, (char_x, text_y, 4, 8))
        elif self.obstacle_type == "giant_meatball":
            # Draw a giant rolling meatball
            w, h = self.image.get_width(), self.image.get_height()
            
            # Make meatball very big
            meatball_size = min(w, h) - 10
            center_x, center_y = w // 2, h // 2
            
            # Main meatball body
            pygame.draw.circle(self.image, (120, 80, 60), (center_x, center_y), meatball_size // 2)
            pygame.draw.circle(self.image, BLACK, (center_x, center_y), meatball_size // 2, 3)
            
            # Meat texture with darker spots
            for _ in range(8):
                spot_x = center_x + random.randint(-meatball_size//3, meatball_size//3)
                spot_y = center_y + random.randint(-meatball_size//3, meatball_size//3)
                spot_radius = random.randint(3, 8)
                pygame.draw.circle(self.image, (100, 60, 40), (spot_x, spot_y), spot_radius)
            
            # Sauce drips
            for _ in range(5):
                drip_x = center_x + random.randint(-meatball_size//2, meatball_size//2)
                drip_y = center_y + meatball_size//2 - 5
                pygame.draw.circle(self.image, (150, 50, 50), (drip_x, drip_y), 4)
            
            # Rolling effect - add motion blur
            for i in range(3):
                blur_x = center_x + i * 2
                pygame.draw.circle(self.image, (100, 70, 50), (blur_x, center_y), meatball_size // 2 - 2, 1)
        elif self.obstacle_type == "floor_spike":
            # Draw floor spikes for Neon Night
            w, h = self.image.get_width(), self.image.get_height()
            
            # Multiple spikes pointing up
            spike_positions = [(w//4, h-5), (w//2, h-5), (3*w//4, h-5)]
            
            for spike_x, spike_y in spike_positions:
                # Draw spike pointing up
                spike_points = [
                    (spike_x, spike_y),  # Bottom center
                    (spike_x - 8, spike_y - 20),  # Left tip
                    (spike_x + 8, spike_y - 20),  # Right tip
                ]
                pygame.draw.polygon(self.image, (100, 100, 100), spike_points)
                pygame.draw.polygon(self.image, BLACK, spike_points, 2)
        
        elif self.obstacle_type == "falling_tetris":
            # Draw falling Tetris pieces
            w, h = self.image.get_width(), self.image.get_height()
            
            # Different Tetris piece shapes
            tetris_shapes = [
                # I-piece (line)
                [(w//2-15, h//2-5), (w//2+15, h//2-5), (w//2+15, h//2+5), (w//2-15, h//2+5)],
                # T-piece
                [(w//2-10, h//2-10), (w//2+10, h//2-10), (w//2+10, h//2), (w//2+5, h//2), (w//2+5, h//2+10), (w//2-5, h//2+10), (w//2-5, h//2), (w//2-10, h//2)],
                # L-piece
                [(w//2-10, h//2-10), (w//2+10, h//2-10), (w//2+10, h//2+5), (w//2-5, h//2+5), (w//2-5, h//2+10), (w//2-10, h//2+10)]
            ]
            
            shape = random.choice(tetris_shapes)
            neon_color = random.choice([(255, 0, 255), (0, 255, 255), (255, 255, 0), (0, 255, 0), (255, 0, 0)])
            pygame.draw.polygon(self.image, neon_color, shape)
            pygame.draw.polygon(self.image, BLACK, shape, 2)
        
        elif self.obstacle_type == "city_train":
            # Draw city train
            w, h = self.image.get_width(), self.image.get_height()
            
            # Train body
            pygame.draw.rect(self.image, (150, 150, 150), (0, h//2-15, w, 30))
            pygame.draw.rect(self.image, BLACK, (0, h//2-15, w, 30), 2)
            
            # Train windows
            for i in range(0, w, 25):
                pygame.draw.rect(self.image, (100, 150, 255), (i+5, h//2-10, 15, 20))
                pygame.draw.rect(self.image, BLACK, (i+5, h//2-10, 15, 20), 1)
            
            # Train wheels
            pygame.draw.circle(self.image, BLACK, (15, h//2+10), 8)
            pygame.draw.circle(self.image, BLACK, (w-15, h//2+10), 8)
            
            # Train tracks
            pygame.draw.line(self.image, (100, 100, 100), (0, h//2+18), (w, h//2+18), 3)
        
        elif self.obstacle_type == "spiky_coral":
            # Draw spiky coral for underwater maze
            w, h = self.image.get_width(), self.image.get_height()
            
            # Coral base
            pygame.draw.ellipse(self.image, (255, 100, 150), (w//4, h//2, w//2, h//2))
            pygame.draw.ellipse(self.image, BLACK, (w//4, h//2, w//2, h//2), 2)
            
            # Spikes all around
            for angle in range(0, 360, 30):
                import math
                spike_x = w//2 + int(15 * math.cos(math.radians(angle)))
                spike_y = h//2 + int(15 * math.sin(math.radians(angle)))
                pygame.draw.circle(self.image, (200, 50, 100), (spike_x, spike_y), 3)
                pygame.draw.circle(self.image, BLACK, (spike_x, spike_y), 3, 1)
        
        elif self.obstacle_type == "evil_fish":
            # Draw evil fish for underwater maze
            w, h = self.image.get_width(), self.image.get_height()
            
            # Fish body
            pygame.draw.ellipse(self.image, (255, 50, 50), (w//4, h//4, w//2, h//2))
            pygame.draw.ellipse(self.image, BLACK, (w//4, h//4, w//2, h//2), 2)
            
            # Evil eyes
            pygame.draw.circle(self.image, (255, 255, 0), (w//2-8, h//2-5), 4)
            pygame.draw.circle(self.image, (255, 255, 0), (w//2+8, h//2-5), 4)
            pygame.draw.circle(self.image, BLACK, (w//2-8, h//2-5), 4, 1)
            pygame.draw.circle(self.image, BLACK, (w//2+8, h//2-5), 4, 1)
            
            # Sharp teeth
            for i in range(3):
                tooth_x = w//2 - 10 + i * 10
                pygame.draw.polygon(self.image, (255, 255, 255), 
                                  [(tooth_x, h//2+5), (tooth_x-3, h//2+15), (tooth_x+3, h//2+15)])


class Key(pygame.sprite.Sprite):
    """Computer firewall key that can be collected."""
    def __init__(self, x, y, key_color):
        super().__init__()
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.key_color = key_color
        self.float_offset = 0
        self.original_y = y
        self.draw_key()
    
    def draw_key(self):
        """Draw the key based on its color."""
        self.image.fill((0, 0, 0, 0))
        w, h = self.image.get_size()
        
        # Key color
        if self.key_color == "red":
            key_color = ERROR_RED
            glow_color = (255, 100, 100)
        else:  # blue
            key_color = (0, 0, 255)
            glow_color = (100, 100, 255)
        
        # Key blade
        pygame.draw.rect(self.image, key_color, (4, h//2 - 2, 16, 4))
        pygame.draw.rect(self.image, glow_color, (4, h//2 - 2, 16, 4), 1)
        
        # Key head (circular)
        pygame.draw.circle(self.image, key_color, (w//2, h//2), 8)
        pygame.draw.circle(self.image, glow_color, (w//2, h//2), 8, 2)
        
        # Key hole
        pygame.draw.circle(self.image, BLACK, (w//2, h//2), 3)
        
        # Glow effect
        pygame.draw.circle(self.image, glow_color, (w//2, h//2), 10, 1)
    
    def update(self):
        """Float the key up and down."""
        self.float_offset += 0.1
        self.rect.y = self.original_y + int(3 * math.sin(self.float_offset))


