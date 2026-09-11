#!/usr/bin/env python3
"""
cuda_render_tool.py — Main Tool (Render + Fix + Detect + Clean)
Đây là tool trung tâm của cuda-render-style skill.
Mọi chức năng được gộp vào một file duy nhất để tránh phụ thuộc ngoài.

Usage:
    python3 cuda_render_tool.py render     --prompt "..." [options]
    python3 cuda_render_tool.py fix        [diagnose | fix-issue <issue>]
    python3 cuda_render_tool.py detect
    python3 cuda_render_tool.py clean
"""

import argparse
import sys
import os
import json
import time
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — relative to skill directory (cuda-render-style/)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR  # cuda_render_tool.py nằm trong skill/
MODELS_DIR = SKILL_DIR / "models"
SCRIPTS_DIR = SKILL_DIR / "scripts"

# Insert scripts/ into path để import module con
sys.path.insert(0, str(SCRIPTS_DIR))

from detect_gpu import detect_hardware, get_recommendation
from model_manager import (
    list_models, check_model_exists, get_model_path,
    download_model, auto_select_model_key, get_model_info,
)
from error_handler import handle_oom_error, handle_cuda_error, handle_missing_model, safe_generate


# ---------------------------------------------------------------------------
# Hardware detection (shortcut)
# ---------------------------------------------------------------------------
def detect():
    """In hardware info + recommendation."""
    hw = detect_hardware()
    print("=" * 60)
    print("CUDA RENDER — HARDWARE DETECTION")
    print("=" * 60)
    print(f"GPU:          {hw['gpu_name']}")
    print(f"VRAM:         {hw['gpu_vram_mb']} MB ({hw['gpu_vram_gb']} GB)")
    print(f"CUDA Toolkit: {'✅ ' + hw['cuda_version'] if hw['cuda_available'] else '❌ Not found'}")
    print(f"PyTorch:      {hw['pytorch_version']}")
    print(f"PyTorch CUDA: {'✅ Available' if hw['pytorch_cuda'] else '❌ Not available'}")
    if hw['gpu_device']:
        print(f"Device:       {hw['gpu_device']}")
        print(f"Compute Cap:  {hw['compute_capability']}")
    print(f"Disk free:    {hw['disk_free_gb']} GB")
    print(f"Python:       {hw['python_version']}")

    rec = get_recommendation(hw)
    print("\n─── RECOMMENDATION ───")
    print(f"Model:        {rec['model_name']} ({rec['model_repo']})")
    print(f"Resolution:   {rec['width']}x{rec['height']}")
    print(f"Steps:        {rec['steps']}")
    print(f"Guidance:     {rec['guidance']}")
    print(f"CPU Offload:  {rec['cpu_offload']}")
    if rec.get('note'):
        print(f"Note:         {rec['note']}")

    # Model local check
    print("\n─── LOCAL MODELS ───")
    for key in ['sd15', 'sdxl-base', 'sdxl-refiner', 'flux-schnell', 'flux-dev']:
        exists = check_model_exists(key)
        size = 0
        if exists:
            mp = get_model_path(key)
            size = sum(f.stat().st_size for f in mp.rglob('*') if f.is_file()) / 1024**2
        print(f"  {'✅' if exists else '❌'} {key}: {size:.0f} MB" if exists else f"  ❌ {key}: Not found")

    return 0


# ---------------------------------------------------------------------------
# Clean VRAM
# ---------------------------------------------------------------------------
def clean():
    """Dọn VRAM."""
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("✅ VRAM cleaned")
        else:
            print("⚠️ CUDA không available — không cần clean")
        return 0
    except Exception as e:
        print(f"❌ Clean lỗi: {e}")
        return 1


# ---------------------------------------------------------------------------
# Fix / Diagnose
# ---------------------------------------------------------------------------
def fix(args):
    """Chẩn đoán hoặc fix-issue."""
    if args.subcommand == "fix-issue":
        return _fix_issue(args.issue)
    return _diagnose()


