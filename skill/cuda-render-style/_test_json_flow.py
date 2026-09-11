#!/usr/bin/env python3
"""Render test + JSON I/O flow test — self-contained."""
import json
import os
import sys
import subprocess
import tempfile
import time
from pathlib import Path

PLUGIN_ROOT = Path(r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard")
SKILL_DIR = PLUGIN_ROOT / "skill" / "cuda-render-style"
SD_GENERATE = PLUGIN_ROOT / "scripts" / "sd_generate.py"

# Thư mục test output
TEST_DIR = SKILL_DIR / "test_output"
TEST_DIR.mkdir(exist_ok=True)

def run_render_with_json(prompt, output_name, **extra):
    """Render using JSON I/O flow — giống cách 3ds Max sẽ gọi."""
    input_path = TEST_DIR / f"{output_name}_input.json"
    output_path = TEST_DIR / f"{output_name}_output.json"
    png_path = TEST_DIR / f"{output_name}.png"
    
    # Viết input JSON
    input_data = {
        "prompt": prompt,
        "model": "sd15",
        "width": 512,
        "height": 512,
        "steps": 20,
        "guidance": 7.5,
        "seed": int(time.time() * 1000) % 100000,
        **extra
    }
    if "negative" not in extra:
        input_data["negative"] = "blurry, noisy, distorted, low quality"
    input_path.write_text(json.dumps(input_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📝 Input JSON: {input_path}")
    
    # Gọi sd_generate.py với JSON I/O (giống cách 3ds Max shellLaunch sẽ gọi)
    cmd = [
        sys.executable, str(SD_GENERATE),
        "--input-json", str(input_path),
        "--output-json", str(output_path),
        "--output", str(png_path),
    ]
    print(f"🚀 Command: {' '.join(cmd)}")
    
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    elapsed = time.time() - start
    
    print(f"⏱️  Elapsed: {elapsed:.1f}s")
    print(f"📄 STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"⚠️  STDERR:\n{result.stderr}")
    
    # Đọc output JSON
    if output_path.exists():
        output_data = json.loads(output_path.read_text(encoding="utf-8"))
        print(f"📊 Output JSON: {json.dumps(output_data, indent=2, ensure_ascii=False)}")
        return output_data
    else:
        print(f"❌ Output JSON not found: {output_path}")
        return None

def main():
    print("=" * 60)
    print("JSON I/O FLOW TEST — Render test cho plugin 3ds Max")
    print("=" * 60)
    print()
    
    # Test 1: Interior photorealistic (giống scene architecture)
    print("─── TEST 1: Interior photorealistic ───")
    result1 = run_render_with_json(
        "modern architectural interior, photorealistic, soft daylight, polished concrete floor, floor-to-ceiling windows, wooden furniture, minimalist design, 8k, architectural visualization",
        "test_01_interior",
        width=512,
        height=512,
        steps=20,
        guidance=7.5,
    )
    print()
    
    # Test 2: Exterior daylight — resolution 768 (quality cao hơn)
    print("─── TEST 2: Exterior 768x768 ───")
    result2 = run_render_with_json(
        "modern house exterior, bright sunny day, lush green garden, white brick facade, glass windows, architectural visualization, photorealistic, high detail, wide angle",
        "test_02_exterior",
        width=768,
        height=768,
        steps=25,
        guidance=8.0,
    )
    print()
    
    # Test 3: Interior chi tiết — steps cao (quality tối đa SD1.5)
    print("─── TEST 3: Interior quality cao (steps 30, CFG 8) ───")
    result3 = run_render_with_json(
        "luxury penthouse living room, city skyline view through floor-to-ceiling windows, elegant furniture, warm ambient lighting, high ceiling, photorealistic, premium architectural visualization, 8k, highly detailed",
        "test_03_penthouse",
        width=512,
        height=512,
        steps=30,
        guidance=8.0,
    )
    print()
    
    # Tổng kết
    print("=" * 60)
    print("TOTAL SUMMARY")
    print("=" * 60)
    all_ok = True
    for name, result in [("TEST 1", result1), ("TEST 2", result2), ("TEST 3", result3)]:
        if result and result.get("status") == "success":
            print(f"✅ {name}: OK — {result.get('output_path', 'N/A')} — {result.get('inference_time', '?')}s")
        else:
            print(f"❌ {name}: FAILED")
            all_ok = False
    
    png_dir = TEST_DIR
    pngs = list(png_dir.glob("*.png"))
    print(f"\n📁 Total PNG files: {len(pngs)}")
    for p in pngs:
        size_kb = p.stat().st_size / 1024
        print(f"  - {p.name}: {size_kb:.0f} KB")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
