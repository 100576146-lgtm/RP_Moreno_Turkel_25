#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import sys, select, termios, tty

class ControlNode:
    def __init__(self):
        rospy.init_node('control_node', anonymous=True)
        self.pub = rospy.Publisher('keyboard_control', String, queue_size=10)
        self.settings = termios.tcgetattr(sys.stdin)
        rospy.loginfo("CONTROL_NODE initialized")

    def getKey(self):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
            if key == '\x1b':
                key += sys.stdin.read(2)
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def run(self):
        rospy.loginfo("CONTROL_NODE: Starting keyboard input loop")
        rospy.loginfo("CONTROL_NODE: Transitioning to keyboard input mode")
        rospy.loginfo("CONTROL_NODE: Use arrow keys to move. Press 'q' to quit.")
        
        while not rospy.is_shutdown():
            key = self.getKey()
            msg = String()
            
            if key == '\x1b[A':
                msg.data = "UP"
                rospy.loginfo("CONTROL_NODE: UP arrow key detected")
            elif key == '\x1b[B':
                msg.data = "DOWN"
                rospy.loginfo("CONTROL_NODE: DOWN arrow key detected")
            elif key == '\x1b[C':
                msg.data = "RIGHT"
                rospy.loginfo("CONTROL_NODE: RIGHT arrow key detected")
            elif key == '\x1b[D':
                msg.data = "LEFT"
                rospy.loginfo("CONTROL_NODE: LEFT arrow key detected")
            elif key == 'q':
                rospy.loginfo("CONTROL_NODE: Quit command received ('q' key)")
                rospy.loginfo("CONTROL_NODE: Transitioning to shutdown")
                break
            
            if msg.data:
                rospy.loginfo(f"CONTROL_NODE: Publishing movement command: {msg.data}")
                self.pub.publish(msg)
                rospy.loginfo(f"CONTROL_NODE: Published '{msg.data}' to 'keyboard_control' topic")
        
        rospy.loginfo("CONTROL_NODE: Keyboard input loop exited")

if __name__ == '__main__':
    try:
        rospy.loginfo("CONTROL_NODE: Starting CONTROL_NODE...")
        node = ControlNode()
        node.run()
        rospy.loginfo("CONTROL_NODE: Node execution completed")
    except rospy.ROSInterruptException:
        rospy.loginfo("CONTROL_NODE: Node interrupted by user")
    except Exception as e:
        rospy.logerr(f"CONTROL_NODE: Error occurred: {e}")

