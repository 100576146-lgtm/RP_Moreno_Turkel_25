#!/usr/bin/env python3
import rospy
from ros_nodes.msg import user_msg

class InfoUserNode:
    def __init__(self):
        rospy.init_node('info_user', anonymous=True)
        self.pub = rospy.Publisher('user_information', user_msg, queue_size=10)
        rospy.loginfo("INFO_USER node initialized")

    def run(self):
        rospy.loginfo("INFO_USER: Requesting user information...")
        rospy.loginfo("INFO_USER: Transitioning to user input collection phase")
        
        name = input("Enter your name: ")
        rospy.loginfo(f"INFO_USER: Received name: {name}")
        
        username = input("Enter your username: ")
        rospy.loginfo(f"INFO_USER: Received username: {username}")
        
        while True:
            try:
                age = int(input("Enter your age: "))
                rospy.loginfo(f"INFO_USER: Received age: {age}")
                break
            except ValueError:
                print("Invalid age. Please enter a number.")
                rospy.logwarn("INFO_USER: Invalid age input, retrying...")
        
        rospy.loginfo("INFO_USER: All user information collected successfully")
        rospy.loginfo("INFO_USER: Transitioning to message creation phase")
        
        msg = user_msg()
        msg.name = name
        msg.username = username
        msg.age = age
        
        rospy.loginfo("INFO_USER: Message created with user data")
        rospy.loginfo("INFO_USER: Waiting for subscribers to connect...")
        rospy.sleep(1) # Wait for connections
        
        rospy.loginfo("INFO_USER: Transitioning to publish phase")
        self.pub.publish(msg)
        rospy.loginfo(f"INFO_USER: Published user information to 'user_information' topic (Name: {name}, Username: {username}, Age: {age})")
        rospy.loginfo("INFO_USER: User information publishing completed")

if __name__ == '__main__':
    try:
        rospy.loginfo("INFO_USER: Starting INFO_USER node...")
        node = InfoUserNode()
        node.run()
        rospy.loginfo("INFO_USER: Node execution completed")
    except rospy.ROSInterruptException:
        rospy.loginfo("INFO_USER: Node interrupted by user")
    except Exception as e:
        rospy.logerr(f"INFO_USER: Error occurred: {e}")

