#!/usr/bin/env python3
"""
_setup_download.py — Auto-download SD model during plugin setup.
Called by mzp.run installPlugin() when user selects Local SD (CUDA) render method.
Writes status to nc_model_status.txt for mzp.run polling.
"""
import argparse
import os
import sys
import time
from pathlib import Path

# Thêm skill script directory vào path để import model_manager
SKILL_SCRIPTS = Path(__file__).parent
PLUGIN_ROOT = SKILL_SCRIPTS.parent

sys.path.insert(0, str(SKILL_SCRIPTS))

STATUS_FILE = Path(os.path.join(os.environ.get("TEMP", "C:/Temp"), "nc_model_status.txt"))
MODEL_DIR = PLUGIN_ROOT / "skill" / "cuda-render-style" / "models"

# Model definitions (consistent with model_manager.py)
MODELS = {
    "sd15": {
        "repo": "runwayml/stable-diffusion-v1-5",
        "path": "models/sd15",
        "min_vram_mb": 4096,
        "description": "SD 1.5 — nhanh, nhẹ, phù hợp VRAM < 6GB",
        "torch_dtype": "float16",
    },
    "sdxl-base": {
        "repo": "stabilityai/stable-diffusion-xl-base-1.0",
        "path": "models/sdxl-base",
        "min_vram_mb": 6144,
        "description": "SDXL Base — chất lượng cao, cần VRAM ≥ 6GB",
        "torch_dtype": "float16",
    },
    "flux-schnell": {
        "repo": "black-forest-labs/FLUX.1-schnell",
        "path": "models/flux-schnell",
        "min_vram_mb": 8192,
        "description": "FLUX.1-schnell — nhanh, quality cao, cần VRAM ≥ 8GB",
        "torch_dtype": "bfloat16",
    },
    "flux-dev": {
        "repo": "black-forest-labs/FLUX.1-dev",
        "path": "models/flux-dev",
        "min_vram_mb": 8192,
        "description": "FLUX.1-dev — quality cao nhất, cần VRAM ≥ 8GB",
        "torch_dtype": "bfloat16",
    },
}


def auto_select_model_key_with_token(vram_mb, hf_token=None):
    """
    Auto-select model based on VRAM, considering token availability.
    
    If user has HF token: can use gated models (FLUX).
    If no token: only public models (SD1.5, SDXL), FLUX requires token.
    """
    has_token = hf_token is not None and hf_token.strip() != ""
    
    if not has_token:
        # No token — use only public models
        if vram_mb >= 8192:
            return "sdxl-base"  # SDXL public, good quality, fits 8GB
        elif vram_mb >= 6144:
            return "sdxl-base"
        else:
            return "sd15"
    else:
        # Has token — can use gated models
        if vram_mb >= 12288:
            return "flux-dev"
        elif vram_mb >= 8192:
            return "flux-schnell"
        elif vram_mb >= 6144:
            return "sdxl-base"
        else:
            return "sd15"


# Legacy alias for backward compat
def auto_select_model_key(vram_mb):
    """Backward-compatible alias — calls with no token (public models only)."""
    return auto_select_model_key_with_token(vram_mb, hf_token=None)


def check_model_exists(model_key):
    """Check if model directory exists locally."""
    if model_key not in MODELS:
        return False
    model_path = MODEL_DIR / MODELS[model_key]["path"]
    return model_path.exists()


def write_status(status):
    """Write status to file for mzp.run polling."""
    try:
        STATUS_FILE.write_text(status)
    except Exception as e:
        print(f"Warning: Could not write status file: {e}", file=sys.stderr)


