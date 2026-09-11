#!/usr/bin/env python3
"""
NC-Render AI Studio — CUDA Local Render Test (v2)
Sử dụng diffusers DiffusionPipeline để sinh ảnh từ prompt bằng GPU local.
Được gọi từ NC_Render_Bridge_v1.mcr button "Render Test (CUDA Local)".

Usage:
    python3 nc_cuda_render.py --prompt "..." --width 512 --height 512 --output out.png
"""

import argparse
import sys
import os
import time
import json
from pathlib import Path

import torch
from PIL import Image
from diffusers import DiffusionPipeline

# ---------------------------------------------------------------------------
# Cấu hình
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "runwayml/stable-diffusion-v1-5"
CACHE_DIR = os.path.expanduser("~/.cache/huggingface/hub")
OUTPUT_DIR = os.environ.get("NC_RENDER_OUTPUT_DIR", str(Path.home() / "AppData/Local/Temp"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NC-Render CUDA Local Render Test")
    parser.add_argument("--prompt", type=str, required=True, help="Prompt sinh ảnh")
    parser.add_argument("--negative_prompt", type=str, default="", help="Negative prompt")
    parser.add_argument("--width", type=int, default=512, help="Width")
    parser.add_argument("--height", type=int, default=512, help="Height")
    parser.add_argument("--steps", type=int, default=20, help="Inference steps")
    parser.add_argument("--guidance_scale", type=float, default=7.5, help="CFG scale")
    parser.add_argument("--seed", type=int, default=-1, help="Seed (-1 = random)")
    parser.add_argument("--output", type=str, default="", help="Output PNG path")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Model ID or local path")
    parser.add_argument("--json-out", type=str, default="", help="JSON metadata output path")
    return parser.parse_args()


def load_pipeline(model_id: str):
    """Load DiffusionPipeline. Chỉ dùng fp16 nếu GPU hỗ trợ."""
    if not torch.cuda.is_available():
        print("[NC-CUDA] LỖI: CUDA không sẵn có.", file=sys.stderr)
        sys.exit(1)

    device_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"[NC-CUDA] GPU: {device_name} | VRAM: {vram_gb:.1f} GB", flush=True)

    dtype = torch.float16 if torch.cuda.is_bf16_supported() else torch.float32
    print(f"[NC-CUDA] Loading pipeline '{model_id}' (dtype={dtype.__name__}) ...", flush=True)
    t0 = time.time()

    pipe = DiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=dtype,
        cache_dir=CACHE_DIR,
        safety_checker=None,
        variant="fp16" if dtype == torch.float16 else None,
    )
    pipe = pipe.to("cuda")

    elapsed = time.time() - t0
    print(f"[NC-CUDA] Pipeline loaded in {elapsed:.1f}s", flush=True)
    return pipe


def render(pipe, prompt: str, negative_prompt: str, width: int, height: int,
           steps: int, guidance_scale: float, seed: int) -> Image.Image:
    generator = None
    if seed >= 0:
        generator = torch.Generator("cuda").manual_seed(seed)

    t0 = time.time()
    result = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt or None,
        height=height,
        width=width,
        num_inference_steps=steps,
        guidance_scale=guidance_scale,
        generator=generator,
    )
    img = result.images[0]
    elapsed = time.time() - t0
    print(f"[NC-CUDA] Render xong: {width}x{height} — {elapsed:.1f}s", flush=True)
    return img


def main() -> int:
    args = parse_args()

    device_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"[NC-CUDA] GPU: {device_name} | VRAM: {vram_gb:.1f} GB", flush=True)

    pipe = load_pipeline(args.model)

    img = render(
        pipe,
        args.prompt,
        args.negative_prompt,
        args.width,
        args.height,
        args.steps,
        args.guidance_scale,
        args.seed,
    )

    if not args.output:
        ts = int(time.time() * 1000)
        args.output = os.path.join(OUTPUT_DIR, f"nc_cuda_render_{ts}.png")
    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    print(f"[NC-CUDA] Đã lưu: {out_path}", flush=True)

    if args.json_out:
        meta = {
            "prompt": args.prompt,
            "negative_prompt": args.negative_prompt,
            "width": args.width,
            "height": args.height,
            "steps": args.steps,
            "guidance_scale": args.guidance_scale,
            "seed": args.seed if args.seed >= 0 else None,
            "model": args.model,
            "gpu": device_name,
            "vram_gb": round(vram_gb, 2),
            "output_path": out_path,
        }
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"[NC-CUDA] Metadata saved: {args.json_out}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
