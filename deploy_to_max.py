#!/usr/bin/env python3
r"""
deploy_to_max.py — Deploy NC-Render AI Studio v1.0.3 vào 3ds Max theo chuẩn
Autodesk ApplicationPlugins (giống cách MCP bridge và Forest Pack cài đặt).

KHÔNG dùng drag-drop .mzp nữa (3ds Max 2024 không handle .mzp qua drag-drop).
Cách chuẩn: folder giải nén + PackageContents.xml tại:
  C:\ProgramData\Autodesk\ApplicationPlugins\NC_Render_Standard\

Sau khi deploy: RESTART 3ds Max → startup script tự sync macroScript.
"""
import shutil
import sys
from pathlib import Path

PLUGIN_ROOT = Path(r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard")
PKG_DIR = Path(r"C:/ProgramData/Autodesk/ApplicationPlugins/NC_Render_Standard")
CONTENTS = PKG_DIR / "Contents"


def deploy():
    print("=== Deploy NC-Render AI Studio v1.0.3 ===")
    print(f"Source : {PLUGIN_ROOT}")
    print(f"Target : {PKG_DIR}")
    print()

    if not PLUGIN_ROOT.exists():
        print(f"x Source not found: {PLUGIN_ROOT}")
        sys.exit(1)

    # 1. Xóa bản cũ (build artifact, không có user data)
    if PKG_DIR.exists():
        shutil.rmtree(PKG_DIR)
        print("- Da xoa ban cu trong ApplicationPlugins")

    # 2. Tạo cấu trúc chuẩn
    for sub in ["Contents/startup", "Contents/usermacros", "Contents/scripts",
                "Contents/skill", "Contents/usericons"]:
        (PKG_DIR / sub).mkdir(parents=True, exist_ok=True)

    # 3. Copy payloads
    for f in (PLUGIN_ROOT / "usermacros").glob("*"):
        if f.suffix in (".mcr", ".ms"):
            shutil.copy2(f, CONTENTS / "usermacros" / f.name)
    for f in (PLUGIN_ROOT / "scripts").glob("*.py"):
        shutil.copy2(f, CONTENTS / "scripts" / f.name)
    for f in (PLUGIN_ROOT / "usericons").glob("*.png"):
        shutil.copy2(f, CONTENTS / "usericons" / f.name)

    # skill: copy toàn bộ trừ weights + cache
    src_skill = PLUGIN_ROOT / "skill" / "cuda-render-style"
    dst_skill = CONTENTS / "skill" / "cuda-render-style"
    if src_skill.exists():
        shutil.copytree(src_skill, dst_skill, ignore=shutil.ignore_patterns(
            "*.safetensors", "*.bin", "*.pt", "test_*.png", "__pycache__"))

    # mzp.run + install.ms (legacy installer)
    for name in ["mzp.run", "install.ms"]:
        p = PLUGIN_ROOT / name
        if p.exists():
            shutil.copy2(p, CONTENTS / name)

    # 4. Startup script — chạy mỗi lần Max khởi động
    startup = CONTENTS / "startup" / "nc_render_startup.ms"
    startup.write_text(
        '-- nc_render_startup.ms — NC-Render AI Studio v1.0.3 startup\n'
        '-- Dong bo macroScript vao usermacros + dang ky plugin root\n'
        'try\n'
        '(\n'
        '    local pkgRoot = @"' + str(CONTENTS.as_posix()) + '"\n'
        '    local mcrSrc = pkgRoot + "/usermacros/NC_Render_Bridge_v1.mcr"\n'
        '    local mcrDst = (getDir #usermacros) + "/NC_Render_Bridge_v1.mcr"\n'
        '\n'
        '    if (doesFileExist mcrSrc) then\n'
        '    (\n'
        '        copyFile mcrSrc mcrDst\n'
        '        macros.reload()\n'
        '        format "NC-Render: MacroScript v1.0.3 synced to usermacros\\n"\n'
        '    )\n'
        '    else\n'
        '    (\n'
        '        format "NC-Render: WARNING - macroScript not found at %\\n" mcrSrc\n'
        '    )\n'
        '\n'
        '    global NCRenderPluginRoot = pkgRoot\n'
        ')\n'
        'catch (format "NC-Render: startup error: %\\n" (getCurrentException()))\n',
        encoding="utf-8", newline="\n")  # KHÔNG BOM

    # 5. PackageContents.xml tại ROOT
    (PKG_DIR / "PackageContents.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<ApplicationPackage SchemaVersion="1.0"\n'
        '        AutodeskProduct="3ds Max"\n'
        '        ProductType="Application"\n'
        '        Name="NC-Render AI Studio"\n'
        '        AppVersion="1.0.3"\n'
        '        Author="Neito"\n'
        '        ProductCode="{a3f1c2d4-5b6e-47f8-9a0b-c1d2e3f4a5b6}"\n'
        '        UpgradeCode="{b4e2d3f5-6c7f-4809-ab1c-d2e3f4a5b6c7}">\n'
        '    <CompanyDetails Name="Neito" />\n'
        '    <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="2024" SeriesMax="2027" />\n'
        '\n'
        '    <Components Description="startup script parts">\n'
        '        <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="2024" SeriesMax="2027" />\n'
        '        <ComponentEntry ModuleName="./Contents/startup/nc_render_startup.ms" />\n'
        '    </Components>\n'
        '\n'
        '    <Components Description="macroscript parts">\n'
        '        <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="2024" SeriesMax="2027" />\n'
        '        <ComponentEntry ModuleName="./Contents/usermacros" />\n'
        '    </Components>\n'
        '\n'
        '    <Components Description="resource parts">\n'
        '        <RuntimeRequirements OS="Win64" Platform="3ds Max" SeriesMin="2024" SeriesMax="2027" />\n'
        '        <ComponentEntry ModuleName="./Contents/scripts" />\n'
        '        <ComponentEntry ModuleName="./Contents/skill" />\n'
        '        <ComponentEntry ModuleName="./Contents/usericons" />\n'
        '    </Components>\n'
        '</ApplicationPackage>\n',
        encoding="utf-8", newline="\n")

    print("- PackageContents.xml (root) OK")
    print("- Contents/startup/nc_render_startup.ms OK (khong BOM)")
    print("- Contents/usermacros/*.mcr OK")
    print("- Contents/scripts/*.py OK")
    print("- Contents/skill/cuda-render-style/ OK (khong weights)")
    print("- Contents/usericons/*.png OK")

    # 6. Sanitize MaxScript sang pure ASCII (parser Max fail im lặng với non-ASCII)
    from sanitize_maxscript import sanitize_file
    for p in [CONTENTS / "usermacros" / "NC_Render_Bridge_v1.mcr",
              CONTENTS / "usermacros" / "NC_Render_Bridge.mcr",
              CONTENTS / "startup" / "nc_render_startup.ms",
              CONTENTS / "mzp.run"]:
        if p.exists():
            sanitize_file(p)

    # 7. Verify BOM
    problems = []
    for name, p in [("PackageContents.xml", PKG_DIR / "PackageContents.xml"),
                    ("nc_render_startup.ms", startup),
                    ("NC_Render_Bridge_v1.mcr", CONTENTS / "usermacros" / "NC_Render_Bridge_v1.mcr"),
                    ("mzp.run", CONTENTS / "mzp.run")]:
        if p.exists():
            with open(p, "rb") as f:
                if f.read(3) == b"\xef\xbb\xbf":
                    problems.append(name)
    if problems:
        print(f"!! CO BOM trong: {problems} — 3ds Max co the khong parse duoc")
    else:
        print("- Verify: khong file nao co BOM OK")

    print()
    print("== DEPLOY HOAN TAT ==")
    print("  -> RESTART 3ds Max de startup script chay.")
    print("  -> Kiem tra MaxScript Listener (F11), phai hien dong:")
    print('     "NC-Render: MacroScript v1.0.3 synced to usermacros"')


if __name__ == "__main__":
    deploy()
