import random
import math
import pygame
from constants import GRAVITY, JUMP_STRENGTH, PLAYER_SPEED, ENEMY_SPEED, LEVEL_WIDTH, LEVEL_HEIGHT, WHITE, BLACK, SOFT_PURPLE, LIGHT_PURPLE, SOFT_PINK, DUSTY_ROSE, PEACH, CORAL, MOUNTAIN_BLUE, BEIGE, LIGHT_BROWN, SAGE_GREEN, PASTEL_GREEN, MINT_GREEN, SOFT_YELLOW, SOFT_BLUE, CREAM, CHEESE_YELLOW, BURNT_ORANGE, SOOT_GREY, MOSS_GREEN, DARK_BROWN, WET_ROCK_GREY, STEEL_GREY, DARK_GREY, SILVER, MOLTEN_ORANGE, ICE_BLUE, SNOW_WHITE, ECTOPLASM_GREEN, GHOSTLY_WHITE, SHADOW_GREY, GLITCH_GREEN, ERROR_RED, MOZZARELLA_WHITE, TOMATO_RED, BASIL_GREEN, CONCRETE_GREY, IVY_GREEN, DEEP_SEA_BLUE, DARK_BLUE, SEAWEED_GREEN, SKY_BLUE

# Additional colors for new enemies
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
from sprite_animator import SpriteAnimator


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, sound_manager=None):
        super().__init__()
        
        # Initialize sprite animator
        self.sprite_animator = SpriteAnimator()
        
        # Get initial sprite and set up rect
        self.image = self.sprite_animator.get_current_sprite()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Physics
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.jump_count = 0
        self.max_jumps = 1
        self.facing_right = True
        self.sound_manager = sound_manager
        
        # Animation state
        self.animation_state = "idle"
        self.is_dying = False
        self.death_timer = 0
        
        # Star powerup state
        self.star_active = False
        self.star_timer = 0
        self.star_duration = 600  # 10 seconds at 60 FPS
        self.glow_pulse = 0
        
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
        # Keep star powerup active through respawn
    
    def activate_star_powerup(self):
        """Activate the star powerup effect."""
        self.star_active = True
        self.star_timer = self.star_duration
        if self.sound_manager:
            self.sound_manager.play('coin')  # Use coin sound for powerup

    def draw_character(self):
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
            # Adjust rect to account for glow
            old_center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = old_center
        else:
            # Normal sprite without glow
            self.image = base_sprite
            old_center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = old_center
    

    def update(self, platforms, enemies, powerups, obstacles, camera_x, level_width=None):
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
        
        # Calculate speed and jump based on star powerup
        current_speed = PLAYER_SPEED * 1.5 if self.star_active else PLAYER_SPEED
        current_jump = JUMP_STRENGTH * 1.3 if self.star_active else JUMP_STRENGTH
        
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
        
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = current_jump
            self.on_ground = False
            self.animation_state = "jumping"
            self.sprite_animator.set_animation("jumping", self.facing_right)
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
        powerup_collisions = pygame.sprite.spritecollide(self, powerups, True)
        if powerup_collisions:
            if self.sound_manager:
                self.sound_manager.play('coin')
            return "powerup"
        obstacle_collisions = pygame.sprite.spritecollide(self, obstacles, False)
        if obstacle_collisions and not self.star_active:
            # Special handling for sticky cheese globs
            hit = obstacle_collisions[0]
            if getattr(hit, 'obstacle_type', '') == 'cheese_glob':
                # Stick the player in place for ~2 seconds (120 frames)
                if not hasattr(self, 'stuck_timer') or self.stuck_timer <= 0:
                    self.stuck_timer = 120
                # While stuck: zero velocity and prevent jumping
                self.vel_x = 0
                self.vel_y = 0
                self.on_ground = True
                self.animation_state = "idle"
                self.sprite_animator.set_animation("idle", self.facing_right)
                self.stuck_timer -= 1
                # Slight visual sink into glob
                self.rect.bottom = hit.rect.top + 6
                # No damage result; allow game to continue
                self.draw_character()
                return None
            elif getattr(hit, 'obstacle_type', '') in ('jungle_plant', 'rock'):
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
            # Draw a cheese wheel checkpoint
            cx, cy = w//2, h//2 + 10
            radius = min(w, h)//2 - 10
            body = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.circle(body, CHEESE_YELLOW, (cx, cy), radius)
            pygame.draw.circle(body, BURNT_ORANGE, (cx, cy), radius, 4)
            # Wedge cut
            pygame.draw.polygon(body, (0,0,0,0), [(cx, cy), (cx+radius, cy-10), (cx+radius, cy+10)])
            # Cheese holes
            for _ in range(8):
                import random
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
            # Draw a stone/metal archway as checkpoint
            arch = pygame.Surface((w, h), pygame.SRCALPHA)
            base_rect = pygame.Rect(10, h-40, w-20, 30)
            pygame.draw.rect(arch, DARK_GREY, base_rect)
            pygame.draw.rect(arch, BLACK, base_rect, 2)
            # Arch top
            pygame.draw.arc(arch, STEEL_GREY, (10, 10, w-20, h-20), 3.14, 0, 8)
            pygame.draw.arc(arch, BLACK, (10, 10, w-20, h-20), 3.14, 0, 2)
            # Molten glow accents
            pygame.draw.arc(arch, MOLTEN_ORANGE, (14, 14, w-28, h-28), 3.14, 0, 3)
            self.image.blit(arch, (0, 0))
            if self.activated:
                # Small torch flames on sides when activated
                pygame.draw.polygon(self.image, (255,120,0), [(16, h-50), (20, h-70), (24, h-50)])
                pygame.draw.polygon(self.image, (255,200,60), [(18, h-50), (20, h-62), (22, h-50)])
                pygame.draw.polygon(self.image, (255,120,0), [(w-24, h-50), (w-20, h-70), (w-16, h-50)])
                pygame.draw.polygon(self.image, (255,200,60), [(w-22, h-50), (w-20, h-62), (w-18, h-50)])
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
        self.move_offset = 0
        self.theme = theme or {}
        self.draw_platform(width, height)

    def draw_platform(self, width, height):
        # Use theme-based styling
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
        else:
            # Default platform styling
            self.draw_default_platform(width, height)
    
    def draw_cheese_platform(self, width, height):
        # Melted cheese theme
        self.image.fill(CHEESE_YELLOW)
        pygame.draw.rect(self.image, BURNT_ORANGE, (0, 0, width, height), 2)
        # Cheese holes
        for i in range(width // 20):
            hole_x = random.randint(5, width - 10)
            hole_y = random.randint(5, height - 10)
            pygame.draw.circle(self.image, SOOT_GREY, (hole_x, hole_y), 3)
        # Melted edges
        for x in range(0, width, 15):
            pygame.draw.arc(self.image, BURNT_ORANGE, (x, height-8, 15, 12), 0, 3.14, 2)
    
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
            # Draw a sticky glob of cheese
            pygame.draw.ellipse(self.image, CHEESE_YELLOW, (0, 4, 36, 16))
            pygame.draw.ellipse(self.image, BURNT_ORANGE, (0, 4, 36, 16), 2)
            # Holes
            for _ in range(3):
                r = random.randint(2, 4)
                x = random.randint(6, 30)
                y = random.randint(8, 16)
                pygame.draw.circle(self.image, SOOT_GREY, (x, y), r)
        elif self.obstacle_type == "lava_pit":
            # Draw a lava pit (wide, low rectangle with animated-looking waves)
            pygame.draw.rect(self.image, (90, 20, 10), (0, 0, self.image.get_width(), self.image.get_height()))
            for i in range(0, self.image.get_width(), 8):
                pygame.draw.arc(self.image, (255, 100, 0), (i, 2, 12, 12), 0, 3.14, 2)
                pygame.draw.arc(self.image, (255, 180, 60), (i+2, 6, 12, 12), 0, 3.14, 2)


