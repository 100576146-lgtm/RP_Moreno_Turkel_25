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
        rospy.loginfo(f"GAME_NODE: GetUserScore service called with username: {req.username}")
        rospy.loginfo(f"GAME_NODE: Current score: {self.score}")
        
        # Calculate percentage of score (assuming max score 1000)
        # Return as int64 as per service definition
        percentage = (self.score / 1000.0) * 100
        score_as_int64 = int(percentage)  # Convert to int64
        
        rospy.loginfo(f"GAME_NODE: Calculated score percentage: {percentage}%, returning as int64: {score_as_int64}")
        return GetUserScoreResponse(score_as_int64)

    def handle_difficulty(self, req):
        rospy.loginfo(f"GAME_NODE: SetGameDifficulty service called with change_difficulty: {req.change_difficulty}")
        rospy.loginfo(f"GAME_NODE: Current phase: {self.phase}")
        
        # Only allow difficulty change during phase1 (start screen) as per requirements
        if self.phase == "phase1":
            rospy.loginfo("GAME_NODE: Current phase is phase1, difficulty change allowed")
            
            # Validate difficulty value
            if req.change_difficulty in ["easy", "medium", "hard"]:
                old_difficulty = self.difficulty
                self.difficulty = req.change_difficulty
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
                
                return SetGameDifficultyResponse(True, f"Difficulty set to {self.difficulty}")
            else:
                rospy.logwarn(f"GAME_NODE: Invalid difficulty level requested: {req.change_difficulty}")
                return SetGameDifficultyResponse(False, f"Invalid difficulty level. Must be 'easy', 'medium', or 'hard'")
        else:
            rospy.logwarn(f"GAME_NODE: Cannot change difficulty during {self.phase}. Only allowed in phase1.")
            return SetGameDifficultyResponse(False, f"Cannot change difficulty during {self.phase}. Only allowed in phase1 (start screen).")

    def user_info_cb(self, msg):
        rospy.loginfo("GAME_NODE: Received user information message")
        if self.phase == "phase1":
            rospy.loginfo(f"GAME_NODE: Current phase is '{self.phase}' (Welcome phase)")
            rospy.loginfo("GAME_NODE: Transitioning to process user information")
            
            self.user_name = msg.name
            self.user_age = msg.age
            rospy.loginfo(f"GAME_NODE: Stored user name: '{self.user_name}', age: {self.user_age}")
            
            # Set user_name parameter IMMEDIATELY so difficulty_select_gui can proceed
            rospy.set_param('user_name', self.user_name)
            rospy.loginfo(f"GAME_NODE: Set user_name parameter to '{self.user_name}'")
            
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
        
        print(f"Welcome {user_msg.name} ({user_msg.username})! Age: {user_msg.age}")
        
        rospy.loginfo("GAME_NODE: Waiting 2 seconds before transitioning to Game phase...")
        rospy.sleep(2)
        
        rospy.loginfo("GAME_NODE: Transitioning from Welcome phase to Game phase")
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

