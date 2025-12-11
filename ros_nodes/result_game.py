#!/usr/bin/env python3
import rospy
from ros_nodes.msg import user_msg
from ros_nodes.srv import GetUserScore
from std_msgs.msg import Int64

class ResultGameNode:
    def __init__(self):
        rospy.init_node('result_node', anonymous=True)
        
        self.user_name = ""  # Store name for service call (as per requirement)
        self.user_username = ""  # Store username for display
        
        self.sub_info = rospy.Subscriber('user_information', user_msg, self.user_info_cb)
        self.sub_res = rospy.Subscriber('result_information', Int64, self.result_cb)
        
        rospy.loginfo("RESULT_NODE initialized")

    def user_info_cb(self, msg):
        rospy.loginfo("RESULT_NODE: Received user information message")
        rospy.loginfo("RESULT_NODE: Transitioning to process user information")
        
        # Store both name and username
        self.user_name = msg.name  # Store name for service call (as per requirement: "sends the name of the user")
        self.user_username = msg.username  # Store username for display
        rospy.loginfo(f"RESULT_NODE: Stored user name: {self.user_name}, username: {self.user_username}")
        rospy.loginfo(f"RESULT_NODE: User information processed successfully (Name: {msg.name}, Username: {msg.username}, Age: {msg.age})")

    def result_cb(self, msg):
        rospy.loginfo("RESULT_NODE: Received result information message")
        rospy.loginfo("RESULT_NODE: Transitioning to process final score")
        
        score = msg.data
        rospy.loginfo(f"RESULT_NODE: Received final score: {score}")
        rospy.loginfo("RESULT_NODE: Transitioning to display results")
        
        print(f"\nGAME OVER\nUser: {self.user_username}\nScore: {score}")
        rospy.loginfo("RESULT_NODE: Results displayed to user")
        
        # Call service to get percentage
        rospy.loginfo("RESULT_NODE: Transitioning to get score percentage")
        self.get_score_percentage()
        rospy.loginfo("RESULT_NODE: Result processing completed")

    def get_score_percentage(self):
        rospy.loginfo("RESULT_NODE: Waiting for 'user_score' service to become available...")
        rospy.wait_for_service('user_score')
        rospy.loginfo("RESULT_NODE: 'user_score' service is available")
        
        try:
            # As per requirement: "sends to the user_score service the name of the user"
            # Send the name (not username) to the service
            rospy.loginfo(f"RESULT_NODE: Calling 'user_score' service with user name: {self.user_name}")
            get_score = rospy.ServiceProxy('user_score', GetUserScore)
            # Service field is called 'username' but we send the actual name value as per requirement
            resp = get_score(username=self.user_name)
            # Service returns int64 score (percentage)
            rospy.loginfo(f"RESULT_NODE: Service call successful, received score (percentage): {resp.score}")
            # Print the percentage score as per requirement
            print(f"Score Percentage: {resp.score}%")
        except rospy.ServiceException as e:
            rospy.logerr(f"RESULT_NODE: Service call failed: {e}")

    def run(self):
        rospy.loginfo("RESULT_NODE: Starting main loop (rospy.spin())")
        rospy.loginfo("RESULT_NODE: Node is now active and waiting for messages")
        rospy.spin()
        rospy.loginfo("RESULT_NODE: Main loop exited")

if __name__ == '__main__':
    try:
        rospy.loginfo("RESULT_NODE: Starting RESULT_NODE...")
        node = ResultGameNode()
        node.run()
        rospy.loginfo("RESULT_NODE: Node execution completed")
    except rospy.ROSInterruptException:
        rospy.loginfo("RESULT_NODE: Node interrupted by user")
    except Exception as e:
        rospy.logerr(f"RESULT_NODE: Error occurred: {e}")

