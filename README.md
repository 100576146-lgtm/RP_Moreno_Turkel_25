# Rat Race - A Cheesy Adventure

A pygame-based platformer game inspired by the original Mario games.

## Features

- **Animal-like Character**: Purple creature with ears, paws, and expressive eyes that look in the direction you're moving
- **Multiple Enemy Types**: 
  - Basic spiky enemies that patrol platforms
  - Fast enemies that move quickly
  - Big enemies that are larger and more intimidating
  - Jumper enemies that hop around unpredictably
- **Sound Effects**: Properly balanced audio feedback for jumping, collecting coins, defeating enemies, and taking damage
- **Progressive Difficulty**: More enemies are added as your score increases, making the game progressively harder
- **Enhanced Main Menu**: Beautiful start screen with styled buttons and game instructions
- **Improved Game Over Screen**: Polished death menu with score summary, level reached, and styled navigation buttons
- **Varied Powerups**: Soft golden coins with gentle sparkle effects that give extra lives
- **Enhanced Scenic Background**: Improved mountain landscapes with better parallax scrolling, realistic cloud shapes, and smoother gradients
- **Pastel Color Scheme**: Easy-on-the-eyes soft colors throughout the game
- **Multiple Platform Types**: Normal grass platforms, cloud platforms, ice platforms, and moving platforms
- **Obstacles**: Dangerous spikes that damage the player
- **Diverse Plant Life**: Large trees, colorful bushes, and beautiful flowers scattered throughout
- **Enhanced Gameplay**: More intricate level design with varied challenges
- **Scrolling Camera**: Follows the player through a large, detailed level
- **Lives System**: Start with 3 lives, lose one when hit by enemies, obstacles, or falling off the level
- **Score System**: Earn points by defeating enemies and collecting powerups
- **Performance Optimized**: Sprite culling and background caching for smooth gameplay
- **Resizable Window**: Window can be resized by dragging edges, with fullscreen support (F11)

## Controls

- **Movement**: Arrow keys or WASD
- **Jump**: Spacebar, Up arrow, or W key
- **Menu Navigation**: 
  - SPACE or ENTER to start game from main menu
  - ESC to pause game or return to menu
  - R or SPACE to restart from game over screen
  - M to return to main menu from game over screen
- **Display Options**:
  - F11 to toggle fullscreen mode
  - Resize the window by dragging its edges (windowed mode only)

## How to Run

Prerequisites:
- Python 3.8+ installed
- Recommended: create and activate a virtual environment

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the game (from the repository root):
```bash
python3 mario_platformer.py
```

On Windows, you can also use:
```powershell
py -3 mario_platformer.py
```

Alternatively, you can run the file directly by launching `mario_platformer.py` on your IDE.

## Project Structure

```
RP_Moreno_Turkel_25/
  mario_platformer.py    # Simple entry point to run the game
  src/                   # All Python source files
    game.py              # Main game (full-featured) entry and loop
    entities.py          # Player, Enemy, Platform, Powerup, Obstacle, etc.
    background.py        # Gradient skies and themed backgrounds
    camera.py            # Camera tracking and level bounds
    audio.py             # Audio helpers (pygame mixer)
    constants.py         # Shared constants: physics, colors, dimensions
    levels.py            # Level loading helpers
    ui.py                # UI components
    sprite_animator.py   # Sprite animation management
    sprite_analyzer.py   # Sprite sheet analysis and cropping
    smart_level_generator.py  # Level generation utilities
  level_defs/            # Per-level definitions (width/height/theme)
    level_01.py through level_10.py
  game images/           # All image assets
    *.jpeg, *.png        # Background and character images
    sprites_sheet_1/      # Cropped sprite frames
    Sprites.png          # Main sprite sheet
  requirements.txt       # Python dependencies
  README.md              # This file
```

## Developer Guide

