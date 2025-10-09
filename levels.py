import constants as const


def generate_levels():
    themes = [
        # MEADOW: default style but brighter flowers, green platforms, happy colors
        {"name": "Meadow", "sky_top": const.LAVENDER, "sky_bottom": const.SKY_BLUE,
          "enemy_palette": [const.SOFT_PINK, const.PASTEL_GREEN, const.SOFT_YELLOW],
          "platform_style": "grass", "bg_motif": "flowers", "quirks": None},
        # ICE: all blue/white, crystal platforms, snow enemies, platforms are slippery
        {"name": "Ice", "sky_top": const.SOFT_BLUE, "sky_bottom": const.LAVENDER,
          "enemy_palette": [const.SOFT_BLUE, const.WHITE, const.LAVENDER],
          "platform_style": "ice", "bg_motif": "ice_shards", "quirks": "slippery_platforms"},
        # FIRE: red/orange, magma blobs as enemies, platforms are rocky, falling embers
        {"name": "Fire", "sky_top": const.PEACH, "sky_bottom": const.CORAL,
          "enemy_palette": [const.CORAL, const.PEACH, const.SOFT_YELLOW],
          "platform_style": "lava", "bg_motif": "embers", "quirks": "enemies_jump"},
        # FOREST: wooden logs, green enemies, mushroom platforms are bouncy
        {"name": "Forest", "sky_top": const.MINT_GREEN, "sky_bottom": const.PASTEL_GREEN,
          "enemy_palette": [const.SAGE_GREEN, const.MINT_GREEN, const.BEIGE],
          "platform_style": "mushroom", "bg_motif": "vines", "quirks": "bouncy_mushrooms"},
        # UNDERWATER: blue/seaweed, bubble enemies, slow/floating/jiggly jumps
        {"name": "Underwater", "sky_top": const.SOFT_BLUE, "sky_bottom": const.SKY_BLUE,
          "enemy_palette": [const.SKY_BLUE, const.MINT_GREEN, const.PASTEL_GREEN],
          "platform_style": "coral", "bg_motif": "bubbles", "quirks": "slow_jumps"},
        # DESERT: beige/sandy, blocky platforms and sand enemies, moving sand clouds
        {"name": "Desert", "sky_top": const.CREAM, "sky_bottom": const.SOFT_YELLOW,
          "enemy_palette": [const.BEIGE, const.LIGHT_BROWN, const.SOFT_YELLOW],
          "platform_style": "sandstone", "bg_motif": "sand", "quirks": None},
        # NIGHT: dark, purple/blue, spooky enemies, flickering platforms
        {"name": "Night", "sky_top": const.LIGHT_PURPLE, "sky_bottom": const.DUSTY_ROSE,
          "enemy_palette": [const.LIGHT_PURPLE, const.DUSTY_ROSE, const.BLACK],
          "platform_style": "ghost", "bg_motif": "stars", "quirks": "platforms_flicker"},
        # VOLCANO: dark/red, platforms crack, enemies are fast, ash in air
        {"name": "Volcano", "sky_top": const.CORAL, "sky_bottom": const.DUSTY_ROSE,
          "enemy_palette": [const.CORAL, const.DUSTY_ROSE, const.BLACK],
          "platform_style": "volcano", "bg_motif": "ash", "quirks": "fast_enemies"},
        # SKY: sky islands, cloud platforms, rainbow enemies, floaty feel
        {"name": "Sky", "sky_top": const.SKY_BLUE, "sky_bottom": const.SOFT_BLUE,
          "enemy_palette": [const.SOFT_PINK, const.LAVENDER, const.SOFT_YELLOW],
          "platform_style": "cloud", "bg_motif": "rainbow", "quirks": "low_gravity"},
        # NEON: black bg, neon platforms, enemies glow
        {"name": "Neon", "sky_top": const.SOFT_PINK, "sky_bottom": const.LIGHT_PURPLE,
          "enemy_palette": [const.SOFT_PINK, const.MINT_GREEN, const.SOFT_YELLOW],
          "platform_style": "neon", "bg_motif": "glow", "quirks": "enemies_glow"},
    ]
    levels = []
    for i in range(10):
        width = 2800 + i * 400
        difficulty = i
        levels.append({
            "width": width,
            "height": 600,
            "difficulty": difficulty,
            "theme": themes[i % len(themes)]
        })
    return levels


