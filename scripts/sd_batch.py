#!/usr/bin/env python3
"""
sd_batch.py — Batch render từ 3ds Max macroScript.
Được gọi từ NC_Render_Bridge_v1.mcr btnRender3 (Local SD CUDA, batch mode).

Input: --prompts "p1|||p2|||p3"
Output: nhiều PNG trong thư mục batch
"""

import argparse
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Thêm paths để import sd_generate
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
PLUGIN_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import sd_generate  # noqa: E402


def parse_batch_args():
    parser = argparse.ArgumentParser(
        description="sd_batch.py — Batch render cho NC-Render"
    )
    parser.add_argument("--prompts", type=str, required=True,
                        help="Danh sách prompt phân cách bằng |||")
    parser.add_argument("--model", type=str, default="sd15")
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--guidance", type=float, default=7.5)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--negative", type=str, default="")
    parser.add_argument("--output", type=str, default="",
                        help="Thư mục output (mặc định: temp/nc_batch_<ts>)")
    parser.add_argument("--reference", type=str, default="")
    parser.add_argument("--strength", type=float, default=None)
    return parser.parse_args()


def main():
    args = parse_batch_args()

    prompts = [p.strip() for p in args.prompts.split("|||") if p.strip()]
    if not prompts:
        print("❌ Không có prompt nào")
        return 1

    ts = int(time.time() * 1000)
    output_dir = args.output or os.path.join(
        os.environ.get("NC_RENDER_OUTPUT_DIR",
                        str(Path.home() / "AppData/Local/Temp")),
        f"nc_batch_{ts}"
    )
    os.makedirs(output_dir, exist_ok=True)

    print(f"Batch: {len(prompts)} prompts → {output_dir}")

    results = []
    for i, prompt in enumerate(prompts, 1):
        out_path = os.path.join(output_dir, f"batch_{i:02d}.png")
        print(f"\n─── [{i}/{len(prompts)}] {prompt[:70]}... ───")

        # Gọi sd_generate cmd_generate với args cụ thể
        gen_args = argparse.Namespace(
            prompt=prompt,
            model=args.model,
            width=args.width,
            height=args.height,
            steps=args.steps,
            guidance=args.guidance,
            seed=args.seed,
            output=out_path,
            reference=args.reference if i == 1 else "",
            strength=args.strength,
            negative=args.negative,
        )
        code = sd_generate.cmd_generate(gen_args)
        results.append((i, prompt[:50], code))

    # Summary
    print("\n" + "=" * 50)
    print("BATCH SUMMARY")
    print("=" * 50)
    ok = sum(1 for _, _, c in results if c == 0)
    fail = len(results) - ok
    for i, p, c in results:
        status = "✅" if c == 0 else "❌"
        print(f"  {status} [{i}] {p}... → {'OK' if c == 0 else 'FAIL'}")
    print(f"\nTotal: {ok} OK, {fail} FAIL — output: {output_dir}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
