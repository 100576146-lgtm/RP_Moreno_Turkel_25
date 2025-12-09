# How to Launch the Game

## Quick Start

### Terminal 1: Start ROS Core
```bash
roscore
```

### Terminal 2: Launch the Game
```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
roslaunch ros_nodes game.launch
```

## Complete Launch Sequence

### Step 1: Start ROS Core (Terminal 1)
```bash
roscore
```

### Step 2: Source ROS and Launch (Terminal 2)
```bash
# Source ROS environment
source /opt/ros/noetic/setup.bash

# Source catkin workspace
source ~/catkin_ws/devel/setup.bash

# Launch the game
roslaunch ros_nodes game.launch
```

## What Gets Launched

The `game.launch` file launches the following nodes:

1. **result_node** - Displays final game results
2. **game_node** - Main game logic with services and parameters
3. **gui_game_node** - Launches the visual game (mario_platformer.py)
4. **info_user** - GUI for collecting user information (name, username, age)
5. **control_node** - Keyboard control node (runs in separate terminal)

## Expected Flow

1. **User Info GUI** appears first - Enter your name, username, and age
2. **Main Game GUI** launches - Shows difficulty selection screen
3. **Difficulty Selection** - Choose Easy (1), Medium (2), or Hard (3)
4. **Player Color Selection** - Press R (Red), P (Purple), or B (Blue)
5. **Game Starts** - Play through the levels!

## Troubleshooting

If you get errors:

1. **Make sure roscore is running**:
   ```bash
   roscore
   ```

2. **Rebuild the catkin workspace**:
   ```bash
   cd ~/catkin_ws
   catkin_make
   source devel/setup.bash
   ```

3. **Check if all files are in place**:
   ```bash
   ls ~/catkin_ws/src/ros_nodes/*.py
   ls ~/catkin_ws/src/ros_nodes/launch/
   ```

4. **Verify ROS can find the package**:
   ```bash
   source ~/catkin_ws/devel/setup.bash
   rospack find ros_nodes
   ```

## Alternative: One-Line Launch Script

You can create a launch script for convenience:

```bash
#!/bin/bash
# save as ~/launch_game.sh

source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
roslaunch ros_nodes game.launch
```

Make it executable:
```bash
chmod +x ~/launch_game.sh
```

Then run:
```bash
~/launch_game.sh
```