def _diagnose():
    """Chạy full diagnosis."""
    hw = detect_hardware()
    pt_info = {
        "available": False,
        "version": "N/A",
        "cuda_available": False,
        "device": None,
        "compute_cap": None,
        "error": None,
    }
    try:
        import torch
        pt_info = {
            "available": True,
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "compute_cap": torch.cuda.get_device_capability(0) if torch.cuda.is_available() else None,
        }
    except Exception as e:
        pt_info["error"] = str(e)

    print("\n" + "=" * 60)
    print("CUDA RENDER FIX TOOL — DIAGNOSIS")
    print("=" * 60)

    print(f"\n[1/4] GPU: {hw['gpu_name']} ({hw['gpu_vram_mb']} MB VRAM)")

    cuda_avail = hw['cuda_available']
    print(f"\n[2/4] CUDA Toolkit: {'✅ ' + hw['cuda_version'] if cuda_avail else '❌ Not found'}")

    print(f"\n[3/4] PyTorch: {'✅ ' + pt_info.get('version', 'N/A')}")
    print(f"        CUDA Available: {'✅' if pt_info.get('cuda_available') else '❌'}")
    if pt_info.get('cuda_available'):
        print(f"        Device: {pt_info.get('device')}")
        print(f"        Compute Cap: {pt_info.get('compute_cap')}")
    else:
        if pt_info.get('error'):
            print(f"        Error: {pt_info.get('error')}")

    print(f"\n[4/4] Model Check:")
    for key in ['sd15', 'sdxl-base', 'flux-schnell', 'flux-dev']:
        exists, size = (check_model_exists(key),
                         sum(f.stat().st_size for f in get_model_path(key).rglob('*') if f.is_file()) / 1024**2
                         if check_model_exists(key) else 0)
        if exists:
            print(f"  ✅ {key}: {size:.0f} MB")
        else:
            print(f"  ❌ {key}: Not found")

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    issues = []
    if not cuda_avail:
        issues.append(("CUDA Toolkit missing", "Install CUDA Toolkit from https://developer.nvidia.com/cuda-toolkit"))
    if not pt_info.get('cuda_available'):
        if pt_info.get('available'):
            issues.append(("PyTorch CUDA not enabled",
                           "Reinstall PyTorch CUDA: python3 -m pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128"))
        else:
            issues.append(("PyTorch not installed", "Install PyTorch: python3 -m pip install torch"))
    if pt_info.get('cuda_available') and hw['gpu_vram_mb'] < 4096:
        issues.append(("Low VRAM", "Use SD1.5 model, resolution 512x512"))

    if not issues:
        print("✅ System OK — ready to render")
        print("\nQuick start:")
        print("  python3 cuda_render_tool.py render --prompt 'your prompt here'")
    else:
        print(f"⚠️ Found {len(issues)} issue(s):")
        for i, (issue, fix_cmd) in enumerate(issues, 1):
            print(f"\n  {i}. {issue}")
            print(f"     Fix: {fix_cmd}")

    return 0


def _fix_issue(issue: str):
    """Fix specific issue — in ra command."""
    print("\n" + "=" * 60)
    print(f"FIX ISSUE: {issue.upper()}")
    print("=" * 60)

    commands = {
        "cuda": [
            ("Check CUDA Toolkit", "nvcc --version"),
            ("Check PyTorch CUDA", "python3 -c 'import torch; print(torch.cuda.is_available())'"),
            ("Reinstall PyTorch CUDA",
             "python3 -m pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128"),
        ],
        "oom": [
            ("Clean VRAM", "python3 cuda_render_tool.py clean"),
            ("Reduce resolution", "python3 cuda_render_tool.py render --prompt '...' --width 512 --height 512"),
            ("Use smaller model", "python3 cuda_render_tool.py render --prompt '...' --model sd15"),
            ("Use tile-based upscale", "python3 cuda_render_tool.py render --prompt '...' --upscale"),
        ],
        "model": [
            ("List available models", "python3 scripts/model_manager.py --list"),
            ("Download model", "python3 scripts/model_manager.py sd15"),
            ("Auto-select & download", "python3 scripts/model_manager.py --auto --download"),
        ],
        "quality": [
            ("Increase steps", "python3 cuda_render_tool.py render --prompt '...' --steps 50"),
            ("Increase guidance", "python3 cuda_render_tool.py render --prompt '...' --guidance 9.0"),
            ("Use better model", "python3 cuda_render_tool.py render --prompt '...' --model sdxl-base"),
            ("Improve prompt", "python3 scripts/prompt_builder.py --random --count 5"),
        ],
        "disk": [
            ("Check disk space", "df -h"),
            ("Clean pip cache", "python3 -m pip cache purge"),
            ("Move model to external drive", "Download model to external drive, set MODEL_PATH env"),
        ],
    }

    if issue not in commands:
        print(f"❌ Unknown issue: {issue}")
        print(f"Available: {', '.join(commands.keys())}")
        return 1

    for desc, cmd in commands[issue]:
        print(f"\n[{desc}]")
        print(f"  → {cmd}")

    return 0


