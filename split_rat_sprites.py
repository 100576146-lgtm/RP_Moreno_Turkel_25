#!/usr/bin/env python3
"""
Split rat sprite sheets (redRat, blueRat, purpleRat) into individual sprites.
Organizes them similar to sprites_sheet_1 structure.
"""
import pygame
import os
import sys

def split_sprite_sheet(sheet_path, output_dir, cols=4, rows=3):
    """Split a sprite sheet into individual sprites."""
    if not os.path.exists(sheet_path):
        print(f"Error: {sheet_path} not found!")
        return False
    
    # Initialize pygame
    pygame.init()
    
    # Load the sprite sheet
    try:
        image = pygame.image.load(sheet_path)
        width, height = image.get_size()
        print(f"\nProcessing: {os.path.basename(sheet_path)}")
        print(f"  Dimensions: {width}x{height}")
    except Exception as e:
        print(f"Error loading {sheet_path}: {e}")
        return False
    
    # Calculate sprite dimensions
    sprite_width = width // cols
    sprite_height = height // rows
    print(f"  Grid: {cols}x{rows}")
    print(f"  Sprite size: {sprite_width}x{sprite_height}")
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"  Created directory: {output_dir}")
    
    # Split into individual sprites
    sprites_created = 0
    for row in range(rows):
        for col in range(cols):
            x = col * sprite_width
            y = row * sprite_height
            
            # Create a surface for the sprite
            sprite = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
            sprite.blit(image, (0, 0), (x, y, sprite_width, sprite_height))
            
            # Save the sprite (same naming convention as sprites_sheet_1)
            filename = f"sprite_{row}_{col}.png"
            filepath = os.path.join(output_dir, filename)
            pygame.image.save(sprite, filepath)
            
            sprites_created += 1
            print(f"  Saved: {filename}")
    
    print(f"  ✓ Created {sprites_created} sprites in {output_dir}")
    return True

def main():
    # Get the game images directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    game_images_dir = os.path.join(script_dir, "game images")
    
    # Define sprite sheets and their output directories
    sprite_sheets = [
        ("redRat.png", "redrat"),
        ("blueRat.png", "bluerat"),
        ("purpleRat.png", "purplerat"),
    ]
    
    print("=" * 60)
    print("Rat Sprite Sheet Splitter")
    print("=" * 60)
    
    # Try different grid sizes - start with 4x3 (like sprites_sheet_1)
    # If that doesn't work well, we can try 4x4
    cols = 4
    rows = 3
    
    success_count = 0
    for sheet_name, output_folder in sprite_sheets:
        sheet_path = os.path.join(game_images_dir, sheet_name)
        output_dir = os.path.join(game_images_dir, output_folder)
        
        if split_sprite_sheet(sheet_path, output_dir, cols, rows):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"✓ Successfully processed {success_count}/{len(sprite_sheets)} sprite sheets")
    print("=" * 60)
    
    if success_count == len(sprite_sheets):
        print("\nNext steps:")
        print("1. Check the generated sprite folders (redrat, bluerat, purplerat)")
        print("2. Verify the sprites look correct")
        print("3. Update sprite_animator.py to load these new sprite sets")
        print("4. Update Player class to use the appropriate sprite set based on color")

if __name__ == "__main__":
    main()

