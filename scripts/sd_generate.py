#!/usr/bin/env python3
"""
sd_generate.py — Wrapper gọi CUDA render từ 3ds Max macroScript (NC_Render_Bridge_v1.mcr).
Đây là file duy nhất plugin gọi trực tiếp. Nó kiểm tra environment, chọn tool phù hợp,
và delegate về cuda_render_tool.py hoặc nc_cuda_render.py tùy tình huống.

Được gọi từ: NC_Render_Bridge_v1.mcr button "Generate from Prompt (CUDA)"
              NC_Render_Bridge_v1.mcr button "Generate + Upscale"
              NC_Render_Bridge_v1.mcr button "Batch Generate"
"""

import argparse
import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths —-relative to plugin root
# ---------------------------------------------------------------------------
PLUGIN_ROOT = Path(__file__).parent.parent  # NC_Render_Standard/
SKILL_DIR = PLUGIN_ROOT / "skill" / "cuda-render-style"
CUDA_RENDER_TOOL = SKILL_DIR / "cuda_render_tool.py"
NC_CUDA_RENDER = PLUGIN_ROOT / "scripts" / "nc_cuda_render.py"
CONFIG_FILE = SKILL_DIR / "cuda_render_config.json"


def detect_pytorch_cuda():
    """Check nhanh PyTorch CUDA availability."""
    try:
        import torch
        return torch.cuda.is_available(), torch.__version__
    except Exception:
        return False, "not installed"


def check_model_local(model_key: str) -> bool:
    """Kiểm tra model đã tải local chưa (dùng model_manager)."""
    sys.path.insert(0, str(SKILL_DIR))
    try:
        from scripts.model_manager import check_model_exists
        return check_model_exists(model_key)
    except Exception:
        return False


def get_model_path_local(model_key: str) -> Path:
    """Get local model path nếu tồn tại."""
    sys.path.insert(0, str(SKILL_DIR))
    try:
        from scripts.model_manager import get_model_path
        return get_model_path(model_key)
    except Exception:
        return None


def _write_output_json(args, ok, image, message=""):
    """Ghi JSON ket qua de macro 3ds Max doc duoc (field 'image' la uoc mo)."""
    if not getattr(args, "output_json", None):
        return
    import json
    try:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump({"ok": bool(ok), "image": image or "", "message": message}, f)
        print("[output-json] " + str(args.output_json))
    except Exception as e:
        print("warn: cannot write output-json: " + str(e))


def _default_output_path(args):
    """Mac dinh PNG vao Temp de macro luon biet duong dan ket qua."""
    if not args.output:
        import tempfile
        import time as _t
        args.output = str(Path(tempfile.gettempdir()) / ("nc_sd_" + str(int(_t.time() * 1000)) + ".png"))
    return args.output

