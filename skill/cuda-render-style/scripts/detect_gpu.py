"""
detect_gpu.py — Hardware detection module

Quét GPU, VRAM, CUDA, PyTorch → trả về dict thông tin hardware.
"""

import os
import sys
import subprocess
import shutil

def detect_gpu_wmi():
    """Detect NVIDIA GPU via WMI (Windows)"""
    try:
        import wmi
        w = wmi.WMI()
        for gpu in w.Win32_VideoController():
            name = gpu.Name or ""
            if "nvidia" in name.lower():
                vram_bytes = gpu.AdapterRAM or 0
                vram_mb = vram_bytes // (1024 * 1024) if vram_bytes > 0 else 0
                return {"name": name, "vram_mb": vram_mb}
        return {"name": "Unknown (no NVIDIA GPU via WMI)", "vram_mb": 0}
    except ImportError:
        return {"name": "Unknown (wmi module not available)", "vram_mb": 0}
    except Exception as e:
        return {"name": f"Unknown (WMI error: {e})", "vram_mb": 0}

def detect_gpu_nvidia_smi():
    """Detect GPU via nvidia-smi (cross-platform)"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            if lines:
                parts = lines[0].split(",")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    vram_mb = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                    return {"name": name, "vram_mb": vram_mb}
        return {"name": "Unknown (nvidia-smi failed)", "vram_mb": 0}
    except FileNotFoundError:
        return {"name": "Unknown (nvidia-smi not found)", "vram_mb": 0}
    except Exception as e:
        return {"name": f"Unknown (nvidia-smi error: {e})", "vram_mb": 0}

def check_cuda_toolkit():
    """Check if CUDA Toolkit installed"""
    cuda_paths = [
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.8",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.6",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.4",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.2",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.1",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.8",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.7",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.6",
    ]
    
    for path in cuda_paths:
        bin_dir = os.path.join(path, "bin")
        dll_path = os.path.join(bin_dir, "cudart64_12.dll" if "v12" in path else "cudart64_11.dll")
        if os.path.exists(dll_path) or os.path.exists(os.path.join(bin_dir, "nvcc.exe")):
            version = path.split("/")[-1].replace("CUDA", "").strip()
            return True, version
    
    try:
        result = subprocess.run(["nvcc", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and "release" in result.stdout:
            for line in result.stdout.split("\n"):
                if "release" in line.lower():
                    import re
                    match = re.search(r"release\s+(\d+\.\d+)", line)
                    if match:
                        return True, f"nvcc-{match.group(1)}"
    except:
        pass
    
    return False, None

def check_pytorch_cuda():
    """Check PyTorch CUDA capability"""
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        device_name = None
        compute_cap = None
        
        if cuda_avail:
            device_name = torch.cuda.get_device_name(0)
            compute_cap = torch.cuda.get_device_capability(0)
        
        return {
            "available": cuda_avail,
            "device_name": device_name,
            "compute_capability": compute_cap,
            "version": torch.__version__,
        }
    except Exception as e:
        return {
            "available": False,
            "device_name": None,
            "compute_capability": None,
            "version": None,
            "error": str(e)
        }

def get_disk_free(path="."):
    """Get free disk space in GB"""
    try:
        usage = shutil.disk_usage(path)
        return usage.free / (1024**3)
    except:
        return 0.0

def detect_hardware():
    """
    Main detection function — returns hardware info dict
    
    Returns:
        {
            "gpu_name": str,
            "gpu_vram_mb": int,
            "gpu_vram_gb": float,
            "cuda_available": bool,
            "cuda_version": str or None,
            "pytorch_version": str,
            "pytorch_cuda": bool,
            "gpu_device": str or None,
            "compute_capability": tuple or None,
            "disk_free_gb": float,
            "python_version": str,
        }
    """
    # GPU detection
    gpu_wmi = detect_gpu_wmi()
    gpu_smi = detect_gpu_nvidia_smi()
    
    if gpu_smi["vram_mb"] > 0:
        gpu_name = gpu_smi["name"]
        gpu_vram_mb = gpu_smi["vram_mb"]
    else:
        gpu_name = gpu_wmi["name"]
        gpu_vram_mb = gpu_wmi["vram_mb"]
    
    gpu_vram_gb = gpu_vram_mb / 1024
    
    # CUDA toolkit
    cuda_avail, cuda_version = check_cuda_toolkit()
    
    # PyTorch
    pt_info = check_pytorch_cuda()
    
    result = {
        "gpu_name": gpu_name,
        "gpu_vram_mb": gpu_vram_mb,
        "gpu_vram_gb": round(gpu_vram_gb, 1),
        "cuda_available": cuda_avail,
        "cuda_version": cuda_version,
        "pytorch_version": pt_info.get("version", "Unknown"),
        "pytorch_cuda": pt_info.get("available", False),
        "gpu_device": pt_info.get("device_name", None),
        "compute_capability": pt_info.get("compute_capability", None),
        "disk_free_gb": round(get_disk_free(), 1),
        "python_version": sys.version.split()[0],
    }
    
    return result

def get_recommendation(hw):
    """
    Recommendation based on hardware detection
    
    Returns:
        {
            "model_key": str,
            "model_type": str,
            "model_repo": str,
            "model_name": str,
            "width": int,
            "height": int,
            "steps": int,
            "guidance": float,
            "cpu_offload": bool,
            "vram_estimate_mb": int,
            "note": str,
        }
    """
    vram_mb = hw["gpu_vram_mb"]
    has_cuda = hw["cuda_available"] and hw["pytorch_cuda"]
    
    if not has_cuda:
        return {
            "model_key": "none",
            "model_type": "none",
            "model_repo": "N/A",
            "model_name": "No GPU CUDA available",
            "width": 512,
            "height": 512,
            "steps": 20,
            "guidance": 7.0,
            "cpu_offload": False,
            "vram_estimate_mb": 0,
            "note": "CUDA not available — cannot generate locally",
        }
    
    if vram_mb == 0:
        return {
            "model_key": "none",
            "model_type": "none",
            "model_repo": "N/A",
            "model_name": "VRAM not detectable",
            "width": 512,
            "height": 512,
            "steps": 20,
            "guidance": 7.0,
            "cpu_offload": True,
            "vram_estimate_mb": 0,
            "note": "VRAM not detected — using conservative settings",
        }
    
    # VRAM-based recommendation with presence check fallback
    preferred = None
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

    model_key = _resolve_model_key(preferred)
    return _build_recommendation_dict(model_key)


# ---------------------------------------------------------------------------
# Helper functions (defined here to avoid circular import with model_manager)
# ---------------------------------------------------------------------------
_MODEL_INFO = {
    "sd15": {
        "repo": "runwayml/stable-diffusion-v1-5",
        "type": "sd15",
        "description": "SD 1.5 — nhẹ, nhanh, quality cơ bản",
        "min_vram_mb": 4096,
    },
    "sdxl-base": {
        "repo": "stabilityai/stable-diffusion-xl-base-1.0",
        "type": "sdxl",
        "description": "SDXL Base — quality cao, speed trung bình",
        "min_vram_mb": 6144,
    },
    "sdxl-refiner": {
        "repo": "stabilityai/stable-diffusion-xl-refiner-1.0",
        "type": "sdxl",
        "description": "SDXL Refiner — refinement cho quality tối ưu",
        "min_vram_mb": 6144,
    },
    "flux-schnell": {
        "repo": "black-forest-labs/FLUX.1-schnell",
        "type": "flux",
        "description": "FLUX.1-schnell — fast, quality cao",
        "min_vram_mb": 8192,
    },
    "flux-dev": {
        "repo": "black-forest-labs/FLUX.1-dev",
        "type": "flux",
        "description": "FLUX.1-dev — quality cao nhất, detail tốt nhất",
        "min_vram_mb": 8192,
    },
}


def _resolve_model_key(preferred: str) -> str:
    """
    Given a preferred model key, check local presence and fall back if missing.
    """
    try:
        from pathlib import Path
        scripts_dir = Path(__file__).parent
        model_path = scripts_dir.parent / "models" / preferred
        if model_path.exists():
            return preferred
    except Exception:
        pass

    # Fallback chain by tier
    if preferred in ("flux-schnell", "flux-dev"):
        for fb in ("sdxl-base", "sd15"):
            try:
                from pathlib import Path
                mp = Path(__file__).parent.parent / "models" / fb
                if mp.exists():
                    return fb
            except Exception:
                pass
    elif preferred == "sdxl-base":
        try:
            from pathlib import Path
            mp = Path(__file__).parent.parent / "models" / "sd15"
            if mp.exists():
                return "sd15"
        except Exception:
            pass
    return "sd15"


def _build_recommendation_dict(model_key: str) -> dict:
    """Build recommendation dict from resolved model key."""
    info = _MODEL_INFO.get(model_key, _MODEL_INFO["sd15"])
    vram_mb = 4096  # conservative default

    # Estimate VRAM based on model type
    if model_key.startswith("flux"):
        vram_mb = 8192
    elif model_key.startswith("sdxl"):
        vram_mb = 6144
    else:
        vram_mb = 4096

    # Resolution recommendation based on VRAM
    if vram_mb < 4096:
        width, height = 512, 512
    elif vram_mb < 8192:
        width, height = 768, 768
    else:
        width, height = 1024, 1024

    return {
        "model_key": model_key,
        "model_type": info["type"],
        "model_repo": info["repo"],
        "model_name": info["description"],
        "width": width,
        "height": height,
        "steps": 20 if model_key == "sd15" else 30,
        "guidance": 7.5 if model_key == "sd15" else 7.0,
        "cpu_offload": False,
        "vram_estimate_mb": vram_mb,
        "note": f"Min VRAM: {vram_mb // 1024} GB — {'local model presence not verified' if model_key != 'sd15' else ''}",
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Detect GPU hardware")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    hw = detect_hardware()
    
    if args.json:
        import json
        print(json.dumps(hw, indent=2))
    else:
        print("=" * 60)
        print("HARDWARE DETECTION")
        print("=" * 60)
        print(f"GPU: {hw['gpu_name']}")
        print(f"VRAM: {hw['gpu_vram_mb']} MB ({hw['gpu_vram_gb']} GB)")
        print(f"CUDA Toolkit: {'✅ ' + hw['cuda_version'] if hw['cuda_available'] else '❌ Not found'}")
        print(f"PyTorch: {hw['pytorch_version']}")
        print(f"PyTorch CUDA: {'✅ Available' if hw['pytorch_cuda'] else '❌ Not available'}")
        if hw['gpu_device']:
            print(f"GPU Device: {hw['gpu_device']}")
            print(f"Compute Capability: {hw['compute_capability']}")
        print(f"Disk free: {hw['disk_free_gb']} GB")
        print(f"Python: {hw['python_version']}")
        
        rec = get_recommendation(hw)
        print(f"\n─── RECOMMENDATION ───")
        print(f"Model: {rec['model_name']} ({rec['model_repo']})")
        print(f"Resolution: {rec['width']}x{rec['height']}")
        print(f"Steps: {rec['steps']}")
        print(f"Guidance: {rec['guidance']}")
        print(f"CPU Offload: {rec['cpu_offload']}")
        if rec.get('note'):
            print(f"Note: {rec['note']}")
