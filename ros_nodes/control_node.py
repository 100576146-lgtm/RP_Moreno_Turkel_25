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
        rospy.loginfo("Use arrow keys to move. Press 'q' to quit.")
        while not rospy.is_shutdown():
            key = self.getKey()
            msg = String()
            if key == '\x1b[A':
                msg.data = "UP"
            elif key == '\x1b[B':
                msg.data = "DOWN"
            elif key == '\x1b[C':
                msg.data = "RIGHT"
            elif key == '\x1b[D':
                msg.data = "LEFT"
            elif key == 'q':
                break
            
            if msg.data:
                self.pub.publish(msg)
                # rospy.loginfo(f"Sent: {msg.data}")

if __name__ == '__main__':
    node = ControlNode()
    try:
        node.run()
    except rospy.ROSInterruptException:
        pass

