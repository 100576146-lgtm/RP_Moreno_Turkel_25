#!/usr/bin/env python3
import rospy
import pygame
from std_msgs.msg import String

class ControlNodePygame:
    def __init__(self):
        rospy.init_node('control_node_pygame', anonymous=True)
        self.pub = rospy.Publisher('keyboard_control', String, queue_size=10)
        pygame.init()
        self.screen = pygame.display.set_mode((300, 200))
        pygame.display.set_caption("ROS Control Node")
        rospy.loginfo("CONTROL_NODE_PYGAME initialized")

    def run(self):
        rospy.loginfo("Focus on the Pygame window and use arrow keys.")
        running = True
        clock = pygame.time.Clock()
        
        while not rospy.is_shutdown() and running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    msg = String()
                    if event.key == pygame.K_UP:
                        msg.data = "UP"
                    elif event.key == pygame.K_DOWN:
                        msg.data = "DOWN"
                    elif event.key == pygame.K_LEFT:
                        msg.data = "LEFT"
                    elif event.key == pygame.K_RIGHT:
                        msg.data = "RIGHT"
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                    
                    if msg.data:
                        self.pub.publish(msg)
                        # rospy.loginfo(f"Sent: {msg.data}")
            
            clock.tick(30)
        pygame.quit()

if __name__ == '__main__':
    try:
        node = ControlNodePygame()
        node.run()
    except rospy.ROSInterruptException:
        pass

