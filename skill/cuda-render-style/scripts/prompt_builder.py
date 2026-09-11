#!/usr/bin/env python3
"""
prompt_builder.py — Prompt engineering helper

Tự động build prompt chất lượng cao cho architectural visualization
dựa trên các templates và rules.
"""

import argparse
import random
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

# ──────────────────────────────────────────────────────────────────────
# Prompt component libraries
# ──────────────────────────────────────────────────────────────────────

TIME_OF_DAY = [
    "morning sunlight streaming through windows",
    "golden hour warm glow",
    "soft overcast daylight",
    "dramatic afternoon shadows",
    "blue hour twilight",
    "night interior with warm artificial lighting",
    "bright midday sun",
    "diffused cloudy day light",
]

LIGHTING_STYLES = [
    "natural soft daylight",
    "cinematic dramatic lighting",
    "studio softbox lighting",
    "volumetric light rays",
    "high contrast chiaroscuro",
    "ambient occlusion rich shadows",
    "global illumination warm",
    "cool tone ambient fill",
]

ARCHITECTURE_TYPES = [
    "modern minimalist interior",
    "industrial loft space",
    "contemporary residential interior",
    "commercial office space",
    "luxury penthouse",
    "scandinavian design interior",
    "japanese zen interior",
    "mid-century modern",
    "brutalist concrete architecture",
    "glass and steel contemporary",
]

MATERIALS = [
    "polished concrete floors",
    "oak wood flooring",
    "marble surfaces",
    "exposed brick walls",
    "microcement walls",
    "large format tile",
    "warm maple wood",
    "black steel frame windows",
    "floor-to-ceiling glass",
    "natural stone cladding",
]

DECOR_ELEMENTS = [
    "minimalist furniture",
    "abstract art on walls",
    "potted indoor plants",
    "sculptural lighting fixtures",
    "textured rugs",
    "modern seating area",
    "coffee table with magazine",
    "bookshelf with curated books",
]

CAMERA_ANGLES = [
    "eye-level perspective",
    "slightly elevated wide angle",
    "corner perspective showing depth",
    "low angle dramatic view",
    "symmetrical frontal view",
    "diagonal leading lines",
]

NEXUS_QUALITIES = [
    "photorealistic",
    "8k resolution",
    "architectural digest style",
    "highly detailed",
    "unreal engine 5 render quality",
    "corona renderer aesthetic",
    "ray tracing realistic",
    "sharp focus",
    "depth of field subtle",
]

NEGATIVE_PROMPT = (
    "blurry, low quality, deformed, ugly, bad proportions, "
    "cartoon, anime, painting, drawing, sketch, watermark, text, logo"
)


def build_prompt(
    arch_type=None,
    time_of_day=None,
    lighting=None,
    materials=None,
    decor=None,
    camera=None,
    quality=None,
    custom=None,
    separator="|",
):
    """
    Build một prompt architectural visualization từ các component.

    Args:
        arch_type: Loại kiến trúc (mặc định random)
        time_of_day: Thời gian trong ngày
        lighting: Phong cách ánh sáng
        materials: Vật liệu
        decor: decor elements
        camera: Góc máy
        quality: Độ chất lượng
        custom: Custom prompt bổ sung
        separator: Separator giữa các component

    Returns:
        Tuple (positive_prompt, negative_prompt)
    """
    arch_type = arch_type or random.choice(ARCHITECTURE_TYPES)
    time_of_day = time_of_day or random.choice(TIME_OF_DAY)
    lighting = lighting or random.choice(LIGHTING_STYLES)
    materials = materials or random.choice(MATERIALS)
    decor = decor or random.choice(DECOR_ELEMENTS)
    camera = camera or random.choice(CAMERA_ANGLES)
    quality = quality or random.choice(NEXUS_QUALITIES)

    parts = [
        arch_type,
        time_of_day,
        lighting,
        materials,
        decor,
        camera,
        quality,
    ]

    if custom:
        parts.append(custom)

    positive = ", ".join(parts)
    return positive, NEGATIVE_PROMPT


