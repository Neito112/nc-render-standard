#!/usr/bin/env python3
"""
NC-Render AI Studio — CUDA Auto-Install Script
Được gọi từ MZP installer để tự động cài PyTorch CUDA nếu cần
"""
import os
import sys
import subprocess
import time
import json
import argparse
import shutil

def detect_gpu():
    """Detect GPU using WMI (Windows)"""
    import wmi
    try:
        c = wmi.WMI()
        for gpu in c.Win32_VideoController():
            if "NVIDIA" in gpu.Name:
                return {
                    "name": gpu.Name,
                    "memory_mb": int(gpu.AdapterRAM) // (1024 * 1024) if gpu.AdapterRAM else 0
                }
        return {"name": "Unknown", "memory_mb": 0}
    except Exception as e:
        print(f"WMI detection failed: {e}")
        return {"name": "Unknown", "memory_mb": 0}

def check_cuda():
    """Check if CUDA toolkit is available"""
    cuda_paths = [
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.8/bin/cudart64_12.dll",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.4/bin/cudart64_12.dll",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.6/bin/cudart64_12.dll",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.8/bin/cudart64_12.dll",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.7/bin/cudart64_12.dll",
    ]
    for path in cuda_paths:
        if os.path.exists(path):
            return True, os.path.basename(os.path.dirname(os.path.dirname(path)))
    return False, None

def check_pytorch_cuda():
    """Check if PyTorch with CUDA is installed"""
    try:
        import torch
        return torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None, torch.__version__
    except Exception as e:
        return False, None, None

def install_pytorch_cuda(version="cu128"):
    """Install PyTorch CUDA version"""
    print(f"Installing PyTorch {version}...")
    cmd = [
        sys.executable, "-m", "pip", "install", 
        "--upgrade", "torch", "torchvision", "torchaudio",
        "--index-url", f"https://download.pytorch.org/whl/{version}",
        "--quiet"
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode == 0:
        print("PyTorch CUDA installed successfully")
        return True
    else:
        print(f"Installation failed: {proc.stderr[:500]}")
        return False

def main():
    parser = argparse.ArgumentParser(description="NC-Render CUDA Auto-Install")
    parser.add_argument("--check", action="store_true", help="Just check, don't install")
    parser.add_argument("--install", action="store_true", help="Install if needed")
    parser.add_argument("--version", default="cu128", choices=["cu128", "cu124", "cu121", "cu118", "cu117"], help="CUDA version to install")
    parser.add_argument("--output", default="json", help="Output format: json or text")
    args = parser.parse_args()
    
    result = {
        "gpu": detect_gpu(),
        "cuda_available": None,
        "cuda_version": None,
        "pytorch_cuda": False,
        "pytorch_version": None,
        "pytorch_device": None,
        "action": "none"
    }
    
    cuda_avail, cuda_ver = check_cuda()
    result["cuda_available"] = cuda_avail
    result["cuda_version"] = cuda_ver
    
    pytorch_cuda, device, version = check_pytorch_cuda()
    result["pytorch_cuda"] = pytorch_cuda
    result["pytorch_version"] = version
    result["pytorch_device"] = device
    
    if args.check:
        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            print("=== CUDA Check Result ===")
            print(f"GPU: {result['gpu']['name']} ({result['gpu']['memory_mb']} MB)")
            print(f"CUDA: {'✅ Available (' + result['cuda_version'] + ')' if result['cuda_available'] else '❌ Not found'}")
            print(f"PyTorch CUDA: {'✅ Available' if result['pytorch_cuda'] else '❌ Not available'}")
            if result['pytorch_cuda']:
                print(f"  Device: {result['pytorch_device']}")
                print(f"  Version: {result['pytorch_version']}")
        return 0
    
    # Decide action
    if not result["pytorch_cuda"] and result["cuda_available"]:
        print(f"PyTorch CUDA not installed, CUDA toolkit found — installing PyTorch CUDA {args.version}...")
        success = install_pytorch_cuda(args.version)
        result["action"] = "installed" if success else "failed"
        
        # Re-check after install
        if success:
            pytorch_cuda, device, version = check_pytorch_cuda()
            result["pytorch_cuda"] = pytorch_cuda
            result["pytorch_version"] = version
            result["pytorch_device"] = device
    elif not result["cuda_available"]:
        print("CUDA toolkit not found — cannot install PyTorch CUDA")
        result["action"] = "skipped_no_cuda"
    elif result["pytorch_cuda"]:
        print("PyTorch CUDA already installed — no action needed")
        result["action"] = "already_installed"
    
    if args.output == "json":
        print(json.dumps(result, indent=2))
    
    return 0 if result["action"] in ["installed", "already_installed", "skipped_no_cuda"] else 1

if __name__ == "__main__":
    sys.exit(main())
