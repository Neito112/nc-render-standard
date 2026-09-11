#!/usr/bin/env python3
"""
build_mzp.py — Canonical MZP package builder for NC_Render_Standard v1.0

KHÔNG bundle model weights — model sẽ được tải tự động trong bước setup.
Model download dựa trên VRAM detected, chọn model tối ưu cho hardware.

⚠️ KHÔNG sử dụng BOM trong mzp.run — 3ds Max parser C++ lỗi
"""
import os
import sys
import zipfile
from pathlib import Path

PLUGIN_ROOT = Path(r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard")
MZP_OUTPUT = PLUGIN_ROOT / "NC_Render_Standard_v1.mzp"

FILES_TO_PACK = [
    "install_info.ini",
    "mzp.run",
    "install.ms",
    "usermacros/uninstall.ms",
    "usermacros/NC_Render_Bridge_v1.mcr",
    "usermacros/NC_Render_Bridge.mcr",
    "usericons/NC_Render_16.png",
    "usericons/NC_Render_24.png",
    "usericons/NC_Render_32.png",
    "usericons/NC_Render_36.png",
    "usericons/NC_Render_48.png",
    "usericons/NC_Render_64.png",
    "usericons/NC_Render_Icon.png",
    "scripts/cuda_auto_install.py",
    "scripts/nc_cuda_render.py",
    "scripts/sd_generate.py",
    "scripts/sd_batch.py",
    "scripts/_setup_download.py",
    "skill/cuda-render-style/cuda_render_tool.py",
    "skill/cuda-render-style/cuda_fix_tool.py",
    "skill/cuda-render-style/cuda_render_config.json",
    "skill/cuda-render-style/SKILL.md",
    "skill/cuda-render-style/templates/prompt_library.md",
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

def main():
    print(f"=== Building .mzp package (v1.0.3 — No BOM, No PackageContents.xml) ===")
    print(f"Source: {PLUGIN_ROOT}")
    print(f"Output: {MZP_OUTPUT}")
    print()
    
    if not PLUGIN_ROOT.exists():
        print(f"❌ Plugin root không tồn tại: {PLUGIN_ROOT}")
        sys.exit(1)
    
    # Check mzp.run Không BOM trước khi build
    mzp_run = PLUGIN_ROOT / "mzp.run"
    with open(mzp_run, 'rb') as f:
        first_bytes = f.read(3)
    if first_bytes == bytes([0xEF, 0xBB, 0xBF]):
        print("❌ mzp.run vẫn còn BOM — loại bỏ trước khi build")
        print("   Chạy: python3 -c \"from pathlib import Path; p=Path('mzp.run'); c=p.read_bytes(); p.write_bytes(c[3:])\"")
        sys.exit(1)
    else:
        print("✅ mzp.run Không BOM")
    
    # Check tất cả files tồn tại
    missing = []
    for rel_path in FILES_TO_PACK:
        full_path = PLUGIN_ROOT / rel_path
        if not full_path.exists():
            missing.append(rel_path)
    
    if missing:
        print(f"❌ Missing files: {missing}")
        sys.exit(1)
    
    print("All files present:")
    for rel_path in FILES_TO_PACK:
        full_path = PLUGIN_ROOT / rel_path
        size = full_path.stat().st_size
        print(f"  ✅ {rel_path} ({size} bytes)")
    
    print()
    
    # Create .mzp — NO PackageContents.xml, NO BOM in mzp.run
    with zipfile.ZipFile(MZP_OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zf:
        for rel_path in FILES_TO_PACK:
            full_path = PLUGIN_ROOT / rel_path
            zf.write(full_path, rel_path)
    
    size = MZP_OUTPUT.stat().st_size
    print(f"✅ Package: {MZP_OUTPUT}")
    print(f"   Size: {size/1024/1024:.2f} MB")
    print()
    print("⚠️ Model weights will be downloaded during setup.")
    print("   - Detect VRAM → auto-select optimal model → download from HuggingFace")
    print("   - If hardware not sufficient → External API only")

if __name__ == "__main__":
    main()
