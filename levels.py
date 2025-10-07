import constants as const


def generate_levels():
    themes = [
        {"name": "Meadow", "sky_top": const.LAVENDER, "sky_bottom": const.SKY_BLUE},
        {"name": "Ice", "sky_top": const.SOFT_BLUE, "sky_bottom": const.LAVENDER},
        {"name": "Fire", "sky_top": const.PEACH, "sky_bottom": const.CORAL},
        {"name": "Forest", "sky_top": const.MINT_GREEN, "sky_bottom": const.PASTEL_GREEN},
        {"name": "Underwater", "sky_top": const.SOFT_BLUE, "sky_bottom": const.SKY_BLUE},
        {"name": "Desert", "sky_top": const.CREAM, "sky_bottom": const.SOFT_YELLOW},
        {"name": "Night", "sky_top": const.LIGHT_PURPLE, "sky_bottom": const.DUSTY_ROSE},
        {"name": "Volcano", "sky_top": const.CORAL, "sky_bottom": const.DUSTY_ROSE},
        {"name": "Sky", "sky_top": const.SKY_BLUE, "sky_bottom": const.SOFT_BLUE},
        {"name": "Neon", "sky_top": const.SOFT_PINK, "sky_bottom": const.LIGHT_PURPLE},
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