def build_from_scene_context(object_count, material_count, has_textures, camera_focal_mm):
    """
    Build prompt từ ngữ cảnh scene 3ds Max.

    Args:
        object_count: Số object trong view
        material_count: Số material detected
        has_textures: Có texture hay không
        camera_focal_mm: Focal length camera (mm)

    Returns:
        Tuple (positive, negative)
    """
    # Xác định style từ scene
    if object_count > 20:
        arch_desc = "complex architectural scene with multiple elements"
    elif object_count > 10:
        arch_desc = "architectural interior with moderate detail"
    else:
        arch_desc = "minimalist architectural space"

    if camera_focal_mm and camera_focal_mm > 0:
        if camera_focal_mm < 20:
            lens_desc = "ultra-wide angle lens distortion"
        elif camera_focal_mm < 35:
            lens_desc = "wide angle architectural lens"
        elif camera_focal_mm < 85:
            lens_desc = "standard architectural perspective"
        else:
            lens_desc = "telephoto architectural compression"
    else:
        lens_desc = "natural architectural perspective"

    has_texture_note = "with detailed textures" if has_textures else "with material definition"

    positive = f"{arch_desc}, {lens_desc}, {has_texture_note}, natural daylight, photorealistic, 8k"
    return positive, NEGATIVE_PROMPT


def generate_variations(base_prompt, count=5, seed=None):
    """
    Tạo nhiều biến thể của một prompt cơ bản.

    Args:
        base_prompt: Prompt gốc
        count: Số biến thể
        seed: Seed cho random

    Returns:
        List các prompt string
    """
    if seed is not None:
        random.seed(seed)

    variations = []
    modifiers = [
        "cinematic lighting",
        "studio lighting",
        "golden hour",
        "soft overcast",
        "dramatic shadows",
        "warm interior glow",
        "cool ambient",
        "volumetric rays",
        "high contrast",
        "minimalist clean",
    ]

    for i in range(count):
        mod = random.choice(modifiers)
        variation = f"{base_prompt}, {mod}"
        variations.append(variation)

    return variations


def main():
    parser = argparse.ArgumentParser(description="Prompt Builder for Architectural Visualization")
    parser.add_argument("--random", action="store_true", help="Generate random prompt")
    parser.add_argument("--count", type=int, default=1, help="Number of prompts to generate")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--arch", type=str, help="Architecture type")
    parser.add_argument("--time", type=str, help="Time of day")
    parser.add_argument("--light", type=str, help="Lighting style")
    parser.add_argument("--material", type=str, help="Material")
    parser.add_argument("--decor", type=str, help="Decor element")
    parser.add_argument("--camera", type=str, help="Camera angle")
    parser.add_argument("--quality", type=str, help="Quality tag")
    parser.add_argument("--custom", type=str, help="Custom prompt addition")
    parser.add_argument("--scene", action="store_true", help="Build from scene context (uses random stats)")
    parser.add_argument("--list", action="store_true", help="List available components")
    args = parser.parse_args()

    if args.list:
        print("Available components:")
        print(f"\nArchitecture types ({len(ARCHITECTURE_TYPES)}):")
        for i, a in enumerate(ARCHITECTURE_TYPES, 1):
            print(f"  {i}. {a}")
        print(f"\nTime of day ({len(TIME_OF_DAY)}):")
        for i, t in enumerate(TIME_OF_DAY, 1):
            print(f"  {i}. {t}")
        print(f"\nLighting styles ({len(LIGHTING_STYLES)}):")
        for i, l in enumerate(LIGHTING_STYLES, 1):
            print(f"  {i}. {l}")
        return 0

    if args.scene:
        # Simulate scene context
        positive, negative = build_from_scene_context(
            object_count=random.randint(5, 30),
            material_count=random.randint(1, 8),
            has_textures=random.choice([True, False]),
            camera_focal_mm=random.choice([24, 35, 50, 85]),
        )
        print(f"Positive: {positive}")
        print(f"Negative: {negative}")
        return 0

    if args.random:
        for i in range(args.count):
            pos, neg = build_prompt(seed=args.seed)
            print(f"\n--- Variation {i + 1} ---")
            print(f"Positive: {pos}")
            print(f"Negative: {neg}")
        return 0

    pos, neg = build_prompt(
        arch_type=args.arch,
        time_of_day=args.time,
        lighting=args.light,
        materials=args.material,
        decor=args.decor,
        camera=args.camera,
        quality=args.quality,
        custom=args.custom,
    )
    print(f"Positive: {pos}")
    print(f"Negative: {neg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
