#!/usr/bin/env python3
"""
Sprite animation system for the platformer game.
Handles loading, organizing, and animating sprite sheets.
"""
import pygame
import os
import glob

class SpriteAnimator:
    """Manages sprite animations for the player character."""
    
    def __init__(self):
        self.sprites = {}
        self.animations = {}
        self.current_animation = "idle"
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 8  # frames per second
        self.facing_right = True
        
        # Animation control - only animate during actions
        self.should_animate = False
        self.action_animations = {"walking", "jumping", "falling", "stomping", "dying"}
        self.static_animations = {"idle"}
        
        # Initialize pygame if not already done
        if not pygame.get_init():
            pygame.init()
        
        # Set up a dummy display for loading images
        if not pygame.display.get_surface():
            pygame.display.set_mode((1, 1))
        
        # Load all sprite sheets
        self.load_sprite_sheets()
        self.organize_animations()
    
    def load_sprite_sheets(self):
        """Load sprites from the cropped sprite directories."""
        # Try different grid sizes to find the best organization
        sprite_dirs = [
            "sprites_sheet_1",      # 4x4 grid
            "sprites_sheet_1_6x4",  # 6x4 grid  
            "sprites_sheet_1_8x4",  # 8x4 grid
        ]
        
        for dir_name in sprite_dirs:
            if os.path.exists(dir_name):
                print(f"Loading sprites from {dir_name}")
                sprites = self.load_sprites_from_dir(dir_name)
                if sprites:
                    self.sprites[dir_name] = sprites
                    print(f"  Loaded {len(sprites)} sprites")
    
    def load_sprites_from_dir(self, dir_path):
        """Load all sprites from a directory."""
        sprites = []
        sprite_files = sorted(glob.glob(os.path.join(dir_path, "*.png")))
        
        for sprite_file in sprite_files:
            try:
                sprite = pygame.image.load(sprite_file)
                # Convert to ensure proper alpha handling
                sprite = sprite.convert_alpha()
                sprites.append(sprite)
            except Exception as e:
                print(f"Error loading {sprite_file}: {e}")
        
        return sprites
    
    def organize_animations(self):
        """Organize sprites into animation sequences."""
        # Use the 4x3 grid (12 sprites total)
        if "sprites_sheet_1" in self.sprites:
            sprites = self.sprites["sprites_sheet_1"]
            
            # Organize into animation sequences for 4x3 grid:
            # Row 0: Idle animation (4 frames)
            # Row 1: Walking animation (4 frames) 
            # Row 2: Jumping/Falling animation (4 frames)
            
            self.animations = {
                "idle": [sprites[0]],            # Row 0, first frame only (static)
                "walking": sprites[4:8],         # Row 1 (sprites 4-7)
                "jumping": sprites[8:12],        # Row 2 (sprites 8-11)
                "falling": sprites[8:12],        # Same as jumping
                "stomping": sprites[8:12],       # Same as jumping for now
                "dying": sprites[8:12],          # Same as jumping for now
            }
            
            print("Organized animations:")
            for anim_name, frames in self.animations.items():
                print(f"  {anim_name}: {len(frames)} frames")
    
    def set_animation(self, animation_name, facing_right=True):
        """Set the current animation."""
        if animation_name in self.animations:
            if self.current_animation != animation_name:
                self.current_animation = animation_name
                self.current_frame = 0
                self.animation_timer = 0
                
                # Only animate for action animations, not static ones
                self.should_animate = animation_name in self.action_animations
                
            self.facing_right = facing_right
    
    def update(self):
        """Update the animation frame."""
        if self.current_animation in self.animations and self.should_animate:
            frames = self.animations[self.current_animation]
            if len(frames) > 1:
                self.animation_timer += 1
                if self.animation_timer >= 60 // self.animation_speed:
                    self.animation_timer = 0
                    self.current_frame = (self.current_frame + 1) % len(frames)
    
    def get_current_sprite(self):
        """Get the current sprite frame."""
        if self.current_animation in self.animations:
            frames = self.animations[self.current_animation]
            if frames:
                sprite = frames[self.current_frame]
                
                # Scale sprite to maintain character size (32x48)
                sprite = pygame.transform.scale(sprite, (32, 48))
                
                # Flip sprite if facing left
                if not self.facing_right:
                    sprite = pygame.transform.flip(sprite, True, False)
                
                return sprite
        
        # Fallback to a default sprite
        return self.create_fallback_sprite()
    
    def create_fallback_sprite(self):
        """Create a simple fallback sprite if no sprites are loaded."""
        sprite = pygame.Surface((32, 48), pygame.SRCALPHA)
        pygame.draw.ellipse(sprite, (128, 128, 128), (4, 18, 24, 26))
        pygame.draw.ellipse(sprite, (64, 64, 64), (6, 4, 22, 18))
        return sprite
    
    def get_sprite_size(self):
        """Get the size of the current sprite."""
        sprite = self.get_current_sprite()
        return sprite.get_size()

def test_sprite_animator():
    """Test the sprite animator system."""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    
    animator = SpriteAnimator()
    
    running = True
    current_anim = "idle"
    facing_right = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    current_anim = "idle"
                elif event.key == pygame.K_2:
                    current_anim = "walking"
                elif event.key == pygame.K_3:
                    current_anim = "jumping"
                elif event.key == pygame.K_4:
                    current_anim = "falling"
                elif event.key == pygame.K_5:
                    current_anim = "stomping"
                elif event.key == pygame.K_6:
                    current_anim = "dying"
                elif event.key == pygame.K_f:
                    facing_right = not facing_right
        
        # Update animator
        animator.set_animation(current_anim, facing_right)
        animator.update()
        
        # Draw
        screen.fill((50, 50, 50))
        
        # Draw current sprite
        sprite = animator.get_current_sprite()
        sprite_rect = sprite.get_rect(center=(400, 300))
        screen.blit(sprite, sprite_rect)
        
        # Draw info
        font = pygame.font.Font(None, 36)
        info_text = f"Animation: {current_anim} | Frame: {animator.current_frame} | Facing: {'Right' if facing_right else 'Left'}"
        text_surface = font.render(info_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))
        
        # Draw controls
        controls = [
            "Controls:",
            "1-6: Change animation",
            "F: Flip direction",
            "ESC: Quit"
        ]
        
        for i, control in enumerate(controls):
            text = font.render(control, True, (200, 200, 200))
            screen.blit(text, (10, 50 + i * 30))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    test_sprite_animator()

