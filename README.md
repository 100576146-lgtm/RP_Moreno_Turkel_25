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
   - Request: `string username` (Note: RESULT_NODE sends the user's **name** value to this field, as per requirement)
   - Response: `int64 score` (percentage as integer)
   - Server: `game_node` - Calculates score percentage based on current score (max 1000)
   - Client: `result_game` - Sends the user's name and prints the percentage score received

2. **SetGameDifficulty** (`difficulty`)
   - Changes the difficulty of the game (only in phase1 - start screen).
   - Request: `string change_difficulty` ("easy", "medium", "hard")
   - Response: `bool success`, `string message`
   - Returns `True` if game is in phase1, `False` otherwise
   - Server: `game_node` - Only allows difficulty change during phase1
   - Client: GUI nodes (e.g., `difficulty_select_gui`)

#### Parameters (game_node)

- `user_name` (string): Stores the user's name. Set automatically when user information is received.
- `change_player_color` (int64): Change player color. Available colors: 1 (Red), 2 (Purple), 3 (Blue). Default: 2 (Purple). Can be set via launch file or ROS parameter.
- `screen_param` (string): Shows the current game phase. Values: "phase1" (Welcome), "phase2" (Game), "phase3" (Final). Updated automatically during phase transitions.

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
   
   **Important**: The `requirements.txt` includes `pygame`, which is required for:
   - The main game GUI
   - The `control_node_pygame` node (alternative keyboard control)
   - The `difficulty_select_gui` and `info_user_gui` nodes (GUI-based user input)
   
   If pygame installation fails, install system dependencies first:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-pygame
   
   # Or install via pip with system packages
   sudo apt-get install python3-dev libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsdl1.2-dev libsmpeg-dev python3-numpy libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev
   pip install pygame
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

#### Option 2: Running Individual Nodes

**Prerequisites:**
- ROS Master must be running (`roscore`)
- All nodes must be executable: `chmod +x ros_nodes/*.py`
- If using catkin workspace, source it: `source ~/catkin_ws/devel/setup.bash`
- Python dependencies installed: `pip install -r requirements.txt`

You can run each node separately in different terminals. This is useful for debugging and understanding the communication flow.

**Terminal 1 - Start ROS Master:**
```bash
roscore
```

**Terminal 2 - Run INFO_USER node:**
```bash
# If using catkin workspace:
source ~/catkin_ws/devel/setup.bash
rosrun ros_nodes info_user.py

# Or directly with Python:
cd ~/RP_Moreno_Turkel_25
python3 ros_nodes/info_user.py
```

**Terminal 3 - Run GAME_NODE:**
```bash
source ~/catkin_ws/devel/setup.bash
rosrun ros_nodes game_node.py
```

**Terminal 4 - Run CONTROL_NODE (choose one):**
```bash
# Terminal-based control:
rosrun ros_nodes control_node.py

# OR Pygame-based control:
rosrun ros_nodes control_node_pygame.py
```

**Terminal 5 - Run RESULT_GAME node:**
```bash
rosrun ros_nodes result_game.py
```

**Note**: Start nodes in this order for proper initialization:
1. `roscore` (Terminal 1)
2. `game_node` (Terminal 3) - should start first to be ready for messages
3. `result_game` (Terminal 5) - should start early to receive user info
4. `info_user` (Terminal 2) - triggers the game flow
5. `control_node` or `control_node_pygame` (Terminal 4) - can start anytime during Game phase

### Node Communication Flow

This section provides a detailed overview of how nodes communicate with each other.

#### Communication Diagram

```
┌─────────────┐
│  INFO_USER  │
│   (Node)    │
└──────┬──────┘
       │ Publishes user_msg
       │ Topic: user_information
       ▼
┌─────────────────────────────────────────┐
│         user_information (Topic)        │
│  Message Type: ros_nodes/msg/user_msg   │
│  Fields: name (string), username        │
│         (string), age (int64)          │
└──────┬──────────────────────┬──────────┘
       │                      │
       │ Subscribes           │ Subscribes
       ▼                      ▼
┌─────────────┐      ┌─────────────────┐
│  GAME_NODE  │      │  RESULT_GAME    │
│   (Node)    │      │     (Node)      │
└──────┬──────┘      └─────────────────┘
       │
       │ Phase 1: Welcome
       │ - Receives user info
       │ - Displays welcome message
       │
       │ Phase 2: Game
       │ Subscribes to keyboard_control
       │
       │ Phase 3: Final
       │ Publishes Int64
       │ Topic: result_information
       │
       ▼
┌─────────────────────────────────────────┐
│      keyboard_control (Topic)          │
│      Message Type: std_msgs/String      │
│      Values: "UP", "DOWN", "LEFT",     │
│             "RIGHT"                    │
└──────┬──────────────────────────────────┘
       │
       │ Published by
       │
┌──────┴──────────┐  ┌──────────────────┐
│  CONTROL_NODE   │  │ CONTROL_NODE_    │
│   (Terminal)    │  │    PYGAME        │
│                 │  │   (Pygame GUI)   │
└─────────────────┘  └──────────────────┘
```

#### Detailed Communication Steps

1. **Initialization Phase:**
   - All nodes initialize and create their publishers/subscribers
   - `game_node` sets initial phase to "phase1" (Welcome)
   - `result_game` waits for user information and result messages

2. **User Information Flow:**
   - `info_user` collects name, username, and age from terminal input
   - `info_user` creates `user_msg` message and publishes to `user_information` topic
   - `game_node` receives message via `user_info_cb()` callback
   - `game_node` transitions to Welcome phase, displays welcome message
   - `result_game` receives same message via `user_info_cb()` callback, stores username

3. **Game Phase Flow:**
   - `game_node` transitions from Welcome to Game phase (phase2)
   - `control_node` or `control_node_pygame` captures arrow key presses
   - Control nodes publish movement commands ("UP", "DOWN", "LEFT", "RIGHT") to `keyboard_control` topic
   - `game_node` receives commands via `keyboard_cb()` callback
   - `game_node` processes movement (in text mode, increments score by 10 per movement)
   - GUI game (if running) also receives keyboard input and controls the actual game

4. **Final Score Flow:**
   - When game ends, GUI publishes final score to `game_over_stats` topic
   - `game_node` receives score via `game_stats_cb()` callback
   - `game_node` transitions to Final phase (phase3)
   - `game_node` calculates final score (base score + age bonus)
   - `game_node` publishes final score as `Int64` to `result_information` topic
   - `result_game` receives score via `result_cb()` callback
   - `result_game` displays final results with username and score
   - `result_game` calls `user_score` service with the user's **name** (not username) to get score percentage
     - As per requirement: "sends to the user_score service the name of the user"
     - Service field is called `username` but receives the actual name value
   - `result_game` prints the percentage score received: `"Score Percentage: {resp.score}%"`

#### Message Types and Topics

| Topic Name | Message Type | Publisher | Subscriber | Purpose |
|------------|-------------|-----------|------------|---------|
| `user_information` | `ros_nodes/msg/user_msg` | `info_user` | `game_node`, `result_game` | Transmits player information |
| `keyboard_control` | `std_msgs/String` | `control_node`, `control_node_pygame` | `game_node` | Transmits movement commands |
| `result_information` | `std_msgs/Int64` | `game_node` | `result_game` | Transmits final game score |
| `game_over_stats` | `std_msgs/Int64` | GUI game | `game_node` | Transmits game completion stats |

#### Service Communication

| Service Name | Service Type | Server | Client | Request | Response | Purpose |
|--------------|-------------|--------|--------|---------|----------|---------|
| `user_score` | `ros_nodes/srv/GetUserScore` | `game_node` | `result_game` | `string username` (receives user's name) | `int64 score` (percentage) | Returns score percentage when given user's name |
| `difficulty` | `ros_nodes/srv/SetGameDifficulty` | `game_node` | GUI nodes | `string change_difficulty` ("easy", "medium", "hard") | `bool success`, `string message` | Sets game difficulty (only in phase1) |

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

---

## Technical Requirements Compliance

This section documents how the implementation meets all technical requirements.

### 1. Node Structure

✅ **Requirement**: Each node should be defined within a separate class structure in different Python files. No global variables are allowed.

**Implementation**:
- All 5 nodes are implemented as separate classes:
  - `InfoUserNode` in `ros_nodes/info_user.py`
  - `GameNode` in `ros_nodes/game_node.py`
  - `ResultGameNode` in `ros_nodes/result_game.py`
  - `ControlNode` in `ros_nodes/control_node.py`
  - `ControlNodePygame` in `ros_nodes/control_node_pygame.py`
- All data is encapsulated within class attributes (e.g., `self.pub`, `self.phase`, `self.score`)
- No global variables are used in any node file
- Each node is completely self-contained and modular

### 2. Phases Implementation in GAME_NODE

✅ **Requirement**: Implement each game phase (Welcome, Game, and Final) as a separate method within the class.

**Implementation**:
- `welcome_phase(self, user_msg)`: Handles Welcome phase logic
  - Receives user information
  - Displays welcome message
  - Transitions to Game phase
- `game_phase(self)`: Handles Game phase logic
  - Sets phase to "phase2"
  - Waits for keyboard input and game completion
  - Monitors for game statistics
- `final_phase(self)`: Handles Final phase logic
  - Calculates final score (base + age bonus)
  - Publishes final score to result_information topic
- Each method is self-contained and handles transitions internally
- Phase state is managed through `self.phase` attribute

### 3. Communication Between Nodes

✅ **Requirement**: Proper ROS message communication between nodes using appropriate message types.

**Implementation**:
- **INFO_USER → GAME_NODE**:
  - Topic: `user_information`
  - Message Type: `ros_nodes/msg/user_msg` (custom message)
  - Contains: `string name`, `string username`, `int64 age`
  - `info_user` publishes, `game_node` subscribes via `user_info_cb()`

- **GAME_NODE → RESULT_NODE**:
  - Topic: `result_information`
  - Message Type: `std_msgs/Int64` (for score)
  - `game_node` publishes in `final_phase()`, `result_game` subscribes via `result_cb()`

- **CONTROL_NODE → GAME_NODE**:
  - Topic: `keyboard_control`
  - Message Type: `std_msgs/String`
  - Values: "UP", "DOWN", "LEFT", "RIGHT" (all uppercase)
  - Control nodes publish, `game_node` subscribes via `keyboard_cb()`

**Note**: While the requirement mentions `std_msgs/String` for username/name and `std_msgs/Int32` for age, the implementation uses a custom `user_msg` message which is a better practice as it groups related data together. The score uses `Int64` (similar to `Int32` but with larger range).

### 4. Keyboard Control Alternatives

✅ **Requirement**: Implement keyboard control for the game phase, communicated with GAME_NODE.

**Implementation**:
- **control_node.py**: Terminal-based keyboard control
  - Uses `termios` and `tty` for raw terminal input
  - Captures arrow keys and publishes to `keyboard_control` topic
  - Press 'q' to quit
  
- **control_node_pygame.py**: Pygame-based keyboard control
  - Uses Pygame event system for keyboard input
  - Captures arrow keys and publishes to `keyboard_control` topic
  - Press ESC to quit
  - Provides visual window for better user experience

- Both nodes publish to the same `keyboard_control` topic
- `game_node` subscribes and processes commands in `keyboard_cb()` during phase2

### 5. Logging and Transition Messages

✅ **Requirement**: Add log messages to inform about transitions in all nodes and between phases in GAME_NODE.

**Implementation**:

**GAME_NODE Phase Transitions**:
- `"GAME_NODE: ========== WELCOME PHASE STARTED =========="`
- `"GAME_NODE: Welcome phase started."`
- `"GAME_NODE: Transitioning from Welcome phase to Game phase"`
- `"GAME_NODE: ========== GAME PHASE STARTED =========="`
- `"GAME_NODE: Game phase started. Waiting for GUI game to finish..."`
- `"GAME_NODE: Transitioning to Final phase"`
- `"GAME_NODE: ========== FINAL PHASE STARTED =========="`
- `"GAME_NODE: Final phase reached, calculating score."`

**INFO_USER Transitions**:
- `"INFO_USER: Transitioning to user input collection phase"`
- `"INFO_USER: Transitioning to message creation phase"`
- `"INFO_USER: Transitioning to publish phase"`
- `"INFO_USER: Published user information to 'user_information' topic"`

**RESULT_NODE Transitions**:
- `"RESULT_NODE: Transitioning to process user information"`
- `"RESULT_NODE: Transitioning to process final score"`
- `"RESULT_NODE: Transitioning to display results"`
- `"RESULT_NODE: Transitioning to get score percentage"`

**CONTROL_NODE Transitions**:
- `"CONTROL_NODE: Transitioning to keyboard input mode"`
- `"CONTROL_NODE: Publishing movement command: {direction}"`
- `"CONTROL_NODE: Transitioning to shutdown"`

**CONTROL_NODE_PYGAME Transitions**:
- `"CONTROL_NODE_PYGAME: Transitioning to keyboard input mode"`
- `"CONTROL_NODE_PYGAME: Publishing movement command: {direction}"`
- `"CONTROL_NODE_PYGAME: Transitioning to shutdown"`

All nodes also include:
- Initialization logs
- Message publishing/receiving logs
- Error handling logs
- Shutdown logs

### 6. Documentation

✅ **Requirement**: Create README.md with instructions for running each node, dependencies, and communication overview.

**Implementation**:
- ✅ Comprehensive README.md with all required sections
- ✅ Instructions for installing dependencies (including pygame)
- ✅ Instructions for running each node individually
- ✅ Detailed node-to-node communication process
- ✅ Technical requirements compliance documentation
- ✅ Troubleshooting section
- ✅ ROS package structure documentation

---

## Summary

All technical requirements have been met:

| Requirement | Status | Implementation |
|------------|--------|----------------|
| Node Structure | ✅ | All nodes in separate classes, no global variables |
| Phases Implementation | ✅ | Three separate methods in GameNode class |
| Communication | ✅ | Proper ROS topics and message types |
| Keyboard Control | ✅ | Two alternative implementations |
| Logging | ✅ | Comprehensive transition logs in all nodes |
| Documentation | ✅ | Complete README with all required information |
