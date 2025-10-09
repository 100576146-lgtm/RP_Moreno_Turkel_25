import constants as const
import random
from typing import List, Dict, Any

# --- Themes updated to include specific texture/asset filenames ---
LEVEL_THEMES: List[Dict[str, Any]] = [
    {
        "name": "The Big Melt-down",
        "sky_top": const.HAZY_ORANGE, "sky_bottom": const.MOLTEN_RED,
        "enemy_palette": [const.FONDUE_YELLOW, const.BURNT_ORANGE, const.SOOT_GREY],
        "ground_texture": "melted_cheese_floor.png",
        "platform_texture": "cheese_platform.png",
        "background_image": "fondue_factory_bg.png",
        "quirks": "slowing_cheese_pools"
    },
    {
        "name": "Moss-t Be Joking",
        "sky_top": const.MISTY_GREY, "sky_bottom": const.FOREST_FLOOR_GREEN,
        "enemy_palette": [const.MOSS_GREEN, const.WET_ROCK_GREY, const.DARK_BROWN],
        "ground_texture": "mossy_ground.png",
        "platform_texture": "mossy_boulder.png",
        "background_image": "ancient_ruins_bg.png",
        "quirks": "slippery_platforms"
    },
    {
        "name": "Smelted Dreams",
        "sky_top": const.SMOKE_GREY, "sky_bottom": const.FORGE_GLOW,
        "enemy_palette": [const.STEEL_GREY, const.MOLTEN_ORANGE, const.ELECTRIC_BLUE],
        "ground_texture": "grated_metal_floor.png",
        "platform_texture": "metal_beam.png",
        "background_image": "smeltery_gears_bg.png",
        "quirks": "magnetic_platforms"
    },
    {
        "name": "Frost and Furious",
        "sky_top": const.GLACIER_WHITE, "sky_bottom": const.FROST_BLUE,
        "enemy_palette": [const.ICE_BLUE, const.SNOW_WHITE, const.WARNING_RED],
        "ground_texture": "packed_snow_ground.png",
        "platform_texture": "ice_ramp.png",
        "background_image": "blizzard_speed_bg.png",
        "quirks": "forced_movement_slides"
    },
    {
        "name": "Boo Who?",
        "sky_top": const.MIDNIGHT_PURPLE, "sky_bottom": const.BLACK,
        "enemy_palette": [const.ECTOPLASM_GREEN, const.GHOSTLY_WHITE, const.SHADOW_GREY],
        "ground_texture": "haunted_floorboards.png",
        "platform_texture": "spectral_platform.png",
        "background_image": "haunted_mansion_bg.png",
        "quirks": "look_away_platforms"
    },
    {
        "name": "404: Floor Not Found",
        "sky_top": const.BLACK, "sky_bottom": const.BLACK,
        "enemy_palette": [const.GLITCH_GREEN, const.ERROR_RED, const.STATIC_WHITE],
        "ground_texture": "digital_grid_floor.png",
        "platform_texture": "glitch_block.png",
        "background_image": "matrix_code_bg.png",
        "quirks": "random_disappearing_platforms"
    },
    {
        "name": "Pasta La Vista",
        "sky_top": const.PARMESAN_YELLOW, "sky_bottom": const.MARINARA_RED,
        "enemy_palette": [const.TOMATO_RED, const.BASIL_GREEN, const.MOZZARELLA_WHITE],
        "ground_texture": "marinara_sauce_ground.png",
        "platform_texture": "meatball_platform.png",
        "background_image": "giant_kitchen_bg.png",
        "quirks": "spaghetti_vines_swing"
    },
    {
        "name": "Concrete Jungle",
        "sky_top": const.CITY_SMOG_GREY, "sky_bottom": const.OVERGROWTH_GREEN,
        "enemy_palette": [const.RUST_ORANGE, const.CONCRETE_GREY, const.IVY_GREEN],
        "ground_texture": "overgrown_pavement.png",
        "platform_texture": "cracked_concrete_vines.png",
        "background_image": "ruined_cityscape_bg.png",
        "quirks": "hostile_robotic_turrets"
    },
    {
        "name": "Kraken Me Up",
        "sky_top": const.MURKY_TEAL, "sky_bottom": const.ABYSSAL_BLACK,
        "enemy_palette": [const.DEEP_SEA_BLUE, const.BIOLUMINESCENT_GREEN, const.INK_BLACK],
        "ground_texture": "sandy_seabed.png",
        "platform_texture": "sunken_ship_plank.png",
        "background_image": "deep_sea_abyss_bg.png",
        "quirks": "tentacle_attacks_from_background"
    },
]


def generate_levels(num_levels: int = 10) -> List[Dict[str, Any]]:
    """
    Generates a list of unique, progressively difficult game levels.
    """
    levels = []
    available_themes = LEVEL_THEMES.copy()
    random.shuffle(available_themes)

    for i in range(num_levels):
        width = 2800 + i * 400
        difficulty = i
        theme = available_themes[i % len(available_themes)]

        levels.append({
            "width": width,
            "height": 600,
            "difficulty": difficulty,
            "theme": theme
        })

    return levels