- Entry point: run `python3 mario_platformer.py`
- Game loop lives in `game.py` (`Game.update` / `Game.draw`)
- Player physics and collisions in `entities.py` (`Player` class)
- Add new enemies in `entities.py` (`Enemy` variants)
- Level themes come from `level_defs/level_*.py` and `levels.py`
- Camera clamps to level width via `camera.py`

### Contributing

1. Create a virtualenv and install requirements
2. Make changes with clear docstrings and small commits
3. Test by running the game locally
4. Submit PRs with a brief description and screenshots if UI-related

## Gameplay

- Navigate through the level by jumping on platforms
- Jump on enemies (brown rectangles) to defeat them and earn 100 points
- Collect powerups (golden coins) to gain extra lives and earn 200 points
- Jump on different types of platforms - some are clouds, some are icy, and some move!
- Avoid touching enemies from the side or you'll lose a life
- Watch out for spike obstacles on the ground - they'll hurt you!
- Don't fall off the bottom of the level or you'll lose a life
- Game ends when you run out of lives - press R to restart

## Game Elements

- **Animal Character**: Purple creature with triangular ears, paw pads, and a pink nose
- **Varied Enemy Types**:
  - **Basic Enemies**: Coral-colored with spikes, patrol platforms
  - **Fast Enemies**: Smaller, pink, move quickly
  - **Big Enemies**: Large with prominent spikes, slow but intimidating
  - **Jumper Enemies**: Spring-like creatures that hop unpredictably
- **Varied Platforms**: 
  - Normal grass-topped platforms with earthy textures
  - Fluffy white cloud platforms
  - Crystalline ice platforms with sparkles
  - Moving platforms that slide back and forth
- **Soft Golden Coins**: Gentle yellow coins with cream highlights and star sparkles
- **Rich Plant Life**: 
  - Large trees with multiple leaf clusters
  - Colorful bushes with detailed foliage
  - Beautiful flowers with colorful petals
- **Spike Obstacles**: Sharp ground spikes that damage the player
- **Scenic Background**: 
  - Gradient sky from lavender to soft blue
  - Layered mountains with parallax scrolling
  - Floating white clouds that drift slowly
- **Progressive Gameplay**: Difficulty increases every 1000 points with more enemies

The level is much larger than the screen and the camera will follow you as you progress through it!

---

## ROS Integration

This project includes ROS (Robot Operating System) nodes for distributed game control and communication.

### ROS Architecture

The game is controlled through five ROS nodes that communicate via topics:

#### Nodes

1. **info_user** - Collects player information (name, username, age) from terminal input
2. **game_node** - Main game logic node with three phases:
   - Welcome: Receives and displays player information
   - Game: Processes movement commands and manages gameplay
   - Final: Calculates and publishes final score
3. **control_node** - Terminal-based keyboard control (arrow keys)
4. **control_node_pygame** - Pygame-based keyboard control (arrow keys)
5. **result_game** - Displays final game results with score and username

#### Topics

- **user_information** (`ros_nodes/msg/user_msg`) - Player information (name, username, age)
- **keyboard_control** (`std_msgs/String`) - Movement commands ("UP", "DOWN", "LEFT", "RIGHT")
- **result_information** (`std_msgs/Int64`) - Final game score

#### Custom Messages

- **user_msg** - Contains:
  - `string name` - Player's name
  - `string username` - Player's username
  - `int64 age` - Player's age

#### Services

1. **GetUserScore** (`user_score`)
   - Returns the percentage of the score when it receives the user's name.
   - Request: `string name`
   - Response: `float32 score_percentage`

2. **SetGameDifficulty** (`difficulty`)
   - Changes the difficulty of the game (only in Welcome phase).
   - Request: `string difficulty` ("easy", "medium", "hard")
   - Response: `bool success`, `string message`

#### Parameters (game_node)

- `user_name` (string): Stores the user's name.
- `change_player_color` (int64): Change player color (1: Red, 2: Purple, 3: Blue).
- `screen_param` (string): Shows the game phase (phase1, phase2, phase3).

### Prerequisites for ROS

