#!/usr/bin/env python3
"""
build_mzp.py — Canonical MZP package builder for NC_Render_Standard v1.0

KHÔNG bundle model weights — model sẽ được tải tự động trong bước setup.
Model download dựa trên VRAM detected, chọn model tối ưu cho hardware.
"""
import os
import sys
import zipfile
from pathlib import Path

PLUGIN_ROOT = Path(r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard")
MZP_OUTPUT = PLUGIN_ROOT / "NC_Render_Standard_v1.mzp"

FILES_TO_PACK = [
    # Package info
    "install_info.ini",
    "mzp.run",
    "install.ms",
    "usermacros/uninstall.ms",
    # MacroScript files
    "usermacros/NC_Render_Bridge_v1.mcr",
    "usermacros/NC_Render_Bridge.mcr",
    # Icons
    "usericons/NC_Render_16.png",
    "usericons/NC_Render_24.png",
    "usericons/NC_Render_32.png",
    "usericons/NC_Render_36.png",
    "usericons/NC_Render_48.png",
    "usericons/NC_Render_64.png",
    "usericons/NC_Render_Icon.png",
    # Python scripts
    "scripts/cuda_auto_install.py",
    "scripts/nc_cuda_render.py",
    "scripts/sd_generate.py",
    "scripts/sd_batch.py",
    "scripts/_setup_download.py",
    # CUDA Render Skill
    "skill/cuda-render-style/cuda_render_tool.py",
    "skill/cuda-render-style/cuda_fix_tool.py",
    "skill/cuda-render-style/cuda_render_config.json",
    "skill/cuda-render-style/SKILL.md",
    "skill/cuda-render-style/templates/prompt_library.md",
    # SD1.5 Model — config files ONLY (no weights)
    "skill/cuda-render-style/models/sd15/model_index.json",
    "skill/cuda-render-style/models/sd15/unet/config.json",
    "skill/cuda-render-style/models/sd15/text_encoder/config.json",
    "skill/cuda-render-style/models/sd15/vae/config.json",
    "skill/cuda-render-style/models/sd15/tokenizer/tokenizer.json",
    "skill/cuda-render-style/models/sd15/tokenizer/tokenizer_config.json",
    "skill/cuda-render-style/models/sd15/scheduler/scheduler_config.json",
    "skill/cuda-render-style/models/sd15/safety_checker/config.json",
    "skill/cuda-render-style/models/sd15/feature_extractor/preprocessor_config.json",
]


def pack_missing_report() -> list[str]:
    """Return list of missing files (for diagnostics, not a hard failure)."""
    missing = []
    for rel in FILES_TO_PACK:
        if not (PLUGIN_ROOT / rel).exists():
            missing.append(rel)
    return missing


def build() -> bool:
    print(f"=== Building .mzp package (v1.0 — NO model weights) ===")
    print(f"Source: {PLUGIN_ROOT}")
    print(f"Output: {MZP_OUTPUT}")
    print(f"\n⚠️ Model weights NOT included — sẽ tự động tải trong bước setup.")
    print(f"   Installer sẽ detect VRAM → chọn model tối ưu → tải từ HuggingFace.")

    missing = pack_missing_report()
    if missing:
        print(f"⚠ {len(missing)} file(s) not found (will be skipped):")
        for m in missing:
            print(f"   - {m}")
    else:
        print("All files present.")

    with zipfile.ZipFile(str(MZP_OUTPUT), "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in FILES_TO_PACK:
            abs_path = PLUGIN_ROOT / rel
            if abs_path.exists():
                zf.write(str(abs_path), arcname=rel)
                size = abs_path.stat().st_size
                print(f"  ✅ {rel} ({size:,} bytes)")
            else:
                print(f"  ⏭  skipped (missing): {rel}")

    if MZP_OUTPUT.exists():
        size_mb = MZP_OUTPUT.stat().st_size / (1024 * 1024)
        print(f"\n✅ Package: {MZP_OUTPUT}")
        print(f"   Size: {size_mb:.2f} MB (code + config only)")
        print("\n⚠️ Model weights will be downloaded during setup.")
        print("   - Detect VRAM → auto-select optimal model → download from HuggingFace")
        print("   - If hardware not sufficient → External API only")
        return True
    else:
        print("\n❌ Package creation failed")
        return False


if __name__ == "__main__":
    ok = build()
    missing = pack_missing_report()
    if missing:
        print(f"\n⚠ Missing files ({len(missing)}):")
        for m in missing:
            print(f"   - {m}")
    sys.exit(0 if ok else 1)