def cmd_generate(args):
    """Generate ảnh từ prompt — xử lý tất cả cases."""
    print("=" * 55)
    print("NC-RENDER SD_GENERATE — Processing")
    print("=" * 55)

    # Nếu có input JSON, đọc và override args
    if args.input_json:
        import json
        print(f"Reading input from: {args.input_json}")
        try:
            with open(args.input_json) as f:
                input_data = json.load(f)
            if 'prompt' in input_data:
                args.prompt = input_data['prompt']
                print(f"  → prompt: {args.prompt[:60]}...")
            if 'model' in input_data:
                args.model = input_data['model']
            if 'width' in input_data:
                args.width = input_data['width']
            if 'height' in input_data:
                args.height = input_data['height']
            if 'steps' in input_data:
                args.steps = input_data['steps']
            if 'guidance' in input_data:
                args.guidance = input_data['guidance']
            if 'seed' in input_data:
                args.seed = input_data['seed']
            if 'negative' in input_data:
                args.negative = input_data['negative']
            if 'reference' in input_data and input_data['reference']:
                args.reference = input_data['reference']
            if 'strength' in input_data:
                args.strength = input_data['strength']
            if 'output' in input_data and input_data['output']:
                args.output = input_data['output']
            if 'upscale' in input_data and input_data['upscale']:
                args.upscale = True
        except Exception as e:
            print(f"❌ Error reading input JSON: {e}")
            return 1

    _default_output_path(args)
    has_cuda, pt_ver = detect_pytorch_cuda()
    print(f"PyTorch CUDA: {'✅' if has_cuda else '❌'} ({pt_ver})")

    # Xác định model key
    model_key = args.model or "sd15"
    print(f"Model: {model_key}")

    # Case 1: Có CUDA + model local → dùng cuda_render_tool.py (đầy đủ nhất)
    # Ưu tiên model local nếu có, dùng path trực tiếp để tránh download lại
    if has_cuda and check_model_local(model_key):
        model_path = get_model_path_local(model_key)
        if model_path and model_path.exists():
            print(f"  → Model local found: {model_path}")
        print(f"→ Đang dùng cuda_render_tool.py ({model_key} local)")
        render_cmd = [
            sys.executable, str(CUDA_RENDER_TOOL), "render",
            "--prompt", args.prompt,
            "--model", model_key,
            "--width", str(args.width),
            "--height", str(args.height),
            "--steps", str(args.steps),
            "--guidance", str(args.guidance),
        ]
        if args.seed is not None:
            render_cmd += ["--seed", str(args.seed)]
        if args.output:
            render_cmd += ["--output", args.output]
        if args.reference:
            render_cmd += ["--reference", args.reference]
        if args.strength is not None:
            render_cmd += ["--strength", str(args.strength)]
        if args.negative:
            render_cmd += ["--negative", args.negative]

        print(f"  Command: {' '.join(render_cmd)}")
        result = subprocess.run(render_cmd, cwd=str(SKILL_DIR),
                                capture_output=True, text=True, timeout=600)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        ok = result.returncode == 0 and Path(args.output).exists()
        _write_output_json(args, ok, args.output if ok else "",
                           (result.stdout[-500:] if ok else (result.stderr or "")[-500:]))
        return 0 if ok else 1

    # Case 2: Có CUDA, model chưa local → tải model trước (HuggingFace)
    if has_cuda:
        print(f"→ Model {model_key} chưa local, Attempting download...")
        sys.path.insert(0, str(SKILL_DIR))
        try:
            from scripts.model_manager import download_model
            ok = download_model(model_key, progress=True)
            if ok:
                print("→ Model downloaded, retrying with cuda_render_tool.py")
                return cmd_generate(args)  # recursive retry
            else:
                print("❌ Download failed — fallback ke nc_cuda_render.py (online)")
        except Exception as e:
            print(f"❌ Model manager error: {e}")

    # Case 3: Fallback — dùng nc_cuda_render.py (download model on-the-fly từ HF)
    if has_cuda:
        print("→ Fallback: nc_cuda_render.py (online HF model)")
        render_cmd = [
            sys.executable, str(NC_CUDA_RENDER),
            "--prompt", args.prompt,
            "--model", model_key if model_key != "sd15" else "runwayml/stable-diffusion-v1-5",
            "--width", str(args.width),
            "--height", str(args.height),
            "--steps", str(args.steps),
            "--guidance_scale", str(args.guidance),
        ]
        if args.seed is not None and args.seed >= 0:
            render_cmd += ["--seed", str(args.seed)]
        if args.output:
            render_cmd += ["--output", args.output]
        if args.negative:
            render_cmd += ["--negative_prompt", args.negative]

        print(f"  Command: {' '.join(render_cmd)}")
        result = subprocess.run(render_cmd, cwd=str(PLUGIN_ROOT / "scripts"),
                                capture_output=True, text=True, timeout=900)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        ok = result.returncode == 0 and Path(args.output).exists()
        _write_output_json(args, ok, args.output if ok else "",
                           (result.stdout[-500:] if ok else (result.stderr or "")[-500:]))
        return 0 if ok else 1

    # Case 4: Không có CUDA
    print("❌ Không có CUDA — không thể render local")
    print("  Gỡ về External API hoặc cài PyTorch CUDA:")
    print("  python3 -m pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128")
    _write_output_json(args, False, "", "No CUDA / PyTorch CUDA not installed")
    return 1


