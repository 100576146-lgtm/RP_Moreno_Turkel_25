# Quick Start Guide

## ✅ Project Status: ALL SYSTEMS OPERATIONAL

All components have been verified and are working correctly.

## Running the Game

### Standalone (Without ROS)
```bash
cd ~/RP_Moreno_Turkel_25
python3 mario_platformer.py
```

### With ROS Integration

**Terminal 1: Start ROS Master**
```bash
source /opt/ros/noetic/setup.bash
roscore
```

**Terminal 2: Launch All Nodes**
```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
roslaunch ros_nodes game_launcher.launch
```

**Terminal 3: Test Services (Optional)**
```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash

# Set difficulty (must be in phase1)
rosservice call /difficulty "level_number: 5"

# Get user score
rosservice call /user_score "user_name: 'TestUser'"

# Check parameters
rosparam get /ros_game_node/screen_param
```

## Project Structure

```
RP_Moreno_Turkel_25/
├── mario_platformer.py          # Entry point
├── src/                          # All Python source files
│   ├── game.py                   # Main game loop
│   ├── entities.py               # Player, enemies, platforms
│   ├── background.py             # Background rendering
│   ├── camera.py                 # Camera system
│   ├── audio.py                  # Sound manager
│   ├── constants.py               # Game constants
│   ├── levels.py                 # Level loading
│   └── ui.py                     # UI components
├── level_defs/                   # 10 level definitions
├── game images/                  # All image assets
└── README.md                     # Full documentation

catkin_ws/src/ros_nodes/
├── ros_game_node.py              # Main ROS game node
├── result_game.py                # Result node (service client)
├── info_user_gui.py             # User input GUI
├── control_node.py              # Keyboard control
├── difficulty_select_gui.py     # Difficulty selection GUI
├── srv/                         # ROS services
│   ├── GetUserScore.srv
│   └── SetGameDifficulty.srv
├── msg/                         # ROS messages
│   └── user_msg.msg
└── launch/                      # Launch files
    └── game_launcher.launch
```

## Verification

Run the diagnostic script to verify everything:
```bash
cd ~/RP_Moreno_Turkel_25
python3 test_project.py
```

All tests should pass ✓

## Troubleshooting

### Game Won't Start
1. Check Python version: `python3 --version` (needs 3.8+)
2. Install dependencies: `pip install -r requirements.txt`
3. Run diagnostic: `python3 test_project.py`

### ROS Nodes Won't Start
1. Build workspace: `cd ~/catkin_ws && catkin_make`
2. Source workspace: `source ~/catkin_ws/devel/setup.bash`
3. Check roscore is running: `roscore`

### Services Not Found
1. Verify ros_game_node is running: `rosnode list | grep ros_game_node`
2. Rebuild workspace: `cd ~/catkin_ws && catkin_make`
3. Source workspace: `source ~/catkin_ws/devel/setup.bash`

## Level Order

1. The Big Melt-down (Easy)
2. Moss-t Be Joking (Easy)
3. Smelted Dreams (Easy)
4. Frost and Furious (Medium)
5. Boo Who? (Medium)
6. Pasta La Vista (Medium)
7. 404: Floor Not Found (Hard)
8. Concrete Jungle (Hard)
9. Kraken Me Up (Hard)
10. Neon Night (Hard)

## Difficulty Selection

- **Easy**: Levels 1-3 (starts at Level 1)
- **Medium**: Levels 4-6 (starts at Level 4)
- **Hard**: Levels 7-10 (starts at Level 7)

Use the difficulty selection GUI or call the service directly.

