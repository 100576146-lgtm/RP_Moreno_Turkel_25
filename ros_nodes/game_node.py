#!/usr/bin/env python3
import rospy
from ros_nodes.msg import user_msg
from ros_nodes.srv import GetUserScore, GetUserScoreResponse
from ros_nodes.srv import SetGameDifficulty, SetGameDifficultyResponse
from std_msgs.msg import String, Int64

class GameNode:
    def __init__(self):
        rospy.init_node('game_node', anonymous=True)
        
        # Parameters
        # change_player_color: int64 - Change player color (1: Red, 2: Purple, 3: Blue)
        # Read parameter (launch file sets it without ~ prefix, but also check with ~ for compatibility)
        if rospy.has_param('change_player_color'):
            self.color_param = rospy.get_param('change_player_color')
        elif rospy.has_param('~change_player_color'):
            self.color_param = rospy.get_param('~change_player_color')
        else:
            self.color_param = 2  # Default Purple
        rospy.loginfo(f"GAME_NODE: change_player_color parameter set to: {self.color_param}")
        
        # screen_param: string - Show game phase (phase1, phase2, phase3)
        rospy.set_param('screen_param', 'phase1')
        
        # State
        self.phase = "phase1" # phase1=Welcome, phase2=Game, phase3=Final
        self.score = 0
        self.user_name = ""
        self.difficulty = "medium"
        
        # Publishers & Subscribers
        self.result_pub = rospy.Publisher('result_information', Int64, queue_size=10)
        self.sub_info = rospy.Subscriber('user_information', user_msg, self.user_info_cb)
        self.sub_key = rospy.Subscriber('keyboard_control', String, self.keyboard_cb)
        self.sub_stats = rospy.Subscriber('game_over_stats', Int64, self.game_stats_cb)
        
        # Services
        self.srv_score = rospy.Service('user_score', GetUserScore, self.handle_user_score)
        self.srv_diff = rospy.Service('difficulty', SetGameDifficulty, self.handle_difficulty)
        
        rospy.loginfo("GAME_NODE initialized")

    def handle_user_score(self, req):
        # Get username value - handle different possible field names
        username_value = None
        
        # Log all available attributes for debugging
        all_attrs = [a for a in dir(req) if not a.startswith('_')]
        rospy.loginfo(f"GAME_NODE: GetUserScore request object type: {type(req)}, attributes: {all_attrs}")
        
        # Try different possible field names
        if hasattr(req, 'username'):
            try:
                username_value = req.username
                rospy.loginfo(f"GAME_NODE: Found 'username' field: {username_value}")
            except AttributeError:
                pass
        elif hasattr(req, 'name'):
            try:
                username_value = req.name
                rospy.loginfo(f"GAME_NODE: Found 'name' field: {username_value}")
            except AttributeError:
                pass
        
        # Try to get from __dict__ if available
        if username_value is None and hasattr(req, '__dict__'):
            for key, val in req.__dict__.items():
                if isinstance(val, str):
                    username_value = val
                    rospy.logwarn(f"GAME_NODE: Using __dict__ key '{key}' for username: {username_value}")
                    break
        
        # Last resort: try to get the first string attribute
        if username_value is None:
            for attr in all_attrs:
                try:
                    val = getattr(req, attr)
                    if isinstance(val, str):
                        username_value = val
                        rospy.logwarn(f"GAME_NODE: Using field '{attr}' for username (expected 'username'): {username_value}")
                        break
                except:
                    continue
        
        if username_value is None:
            rospy.logerr("GAME_NODE: Could not find username field in request")
            rospy.logerr(f"GAME_NODE: Available attributes: {all_attrs}")
            # Return a default score
            return GetUserScoreResponse(0)
        
        rospy.loginfo(f"GAME_NODE: GetUserScore service called with user name: {username_value}")
        rospy.loginfo(f"GAME_NODE: Current score: {self.score}")
        
        # Calculate percentage of score (assuming max score 1000)
        # Return as int64 as per service definition
        percentage = (self.score / 1000.0) * 100
        score_as_int64 = int(percentage)  # Convert to int64
        
        rospy.loginfo(f"GAME_NODE: Calculated score percentage: {percentage}%, returning as int64: {score_as_int64}")
        return GetUserScoreResponse(score_as_int64)

    def handle_difficulty(self, req):
        # Get difficulty value - handle different possible field names
        difficulty_value = None
        
        # First, check if req is already a string (unlikely but possible)
        if isinstance(req, str):
            difficulty_value = req
            rospy.loginfo(f"GAME_NODE: Request is a string: {difficulty_value}")
        else:
            # Log all available attributes for debugging
            all_attrs = [a for a in dir(req) if not a.startswith('_')]
            rospy.loginfo(f"GAME_NODE: Request object type: {type(req)}, attributes: {all_attrs}")
            
            # Try to inspect __dict__ if available
            try:
                if hasattr(req, '__dict__'):
                    rospy.loginfo(f"GAME_NODE: Request __dict__: {req.__dict__}")
            except:
                pass
            
            # Try different possible field names (ROS might generate different names)
            # Check for 'difficulty' field first (matches generated code)
            if hasattr(req, 'difficulty'):
                try:
                    difficulty_value = req.difficulty
                    rospy.loginfo(f"GAME_NODE: Found 'difficulty' field: {difficulty_value}")
                except AttributeError:
                    pass
            elif hasattr(req, 'change_difficulty'):
                try:
                    difficulty_value = req.change_difficulty
                    rospy.loginfo(f"GAME_NODE: Found 'change_difficulty' field: {difficulty_value}")
                except AttributeError:
                    pass
            elif hasattr(req, 'level'):
                try:
                    difficulty_value = req.level
                    rospy.loginfo(f"GAME_NODE: Found 'level' field: {difficulty_value}")
                except AttributeError:
                    pass
            else:
                # Try to access as if it's a tuple/list (positional argument)
                try:
                    if isinstance(req, (tuple, list)) and len(req) > 0:
                        difficulty_value = req[0]
                        rospy.loginfo(f"GAME_NODE: Accessed request as sequence: {difficulty_value}")
                except (TypeError, IndexError):
                    pass
                
                # Try to get from __dict__ if available
                if difficulty_value is None and hasattr(req, '__dict__'):
                    for key, val in req.__dict__.items():
                        if isinstance(val, str) and val in ["easy", "medium", "hard"]:
                            difficulty_value = val
                            rospy.logwarn(f"GAME_NODE: Using __dict__ key '{key}' for difficulty: {difficulty_value}")
                            break
                
                # Last resort: try to get the first string attribute
                if difficulty_value is None:
                    for attr in all_attrs:
                        try:
                            val = getattr(req, attr)
                            if isinstance(val, str) and val in ["easy", "medium", "hard"]:
                                difficulty_value = val
                                rospy.logwarn(f"GAME_NODE: Using field '{attr}' for difficulty (expected 'change_difficulty'): {difficulty_value}")
                                break
                        except:
                            continue
        
        if difficulty_value is None:
            rospy.logerr("GAME_NODE: Could not find difficulty field in request")
            rospy.logerr(f"GAME_NODE: Request type: {type(req)}")
            rospy.logerr(f"GAME_NODE: Available attributes: {all_attrs}")
            # Try to get all attribute values
            for attr in all_attrs:
                try:
                    val = getattr(req, attr)
                    rospy.logerr(f"GAME_NODE:   {attr} = {val} (type: {type(val)})")
                except:
                    pass
            return SetGameDifficultyResponse(False)
        
        rospy.loginfo(f"GAME_NODE: SetGameDifficulty service called with difficulty: {difficulty_value}")
        rospy.loginfo(f"GAME_NODE: Current phase: {self.phase}")
        
        # Only allow difficulty change during phase1 (start screen) as per requirements
        if self.phase == "phase1":
            rospy.loginfo("GAME_NODE: Current phase is phase1, difficulty change allowed")
            
            # Validate difficulty value
            if difficulty_value in ["easy", "medium", "hard"]:
                old_difficulty = self.difficulty
                self.difficulty = difficulty_value
                rospy.loginfo(f"GAME_NODE: Difficulty changed from '{old_difficulty}' to '{self.difficulty}'")
                
                # Set start level based on difficulty
                start_level = 0  # 0-indexed (Level 1)
                if self.difficulty == "easy":
                    start_level = 0  # Levels 1-3 (0-indexed: 0, 1, 2)
                elif self.difficulty == "medium":
                    start_level = 3  # Levels 4-6 (0-indexed: 3, 4, 5)
                elif self.difficulty == "hard":
                    start_level = 6  # Levels 7-10 (0-indexed: 6, 7, 8, 9)
                
                rospy.set_param('start_level', start_level)
                rospy.set_param('selected_difficulty', self.difficulty)  # Store difficulty name for game
                rospy.loginfo(f"GAME_NODE: Difficulty set to {self.difficulty}, Start Level: {start_level + 1}")
                
                # Return response - handle both old (with message) and new (without message) service definitions
                try:
                    return SetGameDifficultyResponse(True, "Difficulty set successfully")
                except TypeError:
                    # New service definition without message field
                    return SetGameDifficultyResponse(True)
            else:
                rospy.logwarn(f"GAME_NODE: Invalid difficulty level requested: {difficulty_value}")
                try:
                    return SetGameDifficultyResponse(False, "Invalid difficulty level")
                except TypeError:
                    return SetGameDifficultyResponse(False)
        else:
            rospy.logwarn(f"GAME_NODE: Cannot change difficulty during {self.phase}. Only allowed in phase1.")
            try:
                return SetGameDifficultyResponse(False, f"Cannot change difficulty during {self.phase}")
            except TypeError:
                return SetGameDifficultyResponse(False)

    def user_info_cb(self, msg):
        rospy.loginfo("GAME_NODE: Received user information message")
        if self.phase == "phase1":
            rospy.loginfo(f"GAME_NODE: Current phase is '{self.phase}' (Welcome phase)")
            rospy.loginfo("GAME_NODE: Transitioning to process user information")
            
            self.user_name = msg.name
            self.user_age = msg.age
            rospy.loginfo(f"GAME_NODE: Stored user name: '{self.user_name}', age: {self.user_age}")
            
            # Set user_name parameter IMMEDIATELY so difficulty_select_gui can proceed
            # This MUST happen before welcome_phase to ensure difficulty GUI can start
            try:
                rospy.set_param('user_name', self.user_name)
                rospy.loginfo(f"GAME_NODE: ✓✓✓ Set user_name parameter to '{self.user_name}'")
                # Verify it was set
                if rospy.has_param('user_name'):
                    rospy.loginfo(f"GAME_NODE: ✓ Verified user_name parameter exists: {rospy.get_param('user_name')}")
                else:
                    rospy.logerr("GAME_NODE: ✗ ERROR: user_name parameter was not set!")
            except Exception as e:
                rospy.logerr(f"GAME_NODE: ✗ ERROR setting user_name parameter: {e}")
                import traceback
                rospy.logerr(f"GAME_NODE: Traceback: {traceback.format_exc()}")
            
            # Call welcome_phase to print user name as per exercise requirements
            rospy.loginfo("GAME_NODE: Transitioning to Welcome phase method")
            self.welcome_phase(msg)
        else:
            rospy.logwarn(f"GAME_NODE: Received user info but not in phase1 (current phase: {self.phase})")
            
    def game_stats_cb(self, msg):
        """Callback from GUI game when it finishes."""
        rospy.loginfo("GAME_NODE: Received game statistics message")
        if self.phase == "phase2":
            rospy.loginfo(f"GAME_NODE: Current phase is '{self.phase}' (Game phase)")
            rospy.loginfo(f"GAME_NODE: Received Game Over stats. Score: {msg.data}")
            rospy.loginfo("GAME_NODE: Transitioning to process final score")
            
            self.score = msg.data
            rospy.loginfo(f"GAME_NODE: Updated score to {self.score}")
            rospy.loginfo("GAME_NODE: Transitioning to Final phase")
            self.final_phase()
        else:
            rospy.logwarn(f"GAME_NODE: Received game stats but not in phase2 (current phase: {self.phase})")

    def keyboard_cb(self, msg):
        rospy.logdebug("GAME_NODE: Received keyboard control message")
        if self.phase == "phase2":
            rospy.loginfo(f"GAME_NODE: Processing movement command: {msg.data}")
            # Simple score increment for movement (legacy text-mode)
            old_score = self.score
            self.score += 10
            rospy.logdebug(f"GAME_NODE: Score updated from {old_score} to {self.score} (+10 for movement)")
        else:
            rospy.logdebug(f"GAME_NODE: Received keyboard input but not in phase2 (current phase: {self.phase}, ignoring)")

    def welcome_phase(self, user_msg):
        rospy.loginfo("GAME_NODE: ========== WELCOME PHASE STARTED ==========")
        rospy.set_param('screen_param', 'phase1')
        rospy.loginfo("GAME_NODE: Welcome phase started.")
        rospy.loginfo(f"GAME_NODE: Displaying welcome message for user: {user_msg.name} ({user_msg.username}), Age: {user_msg.age}")
        
        # Print the name of the user as per requirement: "prints in the screen the name of the user"
        # This is the WELCOME SCREEN - show it first
        print(f"\n{'='*50}")
        print(f"Welcome {user_msg.name}!")
        print(f"{'='*50}\n")
        
        rospy.loginfo("GAME_NODE: Welcome message displayed. Waiting for difficulty GUI to appear...")
        # Give time for difficulty GUI to initialize and appear
        rospy.sleep(1.0)
        
        # Wait for difficulty to be selected before transitioning to game phase
        rospy.loginfo("GAME_NODE: Waiting for difficulty selection before starting game phase...")
        rospy.loginfo("GAME_NODE: Please select a difficulty in the difficulty selection window")
        wait_count = 0
        while not rospy.has_param('difficulty_selected') and not rospy.is_shutdown():
            rospy.sleep(0.5)
            wait_count += 1
            # Log status every 4 seconds (every 8 iterations)
            if wait_count % 8 == 0:
                rospy.loginfo("GAME_NODE: Still waiting for difficulty selection... (Please select a difficulty in the GUI)")
        
        if rospy.is_shutdown():
            rospy.loginfo("GAME_NODE: Node shutdown requested while waiting for difficulty selection")
            return
        
        rospy.loginfo("GAME_NODE: ✓ Difficulty selected! Waiting for color selection and game GUI to be ready...")
        
        # Wait for game GUI to be ready before transitioning to phase2
        # This ensures both difficulty AND color are selected
        rospy.loginfo("GAME_NODE: Waiting for 'ready_to_start_game' parameter...")
        wait_count = 0
        while not rospy.has_param('ready_to_start_game') and not rospy.is_shutdown():
            rospy.sleep(0.5)
            wait_count += 1
            if wait_count % 8 == 0:
                rospy.loginfo("GAME_NODE: Still waiting for game GUI to be ready (difficulty and color must be selected)...")
        
        if rospy.is_shutdown():
            rospy.loginfo("GAME_NODE: Node shutdown requested while waiting for game GUI")
            return
        
        rospy.loginfo("GAME_NODE: ✓ Game GUI is ready! Transitioning from Welcome phase to Game phase")
        # Small delay to ensure difficulty GUI has closed
        rospy.sleep(0.5)
        self.game_phase()

    def game_phase(self):
        rospy.loginfo("GAME_NODE: ========== GAME PHASE STARTED ==========")
        old_phase = self.phase
        self.phase = "phase2"
        rospy.set_param('screen_param', 'phase2')
        rospy.loginfo(f"GAME_NODE: Phase transitioned from '{old_phase}' to '{self.phase}'")
        rospy.loginfo("GAME_NODE: Game phase started. Waiting for GUI game to finish...")
        rospy.loginfo("GAME_NODE: Ready to receive keyboard control messages")
        rospy.loginfo("GAME_NODE: Ready to receive game statistics from GUI")
        
        print("Game started! GUI should be active now.")
        
        # The game_stats_cb will be called when GUI publishes game_over_stats
        # and it will automatically call final_phase()
        rospy.loginfo("GAME_NODE: Game phase active, monitoring for game completion...")

    def final_phase(self):
        rospy.loginfo("GAME_NODE: ========== FINAL PHASE STARTED ==========")
        old_phase = self.phase
        self.phase = "phase3"
        rospy.set_param('screen_param', 'phase3')
        rospy.loginfo(f"GAME_NODE: Phase transitioned from '{old_phase}' to '{self.phase}'")
        rospy.loginfo("GAME_NODE: Final phase reached, calculating score.")
        rospy.loginfo("GAME_NODE: Transitioning to score calculation")
        
        # Calculate final score (Score from GUI + Age Bonus)
        base_score = self.score
        age_bonus = self.user_age * 10 if hasattr(self, 'user_age') and self.user_age else 0
        final_score = base_score + age_bonus
        
        rospy.loginfo(f"GAME_NODE: Score calculation complete - Base: {base_score}, Age Bonus: {age_bonus}, Final: {final_score}")
        
        rospy.loginfo("GAME_NODE: Transitioning to publish final score")
        msg = Int64()
        msg.data = final_score
        self.result_pub.publish(msg)
        rospy.loginfo(f"GAME_NODE: Published final score: {final_score} (Base: {base_score} + Age Bonus: {age_bonus}) to 'result_information' topic")
        rospy.loginfo("GAME_NODE: Final phase completed successfully")

    def run(self):
        rospy.loginfo("GAME_NODE: Starting main loop (rospy.spin())")
        rospy.loginfo("GAME_NODE: Node is now active and waiting for messages")
        rospy.spin()
        rospy.loginfo("GAME_NODE: Main loop exited")

if __name__ == '__main__':
    try:
        rospy.loginfo("GAME_NODE: Starting GAME_NODE...")
        node = GameNode()
        node.run()
        rospy.loginfo("GAME_NODE: Node execution completed")
    except rospy.ROSInterruptException:
        rospy.loginfo("GAME_NODE: Node interrupted by user")
    except Exception as e:
        rospy.logerr(f"GAME_NODE: Error occurred: {e}")

