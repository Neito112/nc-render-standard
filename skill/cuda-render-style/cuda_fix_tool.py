#!/usr/bin/env python3
"""
cuda_fix_tool.py — Standalone Fix Tool

Chẩn đoán lỗi CUDA render, kiểm tra môi trường, đưa ra command fix cụ thể.
Có thể chạy độc lập hoặc cùng cuda_render_tool.py.
"""

import argparse
import torch
import os
import sys
import subprocess
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

def detect_hardware():
    """Detect hardware (simplified)"""
    try:
        import wmi
        w = wmi.WMI()
        for gpu in w.Win32_VideoController():
            if "nvidia" in gpu.Name.lower():
                vram = (gpu.AdapterRAM or 0) // (1024*1024)
                return {"name": gpu.Name, "vram_mb": vram}
    except:
        pass
    
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if lines:
                parts = lines[0].split(",")
                return {"name": parts[0].strip(), "vram_mb": int(parts[1].strip())}
    except:
        pass
    
    return {"name": "Unknown", "vram_mb": 0}

def check_cuda_toolkit():
    """Check CUDA toolkit"""
    cuda_paths = [
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.8",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.4",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.1",
        "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v11.8",
    ]
    for path in cuda_paths:
        if os.path.exists(path):
            return True, path.split("/")[-1]
    return False, None

def check_pytorch():
    """Check PyTorch"""
    try:
        import torch
        return {
            "available": True,
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "compute_cap": torch.cuda.get_device_capability(0) if torch.cuda.is_available() else None,
        }
    except Exception as e:
        return {"available": False, "error": str(e)}

def check_model(model_key):
    """Check model existence"""
    model_path = SCRIPT_DIR / "models" / model_key
    if model_path.exists():
        size_mb = sum(f.stat().st_size for f in model_path.rglob("*") if f.is_file()) / 1024**2
        return True, size_mb
    return False, 0

def print_section(title):
    print(f"\n{'='*60}")
    print(title)
    print(f"{'='*60}")

def cmd_diagnose(args):
    print_section("CUDA RENDER FIX TOOL — DIAGNOSIS")
    
    hw = detect_hardware()
    cuda_avail, cuda_path = check_cuda_toolkit()
    pt_info = check_pytorch()
    
    print(f"\n[1/4] GPU: {hw['name']} ({hw['vram_mb']} MB VRAM)")
    print(f"\n[2/4] CUDA Toolkit: {'✅ ' + cuda_path if cuda_avail else '❌ Not found'}")
    print(f"\n[3/4] PyTorch: {'✅ ' + pt_info.get('version', 'N/A')}")
    print(f"        CUDA Available: {'✅' if pt_info.get('cuda_available') else '❌'}")
    if pt_info.get('cuda_available'):
        print(f"        Device: {pt_info.get('device')}")
        print(f"        Compute Cap: {pt_info.get('compute_cap')}")
    else:
        print(f"        Error: {pt_info.get('error', 'Unknown')}")
    
    print(f"\n[4/4] Model Check:")
    for key in ['sd15', 'sdxl-base', 'flux-schnell', 'flux-dev']:
        exists, size = check_model(key)
        if exists:
            print(f"  ✅ {key}: {size:.0f} MB")
        else:
            print(f"  ❌ {key}: Not found")
    
    # Recommendations
    print_section("RECOMMENDATIONS")
    
    issues = []
    if not cuda_avail:
        issues.append(("CUDA Toolkit missing", "Install CUDA Toolkit from https://developer.nvidia.com/cuda-toolkit"))
    if not pt_info.get('cuda_available'):
        if pt_info.get('available'):
            issues.append(("PyTorch CUDA not enabled", "Reinstall PyTorch CUDA: python3 -m pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128"))
        else:
            issues.append(("PyTorch not installed", "Install PyTorch: python3 -m pip install torch"))
    
    if pt_info.get('cuda_available') and hw['vram_mb'] < 4096:
        issues.append(("Low VRAM", "Use SD1.5 model, resolution 512x512"))
    
    if not issues:
        print("✅ System OK — ready to render")
        print("\nQuick start:")
        print("  python3 cuda_render_tool.py render --prompt 'your prompt here'")
    else:
        print(f"⚠️ Found {len(issues)} issue(s):")
        for i, (issue, fix) in enumerate(issues, 1):
            print(f"\n  {i}. {issue}")
            print(f"     Fix: {fix}")
    
    return 0

def cmd_fix_issue(args):
    """Fix specific issue"""
    print_section("FIX SPECIFIC ISSUE")
    
    issue = args.issue
    
    if issue == "cuda":
        print("Fixing CUDA...")
        print("1. Check CUDA Toolkit:")
        print("   nvcc --version")
        print("2. Check PyTorch CUDA:")
        print("   python3 -c 'import torch; print(torch.cuda.is_available())'")
        print("3. Reinstall PyTorch CUDA:")
        print("   python3 -m pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128")
    
    elif issue == "oom":
        print("Fixing OOM (Out of Memory)...")
        print("1. Clean VRAM:")
        print("   python3 cuda_render_tool.py clean")
        print("2. Reduce resolution:")
        print("   python3 cuda_render_tool.py render --prompt '...' --width 512 --height 512")
        print("3. Use smaller model:")
        print("   python3 cuda_render_tool.py render --prompt '...' --model sd15")
        print("4. Use tile-based upscale for large images")
    
    elif issue == "model":
        print("Fixing Model Issue...")
        print("1. List available models:")
        print("   python3 scripts/model_manager.py --list")
        print("2. Download model:")
        print("   python3 scripts/model_manager.py sd15")
        print("3. Auto-select model:")
        print("   python3 scripts/model_manager.py --auto")
    
    elif issue == "quality":
        print("Fixing Quality Issue...")
        print("1. Increase steps:")
        print("   python3 cuda_render_tool.py render --prompt '...' --steps 50")
        print("2. Increase guidance:")
        print("   python3 cuda_render_tool.py render --prompt '...' --guidance 9.0")
        print("3. Use better model:")
        print("   python3 cuda_render_tool.py render --prompt '...' --model sdxl-base")
        print("4. Improve prompt:")
        print("   python3 scripts/prompt_builder.py --random --count 5")
    
    elif issue == "disk":
        print("Fixing Disk Space Issue...")
        print("1. Check disk space:")
        print("   df -h")
        print("2. Clean pip cache:")
        print("   python3 -m pip cache purge")
        print("3. Move model to external drive:")
        print("   - Download model to external drive")
        print("   - Set MODEL_PATH environment variable")
    
    else:
        print(f"Unknown issue: {issue}")
        print("Available issues: cuda, oom, model, quality, disk")

def main():
    parser = argparse.ArgumentParser(description="cuda_fix_tool.py — Fix CUDA Render Issues")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("diagnose", help="Run full diagnosis").set_defaults(func=cmd_diagnose)
    subparsers.add_parser("fix", help="Interactive fix").set_defaults(func=cmd_diagnose)
    
    fix_parser = subparsers.add_parser("fix-issue", help="Fix specific issue")
    fix_parser.add_argument("issue", choices=["cuda", "oom", "model", "quality", "disk"], help="Issue to fix")
    fix_parser.set_defaults(func=cmd_fix_issue)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())
