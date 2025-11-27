#!/usr/bin/env python3
import rospy
from ros_nodes.msg import user_msg

class InfoUserNode:
    def __init__(self):
        rospy.init_node('info_user', anonymous=True)
        self.pub = rospy.Publisher('user_information', user_msg, queue_size=10)
        rospy.loginfo("INFO_USER node initialized")

    def run(self):
        rospy.loginfo("Requesting user information...")
        name = input("Enter your name: ")
        username = input("Enter your username: ")
        while True:
            try:
                age = int(input("Enter your age: "))
                break
            except ValueError:
                print("Invalid age. Please enter a number.")
        
        msg = user_msg()
        msg.name = name
        msg.username = username
        msg.age = age
        
        rospy.sleep(1) # Wait for connections
        self.pub.publish(msg)
        rospy.loginfo("Published user information")

if __name__ == '__main__':
    try:
        node = InfoUserNode()
        node.run()
    except rospy.ROSInterruptException:
        pass

