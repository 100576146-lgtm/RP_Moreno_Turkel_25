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
        
        # Services
        self.srv_score = rospy.Service('user_score', GetUserScore, self.handle_user_score)
        self.srv_diff = rospy.Service('difficulty', SetGameDifficulty, self.handle_difficulty)
        
        rospy.loginfo("GAME_NODE initialized")

    def handle_user_score(self, req):
        # Return percentage (assuming max score 1000)
        percentage = (self.score / 1000.0) * 100
        return GetUserScoreResponse(percentage)

    def handle_difficulty(self, req):
        if self.phase == "phase1":
            if req.difficulty in ["easy", "medium", "hard"]:
                self.difficulty = req.difficulty
                rospy.loginfo(f"Difficulty set to {self.difficulty}")
                return SetGameDifficultyResponse(True, f"Difficulty set to {self.difficulty}")
            else:
                return SetGameDifficultyResponse(False, "Invalid difficulty level")
        else:
            return SetGameDifficultyResponse(False, "Cannot change difficulty outside Phase 1")

    def user_info_cb(self, msg):
        if self.phase == "phase1":
            self.user_name = msg.name
            rospy.set_param('user_name', self.user_name)
            self.welcome_phase(msg)

    def keyboard_cb(self, msg):
        if self.phase == "phase2":
            rospy.loginfo(f"Movement: {msg.data}")
            # Simple score increment for movement
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
        rospy.loginfo("Game phase started.")
        print("Game started! Use arrow keys.")
        
        # Simulate game duration
        start_time = rospy.Time.now()
        while (rospy.Time.now() - start_time).to_sec() < 10:
            if rospy.is_shutdown(): return
            rospy.sleep(0.1)
            
        self.final_phase()

    def final_phase(self):
        self.phase = "phase3"
        rospy.set_param('screen_param', 'phase3')
        rospy.loginfo("Final phase reached, calculating score.")
        
        msg = Int64()
        msg.data = self.score
        self.result_pub.publish(msg)
        rospy.loginfo(f"Published score: {self.score}")

    def run(self):
        rospy.spin()

if __name__ == '__main__':
    node = GameNode()
    node.run()

