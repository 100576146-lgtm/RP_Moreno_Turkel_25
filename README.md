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

## Controls

- **Movement**: Arrow keys or WASD
- **Jump**: Spacebar, Up arrow, or W key
- **Menu Navigation**: 
  - SPACE or ENTER to start game from main menu
  - ESC to pause game or return to menu
  - R or SPACE to restart from game over screen
  - M to return to main menu from game over screen

## Installation and Running

1. Install pygame:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the game:
   ```bash
   python3 mario_platformer.py
   ```

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