def download_model(model_key, force=False, hf_token=None):
    """
    Download model from HuggingFace using diffusers.
    Returns (success: bool, message: str, model_path: Path|None)
    If hf_token is provided, uses it for gated models.
    If model is gated and no token, tries fallback public models.
    """
    if model_key not in MODELS:
        return False, f"Unknown model key: {model_key}", None

    model_info = MODELS[model_key]
    dest = MODEL_DIR / model_info["path"]

    if dest.exists() and not force:
        return True, f"Model already exists: {dest}", dest

    print(f"Downloading {model_key} from {model_info['repo']}...")
    print(f"Destination: {dest}")
    write_status(f"DOWNLOADING {model_key} from {model_info['repo']}")

    try:
        import torch
        from diffusers import DiffusionPipeline

        dtype_str = model_info["torch_dtype"]
        if dtype_str == "float16":
            torch_dtype = torch.float16
        elif dtype_str == "bfloat16":
            torch_dtype = torch.bfloat16
        else:
            torch_dtype = torch.float32

        print(f"  Using dtype: {dtype_str}")

        # Try download with optional token
        kwargs = dict(
            torch_dtype=torch_dtype,
            use_safetensors=True,
            skip_pruning=True,
        )
        if hf_token:
            kwargs["token"] = hf_token

        pipe = DiffusionPipeline.from_pretrained(
            model_info["repo"],
            **kwargs,
        )

        print(f"  Saving to {dest}...")
        pipe.save_pretrained(dest)

        # Calculate size
        total_size = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())
        size_mb = total_size / (1024 * 1024)

        msg = f"Download complete: {model_key} ({size_mb:.0f} MB)"
        print(msg)
        write_status(f"COMPLETE {model_key} {dest} {size_mb:.0f}")

        return True, msg, dest

    except Exception as e:
        error_msg = str(e)
        is_gated = "401" in error_msg or "gated" in error_msg.lower() or "restricted" in error_msg.lower()

        if is_gated and not hf_token:
            # Gated model, no token — fallback to public model
            print(f"  ⚠️ Model {model_key} is gated — no token provided", file=sys.stderr)
            print(f"  🔄 Falling back to public model...", file=sys.stderr)
            write_status(f"FALLBACK {model_key} to public model")

            fallback_key = "sd15"  # Always-safe public choice
            fallback_info = MODELS[fallback_key]
            fallback_dest = MODEL_DIR / fallback_info["path"]

            if fallback_dest.exists() and not force:
                return True, f"Using existing public model: {fallback_key}", fallback_dest

            print(f"  Downloading public fallback: {fallback_key} ({fallback_info['repo']})", file=sys.stderr)
            write_status(f"DOWNLOADING {fallback_key} (fallback) from {fallback_info['repo']}")

            try:
                torch_dtype = torch.float16  # SD1.5 FP16
                pipe = DiffusionPipeline.from_pretrained(
                    fallback_info["repo"],
                    torch_dtype=torch_dtype,
                    use_safetensors=True,
                    skip_pruning=True,
                )
                print(f"  Saving to {fallback_dest}...", file=sys.stderr)
                pipe.save_pretrained(fallback_dest)

                total_size = sum(f.stat().st_size for f in fallback_dest.rglob("*") if f.is_file())
                size_mb = total_size / (1024 * 1024)

                msg = f"Downloaded public fallback {fallback_key} ({size_mb:.0f} MB)"
                print(msg)
                write_status(f"COMPLETE {fallback_key} {fallback_dest} {size_mb:.0f}")

                return True, msg, fallback_dest

            except Exception as fb_e:
                fb_msg = f"Fallback also failed: {fb_e}"
                print(fb_msg, file=sys.stderr)
                write_status(f"FAILED {fb_msg}")
                return False, fb_msg, None

        # Not gated — real error, report as-is
        import traceback
        err_msg = f"Download failed: {e}\n{traceback.format_exc()}"
        print(err_msg, file=sys.stderr)
        write_status(f"FAILED {err_msg}")
        return False, err_msg, None


def main():
    parser = argparse.ArgumentParser(description="Auto-download SD model for plugin setup")
    parser.add_argument("--vram", type=int, required=True, help="VRAM in MB")
    parser.add_argument("--key", type=str, default=None, help="Override model key (default: auto-select)")
    parser.add_argument("--force", action="store_true", help="Force re-download")
    parser.add_argument("--token", type=str, default=None, help="HuggingFace token (for gated models like FLUX)")
    args = parser.parse_args()

    vram_mb = args.vram
    override_key = args.key
    hf_token = args.token

    # Determine model key — considers token availability for gated models
    if override_key and override_key in MODELS and check_model_exists(override_key):
        key = override_key
    elif override_key and override_key in MODELS:
        key = override_key  # Use override even if not exists (will download)
    else:
        key = auto_select_model_key_with_token(vram_mb, hf_token=hf_token)

    info = MODELS[key]
    print(f"VRAM: {vram_mb} MB")
    print(f"Token provided: {'Yes' if hf_token else 'No'}")
    print(f"Auto-selected model: {key}")
    print(f"  Description: {info['description']}")
    print(f"  Repo: {info['repo']}")
    print(f"  Min VRAM: {info['min_vram_mb']} MB")
    print()

    # Check existence
    if check_model_exists(key):
        print(f"Model already present locally: {key}")
        model_path = MODEL_DIR / info["path"]
        write_status(f"COMPLETE {key} {model_path} PRESENT")
        sys.exit(0)

    # Download (with optional token)
    success, msg, model_path = download_model(key, force=args.force, hf_token=hf_token)

    if success:
        print(f"\nSetup complete. Model {key} ready for use.")
        sys.exit(0)
    else:
        print(f"\nSetup FAILED: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
