#!/usr/bin/env python3
"""
Sprite sheet analyzer and cropper for Gemini-generated character sprites.
"""
import pygame
import os
import sys

def analyze_sprite_sheet(image_path):
    """Analyze a sprite sheet and return information about its structure."""
    try:
        image = pygame.image.load(image_path)
        width, height = image.get_size()
        print(f"Analyzing: {os.path.basename(image_path)}")
        print(f"Dimensions: {width}x{height}")
        
        # Try to detect sprite grid structure
        # Common sprite sheet patterns: 4x4, 6x4, 8x4, etc.
        possible_grids = [
            (4, 4), (6, 4), (8, 4), (4, 6), (6, 6), (8, 6),
            (3, 4), (5, 4), (7, 4), (4, 5), (6, 5), (8, 5)
        ]
        
        print("\nPossible grid structures:")
        for cols, rows in possible_grids:
            sprite_width = width // cols
            sprite_height = height // rows
            print(f"  {cols}x{rows}: {sprite_width}x{sprite_height} per sprite")
        
        return image, width, height
    except Exception as e:
        print(f"Error loading {image_path}: {e}")
        return None, 0, 0

def crop_sprites(image, cols, rows, output_dir="sprites"):
    """Crop sprites from a sprite sheet."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    width, height = image.get_size()
    sprite_width = width // cols
    sprite_height = height // rows
    
    print(f"\nCropping {cols}x{rows} grid:")
    print(f"Sprite size: {sprite_width}x{sprite_height}")
    
    sprites = []
    for row in range(rows):
        for col in range(cols):
            x = col * sprite_width
            y = row * sprite_height
            
            # Create a surface for the sprite
            sprite = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
            sprite.blit(image, (0, 0), (x, y, sprite_width, sprite_height))
            
            # Save the sprite
            filename = f"sprite_{row}_{col}.png"
            filepath = os.path.join(output_dir, filename)
            pygame.image.save(sprite, filepath)
            
            sprites.append(sprite)
            print(f"  Saved: {filename}")
    
    return sprites

def main():
    pygame.init()
    
    # Find sprite sheets
    sprite_sheets = []
    for filename in os.listdir("."):
        if (filename.startswith("Gemini_Generated_Image_") and filename.endswith(".png")) or filename == "Sprites.png":
            sprite_sheets.append(filename)
    
    if not sprite_sheets:
        print("No sprite sheets found!")
        return
    
    print(f"Found {len(sprite_sheets)} sprite sheets:")
    for sheet in sprite_sheets:
        print(f"  - {sheet}")
    
    # Analyze each sprite sheet
    for i, sheet in enumerate(sprite_sheets):
        print(f"\n{'='*50}")
        print(f"SPRITE SHEET {i+1}: {sheet}")
        print('='*50)
        
        image, width, height = analyze_sprite_sheet(sheet)
        if image is None:
            continue
        
        # Try different grid structures and let user choose
        print(f"\nTrying common grid structures for {sheet}:")
        
        # Try 4x4 first (common for character animations)
        if width % 4 == 0 and height % 4 == 0:
            print("\nTrying 4x4 grid:")
            sprites = crop_sprites(image, 4, 4, f"sprites_sheet_{i+1}")
            print(f"Created {len(sprites)} sprites")
        
        # Try 6x4 (common for more complex animations)
        if width % 6 == 0 and height % 4 == 0:
            print("\nTrying 6x4 grid:")
            sprites = crop_sprites(image, 6, 4, f"sprites_sheet_{i+1}_6x4")
            print(f"Created {len(sprites)} sprites")
        
        # Try 8x4 (for very detailed animations)
        if width % 8 == 0 and height % 4 == 0:
            print("\nTrying 8x4 grid:")
            sprites = crop_sprites(image, 8, 4, f"sprites_sheet_{i+1}_8x4")
            print(f"Created {len(sprites)} sprites")

if __name__ == "__main__":
    main()

