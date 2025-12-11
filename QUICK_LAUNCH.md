# Quick Launch Guide - Rat Race ROS Game

## 🚀 Fastest Way to Launch

### Step 1: Start ROS Master
Open **Terminal 1** and run:
```bash
roscore
```

### Step 2: Launch All Nodes
Open **Terminal 2** and run:
```bash
cd ~/RP_Moreno_Turkel_25
./launch_game.sh
```

That's it! The script will:
- ✅ Check if ROS is installed
- ✅ Verify roscore is running
- ✅ Set up environment automatically
- ✅ Launch all required nodes

## 📋 What Gets Launched

The launch file starts these **5 required ROS nodes**:

1. **INFO_USER** (`info_user_gui.py`)
   - Collects player information (name, username, age)
   - Publishes to `user_information` topic

2. **GAME_NODE** (`game_node.py`)
   - Main game logic with 3 phases:
     - **Phase 1 (Welcome)**: Receives user info, prints welcome message
     - **Phase 2 (Game)**: Receives keyboard control, manages gameplay
     - **Phase 3 (Final)**: Calculates score, publishes to `result_information`
   - Subscribes to: `user_information`, `keyboard_control`
   - Publishes to: `result_information`
   - Services: `user_score`, `difficulty`

3. **RESULT_NODE** (`result_game.py`)
   - Displays final game results
   - Subscribes to: `user_information`, `result_information`
   - Calls `user_score` service

4. **CONTROL_NODE** (`control_node_pygame.py`)
   - Keyboard control with real-time visual feedback
   - Publishes to: `keyboard_control` topic
   - Values: "UP", "DOWN", "LEFT", "RIGHT" (all caps)

5. **GUI_NODE** (`gui_node.py`)
   - Launches the visual Pygame game window

**Additional GUI nodes:**
- `difficulty_select_gui.py` - Difficulty and color selection
- `info_user_gui.py` - User input GUI

## 🔧 Manual Launch (Alternative)

If the script doesn't work, launch manually:

```bash
# Terminal 1
roscore

# Terminal 2
cd ~/RP_Moreno_Turkel_25
source ~/catkin_ws/devel/setup.bash  # If using catkin workspace
roslaunch ros_nodes game.launch
```

## ✅ Verification Checklist

After launching, verify:

1. **All nodes are running:**
   ```bash
   rosnode list
   ```
   Should show: `info_user`, `game_node`, `result_node`, `control_node`, `gui_game_node`, etc.

2. **Topics are active:**
   ```bash
   rostopic list
   ```
   Should show: `/user_information`, `/keyboard_control`, `/result_information`

3. **Services are available:**
   ```bash
   rosservice list
   ```
   Should show: `/user_score`, `/difficulty`

4. **Parameters are set:**
   ```bash
   rosparam list
   ```
   Should show: `/game_node/change_player_color`, `/screen_param`, `/user_name`

## 🎮 How to Play

1. **Enter your information** in the INFO_USER GUI window
2. **Select difficulty and color** in the difficulty selection GUI
3. **Use the CONTROL_NODE window** (small Pygame window) to control the player with arrow keys
4. **Play the game** in the main game window
5. **See results** in the terminal when the game ends

## 🐛 Troubleshooting

### "roscore not found"
- Install ROS: http://wiki.ros.org/ROS/Installation
- Source ROS: `source /opt/ros/noetic/setup.bash`

### "ROS Master not running"
- Start roscore in a separate terminal first

### "Launch file not found"
- Make sure you're in the project directory: `cd ~/RP_Moreno_Turkel_25`
- Check launch file exists: `ls ros_nodes/launch/game.launch`

### "Nodes not executable"
- Run: `chmod +x ros_nodes/*.py`

### "Package not found"
- If using catkin workspace: `cd ~/catkin_ws && catkin_make && source devel/setup.bash`
- Or add to ROS_PACKAGE_PATH: `export ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH:$(pwd)`

## 📚 More Information

See `README.md` for complete documentation including:
- Detailed node communication flow
- Service definitions
- Parameter descriptions
- Technical requirements compliance