1. **ROS Installation**: 
   - ROS Noetic (Ubuntu 20.04) or ROS Melodic (Ubuntu 18.04)
   - Install ROS following the official guide: http://wiki.ros.org/ROS/Installation

2. **ROS Dependencies**:
   ```bash
   # For ROS Noetic
   sudo apt-get install ros-noetic-rospy ros-noetic-std-msgs
   
   # For ROS Melodic
   sudo apt-get install ros-melodic-rospy ros-melodic-std-msgs
   ```

3. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Build ROS Package** (if using catkin workspace):
   ```bash
   cd ~/catkin_ws/src
   # Copy or link the ros_nodes directory here
   cd ~/catkin_ws
   catkin_make
   source devel/setup.bash
   ```

### Running ROS Nodes

#### Option 1: Using ROS Launch (Recommended)

1. **Start ROS Master**:
   ```bash
   roscore
   ```

2. **Launch all nodes**:
   ```bash
   # Launch the complete game
   roslaunch ros_nodes game.launch
   ```
   Note: `info_user` and `control_node` will open in separate terminals if possible.

#### Option 2: Using Python Module Import

If you've built the ROS package in a catkin workspace:

```bash
source ~/catkin_ws/devel/setup.bash
rosrun ros_nodes info_user.py
rosrun ros_nodes game_node.py
rosrun ros_nodes control_node.py
rosrun ros_nodes control_node_pygame.py
rosrun ros_nodes result_game.py
```

### Node Communication Flow

1. **info_user** publishes player information → **user_information** topic
2. **game_node** subscribes to **user_information** → enters Welcome phase
3. **control_node** or **control_node_pygame** publishes movement → **keyboard_control** topic
4. **game_node** subscribes to **keyboard_control** → processes movement in Game phase
5. **game_node** calculates score → publishes to **result_information** topic
6. **result_game** subscribes to both **user_information** and **result_information** → displays final result
7. **result_game** calls **user_score** service → gets percentage score

### Control Node Usage

#### control_node (Terminal-based)
- Use arrow keys to send movement commands
- Press 'q' to quit
- Works in terminal without GUI

#### control_node_pygame (Pygame-based)
- Use arrow keys to send movement commands
- Supports continuous key holding
- Press ESC to quit
- Requires pygame (already in requirements.txt)

### Logging

All nodes include comprehensive logging:
- Node initialization messages
- Phase transitions in game_node
- Message publishing/receiving events
- Error handling and shutdown messages

### Troubleshooting

1. **"No module named 'ros_nodes'"**:
   - Ensure ROS_PACKAGE_PATH includes the project directory
   - Or build the package in a catkin workspace

2. **"Topic not found"**:
   - Ensure roscore is running
   - Check that all nodes are started in the correct order

3. **"Permission denied"**:
   - Make nodes executable: `chmod +x ros_nodes/*.py`

4. **Control node not responding**:
   - For control_node: Ensure terminal has focus
   - For control_node_pygame: Ensure pygame window has focus

### ROS Package Structure

```
ros_nodes/
  ├── __init__.py
  ├── package.xml          # ROS package metadata
  ├── CMakeLists.txt       # ROS build configuration
  ├── launch/
  │   └── game.launch      # Main launch file
  ├── msg/
  │   └── user_msg.msg     # Custom message definition
  ├── srv/
  │   ├── GetUserScore.srv      # Service definition
  │   └── SetGameDifficulty.srv # Service definition
  ├── info_user.py         # User information node
  ├── game_node.py         # Main game logic node
  ├── control_node.py      # Terminal keyboard control
  ├── control_node_pygame.py  # Pygame keyboard control
  └── result_game.py       # Result display node
```

### Technical Implementation Details

- **No Global Variables**: All nodes use class-based architecture with encapsulated state
- **Modular Design**: Each node is self-contained in a separate file
- **Phase-based Game Logic**: game_node implements phases as separate methods
- **ROS Message Types**: Uses standard ROS messages and custom user_msg
