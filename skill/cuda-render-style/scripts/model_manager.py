"""
model_manager.py — Model management module

Quản lý model: check existence, download, auto-select theo VRAM.
"""

import os
import torch
from pathlib import Path
from diffusers import DiffusionPipeline

MODELS = {
    "sd15": {
        "repo": "runwayml/stable-diffusion-v1-5",
        "path": "models/sd15",
        "type": "sd15",
        "dtype": torch.float16,
        "variant": "fp16",
        "min_vram_mb": 4096,
        "description": "SD 1.5 — nhẹ, nhanh, quality cơ bản",
    },
    "sdxl-base": {
        "repo": "stabilityai/stable-diffusion-xl-base-1.0",
        "path": "models/sdxl-base",
        "type": "sdxl",
        "dtype": torch.float16,
        "variant": "fp16",
        "min_vram_mb": 6144,
        "description": "SDXL Base — quality cao, speed trung bình",
    },
    "sdxl-refiner": {
        "repo": "stabilityai/stable-diffusion-xl-refiner-1.0",
        "path": "models/sdxl-refiner",
        "type": "sdxl",
        "dtype": torch.float16,
        "variant": "fp16",
        "min_vram_mb": 6144,
        "description": "SDXL Refiner — refinement cho quality tối ưu",
    },
    "flux-schnell": {
        "repo": "black-forest-labs/FLUX.1-schnell",
        "path": "models/flux-schnell",
        "type": "flux",
        "dtype": torch.bfloat16,
        "variant": None,
        "min_vram_mb": 8192,
        "description": "FLUX.1-schnell — fast, quality cao",
    },
    "flux-dev": {
        "repo": "black-forest-labs/FLUX.1-dev",
        "path": "models/flux-dev",
        "type": "flux",
        "dtype": torch.bfloat16,
        "variant": None,
        "min_vram_mb": 8192,
        "description": "FLUX.1-dev — quality cao nhất, detail tốt nhất",
    },
}

def list_models():
    """List all available models"""
    print("Available models:")
    print(f"{'Key':<12} {'Repo':<55} {'VRAM min':<10} {'Description'}")
    print("-" * 100)
    for key, info in MODELS.items():
        print(f"{key:<12} {info['repo']:<55} {info['min_vram_mb']//1024}GB{'':<5} {info['description']}")

def check_model_exists(model_key):
    """Check if model exists locally"""
    if model_key not in MODELS:
        return False
    model_path = Path(__file__).parent.parent / MODELS[model_key]["path"]
    return model_path.exists()

def get_model_path(model_key):
    """Get absolute model path"""
    if model_key not in MODELS:
        return None
    return Path(__file__).parent.parent / MODELS[model_key]["path"]

def get_model_info(model_key):
    """Get model info dict"""
    if model_key not in MODELS:
        return None
    return MODELS[model_key].copy()

