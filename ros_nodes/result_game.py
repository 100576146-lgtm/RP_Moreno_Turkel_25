#!/usr/bin/env python3
import rospy
from ros_nodes.msg import user_msg
from ros_nodes.srv import GetUserScore
from std_msgs.msg import Int64

class ResultGameNode:
    def __init__(self):
        rospy.init_node('result_node', anonymous=True)
        
        self.user_name = ""
        
        self.sub_info = rospy.Subscriber('user_information', user_msg, self.user_info_cb)
        self.sub_res = rospy.Subscriber('result_information', Int64, self.result_cb)
        
        rospy.loginfo("RESULT_NODE initialized")

    def user_info_cb(self, msg):
        self.user_name = msg.name
        rospy.loginfo(f"Received user info: {self.user_name}")

    def result_cb(self, msg):
        score = msg.data
        rospy.loginfo(f"Received final score: {score}")
        print(f"\nGAME OVER\nUser: {self.user_name}\nScore: {score}")
        
        # Call service to get percentage
        self.get_score_percentage()

    def get_score_percentage(self):
        rospy.wait_for_service('user_score')
        try:
            get_score = rospy.ServiceProxy('user_score', GetUserScore)
            resp = get_score(self.user_name)
            print(f"Score Percentage: {resp.score_percentage}%")
        except rospy.ServiceException as e:
            rospy.logerr(f"Service call failed: {e}")

    def run(self):
        rospy.spin()

if __name__ == '__main__':
    node = ResultGameNode()
    node.run()

