#!/usr/bin/env python3
"""
Project Diagnostic Script
Tests all components of the game and ROS integration
"""

import sys
import os

print("=" * 60)
print("PROJECT DIAGNOSTIC TEST")
print("=" * 60)

# Test 1: Check Python version
print("\n[1] Checking Python version...")
print(f"    Python: {sys.version}")

# Test 2: Check core game imports
print("\n[2] Testing core game imports...")
try:
    sys.path.insert(0, 'src')
    from game import Game
    from entities import Player, Enemy, Platform
    from background import Background
    from camera import Camera
    from audio import SoundManager
    from constants import SCREEN_WIDTH, SCREEN_HEIGHT
    from levels import load_levels
    from ui import UI
    print("    ✓ All core modules imported successfully")
except Exception as e:
    print(f"    ✗ Import error: {e}")
    sys.exit(1)

# Test 3: Check level loading
print("\n[3] Testing level loading...")
try:
    levels = load_levels()
    print(f"    ✓ Loaded {len(levels)} levels")
    for i, level in enumerate(levels):
        print(f"      {i+1}. {level['theme']['name']}")
except Exception as e:
    print(f"    ✗ Level loading error: {e}")
    sys.exit(1)

# Test 4: Check image paths
print("\n[4] Testing image paths...")
game_images_dir = os.path.join(os.path.dirname(__file__), "game images")
if os.path.exists(game_images_dir):
    print(f"    ✓ Game images directory exists: {game_images_dir}")
    images = [f for f in os.listdir(game_images_dir) if f.endswith(('.jpeg', '.png'))]
    print(f"    ✓ Found {len(images)} image files")
else:
    print(f"    ✗ Game images directory not found: {game_images_dir}")

# Test 5: Check level_defs
print("\n[5] Testing level definitions...")
level_defs_dir = os.path.join(os.path.dirname(__file__), "level_defs")
if os.path.exists(level_defs_dir):
    level_files = [f for f in os.listdir(level_defs_dir) if f.startswith('level_') and f.endswith('.py')]
    print(f"    ✓ Found {len(level_files)} level definition files")
else:
    print(f"    ✗ Level definitions directory not found")

# Test 6: Check Game initialization
print("\n[6] Testing Game initialization...")
try:
    game = Game(fullscreen=False)
    print("    ✓ Game initialized successfully")
    print(f"    ✓ Screen size: {game.screen_width}x{game.screen_height}")
    print(f"    ✓ Current level: {game.current_level}")
    print(f"    ✓ State: {game.state}")
except Exception as e:
    print(f"    ✗ Game initialization error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Check ROS imports (if available)
print("\n[7] Testing ROS imports...")
try:
    catkin_ws = os.path.expanduser("~/catkin_ws")
    if os.path.exists(catkin_ws):
        sys.path.insert(0, os.path.join(catkin_ws, "devel", "lib", "python3", "dist-packages"))
        from ros_nodes.srv import GetUserScore, SetGameDifficulty
        from ros_nodes.msg import user_msg
        print("    ✓ ROS messages/services imported successfully")
    else:
        print("    ⚠ Catkin workspace not found (ROS testing skipped)")
except Exception as e:
    print(f"    ⚠ ROS imports failed (may not be sourced): {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print("\nIf all tests passed, the game should work!")
print("To run the game: python3 mario_platformer.py")
print("To run with ROS: See README.md for ROS setup instructions")

