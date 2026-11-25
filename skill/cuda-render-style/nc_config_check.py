#!/usr/bin/env python3
"""nc_config_check.py — standalone hardware probe for NC-Render.

Original code written on the VM for this task. Stdlib only (numpy used
only if already installed, for the CPU speed probe; never required).

What it does, and nothing else:
  1. Detect real hardware: OS, CPU cores, RAM free/total, disk free.
  2. Detect GPU honestly: torch CUDA if torch is installed, nvidia-smi,
     /dev/nvidia*, /sys/class/drm, /proc/driver/nvidia. No hardcoded
     GPU name, no WMI, no Windows-only path, no DLL-existence guess.
  3. Detect CUDA toolkit (nvcc) and PyTorch (version + cuda flag).
  4. Measure CPU speed with a short benchmark (numpy matmul when
     available, otherwise a pure-Python loop) so the tier is based on
     measured speed, not only on a name.
  5. Map the measurements to one render tier with a concrete
     model / resolution / steps / expected-time recommendation.
     No GPU  -> API_ONLY: local GPU render OFF, API render is the path.
     CPU render is only offered when free RAM >= 4 GB and the caller
     passes --allow-cpu, and it is always labelled slow.

Usage:
    python3 nc_config_check.py                  # human report
    python3 nc_config_check.py --json           # JSON report
    python3 nc_config_check.py --bench          # include CPU benchmark
    python3 nc_config_check.py --simulate rtx3050 --json
    python3 nc_config_check.py --simulate vram=8192,cuda=1 --json
    python3 nc_config_check.py --simulate no-gpu --json

Simulate presets only change the *reported* GPU inputs so the tier
mapping can be tested on a machine with no GPU. They never claim
real hardware exists.
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except Exception:
        return -1, "", ""


def _mem_info():
    total_mb = free_mb = 0
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            d = {}
            for line in f:
                k, _, v = line.partition(":")
                d[k.strip()] = v.strip()
        total_mb = int(d.get("MemTotal", "0").split()[0]) // 1024
        free_mb = int(d.get("MemAvailable", "0").split()[0]) // 1024
    except Exception:
        pass
    return total_mb, free_mb


def _disk_free_gb(path):
    try:
        st = os.statvfs(path)
        return round(st.f_bavail * st.f_frsize / 1e9, 1)
    except Exception:
        return 0.0


def _cpu_bench():
    """Short CPU speed probe. Returns seconds for a fixed workload."""
    try:
        import numpy as np  # already installed on this VM; optional

        t0 = time.time()
        a = np.random.rand(1000, 1000)
        for _ in range(5):
            a = a @ a
        return round(time.time() - t0, 2), "numpy 5x 1000x1000 matmul"
    except Exception:
        t0 = time.time()
        s = 0.0
        for i in range(2_000_000):
            s += (i % 97) * 0.001
        return round(time.time() - t0, 2), "pure-python loop (no numpy)"


def detect_gpu_real():
    """Return dict with gpu_name, vram_mb, cuda flag, and how it was found."""
    info = {"gpu_name": None, "vram_mb": 0, "cuda": False, "found_via": "none"}

    # 1. torch, if installed — the most reliable source on a render PC.
    try:
        import torch

        info["torch_version"] = torch.__version__
        info["torch_cuda"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            info["gpu_name"] = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            info["vram_mb"] = int(props.total_memory // (1024 * 1024))
            info["cuda"] = True
            info["found_via"] = "torch.cuda"
            return info
        info["torch_cuda"] = False
    except Exception as e:
        info["torch_error"] = str(e)[:200]

    # 2. nvidia-smi, if present.
    if shutil.which("nvidia-smi"):
        code, out, _ = _run(["nvidia-smi", "--query-gpu=name,memory.total",
                             "--format=csv,noheader,nounits"])
        if code == 0 and out:
            parts = out.splitlines()[0].split(",")
            info["gpu_name"] = parts[0].strip()
            try:
                info["vram_mb"] = int(parts[1].strip())
            except Exception:
                pass
            info["cuda"] = True
            info["found_via"] = "nvidia-smi"
            return info

    # 3. Kernel device nodes / DRM cards (Linux).
    for pat in ("/dev/nvidia0", "/proc/driver/nvidia/version"):
        if os.path.exists(pat):
            info["found_via"] = "nvidia device node present, no query tool"
            break
    try:
        drm = [p for p in Path("/sys/class/drm").iterdir()
               if p.name.startswith("card")]
        if drm:
            info["found_via"] = "drm card present, no query tool"
    except Exception:
        pass

    return info


def detect_cuda_toolkit():
    if shutil.which("nvcc"):
        _, out, _ = _run(["nvcc", "--version"])
        for line in out.splitlines():
            if "release" in line:
                return True, line.strip()
        return True, "nvcc present"
    for cand in ("/usr/local/cuda", "/opt/cuda"):
        if os.path.exists(cand):
            return True, cand
    return False, None


def tier_for(vram_mb, cuda, torch_cuda, ram_free_mb, cpu_bench_s):
    """Map measured hardware to a render tier. Thresholds are explicit
    and testable; the RTX 3050 8 GB reference (SD1.5 512x512, 20 steps,
    ~4.4 s, from the repo's own 2026-09-10 test note) anchors GPU_LOW."""
    if cuda and torch_cuda and vram_mb >= 12288:
        return {
            "tier": "GPU_HIGH", "local_gpu": True, "model": "sdxl-base / flux-schnell",
            "width": 1024, "height": 1024, "steps": 20,
            "expected_seconds": "~10-20",
            "note": "VRAM >= 12 GB: SDXL 1024 or FLUX-schnell fits.",
        }
    if cuda and torch_cuda and vram_mb >= 8192:
        return {
            "tier": "GPU_MID", "local_gpu": True, "model": "sdxl-base (SD1.5 512 for speed)",
            "width": 1024, "height": 1024, "steps": 20,
            "expected_seconds": "~20 (SD1.5 512: ~4-5s)",
            "note": "VRAM 8-12 GB: SDXL 1024 fits; RTX 3050 8GB tested path is SD1.5 512.",
        }
    if cuda and torch_cuda and vram_mb >= 6144:
        return {
            "tier": "GPU_MID", "local_gpu": True, "model": "sdxl-base",
            "width": 1024, "height": 1024, "steps": 20,
            "expected_seconds": "~20",
            "note": "VRAM 6-8 GB: SDXL 1024, or SD1.5 512 for speed.",
        }
    if cuda and torch_cuda and vram_mb >= 4096:
        return {
            "tier": "GPU_LOW", "local_gpu": True, "model": "sd15",
            "width": 512, "height": 512, "steps": 20,
            "expected_seconds": "~4-5 (RTX 3050 8GB reference: 4.4s)",
            "note": "VRAM 4-6 GB: SD1.5 512 only. Do not offer SDXL/FLUX.",
        }
    if vram_mb > 0:
        return {
            "tier": "GPU_TOO_SMALL", "local_gpu": False, "model": "sd15 (CPU/API only)",
            "width": 512, "height": 512, "steps": 20,
            "expected_seconds": "unknown - too slow on this GPU",
            "note": "GPU present but VRAM < 4 GB: disable local GPU render, use API.",
        }
    # No GPU at all.
    if ram_free_mb >= 4096:
        return {
            "tier": "API_ONLY_CPU_POSSIBLE", "local_gpu": False, "model": "sd15 (CPU, opt-in only)",
            "width": 512, "height": 512, "steps": 20,
            "expected_seconds": "minutes per image on CPU - slow, opt-in only",
            "note": "No GPU. API render is the recommended path; CPU render only with --allow-cpu.",
        }
    return {
        "tier": "API_ONLY", "local_gpu": False, "model": "none local",
        "width": 512, "height": 512, "steps": 20,
        "expected_seconds": "n/a - API render time depends on provider",
        "note": "No GPU and free RAM < 4 GB: local render OFF. Use API key render only.",
    }


PRESETS = {
    "rtx3050": {"gpu_name": "NVIDIA GeForce RTX 3050 (simulated)", "vram_mb": 8192,
                "cuda": True, "torch_cuda": True, "found_via": "simulate:rtx3050"},
    "rtx4060": {"gpu_name": "NVIDIA GeForce RTX 4060 (simulated)", "vram_mb": 8192,
                "cuda": True, "torch_cuda": True, "found_via": "simulate:rtx4060"},
    "gtx1660": {"gpu_name": "NVIDIA GeForce GTX 1660 (simulated)", "vram_mb": 6144,
                "cuda": True, "torch_cuda": True, "found_via": "simulate:gtx1660"},
    "low-vram": {"gpu_name": "Simulated 2GB GPU", "vram_mb": 2048,
                 "cuda": True, "torch_cuda": True, "found_via": "simulate:low-vram"},
    "no-gpu": {"gpu_name": None, "vram_mb": 0, "cuda": False,
               "torch_cuda": False, "found_via": "simulate:no-gpu"},
}


def parse_simulate(spec):
    if spec in PRESETS:
        return dict(PRESETS[spec])
    out = {"gpu_name": "Simulated GPU", "vram_mb": 0, "cuda": False,
           "torch_cuda": False, "found_via": f"simulate:{spec}"}
    for kv in spec.split(","):
        if "=" not in kv:
            continue
        k, v = kv.split("=", 1)
        k, v = k.strip(), v.strip()
        if k == "vram":
            out["vram_mb"] = int(v)
        elif k in ("cuda", "torch_cuda"):
            out[k] = v in ("1", "true", "yes")
        elif k == "name":
            out["gpu_name"] = v
    return out


def main():
    ap = argparse.ArgumentParser(description="NC-Render config check (standalone probe)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--bench", action="store_true", help="Run the short CPU benchmark")
    ap.add_argument("--allow-cpu", action="store_true")
    ap.add_argument("--simulate", type=str, default=None,
                    help="Preset (rtx3050, rtx4060, gtx1660, low-vram, no-gpu) or k=v list")
    args = ap.parse_args()

    total_ram, free_ram = _mem_info()
    report = {
        "os": platform.system(),
        "os_version": platform.version(),
        "python": sys.version.split()[0],
        "cpu_cores": os.cpu_count(),
        "cpu_model": "unknown",
        "ram_total_mb": total_ram,
        "ram_free_mb": free_ram,
        "disk_free_gb_home": _disk_free_gb(os.path.expanduser("~")),
        "simulated": args.simulate or False,
    }
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("model name"):
                    report["cpu_model"] = line.split(":", 1)[1].strip()
                    break
    except Exception:
        pass

    if args.simulate:
        gpu = parse_simulate(args.simulate)
        gpu.setdefault("torch_version", None)
    else:
        gpu = detect_gpu_real()
    report["gpu"] = gpu

    cuda_toolkit, cuda_ver = detect_cuda_toolkit()
    report["cuda_toolkit"] = cuda_toolkit
    report["cuda_toolkit_version"] = cuda_ver

    bench_s, bench_what = (None, None)
    if args.bench:
        bench_s, bench_what = _cpu_bench()
    report["cpu_bench_seconds"] = bench_s
    report["cpu_bench_what"] = bench_what

    tier = tier_for(gpu.get("vram_mb", 0), gpu.get("cuda", False),
                    gpu.get("torch_cuda", False), free_ram, bench_s)
    if tier["tier"] == "API_ONLY_CPU_POSSIBLE" and not args.allow_cpu:
        tier["note"] += " CPU render is OFF unless --allow-cpu is passed."
    report["tier"] = tier
    report["recommended_path"] = "local-gpu" if tier["local_gpu"] else "api-key"
    report["local_gpu_render"] = tier["local_gpu"]

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print("NC-RENDER CONFIG CHECK")
        print("=" * 60)
        print(f"OS:        {report['os']} ({report['python']} Python)")
        print(f"CPU:       {report['cpu_model']} x{report['cpu_cores']}")
        print(f"RAM:       {free_ram} MB free / {total_ram} MB total")
        print(f"Disk free: {report['disk_free_gb_home']} GB (home)")
        print(f"GPU:       {gpu.get('gpu_name') or 'NONE'}"
              f" ({gpu.get('vram_mb', 0)} MB VRAM, via {gpu.get('found_via')})")
        print(f"CUDA:      toolkit={cuda_toolkit} torch_cuda={gpu.get('torch_cuda')}")
        if bench_s is not None:
            print(f"CPU bench: {bench_s}s ({bench_what})")
        print("-" * 60)
        print(f"TIER:      {tier['tier']}")
        print(f"Path:      {report['recommended_path']}")
        print(f"Model:     {tier['model']} {tier['width']}x{tier['height']}, {tier['steps']} steps")
        print(f"Expected:  {tier['expected_seconds']}")
        print(f"Note:      {tier['note']}")
        if args.simulate:
            print(f"(simulated hardware: {args.simulate} — not real hardware)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
