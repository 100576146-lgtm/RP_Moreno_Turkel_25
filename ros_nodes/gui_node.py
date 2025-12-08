#!/usr/bin/env python3
import rospy
import subprocess
import os
import sys

def run_gui():
    rospy.init_node('gui_node', anonymous=True)
    
    rospy.loginfo("Waiting for user details...")
    # Wait for user_name param to be set by game_node (after info_user input)
    while not rospy.has_param('user_name') and not rospy.is_shutdown():
        rospy.sleep(0.5)
        
    if rospy.is_shutdown():
        return

    rospy.loginfo("User details received! Launching game GUI...")
    
    # Path to the main game file
    game_path = os.path.expanduser("~/RP_Moreno_Turkel_25/mario_platformer.py")
    
    if not os.path.exists(game_path):
        rospy.logerr(f"Game file not found at: {game_path}")
        return

    try:
        # Run the game using the same python interpreter
        subprocess.call([sys.executable, game_path])
    except Exception as e:
        rospy.logerr(f"Failed to start GUI: {e}")
    
    rospy.loginfo("GUI Game closed.")

if __name__ == '__main__':
    try:
        run_gui()
    except rospy.ROSInterruptException:
        pass

