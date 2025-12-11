#!/usr/bin/env python3
"""
DIFFICULTY_SELECT_GUI Node - Difficulty Selection GUI

This node displays a difficulty selection screen that looks like the level select screen,
allowing users to choose Easy (1-3), Medium (4-6), or Hard (7-10) difficulty.
"""

import rospy
import sys
import os

# Import ROS service (this is safe, no pygame)
try:
    from ros_nodes.srv import SetGameDifficulty
except ImportError:
    # Can't use rospy.logerr here because rospy might not be initialized yet
    print("ERROR: Could not import SetGameDifficulty service. Make sure catkin workspace is built and sourced.")
    sys.exit(1)

# DON'T import pygame or game modules here - they will be imported later after user info is received
# This prevents any pygame initialization from happening before we're ready
pygame = None
SCREEN_WIDTH = None
SCREEN_HEIGHT = None
BLACK = None
SOFT_YELLOW = None
MINT_GREEN = None
PEACH = None
CORAL = None
LIGHT_PURPLE = None
CREAM = None
CHEESE_YELLOW = None
MELTED_CHEESE = None
BEIGE = None
UI = None
Background = None
Player = None


class DifficultySelectGUI:
    """Node that displays difficulty selection GUI."""
    
    def __init__(self):
        """Initialize the DifficultySelectGUI."""
        rospy.init_node('difficulty_select_gui', anonymous=True)
        
        # DON'T initialize pygame here - wait until user_name is set
        # This prevents the GUI from showing before user input is complete
        self.screen = None
        self.clock = None
        self.ui = None
        self.bg = None
        self.pygame_initialized = False
        
        # Difficulty options (colors will be set after pygame initialization)
        # Using color tuples directly to avoid importing constants early
        self.difficulties = [
            {"name": "Easy", "levels": "1-3", "level_number": 1, "color": (170, 255, 195)},  # MINT_GREEN
            {"name": "Medium", "levels": "4-6", "level_number": 4, "color": (255, 250, 180)},  # SOFT_YELLOW
            {"name": "Hard", "levels": "7-10", "level_number": 7, "color": (255, 127, 102)}  # CORAL
        ]
        self.selected_difficulty = 0
        
        # Cheese background image - will load after pygame init
        self.cheese_image = None
        
        # Service client - will initialize after pygame
        self.difficulty_service = None
        
        # Status
        self.difficulty_set = False
        # Color is already selected by default (Purple), but user can change it
        self.color_selected = True  # Default color is already set
        self.status_message = None
        self.status_timer = 0
        
        # Player color (1: Red, 2: Purple, 3: Blue)
        self.player_color = 2  # Default Purple
        if rospy.has_param('change_player_color'):
            self.player_color = int(rospy.get_param('change_player_color', 2))
        else:
            # Set default color parameter
            rospy.set_param('change_player_color', self.player_color)
        
        # Player preview
        self.preview_player = None
        
        # Display state
        self.display_active = True
        
        rospy.loginfo("DIFFICULTY_SELECT_GUI node initialized")
        rospy.loginfo("DIFFICULTY_SELECT_GUI: Pygame will NOT initialize until user information is received")
        rospy.loginfo("DIFFICULTY_SELECT_GUI: This ensures the difficulty window appears AFTER username/age input")
    
    def _load_cheese_image(self):
        """Load cheese.jpeg background image."""
        global SCREEN_WIDTH, SCREEN_HEIGHT
        
        if not self.pygame_initialized or pygame is None:
            rospy.logwarn("Cannot load cheese image: pygame not initialized yet")
            return  # Can't load images until pygame is initialized
        
        # Try multiple possible paths
        game_dir = os.path.expanduser("~/RP_Moreno_Turkel_25")
        possible_paths = [
            os.path.expanduser("~/RP_Moreno_Turkel_25/game images/cheese.jpeg"),
            os.path.join(game_dir, "game images", "cheese.jpeg"),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "game images", "cheese.jpeg"),
            "/home/magicgamabob/RP_Moreno_Turkel_25/game images/cheese.jpeg",
        ]
        
        for cheese_path in possible_paths:
            try:
                rospy.loginfo(f"Trying to load cheese.jpeg from: {cheese_path}")
                if os.path.exists(cheese_path):
                    rospy.loginfo(f"✓ Path exists: {cheese_path}")
                    # Load the image
                    self.cheese_image = pygame.image.load(cheese_path)
                    # Convert to ensure proper format
                    self.cheese_image = self.cheese_image.convert()
                    # Scale to screen size
                    if SCREEN_WIDTH and SCREEN_HEIGHT:
                        self.cheese_image = pygame.transform.scale(self.cheese_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                    rospy.loginfo(f"✓✓✓ Successfully loaded cheese.jpeg background ({self.cheese_image.get_width()}x{self.cheese_image.get_height()})")
                    return  # Success, exit function
                else:
                    rospy.logwarn(f"✗ Path does not exist: {cheese_path}")
            except Exception as e:
                rospy.logerr(f"✗ Error loading from {cheese_path}: {e}")
                import traceback
                traceback.print_exc()
                continue  # Try next path
        
        # If we get here, all paths failed
        rospy.logerr("✗✗✗ Failed to load cheese.jpeg from all attempted paths")
        self.cheese_image = None
    
    def draw(self):
        """Draw the difficulty selection screen."""
        # Check if display is still active and pygame is initialized
        if not self.display_active or self.screen is None or not self.pygame_initialized or pygame is None:
            return
        
        try:
            # Draw cheese.jpeg background image
            if self.cheese_image is not None:
                # Draw the background image first
                self.screen.blit(self.cheese_image, (0, 0))
                rospy.logdebug("Drew cheese.jpeg background image")
            else:
                # Try to reload the image if it's None (maybe it failed to load initially)
                rospy.logwarn("cheese_image is None, attempting to reload...")
                self._load_cheese_image()
                if self.cheese_image is not None:
                    self.screen.blit(self.cheese_image, (0, 0))
                    rospy.loginfo("✓ Successfully loaded cheese image on retry")
                else:
                    rospy.logwarn("Still None after retry, using fallback background")
                    # Fallback to cheese themed background
                    cheese_theme = {"sky_top": (248, 240, 202), "sky_bottom": (230, 210, 175), "bg_motif": "cheese"}
                    self.bg.set_theme(cheese_theme)
                    self.bg.draw(self.screen, 0, is_bonus_room=False)
        except pygame.error as e:
            # Display was closed, mark as inactive
            rospy.logerr(f"Pygame error in draw: {e}")
            self.display_active = False
            return
        except Exception as e:
            rospy.logerr(f"Error drawing background: {e}")
            import traceback
            traceback.print_exc()
            # Continue anyway with the fallback fill
            self.screen.fill((50, 50, 50))  # Dark gray fallback
        
        # Light semi-transparent overlay for text readability (reduced opacity to show background)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(40)  # Reduced from 70 to show more of the cheese background
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Get user name if available
        user_name = None
        try:
            if rospy.has_param('user_name'):
                user_name = rospy.get_param('user_name')
        except:
            pass
        
        # Title
        try:
            if user_name:
                self.ui.draw_cheese_title(self.screen, f"Hello, {user_name}!", SCREEN_WIDTH//2, 60, center=True, size=64)
                self.ui.draw_bubble_text(self.screen, "Select Difficulty:", SCREEN_WIDTH//2, 130, center=True, size=48)
            else:
                self.ui.draw_cheese_title(self.screen, "Select Difficulty", SCREEN_WIDTH//2, 90, center=True, size=84)
        except Exception as e:
            rospy.logwarn(f"Error drawing title: {e}")
            # Fallback: draw simple text
            font = pygame.font.Font(None, 72)
            title_text = f"Hello, {user_name}!" if user_name else "Select Difficulty"
            text_surface = font.render(title_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, 90))
            self.screen.blit(text_surface, text_rect)
        
        # Draw difficulty options
        top = 200 if user_name else 200
        for i, diff in enumerate(self.difficulties):
            name = f"{i+1}. {diff['name']} (Levels {diff['levels']})"
            y = top + i * 80
            
            try:
                # Highlight selected difficulty
                if i == self.selected_difficulty:
                    bar = pygame.Rect(SCREEN_WIDTH//2 - 220, y - 20, 440, 60)
                    pygame.draw.rect(self.screen, diff['color'], bar)
                    pygame.draw.rect(self.screen, BLACK, bar, 3)
                
                # Draw difficulty name
                self.ui.draw_bubble_text(self.screen, name, SCREEN_WIDTH//2, y, center=True, size=36)
                
                # Draw level range below
                level_text = f"Starts at Level {diff['level_number']}"
                self.ui.draw_bubble_text(self.screen, level_text, SCREEN_WIDTH//2, y + 30, center=True, size=24)
            except Exception as e:
                rospy.logwarn(f"Error drawing difficulty option {i}: {e}")
                # Fallback: draw simple text
                font = pygame.font.Font(None, 36)
                text_surface = font.render(name, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, y))
                self.screen.blit(text_surface, text_rect)
        
        # Player color selection
        try:
            color_names = {1: "Red", 2: "Purple", 3: "Blue"}
            current_color = color_names.get(self.player_color, "Purple")
            color_y = top + 260
            self.ui.draw_bubble_text(self.screen, f"Player Color: {current_color}", SCREEN_WIDTH//2, color_y, center=True, size=36)
            self.ui.draw_bubble_text(self.screen, "Press R (Red), P (Purple), or B (Blue) to change", SCREEN_WIDTH//2, color_y + 40, center=True, size=28)
            
            # Player preview
            preview_y = color_y + 100
            self.ui.draw_bubble_text(self.screen, "Preview:", SCREEN_WIDTH//2, preview_y, center=True, size=32)
            
            # Initialize preview player if it doesn't exist
            if self.preview_player is None:
                try:
                    self.preview_player = Player(0, 0, None, 1.0, 1.0, player_color=self.player_color)
                    self.preview_player.sprite_animator.set_animation("idle", True)
                except Exception as e:
                    rospy.logwarn(f"Could not create preview player: {e}")
                    self.preview_player = None
            # Ensure preview player color matches current selection
            elif self.preview_player.player_color != self.player_color:
                try:
                    self.preview_player = Player(0, 0, None, 1.0, 1.0, player_color=self.player_color)
                    self.preview_player.sprite_animator.set_animation("idle", True)
                except Exception as e:
                    rospy.logwarn(f"Could not update preview player color: {e}")
            
            # Draw player preview with decorative frame
            if self.preview_player:
                try:
                    # Update animation and apply color - call draw_character to apply color filter
                    self.preview_player.draw_character()
                    
                    # Draw decorative frame background
                    frame_width = 200
                    frame_height = 220
                    frame_x = SCREEN_WIDTH//2 - frame_width//2
                    frame_y = preview_y + 20
                    frame_rect = pygame.Rect(frame_x, frame_y, frame_width, frame_height)
                    frame_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    frame_surface.fill((255, 255, 255, 30))  # Semi-transparent white
                    pygame.draw.rect(frame_surface, CHEESE_YELLOW, (0, 0, frame_width, frame_height), 4, border_radius=10)
                    self.screen.blit(frame_surface, frame_rect)
                    
                    # Draw player preview - use self.image which has the color applied
                    preview_sprite = self.preview_player.image
                    # Scale up for better visibility
                    preview_sprite = pygame.transform.scale(preview_sprite, (preview_sprite.get_width() * 3, preview_sprite.get_height() * 3))
                    sprite_rect = preview_sprite.get_rect(center=(SCREEN_WIDTH//2, preview_y + 60))
                    self.screen.blit(preview_sprite, sprite_rect)
                except Exception as e:
                    rospy.logwarn(f"Error drawing player preview: {e}")
                    import traceback
                    traceback.print_exc()
        except Exception as e:
            rospy.logwarn(f"Error drawing color selection: {e}")
        
        # Status message
        if self.status_message:
            try:
                status_y = SCREEN_HEIGHT - 120
                color = MINT_GREEN if "success" in self.status_message.lower() else CORAL
                # draw_bubble_text doesn't support color parameter, it uses rainbow colors
                self.ui.draw_bubble_text(self.screen, self.status_message, SCREEN_WIDTH//2, status_y, center=True, size=28)
            except Exception as e:
                rospy.logwarn(f"Error drawing status message: {e}")
        
        # Instructions
        try:
            if not (self.difficulty_set and self.color_selected):
                self.ui.draw_bubble_text(self.screen, "Press 1, 2, or 3 to select difficulty", SCREEN_WIDTH//2, SCREEN_HEIGHT - 80, center=True, size=32)
            else:
                # draw_bubble_text doesn't support color parameter, it uses rainbow colors
                self.ui.draw_bubble_text(self.screen, "Starting game...", SCREEN_WIDTH//2, SCREEN_HEIGHT - 80, center=True, size=32)
        except Exception as e:
            rospy.logwarn(f"Error drawing instructions: {e}")
    
    def set_difficulty(self):
        """Call ROS service to set difficulty."""
        if self.difficulty_service is None:
            rospy.logerr("Difficulty service not initialized!")
            return
        
        selected = self.difficulties[self.selected_difficulty]
        difficulty_name = selected['name'].lower()  # "easy", "medium", "hard"
        
        try:
            # Call service - the generated code uses 'difficulty' field (not 'change_difficulty')
            rospy.loginfo(f"DIFFICULTY_SELECT_GUI: Calling difficulty service with: {difficulty_name}")
            try:
                # Try with 'difficulty' field name (matches generated code)
                response = self.difficulty_service(difficulty=difficulty_name)
            except (AttributeError, TypeError) as e:
                # Fallback to positional argument
                rospy.logwarn(f"Keyword argument failed, trying positional: {e}")
                response = self.difficulty_service(difficulty_name)
            
            if response.success:
                self.difficulty_set = True
                rospy.set_param('difficulty_selected', True)
                self.status_message = f"✓ Difficulty: {selected['name']}"
                rospy.loginfo(f"Difficulty set to {selected['name']}")
                self._check_ready_to_start()
            else:
                self.status_message = f"✗ Failed to set difficulty"
                rospy.logwarn(f"Failed to set difficulty: Service returned False (not in phase1 or invalid difficulty)")
        except (rospy.ServiceException, AttributeError, TypeError) as e:
            self.status_message = f"✗ Service call failed: {e}"
            rospy.logerr(f"Service call failed: {e}")
            import traceback
            rospy.logerr(f"Traceback: {traceback.format_exc()}")
        except Exception as e:
            self.status_message = f"✗ Unexpected error: {e}"
            rospy.logerr(f"Unexpected error in set_difficulty: {e}")
            import traceback
            rospy.logerr(f"Traceback: {traceback.format_exc()}")
        
        # Clear status message after 3 seconds
        self.status_timer = 180  # 3 seconds at 60 FPS
    
    def set_player_color(self, color):
        """Set player color parameter."""
        self.player_color = color
        rospy.set_param('change_player_color', color)
        self.color_selected = True
        color_names = {1: "Red", 2: "Purple", 3: "Blue"}
        rospy.loginfo(f"Player color set to {color_names[color]}")
        # Recreate preview player with new color to ensure color change is applied
        try:
            self.preview_player = Player(0, 0, None, 1.0, 1.0, player_color=color)
            self.preview_player.sprite_animator.set_animation("idle", True)
            rospy.loginfo(f"Preview player recreated with {color_names[color]} color")
        except Exception as e:
            rospy.logwarn(f"Could not recreate preview player with new color: {e}")
            self.preview_player = None
        self._check_ready_to_start()
    
    def _check_ready_to_start(self):
        """Check if both difficulty and color are selected, then signal ready."""
        rospy.loginfo(f"Checking readiness: difficulty_set={self.difficulty_set}, color_selected={self.color_selected}")
        if self.difficulty_set and self.color_selected:
            rospy.set_param('ready_to_start_game', True)
            rospy.loginfo("✓ Both difficulty and color selected. Game can start now!")
            # Show "Starting game..." message
            self.status_message = "Starting game..."
            # Update display to show the message
            if self.screen is not None:
                try:
                    self.draw()
                    pygame.display.flip()
                except:
                    pass
            # Wait a moment for user to see the message
            rospy.sleep(2.0)
            # Close this GUI window
            rospy.loginfo("DIFFICULTY_SELECT_GUI: Closing window, game will start now...")
            self.display_active = False
        else:
            rospy.loginfo(f"Still waiting: difficulty_set={self.difficulty_set}, color_selected={self.color_selected}")
    
    def _initialize_pygame(self):
        """Initialize pygame and UI components (called after user_name is set)."""
        global pygame, SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, SOFT_YELLOW, MINT_GREEN
        global PEACH, CORAL, LIGHT_PURPLE, CREAM, CHEESE_YELLOW, MELTED_CHEESE, BEIGE
        global UI, Background, Player
        
        if self.pygame_initialized:
            return
        
        rospy.loginfo("DIFFICULTY_SELECT_GUI: Initializing pygame and UI...")
        
        # NOW import pygame and game modules (only after user info is received)
        import pygame as pg
        pygame = pg
        
        # Add game src directory to path to use UI and constants
        game_dir = os.path.expanduser("~/RP_Moreno_Turkel_25")
        src_dir = os.path.join(game_dir, "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        
        # Import game modules
        from constants import (
            SCREEN_WIDTH as SW, SCREEN_HEIGHT as SH, BLACK as BLK, SOFT_YELLOW as SY, 
            MINT_GREEN as MG, PEACH as PCH, CORAL as CRL, LIGHT_PURPLE as LP, 
            CREAM as CRM, CHEESE_YELLOW as CY, MELTED_CHEESE as MC, BEIGE as BG
        )
        SCREEN_WIDTH = SW
        SCREEN_HEIGHT = SH
        BLACK = BLK
        SOFT_YELLOW = SY
        MINT_GREEN = MG
        PEACH = PCH
        CORAL = CRL
        LIGHT_PURPLE = LP
        CREAM = CRM
        CHEESE_YELLOW = CY
        MELTED_CHEESE = MC
        BEIGE = BG
        
        from ui import UI as UI_Class
        from background import Background as BackgroundClass
        from entities import Player as PlayerClass
        UI = UI_Class
        Background = BackgroundClass
        Player = PlayerClass
        
        # Update difficulty colors to use actual constants now that they're loaded
        self.difficulties[0]["color"] = MINT_GREEN
        self.difficulties[1]["color"] = SOFT_YELLOW
        self.difficulties[2]["color"] = CORAL
        
        # Initialize pygame
        if not pygame.get_init():
            pygame.init()
        
        # Create display (THIS IS WHEN THE WINDOW APPEARS - only happens after user info!)
        rospy.loginfo("DIFFICULTY_SELECT_GUI: Creating pygame window now...")
        rospy.loginfo(f"DIFFICULTY_SELECT_GUI: Screen dimensions: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        try:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("Rat Race - Difficulty Selection")
            self.clock = pygame.time.Clock()
            
            # Fill screen with initial color
            self.screen.fill((50, 50, 50))
            pygame.display.flip()
            rospy.loginfo("DIFFICULTY_SELECT_GUI: ✓✓✓ Pygame window created and displayed!")
        except Exception as e:
            rospy.logerr(f"DIFFICULTY_SELECT_GUI: ERROR creating pygame window: {e}")
            import traceback
            rospy.logerr(f"DIFFICULTY_SELECT_GUI: Traceback: {traceback.format_exc()}")
            self.screen = None
            self.display_active = False
            raise
        
        # UI components
        try:
            self.ui = UI(SCREEN_WIDTH, SCREEN_HEIGHT)
            self.bg = Background(SCREEN_WIDTH, SCREEN_HEIGHT)
        except Exception as e:
            rospy.logerr(f"Error initializing UI components: {e}")
            raise
        
        # Load cheese image for background
        self._load_cheese_image()
        
        # Initialize service client
        rospy.wait_for_service('difficulty')
        self.difficulty_service = rospy.ServiceProxy('difficulty', SetGameDifficulty)
        
        self.pygame_initialized = True
        rospy.loginfo("DIFFICULTY_SELECT_GUI: ✓ Pygame initialized successfully - window should now be visible")
        rospy.loginfo("DIFFICULTY_SELECT_GUI: ✓ This window appeared AFTER user information was entered")
    
    def run(self):
        """Main execution loop."""
        # Wait for user_name to be set BEFORE initializing pygame
        rospy.loginfo("DIFFICULTY_SELECT_GUI: ========== STARTING DIFFICULTY_SELECT_GUI ==========")
        rospy.loginfo("DIFFICULTY_SELECT_GUI: Waiting for user information (name, username, age)...")
        rospy.loginfo("DIFFICULTY_SELECT_GUI: This window will appear after you enter your information in the INFO_USER window")
        
        # Check all available parameters for debugging
        try:
            all_params = rospy.get_param_names()
            user_params = [p for p in all_params if 'user' in p.lower() or 'name' in p.lower()]
            if user_params:
                rospy.loginfo(f"DIFFICULTY_SELECT_GUI: Available ROS parameters with 'user' or 'name': {user_params}")
            else:
                rospy.loginfo("DIFFICULTY_SELECT_GUI: No parameters found with 'user' or 'name' in name")
        except Exception as e:
            rospy.logwarn(f"DIFFICULTY_SELECT_GUI: Could not list parameters: {e}")
        
        wait_count = 0
        max_wait = 60  # Wait up to 30 seconds (60 iterations × 0.5 seconds)
        while not rospy.has_param('user_name') and not rospy.is_shutdown() and wait_count < max_wait:
            rospy.sleep(0.5)
            wait_count += 1
            # Log status every 2 seconds (every 4 iterations)
            if wait_count % 4 == 0:
                rospy.loginfo(f"DIFFICULTY_SELECT_GUI: Still waiting for user information... (iteration {wait_count}/{max_wait})")
                # Try to check if parameter exists with different names
                for param_name in ['user_name', '/user_name', '~user_name', 'game_node/user_name']:
                    if rospy.has_param(param_name):
                        rospy.logwarn(f"DIFFICULTY_SELECT_GUI: Found parameter with different name: {param_name}")
                        try:
                            value = rospy.get_param(param_name)
                            rospy.logwarn(f"DIFFICULTY_SELECT_GUI: Value: {value}")
                            # Use this parameter instead
                            rospy.set_param('user_name', value)
                            rospy.loginfo(f"DIFFICULTY_SELECT_GUI: Copied {param_name} to user_name")
                            break
                        except Exception as e:
                            rospy.logwarn(f"DIFFICULTY_SELECT_GUI: Error copying parameter: {e}")
        
        if rospy.is_shutdown():
            rospy.loginfo("DIFFICULTY_SELECT_GUI: Node shutdown requested while waiting")
            return
        
        if not rospy.has_param('user_name'):
            rospy.logerr("DIFFICULTY_SELECT_GUI: ✗✗✗ user_name parameter was never set! Cannot proceed.")
            rospy.logerr("DIFFICULTY_SELECT_GUI: This means game_node did not receive or process the user information message.")
            rospy.logerr("DIFFICULTY_SELECT_GUI: Check that game_node is running and subscribed to 'user_information' topic.")
            rospy.logerr("DIFFICULTY_SELECT_GUI: Node will exit now.")
            return
        
        user_name = rospy.get_param('user_name', '')
        rospy.loginfo(f"DIFFICULTY_SELECT_GUI: ✓✓✓ User information received! User name: '{user_name}'")
        rospy.loginfo("DIFFICULTY_SELECT_GUI: Initializing difficulty selection GUI...")
        
        # Small delay to ensure info_user_gui has fully closed and user can see the transition
        rospy.sleep(1.0)
        
        # NOW initialize pygame and UI components
        try:
            rospy.loginfo("DIFFICULTY_SELECT_GUI: About to call _initialize_pygame()...")
            self._initialize_pygame()
            rospy.loginfo("DIFFICULTY_SELECT_GUI: _initialize_pygame() completed successfully")
        except Exception as e:
            rospy.logerr(f"DIFFICULTY_SELECT_GUI: CRITICAL ERROR during pygame initialization: {e}")
            import traceback
            rospy.logerr(f"DIFFICULTY_SELECT_GUI: Traceback: {traceback.format_exc()}")
            self.display_active = False
            return
        
        # Verify initialization was successful
        if not self.pygame_initialized:
            rospy.logerr("DIFFICULTY_SELECT_GUI: pygame_initialized is False after _initialize_pygame()!")
            self.display_active = False
            return
        
        if self.screen is None:
            rospy.logerr("DIFFICULTY_SELECT_GUI: screen is None after _initialize_pygame()!")
            self.display_active = False
            return
        
        rospy.loginfo("DIFFICULTY_SELECT_GUI: ✓✓✓ Initialization verified - screen exists and pygame is initialized")
        
        # Draw initial loading frame
        if self.screen is not None:
            try:
                self.screen.fill((50, 50, 50))
                # Draw a simple "Loading..." message first
                font = pygame.font.Font(None, 48)
                loading_text = font.render("Loading game options...", True, (255, 255, 255))
                text_rect = loading_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                self.screen.blit(loading_text, text_rect)
                pygame.display.flip()
                rospy.loginfo("DIFFICULTY_SELECT_GUI: Initial loading frame displayed")
            except Exception as e:
                rospy.logerr(f"DIFFICULTY_SELECT_GUI: Error drawing loading message: {e}")
                import traceback
                rospy.logerr(f"DIFFICULTY_SELECT_GUI: Traceback: {traceback.format_exc()}")
            rospy.sleep(0.5)  # Brief pause to show loading
        
        running = True
        
        # Ensure pygame is available before entering main loop
        if pygame is None:
            rospy.logerr("DIFFICULTY_SELECT_GUI: Pygame not initialized! Cannot start main loop.")
            return
        
        if self.screen is None:
            rospy.logerr("DIFFICULTY_SELECT_GUI: Screen not created! Cannot start main loop.")
            return
        
        rospy.loginfo("DIFFICULTY_SELECT_GUI: Starting main display loop - window should be visible now!")
        
        while running and not rospy.is_shutdown() and self.display_active:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.display_active = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.selected_difficulty = 0
                        self.set_difficulty()
                    elif event.key == pygame.K_2:
                        self.selected_difficulty = 1
                        self.set_difficulty()
                    elif event.key == pygame.K_3:
                        self.selected_difficulty = 2
                        self.set_difficulty()
                    elif event.key == pygame.K_UP:
                        self.selected_difficulty = (self.selected_difficulty - 1) % len(self.difficulties)
                        self.status_message = None  # Clear status on navigation
                    elif event.key == pygame.K_DOWN:
                        self.selected_difficulty = (self.selected_difficulty + 1) % len(self.difficulties)
                        self.status_message = None  # Clear status on navigation
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.set_difficulty()
                    # Player color selection
                    elif event.key == pygame.K_r:
                        self.set_player_color(1)  # Red
                    elif event.key == pygame.K_p:
                        self.set_player_color(2)  # Purple
                    elif event.key == pygame.K_b:
                        self.set_player_color(3)  # Blue
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                        self.display_active = False
            
            # Update status timer
            if self.status_timer > 0:
                self.status_timer -= 1
                if self.status_timer == 0:
                    self.status_message = None
            
            # Draw (only if display is still active)
            if self.display_active:
                try:
                    self.draw()
                    pygame.display.flip()
                    self.clock.tick(60)
                except pygame.error as e:
                    rospy.logerr(f"Pygame error in main loop: {e}")
                    self.display_active = False
                    break
                except Exception as e:
                    rospy.logerr(f"Error in draw loop: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue trying to draw
        
        # Don't quit pygame.display - just mark as inactive
        self.screen = None
        self.display_active = False
        rospy.loginfo("DIFFICULTY_SELECT_GUI node shutting down")


if __name__ == '__main__':
    try:
        node = DifficultySelectGUI()
        node.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("DIFFICULTY_SELECT_GUI node interrupted")
    except KeyboardInterrupt:
        rospy.loginfo("DIFFICULTY_SELECT_GUI node interrupted by user")
    except Exception as e:
        rospy.logerr(f"DIFFICULTY_SELECT_GUI node crashed with error: {e}")
        import traceback
        rospy.logerr(f"Traceback: {traceback.format_exc()}")
        raise

