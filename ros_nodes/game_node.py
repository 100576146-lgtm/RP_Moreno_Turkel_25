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
        self.color_param = rospy.get_param('~change_player_color', 2) # Default Purple
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
        # Return percentage (assuming max score 1000)
        percentage = (self.score / 1000.0) * 100
        return GetUserScoreResponse(percentage)

    def handle_difficulty(self, req):
        # Allow difficulty change during phase1 (before game starts) or phase2 (GUI waiting for difficulty)
        if self.phase == "phase1" or self.phase == "phase2":
            if req.difficulty in ["easy", "medium", "hard"]:
                self.difficulty = req.difficulty
                
                # Set start level based on difficulty
                start_level = 0  # 0-indexed (Level 1)
                if self.difficulty == "easy":
                    start_level = 0  # Levels 1-3 (0-indexed: 0, 1, 2)
                elif self.difficulty == "medium":
                    start_level = 3  # Levels 4-6 (0-indexed: 3, 4, 5)
                elif self.difficulty == "hard":
                    start_level = 6  # Levels 7-10 (0-indexed: 6, 7, 8, 9)
                
                rospy.set_param('start_level', start_level)
                rospy.loginfo(f"Difficulty set to {self.difficulty}, Start Level: {start_level + 1}")
                
                return SetGameDifficultyResponse(True, f"Difficulty set to {self.difficulty}")
            else:
                return SetGameDifficultyResponse(False, "Invalid difficulty level")
        else:
            return SetGameDifficultyResponse(False, f"Cannot change difficulty during {self.phase}")

    def user_info_cb(self, msg):
        if self.phase == "phase1":
            self.user_name = msg.name
            self.user_age = msg.age
            rospy.set_param('user_name', self.user_name)
            self.welcome_phase(msg)
            
    def game_stats_cb(self, msg):
        """Callback from GUI game when it finishes."""
        if self.phase == "phase2":
            rospy.loginfo(f"Received Game Over stats. Score: {msg.data}")
            self.score = msg.data
            self.final_phase()

    def keyboard_cb(self, msg):
        if self.phase == "phase2":
            rospy.loginfo(f"Movement: {msg.data}")
            # Simple score increment for movement (legacy text-mode)
            self.score += 10

    def welcome_phase(self, user_msg):
        rospy.set_param('screen_param', 'phase1')
        rospy.loginfo("Welcome phase started.")
        print(f"Welcome {user_msg.name} ({user_msg.username})! Age: {user_msg.age}")
        rospy.sleep(2)
        self.game_phase()

    def game_phase(self):
        self.phase = "phase2"
        rospy.set_param('screen_param', 'phase2')
        rospy.loginfo("Game phase started. Waiting for GUI game to finish...")
        print("Game started! GUI should be active now.")
        
        # The game_stats_cb will be called when GUI publishes game_over_stats
        # and it will automatically call final_phase()

    def final_phase(self):
        self.phase = "phase3"
        rospy.set_param('screen_param', 'phase3')
        rospy.loginfo("Final phase reached, calculating score.")
        
        # Calculate final score (Score from GUI + Age Bonus)
        base_score = self.score
        age_bonus = self.user_age * 10 if hasattr(self, 'user_age') and self.user_age else 0
        final_score = base_score + age_bonus
        
        msg = Int64()
        msg.data = final_score
        self.result_pub.publish(msg)
        rospy.loginfo(f"Published final score: {final_score} (Base: {base_score} + Age Bonus: {age_bonus})")

    def run(self):
        rospy.spin()

if __name__ == '__main__':
    node = GameNode()
    node.run()

