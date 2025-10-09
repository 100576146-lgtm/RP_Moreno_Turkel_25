import constants as const


def generate_levels():
    themes = [
        # 1. The Big Melt-down – a lava-and-cheese fondue factory
        {"name": "The Big Melt-down", "sky_top": const.PEACH, "sky_bottom": const.CORAL,
         "enemy_palette": [const.CREAM, const.SOFT_YELLOW, const.CORAL],
         "platform_style": "cheese_lava", "bg_motif": "fondue_smoke",
         "quirks": "lava_cheese, fondue_geysers, melty_platforms"},
        # 2. Moss-t Be Joking – slippery moss-covered rocks
        {"name": "Moss-t Be Joking", "sky_top": const.MINT_GREEN, "sky_bottom": const.PASTEL_GREEN,
         "enemy_palette": [const.SAGE_GREEN, const.MINT_GREEN, const.BEIGE],
         "platform_style": "moss_rock", "bg_motif": "moss_spores", "quirks": "slippery_platforms, uneven, lots_moss"},
        # 3. Smelted Dreams – molten metal hazards and magnetic puzzles
        {"name": "Smelted Dreams", "sky_top": const.LIGHT_PURPLE, "sky_bottom": const.DUSTY_ROSE,
         "enemy_palette": [const.LIGHT_PURPLE, const.BLACK, const.SOFT_YELLOW],
         "platform_style": "metallic", "bg_motif": "sparks",
         "quirks": "molten_metal, moving_magnets, polarity_puzzles"},
        # 4. Frost and Furious – speedrun-style icy slides
        {"name": "Frost and Furious", "sky_top": const.SOFT_BLUE, "sky_bottom": const.LAVENDER,
         "enemy_palette": [const.SOFT_BLUE, const.WHITE, const.LAVENDER],
         "platform_style": "ice", "bg_motif": "snow_blur", "quirks": "slippery_platforms, dash_boosts, icy_slopes"},
        # 5. Boo Who? – ghost platforms appear only when you don’t look at them
        {"name": "Boo Who?", "sky_top": const.LIGHT_PURPLE, "sky_bottom": const.DUSTY_ROSE,
         "enemy_palette": [const.LIGHT_PURPLE, const.BLACK, const.WHITE],
         "platform_style": "ghost", "bg_motif": "haunt_fog",
         "quirks": "ghost_platforms, appear_when_not_looking, flicker_enemies"},
        # 6. 404: Floor Not Found – glitchy disappearing platforms
        {"name": "404: Floor Not Found", "sky_top": const.SOFT_PINK, "sky_bottom": const.BLACK,
         "enemy_palette": [const.SOFT_PINK, const.LAVENDER, const.SOFT_YELLOW],
         "platform_style": "glitch", "bg_motif": "glitch",
         "quirks": "disappearing_platforms, fake_floors, glitchy_enemies"},
        # 7. Pasta La Vista – spaghetti ropes to swing from
        {"name": "Pasta La Vista", "sky_top": const.PEACH, "sky_bottom": const.SOFT_YELLOW,
         "enemy_palette": [const.PEACH, const.SOFT_YELLOW, const.BEIGE],
         "platform_style": "spaghetti", "bg_motif": "noodle_rain",
         "quirks": "swing_ropes, pasta_platforms, meatball_obstacles"},
        # 8. Concrete Jungle – overgrown ruins with machines fighting back nature
        {"name": "Concrete Jungle", "sky_top": const.SAGE_GREEN, "sky_bottom": const.LIGHT_BROWN,
         "enemy_palette": [const.SAGE_GREEN, const.LIGHT_BROWN, const.MINT_GREEN],
         "platform_style": "concrete", "bg_motif": "vines_bricks", "quirks": "moving_barriers, machines_vs_plants, overgrowth"},
        # 9. Kraken Me Up – tentacle attacks from the deep
        {"name": "Kraken Me Up", "sky_top": const.SOFT_BLUE, "sky_bottom": const.DUSTY_ROSE,
         "enemy_palette": [const.SOFT_BLUE, const.LIGHT_PURPLE, const.BLACK],
         "platform_style": "tentacle", "bg_motif": "sea_dark",
         "quirks": "tentacle_attacks, water_hazards, rising_flood"},
    ]
    levels = []
    for i in range(9):
        width = 3000 + i * 400
        difficulty = i  # Increase hazards for later levels
        levels.append({
            "width": width,
            "height": 600,
            "difficulty": difficulty,
            "theme": themes[i % len(themes)]
        })
    return levels


