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
        rospy.loginfo("CONTROL_NODE_PYGAME: Starting Pygame keyboard input loop")
        rospy.loginfo("CONTROL_NODE_PYGAME: Transitioning to keyboard input mode")
        rospy.loginfo("CONTROL_NODE_PYGAME: Focus on the Pygame window and use arrow keys.")
        
        running = True
        clock = pygame.time.Clock()
        
        while not rospy.is_shutdown() and running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    rospy.loginfo("CONTROL_NODE_PYGAME: Window close event received")
                    rospy.loginfo("CONTROL_NODE_PYGAME: Transitioning to shutdown")
                    running = False
                elif event.type == pygame.KEYDOWN:
                    msg = String()
                    if event.key == pygame.K_UP:
                        msg.data = "UP"
                        rospy.loginfo("CONTROL_NODE_PYGAME: UP arrow key detected")
                    elif event.key == pygame.K_DOWN:
                        msg.data = "DOWN"
                        rospy.loginfo("CONTROL_NODE_PYGAME: DOWN arrow key detected")
                    elif event.key == pygame.K_LEFT:
                        msg.data = "LEFT"
                        rospy.loginfo("CONTROL_NODE_PYGAME: LEFT arrow key detected")
                    elif event.key == pygame.K_RIGHT:
                        msg.data = "RIGHT"
                        rospy.loginfo("CONTROL_NODE_PYGAME: RIGHT arrow key detected")
                    elif event.key == pygame.K_ESCAPE:
                        rospy.loginfo("CONTROL_NODE_PYGAME: ESC key detected")
                        rospy.loginfo("CONTROL_NODE_PYGAME: Transitioning to shutdown")
                        running = False
                    
                    if msg.data:
                        rospy.loginfo(f"CONTROL_NODE_PYGAME: Publishing movement command: {msg.data}")
                        self.pub.publish(msg)
                        rospy.loginfo(f"CONTROL_NODE_PYGAME: Published '{msg.data}' to 'keyboard_control' topic")
            
            clock.tick(30)
        
        rospy.loginfo("CONTROL_NODE_PYGAME: Keyboard input loop exited")
        rospy.loginfo("CONTROL_NODE_PYGAME: Shutting down Pygame")
        pygame.quit()
        rospy.loginfo("CONTROL_NODE_PYGAME: Pygame shutdown complete")

if __name__ == '__main__':
    try:
        rospy.loginfo("CONTROL_NODE_PYGAME: Starting CONTROL_NODE_PYGAME...")
        node = ControlNodePygame()
        node.run()
        rospy.loginfo("CONTROL_NODE_PYGAME: Node execution completed")
    except rospy.ROSInterruptException:
        rospy.loginfo("CONTROL_NODE_PYGAME: Node interrupted by user")
    except Exception as e:
        rospy.logerr(f"CONTROL_NODE_PYGAME: Error occurred: {e}")

