#!/usr/bin/env python3
r"""
build_mzp.py — Build .mzp từ BẢN DEPLOY ĐÃ SANITIZE trong ApplicationPlugins.

Nguồn sự thật: C:\ProgramData\Autodesk\ApplicationPlugins\NC_Render_Standard\
  (đã sanitize: pure ASCII, -- comments, không BOM, đúng cấu trúc chuẩn)

Cấu trúc .mzp sinh ra:
  PackageContents.xml          (entry ĐẦU TIÊN)
  Contents/mzp.run
  Contents/usermacros/*.mcr
  Contents/scripts/...
  Contents/skill/...           (không model weights)
  Contents/usericons/...

Chạy: python3 build_mzp.py  (sau khi python3 deploy_to_max.py)
"""
import os
import sys
import zipfile
from pathlib import Path

PKG_DIR = Path(r"C:/ProgramData/Autodesk/ApplicationPlugins/NC_Render_Standard")
OUTPUT = Path(r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/NC_Render_Standard_v1.mzp")

SKIP_EXT = (".safetensors", ".bin", ".pt")


def main():
    if not (PKG_DIR / "PackageContents.xml").exists():
        print("X Source deploy folder not found. Run: python3 deploy_to_max.py")
        sys.exit(1)

    if OUTPUT.exists():
        OUTPUT.unlink()

    entries = []
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        # PackageContents.xml là entry ĐẦU TIÊN
        zf.write(PKG_DIR / "PackageContents.xml", "PackageContents.xml")
        entries.append("PackageContents.xml")

        contents = PKG_DIR / "Contents"
        for root, dirs, files in os.walk(contents):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in sorted(files):
                if fn.endswith(SKIP_EXT):
                    continue
                full = Path(root) / fn
                arc = "Contents/" + full.relative_to(contents).as_posix()
                zf.write(full, arc)
                entries.append(arc)

    print(f"OK: {OUTPUT}")
    print(f"   {len(entries)} files, {OUTPUT.stat().st_size/1024:.0f} KB")
    print(f"   First entry: {entries[0]}")

    # Verify nhanh
    with zipfile.ZipFile(OUTPUT) as zf:
        mcr = zf.read("Contents/usermacros/NC_Render_Bridge_v1.mcr")
        assert mcr[:3] != b"\xef\xbb\xbf", "BOM trong .mcr!"
        assert sum(1 for x in mcr if x > 127) == 0, "non-ASCII trong .mcr!"
        assert not any(l.strip().startswith(b"//") for l in mcr.splitlines()), "// comment trong .mcr!"
        run = zf.read("Contents/mzp.run")
        assert run[:3] != b"\xef\xbb\xbf", "BOM trong mzp.run!"
    print("   Verify: no BOM, pure ASCII, -- comments only  ->  SAN CH")


if __name__ == "__main__":
    main()
