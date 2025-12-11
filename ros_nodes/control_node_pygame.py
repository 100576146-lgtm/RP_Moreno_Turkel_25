#!/usr/bin/env python3
import rospy
import pygame
from std_msgs.msg import String

class ControlNodePygame:
    def __init__(self):
        rospy.init_node('control_node_pygame', anonymous=True)
        self.pub = rospy.Publisher('keyboard_control', String, queue_size=10)
        # Subscribe to keyboard_control to see keyboard events from the game
        self.sub = rospy.Subscriber('keyboard_control', String, self.keyboard_callback)
        pygame.init()
        self.screen = pygame.display.set_mode((400, 300))
        pygame.display.set_caption("ROS Control Node - Real-time Feedback")
        
        # Real-time feedback display variables
        self.last_sent = "None"
        self.last_received = "None"
        self.message_count_sent = 0
        self.message_count_received = 0
        self.last_publish_time = None
        
        rospy.loginfo("CONTROL_NODE_PYGAME initialized")
        rospy.loginfo("CONTROL_NODE_PYGAME: Subscribed to 'keyboard_control' topic for bidirectional communication")
    
    def keyboard_callback(self, msg):
        """Handle keyboard messages from the game or other nodes."""
        self.last_received = msg.data
        self.message_count_received += 1
        rospy.loginfo(f"CONTROL_NODE_PYGAME: Received keyboard event from game/other node: {msg.data}")

    def draw_feedback(self):
        """Draw real-time feedback on the screen."""
        # Clear screen with dark background
        self.screen.fill((30, 30, 30))
        
        # Title
        font_large = pygame.font.Font(None, 36)
        font_medium = pygame.font.Font(None, 28)
        font_small = pygame.font.Font(None, 24)
        
        title = font_large.render("ROS Control Node", True, (255, 255, 255))
        self.screen.blit(title, (10, 10))
        
        # Instructions
        instructions = font_small.render("Use ARROW KEYS to control", True, (200, 200, 200))
        self.screen.blit(instructions, (10, 50))
        
        # Last sent command (with highlight)
        sent_label = font_medium.render("SENT to GAME_NODE:", True, (100, 255, 100))
        self.screen.blit(sent_label, (10, 90))
        
        sent_value = font_large.render(self.last_sent, True, (255, 255, 100))
        self.screen.blit(sent_value, (10, 120))
        
        sent_count = font_small.render(f"Total sent: {self.message_count_sent}", True, (150, 150, 150))
        self.screen.blit(sent_count, (10, 160))
        
        # Last received command
        received_label = font_medium.render("RECEIVED from GAME:", True, (100, 200, 255))
        self.screen.blit(received_label, (10, 200))
        
        received_value = font_large.render(self.last_received, True, (200, 200, 255))
        self.screen.blit(received_value, (10, 230))
        
        received_count = font_small.render(f"Total received: {self.message_count_received}", True, (150, 150, 150))
        self.screen.blit(received_count, (10, 270))
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        rospy.loginfo("CONTROL_NODE_PYGAME: Starting Pygame keyboard input loop")
        rospy.loginfo("CONTROL_NODE_PYGAME: Transitioning to keyboard input mode")
        rospy.loginfo("CONTROL_NODE_PYGAME: Focus on the Pygame window and use arrow keys.")
        
        running = True
        clock = pygame.time.Clock()
        
        while not rospy.is_shutdown() and running:
            # Draw feedback every frame
            self.draw_feedback()
            
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
                        # Update real-time feedback
                        self.last_sent = msg.data
                        self.message_count_sent += 1
                        self.last_publish_time = rospy.get_time()
                        
                        rospy.loginfo(f"CONTROL_NODE_PYGAME: Publishing movement command: {msg.data}")
                        self.pub.publish(msg)
                        rospy.loginfo(f"CONTROL_NODE_PYGAME: Published '{msg.data}' to 'keyboard_control' topic (GAME_NODE should receive this)")
            
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