def download_model(model_key, force=False, progress=True):
    """
    Download model from HuggingFace
    
    Returns:
        bool: True if successful, False otherwise
    """
    if model_key not in MODELS:
        print(f"❌ Unknown model key: {model_key}")
        print(f"Available models: {list(MODELS.keys())}")
        return False
    
    model_info = MODELS[model_key]
    dest = Path(__file__).parent.parent / model_info["path"]
    
    if dest.exists() and not force:
        print(f"✅ Model already exists: {dest}")
        print(f"   Use --force to re-download")
        return True
    
    print(f"\n{'='*60}")
    print(f"Downloading model: {model_key}")
    print(f"{'='*60}")
    print(f"  Repository: {model_info['repo']}")
    print(f"  Destination: {dest.absolute()}")
    print(f"  Description: {model_info['description']}")
    print(f"  Min VRAM: {model_info['min_vram_mb'] // 1024} GB")
    
    os.makedirs(dest, exist_ok=True)
    
    try:
        if progress:
            print("  Downloading model components...")
        
        dtype = model_info["dtype"]
        variant = model_info.get("variant")
        
        pipe = DiffusionPipeline.from_pretrained(
            model_info["repo"],
            torch_dtype=dtype,
            variant=variant,
            use_safetensors=True,
            skip_pruning=True,
        )
        
        if progress:
            print("  Saving to local cache...")
        
        pipe.save_pretrained(dest)
        
        # Calculate size
        total_size = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())
        
        print(f"\n✅ Model downloaded successfully!")
        print(f"   Path: {dest.absolute()}")
        print(f"   Size: {total_size / 1024**2:.0f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def _resolve_model_key(preferred):
    """
    Given a preferred model key, check local presence and fall back if missing.
    """
    if check_model_exists(preferred):
        return preferred
    # Fallback chain by tier
    if preferred in ("flux-schnell", "flux-dev"):
        for fb in ("sdxl-base", "sd15"):
            if check_model_exists(fb):
                return fb
    elif preferred == "sdxl-base":
        if check_model_exists("sd15"):
            return "sd15"
    # Ultimate fallback
    return "sd15"


def auto_select_model_key(vram_mb):
    """
    Auto-select model based on VRAM.
    Returns a model key that is confirmed present locally (falls back if missing).
    """
    if vram_mb < 4096:
        preferred = "sd15"
    elif vram_mb < 6144:
        preferred = "sdxl-base"
    elif vram_mb < 8192:
        preferred = "sdxl-base"
    elif vram_mb < 12288:
        preferred = "flux-schnell"
    else:
        preferred = "flux-dev"
    return _resolve_model_key(preferred)


def get_recommendation_for_vram(vram_mb):
    """
    Return full recommendation dict (mirrors detect_gpu.get_recommendation).
    Called by cuda_render_tool.py để display recommendation.
    """
    from .detect_gpu import get_recommendation as _detect_rec
    from .detect_gpu import detect_hardware

    # Build minimal hw dict for get_recommendation
    hw = {
        "gpu_vram_mb": vram_mb,
        "cuda_available": True,  # assume CUDA available when called from tool
        "pytorch_cuda": True,
    }
    return _detect_rec(hw)

def auto_download_for_vram(vram_mb, force=False):
    """
    Auto-detect VRAM and download appropriate model
    
    Args:
        vram_mb: VRAM in megabytes
        force: Force re-download if True
    
    Returns:
        bool: True if successful
    """
    key = auto_select_model_key(vram_mb)
    print(f"Auto-selecting model for {vram_mb} MB VRAM → {key}")
    return download_model(key, force)

def get_model_for_vram(vram_mb):
    """
    Get model info for specific VRAM
    
    Returns:
        dict: Model info or None if no suitable model
    """
    key = auto_select_model_key(vram_mb)
    return get_model_info(key)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Model Manager — Download and manage models")
    parser.add_argument("model", nargs="?", help="Model key to download")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--check", type=str, help="Check if model exists")
    parser.add_argument("--path", type=str, help="Get model path")
    parser.add_argument("--auto", action="store_true", help="Auto-select model based on VRAM")
    parser.add_argument("--force", action="store_true", help="Force re-download")
    parser.add_argument("--download", action="store_true", help="Download after auto-select")
    args = parser.parse_args()
    
    if args.list:
        list_models()
    elif args.check:
        exists = check_model_exists(args.check)
        print(f"Model '{args.check}': {'✅ Exists' if exists else '❌ Not found'}")
    elif args.path:
        path = get_model_path(args.path)
        if path:
            print(f"Model path: {path}")
            print(f"Exists: {path.exists()}")
        else:
            print(f"Unknown model: {args.path}")
    elif args.auto:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from detect_gpu import detect_hardware
        hw = detect_hardware()
        key = auto_select_model_key(hw["gpu_vram_mb"])
        info = get_model_info(key)
        print(f"Auto-selected model for {hw['gpu_vram_mb']} MB VRAM:")
        print(f"  Key: {key}")
        print(f"  Name: {info['description']}")
        print(f"  Repo: {info['repo']}")
        print(f"  Min VRAM: {info['min_vram_mb'] // 1024} GB")
        
        if args.download:
            success = download_model(key, args.force)
            sys.exit(0 if success else 1)
    elif args.model:
        success = download_model(args.model, args.force)
        sys.exit(0 if success else 1)
    else:
        print("Usage:")
        print("  python3 model_manager.py --list                    # List models")
        print("  python3 model_manager.py --check sd15             # Check model")
        print("  python3 model_manager.py --path sd15              # Get path")
        print("  python3 model_manager.py --auto                   # Auto-select")
        print("  python3 model_manager.py sd15                     # Download model")
        print("  python3 model_manager.py --auto --download        # Auto-download")
        sys.exit(1)
