#!/usr/bin/env python3
"""
Smart level generator that ensures all platforms are accessible within jump height.
"""
import random
import math
from constants import SAFE_JUMP_HEIGHT, LEVEL_HEIGHT

class SmartLevelGenerator:
    def __init__(self, level_width, level_height, difficulty=0):
        self.level_width = level_width
        self.level_height = level_height
        self.difficulty = difficulty
        self.platforms = []
        self.rng = random.Random(1337 + difficulty)
        
    def generate_accessible_platforms(self):
        """Generate platforms that are all accessible within jump height."""
        self.platforms = []
        
        # Ground platforms (always accessible)
        for x in range(0, self.level_width, 200):
            self.platforms.append({
                'x': x, 'y': self.level_height - 40, 
                'width': 200, 'height': 40, 
                'type': 'ground'
            })
        
        # Generate floating platforms in segments
        segment_width = self.level_width // 8
        for segment in range(1, 8):
            self._generate_segment_platforms(segment, segment_width)
        
        return self.platforms
    
    def _generate_segment_platforms(self, segment, segment_width):
        """Generate platforms for a level segment."""
        base_x = segment * segment_width
        count = 1 + (self.difficulty // 2)
        
        # Keep track of accessible platforms in this segment
        accessible_platforms = []
        
        for _ in range(count):
            # Try to place platform within jump height of existing platforms
            platform = self._find_accessible_platform_position(
                base_x, accessible_platforms
            )
            
            if platform:
                self.platforms.append(platform)
                accessible_platforms.append(platform)
    
    def _find_accessible_platform_position(self, base_x, existing_platforms):
        """Find a position for a platform that's accessible from existing platforms."""
        # If no existing platforms, place near ground
        if not existing_platforms:
            y = self.level_height - 100 - self.rng.randint(0, SAFE_JUMP_HEIGHT // 2)
        else:
            # Find the highest accessible platform in this area
            reference_platform = max(existing_platforms, key=lambda p: p['y'])
            max_y = reference_platform['y'] - SAFE_JUMP_HEIGHT
            min_y = reference_platform['y'] + 20  # Don't go too low
            
            # Ensure we don't go above the top of the screen
            max_y = max(max_y, 50)
            min_y = min(min_y, self.level_height - 100)
            
            if max_y < min_y:
                return None
                
            y = self.rng.randint(min_y, max_y)
        
        # Generate platform properties
        x = base_x - self.rng.randint(80, 180)
        width = self.rng.choice([100, 120, 150])
        height = 20
        
        # Choose platform type
        platform_types = ["normal", "cloud", "ice"]
        if base_x // (self.level_width // 8) % 2 == 0:
            platform_types.append("moving")
        
        platform_type = self.rng.choice(platform_types)
        
        return {
            'x': x, 'y': y, 'width': width, 'height': height,
            'type': platform_type
        }
    
    def validate_platform_accessibility(self):
        """Validate that all platforms are accessible."""
        # Group platforms by x-coordinate segments
        segments = {}
        for platform in self.platforms:
            segment = platform['x'] // (self.level_width // 8)
            if segment not in segments:
                segments[segment] = []
            segments[segment].append(platform)
        
        # Check each segment for accessibility
        for segment, platforms in segments.items():
            if not self._segment_is_accessible(platforms):
                print(f"Warning: Segment {segment} may have inaccessible platforms")
                return False
        
        return True
    
    def _segment_is_accessible(self, platforms):
        """Check if all platforms in a segment are accessible."""
        if not platforms:
            return True
        
        # Sort platforms by height (lowest first)
        platforms.sort(key=lambda p: p['y'], reverse=True)
        
        # Check if each platform is within jump height of a lower one
        for i, platform in enumerate(platforms):
            if i == 0:  # First platform (lowest)
                continue
            
            # Check if this platform is accessible from any lower platform
            accessible = False
            for lower_platform in platforms[:i]:
                distance = abs(platform['y'] - lower_platform['y'])
                if distance <= SAFE_JUMP_HEIGHT:
                    accessible = True
                    break
            
            if not accessible:
                return False
        
        return True

def test_jump_height_calculation():
    """Test the jump height calculation."""
    from constants import JUMP_STRENGTH, GRAVITY, SAFE_JUMP_HEIGHT
    
    # Calculate jump height manually
    jump_height = (JUMP_STRENGTH * JUMP_STRENGTH) / (2 * GRAVITY)
    print(f"Jump strength: {JUMP_STRENGTH}")
    print(f"Gravity: {GRAVITY}")
    print(f"Calculated jump height: {jump_height}")
    print(f"Safe jump height: {SAFE_JUMP_HEIGHT}")

if __name__ == "__main__":
    test_jump_height_calculation()
    
    # Test level generation
    generator = SmartLevelGenerator(3200, 600, 0)
    platforms = generator.generate_accessible_platforms()
    
    print(f"\nGenerated {len(platforms)} platforms")
    print("Platform accessibility check:", generator.validate_platform_accessibility())
