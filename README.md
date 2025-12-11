# Rat Race - A Cheesy Adventure

A pygame-based platformer game with ROS (Robot Operating System) integration for distributed game control and communication.

## Table of Contents

1. [Game Features](#game-features)
2. [Game Components and Levels](#game-components-and-levels)
3. [ROS Integration Overview](#ros-integration-overview)
4. [ROS Nodes - Detailed Specifications](#ros-nodes---detailed-specifications)
5. [ROS Topics and Messages](#ros-topics-and-messages)
6. [ROS Services](#ros-services)
7. [ROS Parameters](#ros-parameters)
8. [Quick Start - Running the Launcher](#quick-start---running-the-launcher)
9. [Running Individual Nodes](#running-individual-nodes)
10. [Launch File Details](#launch-file-details)
11. [Technical Requirements Compliance](#technical-requirements-compliance)
12. [Prerequisites](#prerequisites)
13. [Troubleshooting](#troubleshooting)

---

## About the Game

**Rat Race - A Cheesy Adventure** is a 2D side-scrolling platformer game inspired by classic Mario games. You play as a purple creature navigating through 10 themed levels filled with enemies, platforms, powerups, and obstacles. The game features smooth physics, beautiful graphics, and progressive difficulty that increases as you advance through levels.

### Game Objective

Navigate through all 10 levels, defeat enemies, collect powerups, and reach the end of each level while avoiding hazards. The game ends when you run out of lives, and your final score is calculated based on enemies defeated, powerups collected, and your age (as a bonus in ROS mode).

### How the Game Works

1. **Start**: Begin with 3 lives at Level 1
2. **Navigate**: Move through each level using arrow keys or WASD
3. **Combat**: Jump on enemies to defeat them and earn points
4. **Collect**: Gather powerups (coins) to gain extra lives and points
5. **Avoid**: Steer clear of spikes, falling off the level, and enemy contact
6. **Progress**: Complete levels to advance to the next one
7. **Survive**: Maintain your lives to continue playing

### Game Mechanics

- **Physics**: Realistic gravity and momentum-based movement
- **Jumping**: Variable jump height based on how long you hold the jump button
- **Collisions**: Precise hitbox detection for player, enemies, and platforms
- **Camera**: Smooth scrolling camera that follows the player
- **Animation**: Sprite-based animations for all characters and objects
- **Sound**: Audio feedback for all actions (jumping, collecting, defeating enemies, taking damage)

## Game Features

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

## How to Run (Standalone - Without ROS)

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

---

## Game Components and Levels

### Project Structure

```
RP_Moreno_Turkel_25/
├── mario_platformer.py          # Entry point for standalone game
├── src/                          # All Python source files
│   ├── game.py                   # Main game loop and state management
│   ├── entities.py               # Player, Enemy, Platform, Powerup, Obstacle classes
│   ├── background.py             # Gradient skies and themed backgrounds
│   ├── camera.py                 # Camera tracking and level bounds
│   ├── audio.py                  # Audio helpers (pygame mixer)
│   ├── constants.py              # Shared constants: physics, colors, dimensions
│   ├── levels.py                 # Level loading helpers
│   ├── ui.py                     # UI components
│   ├── sprite_animator.py        # Sprite animation management
│   ├── sprite_analyzer.py        # Sprite sheet analysis and cropping
│   └── smart_level_generator.py  # Level generation utilities
├── level_defs/                   # Per-level definitions (10 levels)
│   ├── level_01.py               # Level 1 definition
│   ├── level_02.py               # Level 2 definition
│   ├── ...                       # Levels 3-9
│   └── level_10.py               # Level 10 definition
├── game images/                  # All image assets
│   ├── *.jpeg, *.png             # Background and character images
│   ├── sprites_sheet_1/          # Cropped sprite frames
│   └── Sprites.png               # Main sprite sheet
├── ros_nodes/                    # ROS integration package
│   ├── __init__.py
│   ├── package.xml               # ROS package metadata
│   ├── CMakeLists.txt            # ROS build configuration
│   ├── launch/
│   │   └── game.launch           # Main launch file
│   ├── msg/
│   │   └── user_msg.msg          # Custom message definition
│   ├── srv/
│   │   ├── GetUserScore.srv      # Service definition
│   │   └── SetGameDifficulty.srv # Service definition
│   ├── info_user.py              # Terminal-based user info node
│   ├── info_user_gui.py          # GUI-based user info node
│   ├── game_node.py              # Main game logic node
│   ├── control_node.py           # Terminal keyboard control node
│   ├── control_node_pygame.py    # Pygame keyboard control node
│   ├── result_game.py            # Result display node
│   ├── gui_node.py               # Visual game GUI node
│   └── difficulty_select_gui.py  # Difficulty selection GUI node
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

### Game Levels

The game includes **9 unique levels** with different themes, challenges, and increasing difficulty:

1. **Level 1: "The Big Melt-down"** (Difficulty: 0)
   - Theme: Swiss cheese with parmesan/fondue yellow sky
   - Background Motif: Swiss cheese
   - Width: 6400px
   - Introduction level with basic enemies and simple platforming

2. **Level 2: "Moss-t Be Joking"** (Difficulty: 1)
   - Theme: Jungle/forest with misty grey and forest floor green sky
   - Background Motif: Jungle
   - Width: 7200px
   - Features extra floor enemies and jungle-themed obstacles

3. **Level 3: "Smelted Dreams"** (Difficulty: 2)
   - Theme: Forge/lava with smoke grey and forge glow sky
   - Background Motif: Cracking lava
   - Width: 8000px
   - Introduces more challenging enemy patterns

4. **Level 4: "Frost and Furious"** (Difficulty: 3)
   - Theme: Ice/glacier with glacier white and frost blue sky
   - Background Motif: Icy
   - Width: 8800px
   - Ice-themed platforms and frozen enemies

5. **Level 5: "Boo Who?"** (Difficulty: 4)
   - Theme: Ghost/spooky with midnight purple and black sky
   - Background Motif: Stars
   - Width: 9600px
   - Special: Features primarily air enemies (bats, dragons) with flight patterns
   - Enemy Focus: Air enemies (air_bat, air_dragon) are heavily weighted

6. **Level 6: "Pasta La Vista"** (Difficulty: 5)
   - Theme: Pasta/Italian with parmesan yellow and marinara red sky
   - Background Motif: Sand
   - Width: 10400px
   - Special: Features only meatball enemies (angry meatballs)
   - Unique Feature: Falling meatballs from above and ground meatballs

7. **Level 7: "404: Floor Not Found"** (Difficulty: 6)
   - Theme: Geometry Dash style with black sky
   - Background Motif: Glow
   - Width: 11200px
   - Special: Features only worm enemies and unique platforming challenges
   - Unique Feature: Multiple floor levels with gaps, worm enemies on all floors

8. **Level 8: "Kraken Me Up"** (Difficulty: 7)
   - Theme: Underwater/abyssal with murky teal and abyssal black sky
   - Background Motif: Bubbles
   - Width: 12800px
   - Features underwater enemies (sharks, piranhas, crabs)
   - Underwater Theme: Deep sea environment

9. **Level 9: "Tetris Terror"** (Difficulty: 8)
   - Theme: Tetris with soft pink and light purple sky
   - Background Motif: Glow
   - Width: 13600px
   - Features tetris block enemies and wall of death mechanics
   - Unique Feature: Tetris-themed platforms and enemies, wall of death

**Level Progression:**
- Each level increases in width (6400px to 13600px)
- Difficulty increases from 0 to 8
- Enemy density and variety increase with difficulty
- Special themed enemies appear in specific levels:
  - Level 5: Air enemies (bats, dragons) with flight patterns
  - Level 6: Only meatball enemies
  - Level 7: Only worm enemies
  - Level 8: Underwater enemies (sharks, piranhas, crabs)
- Each level has unique color schemes and backgrounds
- Background motifs include: swiss_cheese, jungle, cracking_lava, icy, stars, sand, glow, bubbles

---

## Enemies

The game features **13 different enemy types**, each with unique behaviors, sizes, speeds, and health:

### Ground Enemies

1. **Basic Enemy**
   - Size: 56x56 pixels
   - Speed: Standard (1.0x ENEMY_SPEED)
   - Health: 1 hit
   - Behavior: Patrols platforms, changes direction at edges
   - Appearance: Blobby critter with spikes, themed colors

2. **Fast Enemy**
   - Size: 44x44 pixels
   - Speed: Fast (1.5x ENEMY_SPEED)
   - Health: 1 hit
   - Behavior: Moves quickly across platforms
   - Appearance: Smaller, streamlined with pointed top

3. **Big Enemy**
   - Size: 72x72 pixels
   - Speed: Slow (0.7x ENEMY_SPEED)
   - Health: 1 hit
   - Behavior: Large and intimidating, moves slowly
   - Appearance: Large rectangular body with big eyes

4. **Jumper Enemy**
   - Size: 52x62 pixels
   - Speed: Standard (1.0x ENEMY_SPEED)
   - Health: 1 hit
   - Behavior: Hops unpredictably, can jump over gaps
   - Appearance: Taller enemy with jumping animation

5. **Double Hit Enemy**
   - Size: 64x64 pixels
   - Speed: Moderate (0.8x ENEMY_SPEED)
   - Health: 2 hits
   - Behavior: Requires two jumps to defeat, has armor plates
   - Appearance: Armored with dark grey plates, shrinks when damaged

6. **Meatball Enemy** (Level 6 exclusive)
   - Size: 64x64 pixels
   - Speed: Slow (0.6x ENEMY_SPEED)
   - Health: 1 hit
   - Behavior: Large, slow-moving meatball
   - Appearance: Round, pasta-themed

7. **Fork Enemy**
   - Size: 32x56 pixels (tall)
   - Speed: Fast (1.3x ENEMY_SPEED)
   - Health: 1 hit
   - Behavior: Tall and fast-moving
   - Appearance: Fork-shaped enemy

8. **Worm Enemy** (Level 7 exclusive)
   - Size: 80x24 pixels (long, low)
   - Speed: Moderate (0.8x ENEMY_SPEED)
   - Health: 1 hit
   - Behavior: Crawls along ground, segmented body
   - Appearance: Long worm with multiple segments

9. **Crab Enemy** (Underwater levels)
   - Size: 50x40 pixels
   - Speed: Slow (0.7x ENEMY_SPEED)
   - Health: 1 hit
   - Behavior: Slow but steady movement
   - Appearance: Crab-like enemy

10. **Tetris Block Enemy** (Level 9)
    - Size: 60x60 pixels
    - Speed: Moderate (0.8x ENEMY_SPEED)
    - Health: 1 hit
    - Behavior: Moves like tetris blocks
    - Appearance: Large tetris block shape

### Air Enemies

11. **Air Bat**
    - Size: 48x32 pixels
    - Speed: Fast (1.2x ENEMY_SPEED)
    - Health: 1 hit
    - Behavior: Flies in patterns (horizontal, circular, or zigzag)
    - Appearance: Dark bat with wings and red eyes
    - Flight Patterns: Randomly chooses horizontal, circular, or zigzag movement

12. **Air Dragon**
    - Size: 60x40 pixels
    - Speed: Moderate (0.9x ENEMY_SPEED)
    - Health: 2 hits
    - Behavior: Flies in complex patterns, requires two hits
    - Appearance: Dragon-like with wings, yellow eyes
    - Flight Patterns: More elaborate than bats

### Underwater Enemies

13. **Shark Enemy** (Underwater levels)
    - Size: 80x50 pixels
    - Speed: Fast (1.2x ENEMY_SPEED)
    - Health: 1 hit
    - Behavior: Fast swimming movement
    - Appearance: Large shark

14. **Piranha Enemy** (Underwater levels)
    - Size: 40x30 pixels
    - Speed: Very Fast (1.5x ENEMY_SPEED)
    - Health: 1 hit
    - Behavior: Very fast, small target
    - Appearance: Small piranha

### Enemy Mechanics

- **Patrol Behavior**: Ground enemies patrol platforms, changing direction at edges
- **Jumping**: Jumper enemies can jump over gaps and obstacles
- **Flight Patterns**: Air enemies use three patterns:
  - Horizontal: Straight line movement
  - Circular: Circular path around a base point
  - Zigzag: Diagonal movement pattern
- **Health System**: Most enemies have 1 health, but double-hit and air_dragon have 2
- **Damage Visuals**: Multi-hit enemies shrink when damaged
- **Themed Colors**: Enemies adapt their colors to match level themes
- **Collision**: Jumping on enemies defeats them; touching from the side damages the player

---

## Platforms and Obstacles

### Platform Types

1. **Normal Grass Platforms**
   - Standard platforms with grass texture
   - Solid, stable surfaces
   - Most common platform type

2. **Cloud Platforms**
   - Fluffy white cloud appearance
   - Can be semi-transparent
   - May have special properties

3. **Ice Platforms**
   - Crystalline ice appearance
   - May be slippery
   - Found in ice-themed levels

4. **Moving Platforms**
   - Slide back and forth horizontally
   - Require timing to jump on
   - Add dynamic challenge

5. **Fading Platforms**
   - Appear and disappear
   - Require quick timing
   - Challenge player's reflexes

6. **Spiky Platforms**
   - Have spikes on top
   - Damage player on contact
   - Require careful navigation

### Obstacles

1. **Spikes**
   - Ground-based spikes
   - Damage player on contact
   - Found throughout levels
   - Lose a life when touched

2. **Falling Hazards**
   - Falling off the bottom of the level
   - Results in losing a life
   - Must stay within level bounds

---

## Powerups and Collectibles

1. **Coins (Powerups)**
   - Golden coins with sparkle effects
   - Collect to gain extra lives
   - Worth 200 points each
   - Soft golden color with cream highlights

2. **Star Powerup**
   - Temporary invincibility
   - Lasts 10 seconds (600 frames at 60 FPS)
   - Makes player glow
   - Protects from enemy damage

3. **Big Coins**
   - Larger collectibles
   - Worth more points
   - Special appearance

4. **Checkpoints**
   - Save progress in level
   - Respawn point if player dies
   - Helpful in long levels

---

## Gameplay Mechanics

### Movement

- **Horizontal Movement**: Arrow keys (Left/Right) or WASD (A/D)
- **Jumping**: Spacebar, Up arrow, or W key
- **Variable Jump Height**: Hold jump button longer for higher jumps
- **Maximum Jump Hold**: 15 frames (0.25 seconds) for bonus height
- **Physics**: Realistic gravity and momentum-based movement
- **Speed Multiplier**: Can be adjusted for different difficulty levels

### Combat

- **Defeat Enemies**: Jump on top of enemies to defeat them
- **Points**: Earn 100 points per enemy defeated
- **Multi-hit Enemies**: Some enemies require multiple jumps
- **Star Power**: Temporary invincibility allows walking through enemies
- **Damage**: Touching enemies from the side causes damage and loses a life

### Lives and Health

- **Starting Lives**: 3 lives at game start
- **Lose Life When**:
  - Hit by enemy from the side
  - Touching spikes
  - Falling off the bottom of the level
- **Gain Lives**: Collect coins (powerups) to gain extra lives
- **Game Over**: When all lives are lost

### Scoring System

- **Enemy Defeated**: 100 points
- **Coin Collected**: 200 points
- **Progressive Difficulty**: More enemies spawn as score increases
- **Final Score**: Base score + age bonus (in ROS mode: age × 10)

### Camera System

- **Scrolling Camera**: Follows player through level
- **Smooth Movement**: Camera smoothly tracks player position
- **Level Bounds**: Camera clamps to level width
- **Parallax Background**: Background layers scroll at different speeds for depth

### Animation System

- **Sprite Animations**: All characters use sprite-based animations
- **Player Animations**: Idle, running, jumping, stomping, dying
- **Enemy Animations**: Movement, jumping (for jumper enemies), flight (for air enemies)
- **Direction Facing**: Player and enemies face the direction they're moving

### Sound System

- **Jump Sound**: Plays when player jumps
- **Coin Sound**: Plays when collecting coins/powerups
- **Enemy Kill Sound**: Plays when defeating enemies
- **Hit Sound**: Plays when player takes damage
- **Balanced Audio**: All sounds are properly balanced for gameplay

---

## Game States

The game has multiple states managed by the `GameState` enum:

1. **MENU**: Main menu screen
2. **PLAYING**: Active gameplay
3. **GAME_OVER**: Game over screen with score summary
4. **PAUSED**: Game paused (ESC key)
5. **LEVEL_COMPLETE**: Level completion screen
6. **LEVEL_SELECT**: Level selection screen
7. **LOADING**: Loading screen between levels
8. **BONUS_ROOM**: Special bonus room
9. **DIFFICULTY_SELECT**: Difficulty selection (ROS mode)
10. **VICTORY**: Victory screen after completing all levels

---

## Difficulty Settings

When playing with ROS integration, you can select difficulty:

- **Easy**: Levels 1-3 (starts at Level 1)
- **Medium**: Levels 4-6 (starts at Level 4)
- **Hard**: Levels 7-10 (starts at Level 7)

Difficulty affects:
- Enemy spawn rates
- Enemy variety
- Platform complexity
- Overall challenge level

---

## ROS Integration Overview

This project implements a complete ROS-based game control system with **5 required nodes**, **3 topics**, **1 custom message**, and **2 services**.

### ROS Architecture Summary

- **5 Nodes**: info_user, game_node, control_node, control_node_pygame, result_game
- **3 Topics**: user_information, keyboard_control, result_information
- **1 Custom Message**: user_msg (name, username, age)
- **2 Services**: user_score (GetUserScore), difficulty (SetGameDifficulty)
- **3 Parameters**: user_name, change_player_color, screen_param

---

## ROS Nodes - Detailed Specifications

### 1. INFO_USER Node

**File**: `ros_nodes/info_user.py` (Terminal) or `ros_nodes/info_user_gui.py` (GUI)

**Purpose**: Collects player information (name, username, age) and publishes it to the game system.

**Functionality**:
- Requests player's name, username, and age through terminal input (or GUI)
- Creates a `user_msg` message with the collected information
- Publishes to `user_information` topic
- Triggers the game flow by sending user data

**Publishes**:
- Topic: `user_information`
- Message Type: `ros_nodes/msg/user_msg`
- Fields: `name` (string), `username` (string), `age` (int64)

**Subscribes**: None

**Services**: None

**Parameters**: None

**How to Run**:
```bash
# Terminal version:
rosrun ros_nodes info_user.py

# GUI version (recommended):
rosrun ros_nodes info_user_gui.py
```

**Code Location**: `ros_nodes/info_user.py` or `ros_nodes/info_user_gui.py`

---

### 2. GAME_NODE (Main Game Logic Node)

**File**: `ros_nodes/game_node.py`

**Purpose**: Main game logic node that manages three phases (Welcome, Game, Final) and coordinates game flow.

**Functionality**:

#### Phase 1: Welcome
- Receives player information from INFO_USER via `user_information` topic
- **Prints the user's name** to the screen: `"Welcome {user_msg.name}!"`
- Sets `user_name` parameter with the user's name
- Sets `screen_param` to "phase1"
- Waits for difficulty selection before transitioning to Game phase

#### Phase 2: Game
- Sets `screen_param` to "phase2"
- Receives movement commands from CONTROL_NODE via `keyboard_control` topic
- Processes movement commands during gameplay
- Monitors for game completion statistics

#### Phase 3: Final
- Sets `screen_param` to "phase3"
- Calculates final score: `base_score + (age * 10)` (age bonus)
- Publishes final score to `result_information` topic as `std_msgs/Int64`
- Transitions automatically when game ends

**Publishes**:
- Topic: `result_information`
- Message Type: `std_msgs/Int64`
- Content: Final game score (base score + age bonus)

**Subscribes**:
- Topic: `user_information` (Message Type: `ros_nodes/msg/user_msg`)
- Topic: `keyboard_control` (Message Type: `std_msgs/String`)
- Topic: `game_over_stats` (Message Type: `std_msgs/Int64`) - from GUI game

**Services Provided**:
1. **`user_score`** (Type: `GetUserScore`)
   - Request: `string username` (receives user's name)
   - Response: `int64 score` (percentage as integer)
   - Calculates: `(current_score / 1000.0) * 100` as integer

2. **`difficulty`** (Type: `SetGameDifficulty`)
   - Request: `string change_difficulty` ("easy", "medium", "hard")
   - Response: `bool success`
   - Only works in phase1 (start screen)
   - Returns `True` if in phase1 and difficulty is valid, `False` otherwise

**Parameters**:
- `user_name` (string): Stores the user's name. Set automatically when user information is received.
- `change_player_color` (int64): Player color setting. Values: 1 (Red), 2 (Purple), 3 (Blue). Default: 2 (Purple).
- `screen_param` (string): Current game phase. Values: "phase1" (Welcome), "phase2" (Game), "phase3" (Final). Updated automatically.

**Class Structure**:
- Class: `GameNode`
- Methods:
  - `__init__()`: Initializes node, publishers, subscribers, services, and parameters
  - `welcome_phase(user_msg)`: Handles Welcome phase logic
  - `game_phase()`: Handles Game phase logic
  - `final_phase()`: Handles Final phase logic
  - `user_info_cb(msg)`: Callback for user_information topic
  - `keyboard_cb(msg)`: Callback for keyboard_control topic
  - `game_stats_cb(msg)`: Callback for game_over_stats topic
  - `handle_user_score(req)`: Service handler for GetUserScore
  - `handle_difficulty(req)`: Service handler for SetGameDifficulty
  - `run()`: Main execution loop (rospy.spin())

**How to Run**:
```bash
rosrun ros_nodes game_node.py
```

**Code Location**: `ros_nodes/game_node.py`

---

### 3. CONTROL_NODE (Terminal-based Keyboard Control)

**File**: `ros_nodes/control_node.py`

**Purpose**: Captures keyboard input (arrow keys) from terminal and publishes movement commands.

**Functionality**:
- Uses `termios` and `tty` for raw terminal input
- Captures arrow key presses
- Publishes movement commands to `keyboard_control` topic
- Values published: "UP", "DOWN", "LEFT", "RIGHT" (all uppercase)
- Press 'q' to quit

**Publishes**:
- Topic: `keyboard_control`
- Message Type: `std_msgs/String`
- Values: "UP", "DOWN", "LEFT", "RIGHT" (all capital letters)

**Subscribes**:
- Topic: `keyboard_control` (for bidirectional communication - receives keyboard events from game)

**Services**: None

**Parameters**: None

**How to Run**:
```bash
rosrun ros_nodes control_node.py
```

**Note**: Works best when run manually in a separate terminal. May have issues when launched via roslaunch.

**Code Location**: `ros_nodes/control_node.py`

---

### 4. CONTROL_NODE_PYGAME (Pygame-based Keyboard Control)

**File**: `ros_nodes/control_node_pygame.py`

**Purpose**: Alternative keyboard control using Pygame window (more reliable with roslaunch).

**Functionality**:
- Uses Pygame event system for keyboard input
- Provides visual window showing last command sent/received
- Captures arrow key presses
- Publishes movement commands to `keyboard_control` topic
- Values published: "UP", "DOWN", "LEFT", "RIGHT" (all uppercase)
- Press ESC to quit

**Publishes**:
- Topic: `keyboard_control`
- Message Type: `std_msgs/String`
- Values: "UP", "DOWN", "LEFT", "RIGHT" (all capital letters)

**Subscribes**:
- Topic: `keyboard_control` (for bidirectional communication - receives keyboard events from game)

**Services**: None

**Parameters**: None

**Dependencies**: Requires pygame (included in requirements.txt)

**How to Run**:
```bash
rosrun ros_nodes control_node_pygame.py
```

**Code Location**: `ros_nodes/control_node_pygame.py`

---

### 5. RESULT_GAME Node

**File**: `ros_nodes/result_game.py`

**Purpose**: Displays final game results and calls service to get score percentage.

**Functionality**:
- Receives player information from INFO_USER via `user_information` topic
- Receives final score from GAME_NODE via `result_information` topic
- Displays final message: `"GAME OVER\nUser: {username}\nScore: {score}"`
- **Calls `user_score` service** with the user's **name** (not username)
- **Prints the percentage score** received: `"Score Percentage: {score}%"`

**Publishes**: None

**Subscribes**:
- Topic: `user_information` (Message Type: `ros_nodes/msg/user_msg`)
- Topic: `result_information` (Message Type: `std_msgs/Int64`)

**Services Used**:
- **`user_score`** (Type: `GetUserScore`)
  - Sends: User's **name** (stored from `msg.name`)
  - Receives: `int64 score` (percentage)
  - Prints: `"Score Percentage: {score}%"`

**Parameters**: None

**Class Structure**:
- Class: `ResultGameNode`
- Methods:
  - `__init__()`: Initializes node and subscribers
  - `user_info_cb(msg)`: Callback for user_information topic (stores name and username)
  - `result_cb(msg)`: Callback for result_information topic (displays results and calls service)
  - `get_score_percentage()`: Calls user_score service and prints percentage
  - `run()`: Main execution loop (rospy.spin())

**How to Run**:
```bash
rosrun ros_nodes result_game.py
```

**Code Location**: `ros_nodes/result_game.py`

---

## ROS Topics and Messages

### Topic 1: user_information

**Message Type**: `ros_nodes/msg/user_msg` (Custom Message)

**Definition** (`ros_nodes/msg/user_msg.msg`):
```
string name
string username
int64 age
```

**Publisher**: INFO_USER node (`info_user.py` or `info_user_gui.py`)

**Subscribers**: 
- GAME_NODE (receives in Phase 1: Welcome)
- RESULT_GAME (stores for final display)

**Purpose**: Transmits player information (name, username, age) from INFO_USER to other nodes.

**Message Fields**:
- `name` (string): Player's actual name
- `username` (string): Player's username
- `age` (int64): Player's age

---

### Topic 2: keyboard_control

**Message Type**: `std_msgs/String`

**Publisher**: 
- CONTROL_NODE (`control_node.py`)
- CONTROL_NODE_PYGAME (`control_node_pygame.py`)

**Subscribers**: 
- GAME_NODE (processes in Phase 2: Game)
- GUI game (for player movement)

**Purpose**: Transmits movement commands from control nodes to game.

**Message Values** (all uppercase):
- `"UP"` - Up movement
- `"DOWN"` - Down movement
- `"LEFT"` - Left movement
- `"RIGHT"` - Right movement

**Format**: All values must be in capital letters as specified in requirements.

---

### Topic 3: result_information

**Message Type**: `std_msgs/Int64`

**Publisher**: GAME_NODE (in Phase 3: Final)

**Subscriber**: RESULT_GAME

**Purpose**: Transmits final game score from GAME_NODE to RESULT_GAME.

**Message Content**: 
- Integer value representing final score
- Calculated as: `base_score + (age * 10)` (age bonus)

---

## ROS Services

### Service 1: user_score

**Service Name**: `user_score`

**Service Type**: `ros_nodes/srv/GetUserScore`

**Service Definition** (`ros_nodes/srv/GetUserScore.srv`):
```
string username
---
int64 score
```

**Server**: GAME_NODE (`game_node.py`)

**Client**: RESULT_GAME (`result_game.py`)

**Request**:
- `username` (string): **Note**: RESULT_GAME sends the user's **name** (not username) to this field, as per requirement: "sends to the user_score service the name of the user"

**Response**:
- `score` (int64): Score percentage as integer

**Functionality**:
- Server calculates: `(current_score / 1000.0) * 100` as integer
- Returns the percentage of the score when it receives the user's name
- Client prints: `"Score Percentage: {score}%"`

**Service Handler**: `handle_user_score(req)` in `game_node.py`

**Service Call**: `get_score_percentage()` in `result_game.py`

---

### Service 2: difficulty

**Service Name**: `difficulty`

**Service Type**: `ros_nodes/srv/SetGameDifficulty`

**Service Definition** (`ros_nodes/srv/SetGameDifficulty.srv`):
```
string change_difficulty
---
bool success
```

**Server**: GAME_NODE (`game_node.py`)

**Client**: GUI nodes (e.g., `difficulty_select_gui.py`)

**Request**:
- `change_difficulty` (string): Difficulty level. Valid values: `"easy"`, `"medium"`, `"hard"`

**Response**:
- `success` (bool): 
  - `True` if game is in phase1 (start screen) and difficulty is valid
  - `False` if game is not in phase1 or difficulty is invalid

**Functionality**:
- **Only allows difficulty change during phase1** (start screen)
- If in phase1 and difficulty is valid ("easy", "medium", "hard"), changes the difficulty and returns `True`
- If not in phase1, returns `False` without changing difficulty
- Sets appropriate start level based on difficulty:
  - `"easy"`: Levels 1-3
  - `"medium"`: Levels 4-6
  - `"hard"`: Levels 7-10

**Service Handler**: `handle_difficulty(req)` in `game_node.py`

---

## ROS Parameters

All parameters are managed by GAME_NODE (`game_node.py`).

### Parameter 1: user_name

**Type**: `string`

**Function**: Stores the user's name.

**Set By**: GAME_NODE automatically when user information is received

**Set When**: Phase 1 (Welcome phase) - when `user_information` message is received

**Code**:
```python
rospy.set_param('user_name', self.user_name)
```

**Used By**: 
- `difficulty_select_gui` node (waits for this parameter before initializing)

**Location**: Set in `user_info_cb()` method in `game_node.py`

---

### Parameter 2: change_player_color

**Type**: `int64`

**Function**: Change the player color.

**Available Colors**:
- `1`: Red
- `2`: Purple (default)
- `3`: Blue

**Set By**: 
- Launch file (default: 2 - Purple)
- Can be set via ROS parameter: `rosparam set change_player_color 1`

**Read By**: GAME_NODE in `__init__()` method

**Code**:
```python
if rospy.has_param('change_player_color'):
    self.color_param = rospy.get_param('change_player_color')
else:
    self.color_param = 2  # Default Purple
```

**Location**: Read in `__init__()` method in `game_node.py`

---

### Parameter 3: screen_param

**Type**: `string`

**Function**: Show the game phase.

**Values**:
- `"phase1"`: Welcome phase
- `"phase2"`: Game phase
- `"phase3"`: Final phase

**Set By**: GAME_NODE automatically during phase transitions

**Set When**:
- `"phase1"`: In `welcome_phase()` method
- `"phase2"`: In `game_phase()` method
- `"phase3"`: In `final_phase()` method

**Code**:
```python
rospy.set_param('screen_param', 'phase1')  # Welcome phase
rospy.set_param('screen_param', 'phase2')  # Game phase
rospy.set_param('screen_param', 'phase3')  # Final phase
```

**Location**: Set in phase methods in `game_node.py`

---

## Quick Start - Running the Launcher

**To run the complete ROS game system:**

1. **Make nodes executable** (first time only):
   ```bash
   cd ~/RP_Moreno_Turkel_25
   chmod +x ros_nodes/*.py
   ```

2. **Start ROS Master** (Terminal 1):
   ```bash
   roscore
   ```

3. **Launch all nodes** (Terminal 2):
   ```bash
   # If using catkin workspace:
   source ~/catkin_ws/devel/setup.bash
   roslaunch ros_nodes game.launch
   
   # OR if running from project directory:
   cd ~/RP_Moreno_Turkel_25
   export ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH:$(pwd)
   roslaunch ros_nodes game.launch
   ```

**What the launcher does:**
- Launches all 5 required ROS nodes (INFO_USER, GAME_NODE, RESULT_NODE, CONTROL_NODE)
- Starts GUI nodes for user input and difficulty selection
- Launches the visual game GUI
- Sets up all ROS topics, services, and parameters

**Note:** If you haven't built the ROS package yet, see the "Prerequisites" section below.

---

## Running Individual Nodes

**Prerequisites:**
- ROS Master must be running (`roscore`)
- All nodes must be executable: `chmod +x ros_nodes/*.py`
- If using catkin workspace, source it: `source ~/catkin_ws/devel/setup.bash`
- Python dependencies installed: `pip install -r requirements.txt`

You can run each node separately in different terminals. This is useful for debugging and understanding the communication flow.

**Recommended Startup Order:**

1. **Terminal 1 - Start ROS Master:**
   ```bash
   roscore
   ```

2. **Terminal 2 - Run GAME_NODE** (should start first to be ready for messages):
   ```bash
   # If using catkin workspace:
   source ~/catkin_ws/devel/setup.bash
   rosrun ros_nodes game_node.py
   
   # Or directly with Python:
   cd ~/RP_Moreno_Turkel_25
   python3 ros_nodes/game_node.py
   ```

3. **Terminal 3 - Run RESULT_GAME** (should start early to receive user info):
   ```bash
   source ~/catkin_ws/devel/setup.bash
   rosrun ros_nodes result_game.py
   ```

4. **Terminal 4 - Run INFO_USER** (triggers the game flow):
   ```bash
   # Terminal version:
   rosrun ros_nodes info_user.py
   
   # OR GUI version (recommended):
   rosrun ros_nodes info_user_gui.py
   ```

5. **Terminal 5 - Run CONTROL_NODE** (can start anytime during Game phase):
   ```bash
   # Terminal-based control:
   rosrun ros_nodes control_node.py
   
   # OR Pygame-based control (recommended):
   rosrun ros_nodes control_node_pygame.py
   ```

**Note**: The order matters because:
- GAME_NODE and RESULT_GAME should be ready before INFO_USER publishes
- CONTROL_NODE can start anytime, but only works during Phase 2 (Game phase)

---

## Launch File Details

**File**: `ros_nodes/launch/game.launch`

**Purpose**: Launches all required ROS nodes automatically with proper configuration.

### Nodes Launched

1. **result_node** (`result_game.py`)
   - Displays final game results
   - Subscribes to: `user_information`, `result_information`
   - Calls service: `user_score`

2. **game_node** (`game_node.py`)
   - Main game logic with 3 phases (Welcome, Game, Final)
   - Subscribes to: `user_information`, `keyboard_control`, `game_over_stats`
   - Publishes to: `result_information`
   - Services: `user_score`, `difficulty`
   - Parameters: `change_player_color` (default: 2 - Purple)

3. **info_user** (`info_user_gui.py` - GUI version)
   - Collects user information (name, username, age)
   - Publishes to: `user_information`

4. **control_node** (`control_node_pygame.py` - Pygame version)
   - Keyboard control with visual feedback
   - Publishes to: `keyboard_control`

5. **gui_game_node** (`gui_node.py`)
   - Launches the visual Pygame game window
   - Waits for user info and difficulty/color selection

6. **difficulty_select_gui** (`difficulty_select_gui.py`)
   - Difficulty and color selection GUI
   - Appears after user information is collected
   - Calls `difficulty` service

### Launch File Code

```xml
<launch>
    <!-- RESULT_NODE -->
    <node pkg="ros_nodes" type="result_game.py" name="result_node" output="screen"/>
    
    <!-- GAME_NODE -->
    <node pkg="ros_nodes" type="game_node.py" name="game_node" output="screen">
        <param name="change_player_color" value="2" />  <!-- Default: Purple -->
    </node>
    
    <!-- INFO_USER (GUI version) -->
    <node pkg="ros_nodes" type="info_user_gui.py" name="info_user" output="screen" />
    
    <!-- CONTROL_NODE (Pygame version) -->
    <node pkg="ros_nodes" type="control_node_pygame.py" name="control_node" output="screen" />
    
    <!-- GUI_NODE (Visual Game) -->
    <node pkg="ros_nodes" type="gui_node.py" name="gui_game_node" output="screen" />
    
    <!-- DIFFICULTY_SELECT_GUI -->
    <node pkg="ros_nodes" type="difficulty_select_gui.py" name="difficulty_select_gui" output="screen" />
</launch>
```

### How to Use Launch File

```bash
# Terminal 1: Start ROS Master
roscore

# Terminal 2: Launch all nodes
source ~/catkin_ws/devel/setup.bash  # If using catkin workspace
roslaunch ros_nodes game.launch

# OR from project directory:
cd ~/RP_Moreno_Turkel_25
export ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH:$(pwd)
roslaunch ros_nodes game.launch
```

---

## Technical Requirements Compliance

### FIRST PART - ROS Publisher, Subscriber and Custom MSG

#### Required Components

✅ **5 Nodes**:
1. `info_user` - Collects player information
2. `game_node` - Main game logic with 3 phases
3. `control_node` - Terminal keyboard control
4. `control_node_pygame` - Pygame keyboard control
5. `result_game` - Displays final results

✅ **3 Topics**:
1. `user_information` - Player information (custom message)
2. `keyboard_control` - Movement commands (std_msgs/String)
3. `result_information` - Final score (std_msgs/Int64)

✅ **1 Custom Message**:
- `user_msg` - Contains: `string name`, `string username`, `int64 age`

#### Node Requirements

✅ **INFO_USER Node**:
- Requests player's name, username, and age through terminal (or GUI)
- Publishes to `user_information` topic with `user_msg` type

✅ **GAME_NODE**:
- **Phase 1 (Welcome)**: Receives player info from INFO_USER, **prints the user's name** to screen
- **Phase 2 (Game)**: Receives keyboard control from CONTROL_NODE, processes movement
- **Phase 3 (Final)**: Calculates final score, publishes to `result_information` topic (std_msgs/Int64)

✅ **CONTROL_NODE**:
- Controls player movement using arrow keys
- Publishes to `keyboard_control` topic (std_msgs/String)
- Values: "UP", "DOWN", "LEFT", "RIGHT" (all capital letters)

✅ **RESULT_GAME Node**:
- Receives player info from INFO_USER via `user_information` topic
- Receives score from GAME_NODE via `result_information` topic
- Displays final message with score and username

### Technical Requirements

#### 1. Node Structure

✅ **Requirement**: Each node in separate class structure, different Python files, no global variables.

**Implementation**:
- All 5 nodes are separate classes in separate files
- No global variables - all data encapsulated in class attributes
- Modular and self-contained design

#### 2. Phases Implementation in GAME_NODE

✅ **Requirement**: Each game phase (Welcome, Game, Final) as separate method.

**Implementation**:
- `welcome_phase(user_msg)`: Handles Welcome phase
- `game_phase()`: Handles Game phase
- `final_phase()`: Handles Final phase
- Each method is self-contained

#### 3. Communication Between Nodes

✅ **Requirement**: Proper ROS message communication.

**Implementation**:
- INFO_USER → GAME_NODE: `user_information` topic (user_msg)
- GAME_NODE → RESULT_NODE: `result_information` topic (std_msgs/Int64)
- CONTROL_NODE → GAME_NODE: `keyboard_control` topic (std_msgs/String)

#### 4. Keyboard Control Alternatives

✅ **Requirement**: Keyboard control communicated with GAME_NODE.

**Implementation**:
- `control_node.py`: Terminal-based
- `control_node_pygame.py`: Pygame-based
- Both publish to `keyboard_control` topic

#### 5. Logging and Transition Messages

✅ **Requirement**: Log messages for transitions in all nodes and between phases.

**Implementation**:
- All nodes have comprehensive logging
- GAME_NODE logs: "Welcome phase started.", "Game phase started.", "Final phase reached, calculating score."
- All nodes log transitions and activities

#### 6. Documentation

✅ **Requirement**: README.md with instructions for running nodes, dependencies, communication overview.

**Implementation**: This README.md file.

### SECOND PART - Services and Parameters

#### Service 1: GetUserScore

✅ **Requirement**: Service returns percentage of score when receiving user's name.

**Implementation**:
- Service name: `user_score`
- Service type: `GetUserScore`
- Request: `string username` (receives user's name)
- Response: `int64 score` (percentage)
- Server: `game_node` - Calculates `(score / 1000.0) * 100`
- Client: `result_game` - Sends user's name, prints percentage

#### Service 2: SetGameDifficulty

✅ **Requirement**: Service changes difficulty only in phase1.

**Implementation**:
- Service name: `difficulty`
- Service type: `SetGameDifficulty`
- Request: `string change_difficulty` ("easy", "medium", "hard")
- Response: `bool success` (True if in phase1, False otherwise)
- Server: `game_node` - Only allows in phase1

#### Parameters

✅ **Requirement**: Three parameters in game_node.

**Implementation**:
- `user_name` (string): Stores user's name
- `change_player_color` (int64): Player color (1: Red, 2: Purple, 3: Blue)
- `screen_param` (string): Game phase (phase1, phase2, phase3)

---

## Prerequisites

### 1. ROS Installation

- **ROS Noetic** (Ubuntu 20.04) or **ROS Melodic** (Ubuntu 18.04)
- Install ROS following the official guide: http://wiki.ros.org/ROS/Installation

### 2. ROS Dependencies

```bash
# For ROS Noetic
sudo apt-get install ros-noetic-rospy ros-noetic-std-msgs

# For ROS Melodic
sudo apt-get install ros-melodic-rospy ros-melodic-std-msgs
```

### 3. Python Dependencies

```bash
pip install -r requirements.txt
```

**Important**: The `requirements.txt` includes `pygame`, which is required for:
- The main game GUI
- The `control_node_pygame` node
- The `difficulty_select_gui` and `info_user_gui` nodes

If pygame installation fails, install system dependencies first:
```bash
# Ubuntu/Debian
sudo apt-get install python3-pygame

# Or install via pip with system packages
sudo apt-get install python3-dev libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsdl1.2-dev libsmpeg-dev python3-numpy libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev
pip install pygame
```

### 4. Build ROS Package (if using catkin workspace)

```bash
cd ~/catkin_ws/src
# Copy or link the ros_nodes directory here
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

### 5. Make Nodes Executable

```bash
cd ~/RP_Moreno_Turkel_25
chmod +x ros_nodes/*.py
```

---

## Troubleshooting

### 1. "No module named 'ros_nodes'"

**Solution**:
- Ensure ROS_PACKAGE_PATH includes the project directory:
  ```bash
  export ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH:$(pwd)
  ```
- Or build the package in a catkin workspace

### 2. "Topic not found"

**Solution**:
- Ensure roscore is running
- Check that all nodes are started in the correct order
- Verify topic names match exactly

### 3. "Permission denied"

**Solution**:
- Make nodes executable: `chmod +x ros_nodes/*.py`

### 4. Control node not responding

**Solution**:
- For `control_node`: Ensure terminal has focus
- For `control_node_pygame`: Ensure pygame window has focus
- Try running control node manually in a separate terminal

### 5. Service call fails

**Solution**:
- Ensure service server (game_node) is running
- Check service name matches exactly: `user_score` or `difficulty`
- Verify request format matches service definition

### 6. Difficulty selection not working

**Solution**:
- Ensure game is in phase1 (Welcome phase)
- Check that `difficulty` service is available: `rosservice list | grep difficulty`
- Verify difficulty value is "easy", "medium", or "hard"

### 7. RESULT_NODE not printing score percentage

**Solution**:
- Ensure `user_score` service is available: `rosservice list | grep user_score`
- Check that RESULT_NODE stored the user's name correctly
- Verify GAME_NODE has a score value

---

## Summary

This project implements a complete ROS-based game control system with:

- ✅ **5 Nodes**: info_user, game_node, control_node, control_node_pygame, result_game
- ✅ **3 Topics**: user_information, keyboard_control, result_information
- ✅ **1 Custom Message**: user_msg (name, username, age)
- ✅ **2 Services**: user_score (GetUserScore), difficulty (SetGameDifficulty)
- ✅ **3 Parameters**: user_name, change_player_color, screen_param
- ✅ **3 Phases**: Welcome, Game, Final (in GAME_NODE)
- ✅ **Complete Documentation**: This README with all specifications

All requirements from FIRST PART and SECOND PART are fully implemented and documented.
