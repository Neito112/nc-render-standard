#!/usr/bin/env python3
r"""
build_mzp.py — Build NC_Render_Standard_v1.mzp TỰ NHIÊN TỪ PROJECT FOLDER.

Không copy gì vào thư mục 3ds Max. Người dùng tự kéo .mzp vào Max để cài.

Cơ chế:
  1. Đọc source từ project (giữ nguyên tiếng Việt để dev dễ đọc)
  2. SANITIZE on-the-fly khi đóng gói:
       - bỏ UTF-8 BOM          (parser Max fail im lặng)
       - // comment -> --      (MaxScript không nhận //)
       - non-ASCII -> ASCII    (an toàn encoding)
       - CRLF line endings
  3. Đóng .mzp theo cấu trúc chuẩn ApplicationPlugins:
       PackageContents.xml      (entry ĐẦU TIÊN)
       Contents/startup/*.ms    (Max chạy mỗi lần khởi động, dùng @thisScript — không hardcode path)
       Contents/usermacros/*.mcr
       Contents/scripts/ Contents/skill/ Contents/usericons/
       Contents/mzp.run Contents/install.ms
"""
import os
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

PLUGIN_ROOT = Path(r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard")
OUTPUT = PLUGIN_ROOT / "NC_Render_Standard_v1.mzp"

MAXSCRIPT_EXT = {".mcr", ".ms", ".run"}
SKIP_EXT = (".safetensors", ".bin", ".pt")

REPL = {
    "\u2014": "-", "\u2013": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201f": '"',
    "\u2026": "...", "\u00a0": " ",
    "\u2705": "[OK]", "\u274c": "[x]",
}


def to_ascii(text: str) -> str:
    for k, v in REPL.items():
        text = text.replace(k, v)
    out = []
    for ch in text:
        if ord(ch) < 128:
            out.append(ch)
            continue
        d = unicodedata.normalize("NFD", ch)
        base = "".join(c for c in d if unicodedata.category(c) != "Mn")
        out.append(base if base and all(ord(c) < 128 for c in base) else "?")
    return "".join(out)


def sanitize_maxscript(text: str) -> str:
    """BOM-stripped text (bytes->str đã decode) -> // thành --, ASCII, CRLF."""
    lines = []
    for line in text.split("\n"):
        s = line.lstrip()
        if s.startswith("//"):
            line = line[: len(line) - len(s)] + "--" + s[2:]
        lines.append(line)
    text = "\n".join(lines)
    return to_ascii(text).replace("\r\n", "\n").replace("\n", "\r\n")


def read_bytes(p: Path) -> bytes:
    d = p.read_bytes()
    return d[3:] if d[:3] == b"\xef\xbb\xbf" else d


def main():
    print("=== Build .mzp tu project (sanitize on-the-fly) ===")

    # --- PackageContents.xml sinh trực tiếp ở đây, nhất quán với cấu trúc zip ---
    pkg_xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<ApplicationPackage SchemaVersion="1.0"\n'
        '        AutodeskProduct="3ds Max" ProductType="Application"\n'
        '        Name="NC_Render_Standard"\n'
        '        AppVersion="1.0.3"\n'
        '        Author="Neito"\n'
        '        ProductCode="{a3f1c2d4-5b6e-47f8-9a0b-c1d2e3f4a5b6}"\n'
        '        UpgradeCode="{b4e2d3f5-6c7f-4809-ab1c-d2e3f4a5b6c7}">\n'
        '    <CompanyDetails Name="Neito" />\n'
        '    <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="2024" SeriesMax="2027" />\n'
        '    <Components Description="startup script parts">\n'
        '        <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="2024" SeriesMax="2027" />\n'
        '        <ComponentEntry AppName="NCRenderStartup" ModuleName="./Contents/startup/nc_render_startup.ms" />\n'
        '    </Components>\n'
        '    <Components Description="macroscript parts">\n'
        '        <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="2024" SeriesMax="2027" />\n'
        '        <ComponentEntry AppName="NCRenderMacros" ModuleName="./Contents/usermacros" />\n'
        '    </Components>\n'
        '    <Components Description="resource parts">\n'
        '        <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="2024" SeriesMax="2027" />\n'
        '        <ComponentEntry AppName="NCRenderResources" ModuleName="./Contents/scripts" />\n'
        '        <ComponentEntry AppName="NCRenderSkill" ModuleName="./Contents/skill" />\n'
        '        <ComponentEntry AppName="NCRenderIcons" ModuleName="./Contents/usericons" />\n'
        '    </Components>\n'
        '</ApplicationPackage>\n'
    )

    # --- Startup script chỉ copy .mcr vào usermacros; payload Python nằm lại project ---
    startup_ms = (
        '-- nc_render_startup.ms -- NC-Render AI Studio v1.0.3\n'
        '-- Copy macroScript vao usermacros cua Max (payload van nam trong project).\n'
        'try\n'
        '(\n'
        '    local src = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"\n'
        '    local dst = (getDir #usermacros) + "NC_Render_Bridge_v1.mcr"\n'
        '\n'
        '    if (doesFileExist src) then\n'
        '    (\n'
        '        copyFile src dst\n'
        '        macros.reload()\n'
        '        format "NC-Render: MacroScript v1.0.3 installed to usermacros\\n"\n'
        '    )\n'
        '    else\n'
        '        format "NC-Render: WARNING - macroScript not found at %\\n" src\n'
        ')\n'
        'catch (format "NC-Render: startup error: %\\n" (getCurrentException()))\n'
    )

    if OUTPUT.exists():
        OUTPUT.unlink()

    added = []
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. PackageContents.xml DAU TIEN
        zf.writestr("PackageContents.xml", pkg_xml.replace("\n", "\r\n"))
        added.append("PackageContents.xml")

        # 2. Startup script (dat canh usermacros de @thisScript tro thang file .mcr)
        zf.writestr("Contents/usermacros/NC_Render_Bridge_v1.mcr",
                    sanitize_maxscript(read_bytes(PLUGIN_ROOT / "usermacros" / "NC_Render_Bridge_v1.mcr").decode("utf-8")))
        zf.writestr("Contents/usermacros/uninstall.ms",
                    sanitize_maxscript(read_bytes(PLUGIN_ROOT / "usermacros" / "uninstall.ms").decode("utf-8")))
        zf.writestr("Contents/startup/nc_render_startup.ms", startup_ms.replace("\n", "\r\n"))
        added += ["Contents/usermacros/NC_Render_Bridge_v1.mcr",
                  "Contents/usermacros/uninstall.ms",
                  "Contents/startup/nc_render_startup.ms"]

        # 3. Legacy installer files
        for name in ["mzp.run", "install.ms"]:
            p = PLUGIN_ROOT / name
            if p.exists():
                zf.writestr("Contents/" + name,
                            sanitize_maxscript(read_bytes(p).decode("utf-8")))
                added.append("Contents/" + name)

        # 4. Resources: scripts/, skill/ (bo weights), usericons/
        for sub in ["scripts", "skill", "usericons"]:
            root_dir = PLUGIN_ROOT / sub
            if not root_dir.exists():
                print(f"! {sub}/ not found, skip")
                continue
            for root, dirs, files in os.walk(root_dir):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for fn in sorted(files):
                    full = Path(root) / fn
                    if full.suffix in SKIP_EXT:
                        continue
                    arc = sub + "/" + full.relative_to(root_dir).as_posix()
                    if full.suffix in MAXSCRIPT_EXT or fn == "mzp.run":
                        zf.writestr("Contents/" + arc,
                                    sanitize_maxscript(read_bytes(full).decode("utf-8")))
                    else:
                        zf.write(full, "Contents/" + arc)
                    added.append("Contents/" + arc)

    # 5. Verify (đọc lại sau khi đóng zip)
    with zipfile.ZipFile(OUTPUT) as zf_check:
        for check_name in ["PackageContents.xml",
                           "Contents/startup/nc_render_startup.ms",
                           "Contents/mzp.run",
                           "Contents/usermacros/NC_Render_Bridge_v1.mcr"]:
            data = zf_check.read(check_name)
            assert data[:3] != b"\xef\xbb\xbf", f"BOM trong {check_name}!"
            bad = sum(1 for x in data if x > 127)
            assert bad == 0, f"non-ASCII trong {check_name}: {bad}"
            assert not any(l.strip().startswith(b"//") for l in data.splitlines()), f"// comment trong {check_name}!"

    print(f"\nOK: {OUTPUT}")
    print(f"   {len(added)} files, {OUTPUT.stat().st_size/1024:.0f} KB")
    print("   Verify: khong BOM, pure ASCII, chi dung -- comment")
    print("\n   -> keo tha NC_Render_Standard_v1.mzp vao 3ds Max de cai.")


if __name__ == "__main__":
    main()
