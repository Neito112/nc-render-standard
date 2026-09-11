#!/usr/bin/env python3
"""
vram_monitor.py — VRAM monitoring utility

Monitoring VRAM realtime, dùng để debug memory leak hoặc optimize render settings.
"""

import torch
import time
import argparse
import sys
from pathlib import Path

# Ensure we can import detect_gpu from sibling
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from detect_gpu import detect_hardware
except ImportError:
    def detect_hardware():
        return {"gpu_vram_mb": 0, "gpu_name": "Unknown"}


def get_vram_stats():
    """Lấy current VRAM stats."""
    if not torch.cuda.is_available():
        return None

    allocated = torch.cuda.memory_allocated(0) / 1024**2
    reserved = torch.cuda.memory_reserved(0) / 1024**2
    max_alloc = torch.cuda.max_memory_allocated(0) / 1024**2
    max_reserved = torch.cuda.max_memory_reserved(0) / 1024**2

    return {
        "allocated_mb": allocated,
        "reserved_mb": reserved,
        "max_allocated_mb": max_alloc,
        "max_reserved_mb": max_reserved,
        "total_vram_mb": detect_hardware().get("gpu_vram_mb", 0),
    }


def print_vram_stats(stats):
    """In VRAM stats ra màn hình."""
    if stats is None:
        print("CUDA not available")
        return

    total = stats["total_vram_mb"]
    used_pct = (stats["allocated_mb"] / total * 100) if total > 0 else 0

    print(f"GPU: {detect_hardware().get('gpu_name', 'Unknown')}")
    print(f"Total VRAM: {total} MB")
    print(f"Allocated:  {stats['allocated_mb']:.1f} MB ({used_pct:.1f}%)")
    print(f"Reserved:   {stats['reserved_mb']:.1f} MB")
    print(f"Peak Alloc: {stats['max_allocated_mb']:.1f} MB")
    print(f"Peak Resv:  {stats['max_reserved_mb']:.1f} MB")


def monitor(duration_sec=30, interval_sec=1):
    """Monitoring VRAM trong một khoảng thời gian."""
    print(f"Monitoring VRAM for {duration_sec}s (interval: {interval_sec}s)...")
    print("Press Ctrl+C to stop early.\n")

    start = time.time()
    try:
        while time.time() - start < duration_sec:
            stats = get_vram_stats()
            if stats:
                print_vram_stats(stats)
            else:
                print("CUDA not available")
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


def watch():
    """Continuous watch — không dừng."""
    print("Continuous VRAM watch (Ctrl+C to stop)...")
    try:
        while True:
            stats = get_vram_stats()
            if stats:
                print_vram_stats(stats)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopped.")


def main():
    parser = argparse.ArgumentParser(description="VRAM Monitor")
    parser.add_argument("--monitor", action="store_true", help="Monitor for duration")
    parser.add_argument("--watch", action="store_true", help="Continuous watch")
    parser.add_argument("--duration", type=int, default=30, help="Monitor duration (seconds)")
    parser.add_argument("--interval", type=int, default=1, help="Sampling interval (seconds)")
    args = parser.parse_args()

    if args.monitor:
        monitor(args.duration, args.interval)
    elif args.watch:
        watch()
    else:
        # One-shot
        stats = get_vram_stats()
        print_vram_stats(stats)


if __name__ == "__main__":
    main()
