#!/usr/bin/env python3
"""
INFO_USER_GUI Node - Beautiful GUI version

This node displays a cute pygame GUI window to collect player information
that matches the game's cheese/rat theme.
"""

import rospy
import pygame
import sys
import os
import math
from ros_nodes.msg import user_msg

# Add game src directory to path to use UI and constants
game_dir = os.path.expanduser("~/RP_Moreno_Turkel_25")
src_dir = os.path.join(game_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, SOFT_YELLOW, MINT_GREEN, PEACH, 
    CORAL, LIGHT_PURPLE, CREAM, CHEESE_YELLOW, MELTED_CHEESE, BEIGE
)
from ui import UI
from background import Background


class InfoUserGUI:
    """Node that collects user information through a beautiful GUI."""
    
    def __init__(self):
        """Initialize the InfoUserGUI."""
        rospy.init_node('info_user', anonymous=True)
        self.publisher = rospy.Publisher('user_information', user_msg, queue_size=10)
        
        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Rat Race - Player Information")
        self.clock = pygame.time.Clock()
        self.display_active = True  # Track if display is still active
        
        # UI components
        self.ui = UI(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.bg = Background(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Input fields
        self.name_text = ""
        self.username_text = ""
        self.age_text = ""
        self.active_field = "name"  # name, username, age
        
        # Cursor blink
        self.cursor_visible = True
        self.cursor_timer = 0
        
        # Animation
        self.animation_timer = 0
        self.cheese_rotation = 0
        
        # Cheese background image
        self.cheese_image = None
        self._load_cheese_image()
        
        # Status
        self.info_collected = False
        self.error_message = None
        
        rospy.loginfo("INFO_USER_GUI node initialized")
    
    def _load_cheese_image(self):
        """Load cheese.jpeg background image."""
        try:
            cheese_path = os.path.join(game_dir, "game images", "cheese.jpeg")
            if os.path.exists(cheese_path):
                self.cheese_image = pygame.image.load(cheese_path)
                self.cheese_image = pygame.transform.scale(self.cheese_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                rospy.loginfo("Loaded cheese.jpeg background")
            else:
                rospy.logwarn(f"Cheese image not found at: {cheese_path}")
        except Exception as e:
            rospy.logwarn(f"Could not load cheese image: {e}")
            self.cheese_image = None
    
    def draw_cute_rat(self, x, y, size=80, facing_right=True):
        """Draw a cute rat character."""
        # Body (ellipse)
        body_rect = pygame.Rect(x - size//2, y - size//3, size, size * 2//3)
        pygame.draw.ellipse(self.screen, SOFT_YELLOW, body_rect)
        pygame.draw.ellipse(self.screen, BEIGE, body_rect, 3)
        
        # Head
        head_radius = size // 3
        head_x = x + (size//4 if facing_right else -size//4)
        pygame.draw.circle(self.screen, SOFT_YELLOW, (head_x, y - size//2), head_radius)
        pygame.draw.circle(self.screen, BEIGE, (head_x, y - size//2), head_radius, 3)
        
        # Ears
        ear_size = head_radius // 2
        ear1_x = head_x - head_radius//2
        ear1_y = y - size//2 - head_radius//2
        ear2_x = head_x + head_radius//2
        ear2_y = y - size//2 - head_radius//2
        
        pygame.draw.circle(self.screen, PEACH, (ear1_x, ear1_y), ear_size)
        pygame.draw.circle(self.screen, BEIGE, (ear1_x, ear1_y), ear_size, 2)
        pygame.draw.circle(self.screen, PEACH, (ear2_x, ear2_y), ear_size)
        pygame.draw.circle(self.screen, BEIGE, (ear2_x, ear2_y), ear_size, 2)
        
        # Eyes
        eye_size = 4
        eye_offset = head_radius // 3
        eye1_x = head_x - eye_offset
        eye2_x = head_x + eye_offset
        eye_y = y - size//2
        
        pygame.draw.circle(self.screen, BLACK, (eye1_x, eye_y), eye_size)
        pygame.draw.circle(self.screen, BLACK, (eye2_x, eye_y), eye_size)
        
        # Nose
        nose_x = head_x
        nose_y = y - size//2 + head_radius//3
        pygame.draw.circle(self.screen, PEACH, (nose_x, nose_y), 3)
        
        # Tail (curved)
        tail_start_x = x - size//2
        tail_start_y = y
        tail_end_x = tail_start_x - size//2
        tail_end_y = tail_start_y + size//3
        
        # Draw tail as a curved line
        points = []
        for i in range(10):
            t = i / 9
            px = tail_start_x + (tail_end_x - tail_start_x) * t
            py = tail_start_y + (tail_end_y - tail_start_y) * t + math.sin(t * math.pi) * 10
            points.append((int(px), int(py)))
        
        if len(points) > 1:
            pygame.draw.lines(self.screen, BEIGE, False, points, 4)
    
    def draw_cheese_icon(self, x, y, size=60, rotation=0):
        """Draw a cute cheese icon."""
        # Main cheese circle
        pygame.draw.circle(self.screen, CHEESE_YELLOW, (x, y), size)
        pygame.draw.circle(self.screen, MELTED_CHEESE, (x, y), size, 4)
        
        # Cheese holes
        import random
        rng = random.Random(int(x + y))
        for _ in range(5):
            hole_x = x + rng.randint(-size//2, size//2)
            hole_y = y + rng.randint(-size//2, size//2)
            hole_r = rng.randint(4, 8)
            pygame.draw.circle(self.screen, BEIGE, (hole_x, hole_y), hole_r)
    
    def draw_input_screen(self):
        """Draw the beautiful input screen."""
        # Check if display is still active
        if not self.display_active or self.screen is None:
            return
        
        try:
            # Draw cheese.jpeg background image
            if self.cheese_image is not None:
                self.screen.blit(self.cheese_image, (0, 0))
            else:
                # Fallback to cheese themed background
                cheese_theme = {
                    "sky_top": (248, 240, 202),
                    "sky_bottom": (230, 210, 175),
                    "bg_motif": "cheese"
                }
                self.bg.set_theme(cheese_theme)
                self.bg.draw(self.screen, 0, is_bonus_room=False)
        except pygame.error:
            # Display was closed, mark as inactive
            self.display_active = False
            return
        
        # Light semi-transparent overlay for text readability
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(60)  # Slightly darker for better text readability with image background
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Update animation
        self.animation_timer += 1
        self.cheese_rotation = (self.cheese_rotation + 1) % 360
        
        # Cute decorative elements
        # Left side rat
        rat_y = 150 + math.sin(self.animation_timer * 0.05) * 10
        self.draw_cute_rat(120, int(rat_y), size=70, facing_right=True)
        
        # Right side rat
        rat_y2 = 200 + math.cos(self.animation_timer * 0.07) * 10
        self.draw_cute_rat(SCREEN_WIDTH - 120, int(rat_y2), size=70, facing_right=False)
        
        # Floating cheese icons
        cheese_y1 = 100 + math.sin(self.animation_timer * 0.03) * 15
        cheese_y2 = SCREEN_HEIGHT - 100 + math.cos(self.animation_timer * 0.04) * 15
        self.draw_cheese_icon(SCREEN_WIDTH - 80, int(cheese_y1), size=40)
        self.draw_cheese_icon(80, int(cheese_y2), size=35)
        
        # Title with cute styling
        self.ui.draw_cheese_title(self.screen, "Welcome to Rat Race!", SCREEN_WIDTH//2, 60, center=True, size=72)
        self.ui.draw_bubble_text(self.screen, "🐭 Tell us about yourself! 🧀", SCREEN_WIDTH//2, 120, center=True, size=32)
        
        # Input fields with cute labels
        field_y_start = 220
        field_spacing = 75
        
        # Name field
        self.draw_input_field("👤 Name:", self.name_text, SCREEN_WIDTH//2, field_y_start, self.active_field == "name")
        
        # Username field
        self.draw_input_field("🎮 Username:", self.username_text, SCREEN_WIDTH//2, field_y_start + field_spacing, self.active_field == "username")
        
        # Age field
        self.draw_input_field("🎂 Age:", self.age_text, SCREEN_WIDTH//2, field_y_start + field_spacing * 2, self.active_field == "age")
        
        # Error message
        if self.error_message:
            self.ui.draw_bubble_text(self.screen, self.error_message, SCREEN_WIDTH//2, field_y_start + field_spacing * 3 + 20, center=True, size=24)
        
        # Instructions with cute icons
        instructions_y = field_y_start + field_spacing * 3 + 60
        self.ui.draw_bubble_text(self.screen, "💡 Use TAB to switch fields • Click to focus", SCREEN_WIDTH//2, instructions_y, center=True, size=22)
        self.ui.draw_bubble_text(self.screen, "✨ Press ENTER or click Submit when ready!", SCREEN_WIDTH//2, instructions_y + 30, center=True, size=22)
        
        # Submit button with hover effect
        button_y = instructions_y + 80
        button_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, button_y - 25, 400, 50)
        mouse_pos = pygame.mouse.get_pos()
        hover = button_rect.collidepoint(mouse_pos)
        
        # Animated button
        button_scale = 1.05 if hover else 1.0
        button_width = int(400 * button_scale)
        button_height = int(50 * button_scale)
        
        self.ui.draw_cheese_button(
            self.screen, 
            "🚀 Start Playing!", 
            SCREEN_WIDTH//2, 
            button_y, 
            width=button_width, 
            height=button_height
        )
        
        # Cute footer
        footer_y = SCREEN_HEIGHT - 40
        self.ui.draw_bubble_text(self.screen, "🧀 Get ready for a cheesy adventure! 🐭", SCREEN_WIDTH//2, footer_y, center=True, size=20)
        
        pygame.display.flip()
    
    def draw_input_field(self, label, text, x, y, active):
        """Draw an input field with cute label."""
        field_width = 520
        field_height = 55
        
        # Field background with cute rounded corners
        field_rect = pygame.Rect(x - field_width//2, y - field_height//2, field_width, field_height)
        
        # Color based on active state with cute glow effect
        if active:
            bg_color = SOFT_YELLOW
            border_color = (183, 140, 30)
            border_width = 4
            # Glow effect
            glow_rect = pygame.Rect(x - field_width//2 - 2, y - field_height//2 - 2, field_width + 4, field_height + 4)
            glow_surface = pygame.Surface((field_width + 4, field_height + 4), pygame.SRCALPHA)
            glow_surface.fill((255, 255, 200, 30))
            self.screen.blit(glow_surface, glow_rect)
        else:
            bg_color = CREAM
            border_color = (200, 180, 150)
            border_width = 2
        
        pygame.draw.rect(self.screen, bg_color, field_rect, border_radius=12)
        pygame.draw.rect(self.screen, border_color, field_rect, border_width, border_radius=12)
        
        # Cute label with icon
        label_x = x - field_width//2 - 15
        self.ui.draw_bubble_text(self.screen, label, label_x, y, center=False, size=26)
        
        # Text with blinking cursor - start from right to avoid overlap with label
        text_x = x + field_width//2 - 25  # Start from right side
        display_text = text
        if active and self.cursor_visible:
            display_text = display_text + "|"  # Cursor on right when text is right-aligned
        
        # Render text with cute font
        font = pygame.font.Font(None, 30)
        text_surface = font.render(display_text, True, BLACK)
        text_rect = text_surface.get_rect()
        text_rect.midright = (text_x, y)  # Right-aligned
        
        # Clip text if too long with cute ellipsis (from left, keep rightmost characters)
        if text_rect.width > field_width - 50:
            max_width = field_width - 70
            original_text = text
            cursor_str = "|" if (active and self.cursor_visible) else ""
            # Keep removing characters from the left until it fits
            while text_surface.get_width() > max_width and len(original_text) > 0:
                original_text = original_text[1:]  # Remove leftmost character
                display_text = original_text + cursor_str
                text_surface = font.render(display_text, True, BLACK)
            text_rect.midright = (text_x, y)
        
        self.screen.blit(text_surface, text_rect)
    
    def handle_input(self, event):
        """Handle keyboard input for text fields."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                # Cycle through fields
                fields = ["name", "username", "age"]
                current_idx = fields.index(self.active_field)
                self.active_field = fields[(current_idx + 1) % len(fields)]
                self.cursor_visible = True
                self.cursor_timer = 0
                self.error_message = None
            elif event.key == pygame.K_RETURN:
                # Submit
                if self.validate_and_submit():
                    return True
            elif event.key == pygame.K_BACKSPACE:
                # Delete character
                if self.active_field == "name":
                    self.name_text = self.name_text[:-1]
                elif self.active_field == "username":
                    self.username_text = self.username_text[:-1]
                elif self.active_field == "age":
                    self.age_text = self.age_text[:-1]
                self.error_message = None
            else:
                # Add character (only printable)
                char = event.unicode
                if char.isprintable():
                    if self.active_field == "name":
                        if len(self.name_text) < 30:
                            self.name_text += char
                    elif self.active_field == "username":
                        if len(self.username_text) < 30:
                            self.username_text += char
                    elif self.active_field == "age":
                        # Only allow digits
                        if char.isdigit() and len(self.age_text) < 3:
                            self.age_text += char
                    self.error_message = None
        return False
    
    def validate_and_submit(self):
        """Validate input and submit if valid."""
        if not self.name_text.strip():
            self.error_message = "⚠️ Please enter your name!"
            return False
        if not self.username_text.strip():
            self.error_message = "⚠️ Please enter your username!"
            return False
        try:
            age = int(self.age_text)
            if age < 0:
                self.error_message = "⚠️ Age must be positive!"
                return False
            if age > 150:
                self.error_message = "⚠️ That's quite an age! Try a smaller number."
                return False
        except ValueError:
            self.error_message = "⚠️ Please enter a valid age!"
            return False
        
        # All valid - submit
        self.publish_user_info(self.name_text.strip(), self.username_text.strip(), age)
        return True
    
    def publish_user_info(self, name, username, age):
        """Publish user information to the user_information topic."""
        msg = user_msg()
        msg.name = name
        msg.username = username
        msg.age = age
        
        # Wait for subscribers to be ready
        rospy.sleep(0.5)
        
        self.publisher.publish(msg)
        rospy.loginfo(f"Published user information: Name={name}, Username={username}, Age={age}")
        rospy.loginfo("Waiting for game_node to process user info and set user_name parameter...")
        
        # Show success message (this runs for 2 seconds and then returns)
        self.show_success_message(name, username, age)
        
        # Wait a moment for game_node to process the message and set user_name parameter
        rospy.loginfo("INFO_USER_GUI: Waiting for game_node to process user information...")
        wait_count = 0
        while not rospy.has_param('user_name') and wait_count < 20 and not rospy.is_shutdown():
            rospy.sleep(0.1)
            wait_count += 1
        
        if rospy.has_param('user_name'):
            rospy.loginfo(f"INFO_USER_GUI: ✓ user_name parameter set: {rospy.get_param('user_name')}")
        else:
            rospy.logwarn("INFO_USER_GUI: user_name parameter not set yet, but proceeding anyway...")
        
        # Mark as collected - this will cause the main loop to exit
        self.info_collected = True
        
        # Close the window after success message is shown
        rospy.loginfo("INFO_USER_GUI: Closing window and transitioning to difficulty selection...")
        self.display_active = False
    
    def show_success_message(self, name, username, age):
        """Show a loading/transition screen before closing."""
        success_timer = 0
        max_frames = 120  # 2 seconds at 60 FPS - longer loading screen
        
        while success_timer < max_frames:
            success_timer += 1
            
            # Draw background
            cheese_theme = {
                "sky_top": (248, 240, 202),
                "sky_bottom": (230, 210, 175),
                "bg_motif": "cheese"
            }
            self.bg.set_theme(cheese_theme)
            self.bg.draw(self.screen, 0, is_bonus_room=False)
            
            # Success overlay with fade in
            overlay_alpha = min(180, int(180 * (success_timer / 30)))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(overlay_alpha)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            # Animated success elements
            bounce = math.sin(success_timer * 0.2) * 5
            
            # Success title
            self.ui.draw_cheese_title(
                self.screen, 
                "✓ Information Saved!", 
                SCREEN_WIDTH//2, 
                SCREEN_HEIGHT//2 - 100 + int(bounce), 
                center=True, 
                size=64
            )
            
            # Welcome message
            self.ui.draw_bubble_text(
                self.screen, 
                f"Welcome, {name}! 🐭", 
                SCREEN_WIDTH//2, 
                SCREEN_HEIGHT//2 - 30, 
                center=True, 
                size=36
            )
            
            # Info display
            self.ui.draw_bubble_text(
                self.screen, 
                f"Username: {username} • Age: {age}", 
                SCREEN_WIDTH//2, 
                SCREEN_HEIGHT//2 + 20, 
                center=True, 
                size=28
            )
            
            # Loading message
            loading_dots = "." * ((success_timer // 10) % 4)
            self.ui.draw_bubble_text(
                self.screen, 
                f"Loading{loading_dots}", 
                SCREEN_WIDTH//2, 
                SCREEN_HEIGHT//2 + 70, 
                center=True, 
                size=32
            )
            
            # Cute animated rats
            rat1_x = 150 + math.sin(success_timer * 0.1) * 20
            rat2_x = SCREEN_WIDTH - 150 + math.cos(success_timer * 0.1) * 20
            self.draw_cute_rat(int(rat1_x), SCREEN_HEIGHT - 100, size=60, facing_right=True)
            self.draw_cute_rat(int(rat2_x), SCREEN_HEIGHT - 100, size=60, facing_right=False)
            
            # Floating cheese
            cheese_y = 100 + math.sin(success_timer * 0.15) * 15
            self.draw_cheese_icon(SCREEN_WIDTH//2, int(cheese_y), size=50)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        # Don't quit pygame.display - just mark as inactive
        # The main game will create its own display
        self.display_active = False
        self.screen = None
    
    def run(self):
        """Main execution loop."""
        rospy.loginfo("INFO_USER_GUI node started")
        
        running = True
        while running and not rospy.is_shutdown() and not self.info_collected:
            # Update cursor blink
            self.cursor_timer += 1
            if self.cursor_timer >= 30:  # Blink every 30 frames (0.5 seconds at 60 FPS)
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Click to focus fields
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    field_y_start = 220
                    field_spacing = 75
                    
                    # Check field clicks
                    if 192 < mouse_y < 247:  # Name field
                        self.active_field = "name"
                        self.cursor_visible = True
                        self.cursor_timer = 0
                    elif 267 < mouse_y < 322:  # Username field
                        self.active_field = "username"
                        self.cursor_visible = True
                        self.cursor_timer = 0
                    elif 342 < mouse_y < 397:  # Age field
                        self.active_field = "age"
                        self.cursor_visible = True
                        self.cursor_timer = 0
                    elif 450 < mouse_y < 500:  # Submit button area
                        if self.validate_and_submit():
                            running = False
                    
                    self.error_message = None
                else:
                    if self.handle_input(event):
                        running = False
            
            # Draw screen (only if display is still active)
            if self.display_active:
                try:
                    self.draw_input_screen()
                    self.clock.tick(60)
                except pygame.error:
                    # Display was closed
                    self.display_active = False
                    break
        
        # Don't quit pygame.display - just let the process end naturally
        # The main game will create its own display
        # Setting screen to None is enough
        self.screen = None
        self.display_active = False
        
        rospy.loginfo("User information published successfully. INFO_USER_GUI node shutting down.")


if __name__ == '__main__':
    try:
        node = InfoUserGUI()
        node.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("INFO_USER_GUI node interrupted")
    except Exception as e:
        rospy.logerr(f"Error in INFO_USER_GUI: {e}")
        import traceback
        traceback.print_exc()
        # Don't quit pygame.display - just mark as inactive
        try:
            if hasattr(node, 'screen'):
                node.screen = None
                node.display_active = False
        except:
            pass