def cmd_upscale(args):
    """Upscale ảnh đã có — đơn giản là render lại với higher res + reference."""
    print("=" * 55)
    print("NC-RENDER UPSCALE")
    print("=" * 55)

    if not args.reference:
        print("❌ Cần reference image để upscale")
        _write_output_json(args, False, "", "Can reference image de upscale")
        return 1

    # Tăng resolution 2x
    from PIL import Image
    ref = Image.open(args.reference)
    new_w = ref.width * 2
    new_h = ref.height * 2
    print(f"Upscaling {ref.width}x{ref.height} → {new_w}x{new_h}")

    # Giả lập upscale bằng cách render lại với strength cao
    args.width = new_w
    args.height = new_h
    if args.strength is None:
        args.strength = 0.65
    args.prompt = args.prompt + " | high resolution, detailed, upscale"
    return cmd_generate(args)


def cmd_batch(args):
    """Batch generate — nhiều biến thể prompt."""
    print("=" * 55)
    print("NC-RENDER BATCH GENERATE")
    print("=" * 55)

    prompts = [p.strip() for p in args.prompts.split("|||")]
    print(f"Batch size: {len(prompts)} prompts")

    ts = int(__import__('time').time() * 1000)
    output_dir = args.output or os.path.join(
        os.environ.get("NC_RENDER_OUTPUT_DIR",
                        str(Path.home() / "AppData/Local/Temp")),
        f"nc_batch_{ts}"
    )
    os.makedirs(output_dir, exist_ok=True)

    for i, prompt in enumerate(prompts, 1):
        out_path = os.path.join(output_dir, f"batch_{i:02d}.png")
        print(f"\n─── [{i}/{len(prompts)}] {prompt[:60]}... ───")
        args.prompt = prompt
        args.output = out_path
        code = cmd_generate(args)
        if code != 0:
            print(f"  ❌ Prompt {i} FAILED")
        else:
            print(f"  ✅ Prompt {i} OK")

    print(f"\nBatch done — output dir: {output_dir}")
    pngs = sorted(str(x) for x in Path(output_dir).glob("batch_*.png"))
    _write_output_json(args, len(pngs) > 0, pngs[0] if pngs else "",
                       str(len(pngs)) + "/" + str(len(prompts)) + " images in " + output_dir)
    return 0 if pngs else 1


def main():
    parser = argparse.ArgumentParser(
        description="sd_generate.py — NC-Render CUDA wrapper (called from 3ds Max)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage từ 3ds Max macroScript:
  python3 sd_generate.py --prompt "..." --width 512 --height 512
  python3 sd_generate.py --prompt "..." --reference ref.png --strength 0.7
  python3 sd_generate.py --prompts "p1|||p2|||p3"  # batch
        """
    )

    # Generate
    gen = parser.add_argument_group("Generate")
    gen.add_argument("--prompt", type=str, help="Prompt text")
    gen.add_argument("--prompts", type=str, help="Batch prompts, separated by |||")
    gen.add_argument("--negative", type=str, default="", help="Negative prompt")
    gen.add_argument("--model", type=str, default="sd15", help="Model key: sd15, sdxl-base, flux-schnell, flux-dev")
    gen.add_argument("--width", type=int, default=512, help="Width")
    gen.add_argument("--height", type=int, default=512, help="Height")
    gen.add_argument("--steps", type=int, default=20, help="Inference steps")
    gen.add_argument("--guidance", type=float, default=7.5, help="Guidance scale")
    gen.add_argument("--seed", type=int, default=None, help="Seed")
    gen.add_argument("--output", type=str, default="", help="Output PNG path")
    gen.add_argument("--reference", type=str, default="", help="Reference image (img2img)")
    gen.add_argument("--strength", type=float, default=None, help="Denoising strength 0-1")
    gen.add_argument("--upscale", type=int, default=1, help="Upscale factor (1=off, 2/4=factor)")
    gen.add_argument("--detail", action="store_true", help="Detail enhancement")
    gen.add_argument("--tile", action="store_true", help="Tile-based upscaling")
    gen.add_argument("--input-json", type=str, default=None,
                    help="Input JSON file (instead of cmdline args)")
    gen.add_argument("--output-json", type=str, default=None,
                    help="Write result to JSON file after render")

    args = parser.parse_args()

    if args.prompts:
        return cmd_batch(args)
    elif (args.upscale is not None and args.upscale > 1) or args.reference:
        return cmd_upscale(args)
    elif args.prompt:
        return cmd_generate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
