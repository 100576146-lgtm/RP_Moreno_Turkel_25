#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import sys, select, termios, tty

class ControlNode:
    def __init__(self):
        rospy.init_node('control_node', anonymous=True)
        self.pub = rospy.Publisher('keyboard_control', String, queue_size=10)
        # Subscribe to keyboard_control to see keyboard events from the game
        self.sub = rospy.Subscriber('keyboard_control', String, self.keyboard_callback)
        
        # Check if stdin is a TTY before trying to get terminal settings
        if sys.stdin.isatty():
            try:
                self.settings = termios.tcgetattr(sys.stdin)
                self.use_termios = True
                rospy.loginfo("CONTROL_NODE: Terminal input initialized successfully")
            except (termios.error, OSError, AttributeError) as e:
                rospy.logwarn(f"CONTROL_NODE: Could not get terminal settings: {e}")
                rospy.logwarn("CONTROL_NODE: Falling back to basic input mode")
                self.use_termios = False
                self.settings = None
        else:
            rospy.logwarn("CONTROL_NODE: stdin is not a TTY. Keyboard input may not work properly.")
            rospy.logwarn("CONTROL_NODE: If launched via roslaunch, consider running this node manually in a separate terminal.")
            self.use_termios = False
            self.settings = None
        
        rospy.loginfo("CONTROL_NODE initialized")
        rospy.loginfo("CONTROL_NODE: Subscribed to 'keyboard_control' topic for bidirectional communication")
    
    def keyboard_callback(self, msg):
        """Handle keyboard messages from the game or other nodes."""
        rospy.loginfo(f"CONTROL_NODE: Received keyboard event from game/other node: {msg.data}")

    def getKey(self):
        if not self.use_termios:
            # Fallback mode: try basic select-based input
            try:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    key = sys.stdin.read(1)
                    if key == '\x1b':
                        # Try to read escape sequence for arrow keys
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            key += sys.stdin.read(2)
                    return key
            except (OSError, ValueError) as e:
                rospy.logdebug(f"CONTROL_NODE: Error reading input: {e}")
            return ''
        
        # Original termios-based method (more reliable for arrow keys)
        try:
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
        except (termios.error, OSError, ValueError) as e:
            rospy.logwarn(f"CONTROL_NODE: Error reading key: {e}")
            # Try to restore terminal settings if possible
            if self.settings is not None:
                try:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
                except:
                    pass
            return ''

    def run(self):
        rospy.loginfo("CONTROL_NODE: Starting keyboard input loop")
        rospy.loginfo("CONTROL_NODE: Transitioning to keyboard input mode")
        rospy.loginfo("CONTROL_NODE: Use arrow keys to move. Press 'q' to quit.")
        
        # Wait a moment for publisher to connect
        rospy.sleep(0.5)
        
        # Test that publisher is working
        test_msg = String()
        test_msg.data = "TEST"
        self.pub.publish(test_msg)
        rospy.loginfo("CONTROL_NODE: Test message published to verify connection")
        
        if not self.use_termios:
            rospy.logwarn("=" * 60)
            rospy.logwarn("CONTROL_NODE: WARNING - Running in fallback mode!")
            rospy.logwarn("CONTROL_NODE: stdin is not a proper TTY. Keyboard input may not work.")
            rospy.logwarn("CONTROL_NODE: This usually happens when launched via roslaunch.")
            rospy.logwarn("")
            rospy.logwarn("CONTROL_NODE: Solutions:")
            rospy.logwarn("  1. Run this node manually in a separate terminal:")
            rospy.logwarn("     rosrun ros_nodes control_node.py")
            rospy.logwarn("  2. Use control_node_pygame.py (works better with roslaunch)")
            rospy.logwarn("  3. Make sure the terminal window is focused and try typing")
            rospy.logwarn("=" * 60)
        
        rospy.loginfo("CONTROL_NODE: Node is running and waiting for keyboard input...")
        rospy.loginfo("CONTROL_NODE: If you don't see key detection messages, stdin is not connected properly.")
        rospy.loginfo("=" * 70)
        rospy.loginfo("CONTROL_NODE: REAL-TIME FEEDBACK - Watch for messages below:")
        rospy.loginfo("=" * 70)
        
        input_count = 0
        last_status_time = rospy.get_time()
        last_sent_command = None
        
        while not rospy.is_shutdown():
            key = self.getKey()
            msg = String()
            
            if key:
                input_count += 1
                rospy.loginfo(f"CONTROL_NODE: [INPUT] Received key: {repr(key)} (total: {input_count})")
            
            if key == '\x1b[A':
                msg.data = "UP"
                rospy.loginfo("CONTROL_NODE: [DETECTED] UP arrow key")
            elif key == '\x1b[B':
                msg.data = "DOWN"
                rospy.loginfo("CONTROL_NODE: [DETECTED] DOWN arrow key")
            elif key == '\x1b[C':
                msg.data = "RIGHT"
                rospy.loginfo("CONTROL_NODE: [DETECTED] RIGHT arrow key")
            elif key == '\x1b[D':
                msg.data = "LEFT"
                rospy.loginfo("CONTROL_NODE: [DETECTED] LEFT arrow key")
            elif key == 'q':
                rospy.loginfo("CONTROL_NODE: Quit command received ('q' key)")
                rospy.loginfo("CONTROL_NODE: Transitioning to shutdown")
                break
            
            if msg.data:
                last_sent_command = msg.data
                rospy.loginfo("=" * 70)
                rospy.loginfo(f"CONTROL_NODE: [SENDING] Movement command: '{msg.data}'")
                rospy.loginfo(f"CONTROL_NODE: [TOPIC] Publishing to 'keyboard_control'")
                rospy.loginfo(f"CONTROL_NODE: [TARGET] GAME_NODE will receive this message")
                self.pub.publish(msg)
                rospy.loginfo(f"CONTROL_NODE: [SUCCESS] Published '{msg.data}' to GAME_NODE")
                rospy.loginfo("=" * 70)
            
            # Log status every 10 seconds if no input received
            current_time = rospy.get_time()
            if input_count == 0 and (current_time - last_status_time) >= 10.0:
                rospy.logwarn("CONTROL_NODE: Still waiting for keyboard input... (no input received yet)")
                rospy.logwarn("CONTROL_NODE: Make sure the terminal window is focused and try pressing arrow keys")
                last_status_time = current_time
        
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

