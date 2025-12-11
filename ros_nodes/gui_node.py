#!/usr/bin/env python3
import rospy
import subprocess
import os
import sys

def run_gui():
    rospy.init_node('gui_node', anonymous=True)
    
    rospy.loginfo("GUI_NODE: Waiting for user details and game setup...")
    # Wait for user_name param to be set by game_node (after info_user input)
    while not rospy.has_param('user_name') and not rospy.is_shutdown():
        rospy.sleep(0.5)
    
    if rospy.is_shutdown():
        return
    
    rospy.loginfo("GUI_NODE: ✓ User details received. Waiting for difficulty and color selection...")
    rospy.loginfo("GUI_NODE: The difficulty selection window should appear now.")
    
    # Wait for difficulty and color to be selected
    # This ensures we don't start the game until everything is ready
    wait_count = 0
    while not rospy.has_param('ready_to_start_game') and not rospy.is_shutdown():
        rospy.sleep(0.5)
        wait_count += 1
        if wait_count % 8 == 0:
            rospy.loginfo("GUI_NODE: Still waiting for difficulty and color selection...")
    
    if rospy.is_shutdown():
        return
    
    rospy.loginfo("GUI_NODE: ✓ Difficulty and color selected! Waiting for difficulty_select_gui to close...")
    
    # Wait longer to ensure difficulty_select_gui window has fully closed
    # and user can see the transition
    rospy.sleep(2.0)
    
    rospy.loginfo("GUI_NODE: Launching game GUI now...")
    
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