# ---------------------------------------------------------------------------
# Render — core
# ---------------------------------------------------------------------------
def render(args):
    """Render ảnh từ prompt. Tự động chọn model, xử lý lỗi, fallback."""
    print("=" * 55)
    print("CUDA RENDER TOOL — RENDER")
    print("=" * 55)

    hw = detect_hardware()
    print(f"GPU: {hw['gpu_name']} | VRAM: {hw['gpu_vram_gb']} GB")

    if not hw['pytorch_cuda']:
        print("❌ PyTorch CUDA không available — không thể render local")
        print("  Gỡ về External API hoặc cài lại:")
        print("  python3 -m pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128")
        return 1

    model_key = args.model or "sd15"
    print(f"Model key: {model_key}")

    # Kiểm tra model local
    if not check_model_exists(model_key):
        print(f"❌ Model '{model_key}' không tồn tại local")
        print(f"  Available: sd15, sdxl-base, sdxl-refiner, flux-schnell, flux-dev")
        print(f"  Download: python3 scripts/model_manager.py {model_key}")
        # Fallback tự động: chọn model small nhất có sẵn
        for fallback_key in ['sd15', 'sdxl-base']:
            if check_model_exists(fallback_key):
                print(f"  → Fallback to {fallback_key} (có sẵn local)")
                model_key = fallback_key
                break
        else:
            print("❌ Không có model nào local — render không thể tiến hành")
            return 1

    model_path = get_model_path(model_key)
    print(f"Model path: {model_path}")

    # Load pipeline
    print(f"Loading pipeline '{model_key}' ...")
    t0 = time.time()
    try:
        from diffusers import DiffusionPipeline
        import torch

        model_info = get_model_info(model_key)
        dtype = model_info['dtype'] if model_info else torch.float16
        variant = model_info.get('variant') if model_info else None

        pipe = DiffusionPipeline.from_pretrained(
            str(model_path),
            torch_dtype=dtype,
            safety_checker=None,
        )
        pipe = pipe.to("cuda")
        elapsed = time.time() - t0
        print(f"Pipeline loaded in {elapsed:.1f}s")
    except Exception as e:
        print(f"❌ Load pipeline lỗi: {e}")
        return 1

    # Render
    print(f"Rendering {args.width}x{args.height} ...")
    t0 = time.time()

    try:
        generator = None
        if args.seed >= 0:
            generator = torch.Generator("cuda").manual_seed(args.seed)

        result = safe_generate(
            pipe,
            args.prompt,
            max_retries=2,
            negative_prompt=args.negative or None,
            height=args.height,
            width=args.width,
            num_inference_steps=args.steps,
            guidance_scale=args.guidance,
            generator=generator,
        )
        img = result
    except Exception as e:
        print(f"❌ Render lỗi: {e}")
        err_type = handle_cuda_error(e)
        print(f"  Lỗi loại: {err_type['error_type']}")
        for sug in err_type.get('suggestions', []):
            print(f"  → {sug['description']}: {sug['command']}")
        return 1

    elapsed = time.time() - t0
    print(f"Render xong: {args.width}x{args.height} — {elapsed:.1f}s")

    # Output
    if not args.output:
        ts = int(time.time() * 1000)
        out_dir = os.environ.get("NC_RENDER_OUTPUT_DIR",
                                 str(Path.home() / "AppData/Local/Temp"))
        args.output = os.path.join(out_dir, f"cuda_render_{ts}.png")

    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)
    print(f"Đã lưu: {out_path}")

    # Config metadata
    config_path = SKILL_DIR / "cuda_render_config.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    except Exception:
        config = {}
    config["last_render"] = {
        "path": out_path,
        "prompt": args.prompt,
        "model": model_key,
        "timestamp": time.time(),
    }
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Metadata saved: {config_path}")

    # Cleanup
    try:
        del pipe
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass

    print("Done.")
    return 0


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        description="cuda_render_tool.py — Main Tool (Render + Fix + Detect + Clean)",
        prog="cuda_render_tool.py",
    )
    sub = parser.add_subparsers(dest="command")

    # render
    p_render = sub.add_parser("render", help="Render ảnh từ prompt")
    p_render.add_argument("--prompt", type=str, required=True, help="Prompt")
    p_render.add_argument("--negative", type=str, default="", help="Negative prompt")
    p_render.add_argument("--model", type=str, default="sd15", help="Model key: sd15, sdxl-base, flux-schnell, flux-dev")
    p_render.add_argument("--width", type=int, default=512, help="Width")
    p_render.add_argument("--height", type=int, default=512, help="Height")
    p_render.add_argument("--steps", type=int, default=20, help="Inference steps")
    p_render.add_argument("--guidance", type=float, default=7.5, help="CFG scale")
    p_render.add_argument("--seed", type=int, default=-1, help="Seed (-1 = random)")
    p_render.add_argument("--output", type=str, default="", help="Output PNG path")

    # fix
    p_fix = sub.add_parser("fix", help="Chẩn đoán hoặc fix issue")
    p_fix_sub = p_fix.add_subparsers(dest="subcommand")
    p_fix_sub.add_parser("diagnose", help="Full diagnosis")
    p_fix_issue = p_fix_sub.add_parser("fix-issue", help="Fix specific issue")
    p_fix_issue.add_argument("issue", choices=["cuda", "oom", "model", "quality", "disk"])

    # detect
    sub.add_parser("detect", help="Hardware detection nhanh")

    # clean
    sub.add_parser("clean", help="Clean VRAM")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "render":
        return render(args)
    elif args.command == "fix":
        return fix(args)
    elif args.command == "detect":
        return detect()
    elif args.command == "clean":
        return clean()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
