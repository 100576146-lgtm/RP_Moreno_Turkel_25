#!/usr/bin/env python3
"""
Smart level generator that ensures all platforms are accessible within jump height.
"""
import random
import math
from constants import SAFE_JUMP_HEIGHT, LEVEL_HEIGHT, MAX_JUMP_HEIGHT

class SmartLevelGenerator:
    def __init__(self, level_width, level_height, difficulty=0):
        self.level_width = level_width
        self.level_height = level_height
        self.difficulty = difficulty
        self.platforms = []
        self.enemy_positions = []  # Track enemy positions for stepping stones
        self.ground_holes = []  # Track ground hole positions
        self.rng = random.Random(1337 + difficulty)
        
        # Calculate safe horizontal jump distance (player can move while jumping)
        # Assuming player can move ~5 pixels/frame and jump lasts ~30 frames
        self.safe_horizontal_distance = 250
        
    def generate_accessible_platforms(self):
        """Generate platforms that are all accessible within jump height."""
        self.platforms = []
        self.enemy_positions = []
        
        # Ground platforms with occasional holes based on difficulty
        self._generate_ground_with_holes()
        
        # Generate floating platforms in a connected chain
        self._generate_connected_platforms()
        
        return self.platforms
    
    def _generate_ground_with_holes(self):
        """Generate ground platforms with gaps/holes based on difficulty."""
        # Calculate hole frequency: more holes at higher difficulty
        # difficulty 0: ~2 holes, difficulty 9: ~12 holes
        hole_count = 2 + self.difficulty
        
        # Create full ground first
        ground_segments = []
        for x in range(0, self.level_width, 200):
            ground_segments.append({
                'x': x, 'y': self.level_height - 40, 
                'width': 200, 'height': 40, 
                'type': 'ground'
            })
        
        # Remove segments to create holes
        if hole_count > 0 and len(ground_segments) > 10:
            # Don't put holes at the very start or end
            safe_start = 3  # Keep first 3 segments safe for spawn
            safe_end = 2    # Keep last 2 segments safe for level end
            available_segments = ground_segments[safe_start:-safe_end]
            
            if len(available_segments) > hole_count * 2:
                # Randomly select segments to remove (create holes)
                # Hole size: 1-3 consecutive segments based on difficulty
                holes_created = 0
                attempts = 0
                max_attempts = hole_count * 3
                
                while holes_created < hole_count and attempts < max_attempts:
                    attempts += 1
                    
                    # Random hole size: bigger holes at higher difficulty
                    hole_size = self.rng.randint(1, min(3, 1 + self.difficulty // 3))
                    
                    # Random position
                    if len(available_segments) > hole_size:
                        start_idx = self.rng.randint(0, len(available_segments) - hole_size)
                        
                        # Check if this area already has a hole nearby
                        can_place = True
                        for i in range(max(0, start_idx - 2), min(len(available_segments), start_idx + hole_size + 2)):
                            if available_segments[i] is None:
                                can_place = False
                                break
                        
                        if can_place:
                            # Create hole by removing segments and track hole positions
                            for i in range(hole_size):
                                hole_segment = available_segments[start_idx + i]
                                if hole_segment:
                                    self.ground_holes.append({
                                        'x': hole_segment['x'],
                                        'width': hole_segment['width'],
                                        'y': hole_segment['y']
                                    })
                                available_segments[start_idx + i] = None
                            holes_created += 1
                
                # Rebuild platforms list without None entries
                self.platforms = ground_segments[:safe_start]
                self.platforms.extend([seg for seg in available_segments if seg is not None])
                self.platforms.extend(ground_segments[-safe_end:])
            else:
                self.platforms = ground_segments
        else:
            self.platforms = ground_segments
    
    def get_enemy_stepping_stones(self):
        """Return positions where enemies should be placed as stepping stones."""
        return self.enemy_positions
    
    def _generate_connected_platforms(self):
        """Generate a connected chain of platforms across the level."""
        # Start from ground level and work across the level
        current_x = 400  # Start after spawn point
        current_y = self.level_height - 100  # Start slightly above ground
        
        platforms_per_segment = 3 + self.difficulty
        segment_count = 8
        
        for segment in range(segment_count):
            segment_platforms = []
            
            # Create platforms for this segment
            for i in range(platforms_per_segment):
                # Determine platform height variation
                if i == 0:
                    # First platform in segment - should be reachable from previous
                    y_variation = self.rng.randint(-SAFE_JUMP_HEIGHT + 50, 50)
                else:
                    # Subsequent platforms - vary height
                    y_variation = self.rng.randint(-SAFE_JUMP_HEIGHT + 30, SAFE_JUMP_HEIGHT - 30)
                
                new_y = max(80, min(self.level_height - 100, current_y + y_variation))
                
                # Check if this platform is reachable from current position
                vertical_distance = abs(new_y - current_y)
                
                # If too high, add stepping stones (enemies or intermediate platforms)
                if vertical_distance > SAFE_JUMP_HEIGHT - 20:
                    # Add intermediate platform or enemy
                    if self.rng.random() < 0.6:  # 60% chance for intermediate platform
                        intermediate_y = current_y - (SAFE_JUMP_HEIGHT - 40)
                        intermediate_platform = {
                            'x': current_x + 120,
                            'y': intermediate_y,
                            'width': 100,
                            'height': 20,
                            'type': 'normal'
                        }
                        self.platforms.append(intermediate_platform)
                        segment_platforms.append(intermediate_platform)
                        current_y = intermediate_y
                    else:
                        # Place enemy as stepping stone
                        enemy_y = current_y - 80
                        self.enemy_positions.append({
                            'x': current_x + 100,
                            'y': enemy_y,
                            'type': 'basic'  # Basic enemy for stepping stone
                        })
                
                # Create the platform
                x_advance = self.rng.randint(150, 300)
                current_x += x_advance
                
                width = self.rng.choice([100, 120, 150, 180])
                
                # Choose platform type based on position
                platform_types = ["normal", "cloud"]
                if segment % 2 == 0 and i % 2 == 0:
                    platform_types.append("moving")
                if self.difficulty > 2:
                    platform_types.append("ice")
                
                platform = {
                    'x': current_x,
                    'y': new_y,
                    'width': width,
                    'height': 20,
                    'type': self.rng.choice(platform_types)
                }
                
                self.platforms.append(platform)
                segment_platforms.append(platform)
                current_y = new_y
                
                # Ensure we don't go past level width
                if current_x >= self.level_width - 500:
                    break
            
            # If we've reached the end, stop
            if current_x >= self.level_width - 500:
                break
    
    def find_accessible_star_position(self):
        """Find a challenging but accessible position for the star powerup."""
        # Find platforms in the latter half of the level
        latter_half_platforms = [p for p in self.platforms if p['x'] > self.level_width * 0.6]
        
        if not latter_half_platforms:
            # Fallback to any platform
            latter_half_platforms = self.platforms[-10:] if len(self.platforms) > 10 else self.platforms
        
        # Choose a high platform (but not ground level)
        high_platforms = [p for p in latter_half_platforms if p['y'] < self.level_height - 150]
        
        if high_platforms:
            # Pick a random high platform
            target_platform = self.rng.choice(high_platforms)
            
            # Place star above the platform (reachable by jumping)
            star_x = target_platform['x'] + target_platform['width'] // 2
            star_y = target_platform['y'] - 60  # Just above the platform, easy to get by jumping
            
            return {'x': star_x, 'y': star_y, 'platform': target_platform}
        else:
            # Fallback: place on a random platform
            if latter_half_platforms:
                target_platform = self.rng.choice(latter_half_platforms)
                star_x = target_platform['x'] + target_platform['width'] // 2
                star_y = target_platform['y'] - 60
                return {'x': star_x, 'y': star_y, 'platform': target_platform}
        
        # Ultimate fallback
        return {'x': self.level_width - 800, 'y': self.level_height - 200, 'platform': None}
    
    def is_position_over_hole(self, x, y, width=20):
        """Check if a position overlaps with a ground hole."""
        for hole in self.ground_holes:
            # Check if x position overlaps with hole
            if (x >= hole['x'] - width and x <= hole['x'] + hole['width'] + width):
                # Check if y is near ground level
                if abs(y - hole['y']) < 100:
                    return True
        return False
    
    def validate_platform_accessibility(self):
        """Validate that all platforms are accessible."""
        # Get all non-ground platforms
        floating_platforms = [p for p in self.platforms if p['type'] != 'ground']
        
        if not floating_platforms:
            return True
        
        # Check each platform is reachable from at least one other platform
        accessible_platforms = set()
        
        # Ground platforms are always accessible
        ground_platforms = [p for p in self.platforms if p['type'] == 'ground']
        for p in ground_platforms:
            accessible_platforms.add(id(p))
        
        # Iteratively find all accessible platforms
        changed = True
        max_iterations = 100
        iteration = 0
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            for platform in self.platforms:
                if id(platform) in accessible_platforms:
                    continue
                
                # Check if this platform is reachable from any accessible platform
                for accessible_p in self.platforms:
                    if id(accessible_p) not in accessible_platforms:
                        continue
                    
                    # Check vertical distance
                    vertical_dist = abs(platform['y'] - accessible_p['y'])
                    # Check horizontal distance
                    horizontal_dist = abs(platform['x'] - accessible_p['x'])
                    
                    if vertical_dist <= SAFE_JUMP_HEIGHT and horizontal_dist <= self.safe_horizontal_distance:
                        accessible_platforms.add(id(platform))
                        changed = True
                        break
        
        # Check if all platforms are accessible
        total_platforms = len(self.platforms)
        accessible_count = len(accessible_platforms)
        
        if accessible_count < total_platforms:
            print(f"Warning: {total_platforms - accessible_count} platforms may be inaccessible")
            return False
        
        return True
    
    def add_accessibility_fixes(self):
        """Add platforms or enemies to fix any accessibility issues."""
        # Re-validate and add fixes where needed
        floating_platforms = [p for p in self.platforms if p['type'] != 'ground']
        
        # Sort by x position
        floating_platforms.sort(key=lambda p: p['x'])
        
        fixes_added = 0
        
        for i in range(len(floating_platforms) - 1):
            current = floating_platforms[i]
            next_platform = floating_platforms[i + 1]
            
            # Check if next platform is reachable
            vertical_dist = abs(next_platform['y'] - current['y'])
            horizontal_dist = abs(next_platform['x'] - current['x'])
            
            # If too far, add a stepping stone
            if vertical_dist > SAFE_JUMP_HEIGHT - 30 or horizontal_dist > self.safe_horizontal_distance:
                # Add intermediate platform
                mid_x = (current['x'] + next_platform['x']) // 2
                mid_y = max(current['y'], next_platform['y']) - SAFE_JUMP_HEIGHT // 2
                
                # Make sure it's not too high
                mid_y = max(100, min(self.level_height - 100, mid_y))
                
                intermediate_platform = {
                    'x': mid_x,
                    'y': mid_y,
                    'width': 120,
                    'height': 20,
                    'type': 'normal'
                }
                
                self.platforms.append(intermediate_platform)
                fixes_added += 1
        
        if fixes_added > 0:
            print(f"Added {fixes_added} intermediate platforms for accessibility")
        
        return fixes_added

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
