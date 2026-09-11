#!/usr/bin/env python3
r"""
build_mzp.py — Build NC_Render_Standard_v1.mzp bản DRAG-AND-DROP thuần.

Tất cả file nằm trong thư mục dự án; .mzp chỉ là installer tối giản:

    mzp.run                      <- root of zip, entry point (NO BOM, -- comments, ASCII)
    install_info.ini             <- metadata
    usermacros/NC_Render_Bridge_v1.mcr   <- payload macroScript (đã sanitize)
    usermacros/uninstall.ms

KHÔNG chứa PackageContents.xml — 2 package loader cùng có = silent conflict.

mzp.run copy .mcr vào usermacros của Max, chạy macros.reload().
Mọi payload Python/skill/icon KHÔNG cài đi đâu — macroScript trỏ thẳng
về dự án qua ncPluginRoot đã hardcode trong .mcr.

Chạy:  python3 build_mzp.py
Sau đó: kéo NC_Render_Standard_v1.mzp thả vào cửa sổ 3ds Max.
"""
import sys
import unicodedata
import zipfile
from pathlib import Path

PLUGIN_ROOT = Path(r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard")
OUTPUT = PLUGIN_ROOT / "NC_Render_Standard_v1.mzp"

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


def sanitize(text: str) -> str:
    """// comment -> --, ASCII-fold, CRLF, no BOM."""
    lines = []
    for line in text.replace("\r\n", "\n").split("\n"):
        s = line.lstrip()
        if s.startswith("//"):
            line = line[: len(line) - len(s)] + "--" + s[2:]
        lines.append(line)
    return to_ascii("\n".join(lines)).replace("\n", "\r\n")


def read_clean(p: Path) -> str:
    d = p.read_bytes()
    if d[:3] == b"\xef\xbb\xbf":
        d = d[3:]
    return d.decode("utf-8", errors="replace")


# mzp.run — installer tối giản, tự định vị, có fallback về dự án
MZR_RUN = r'''
-- mzp.run -- NC-Render AI Studio v1.0.3 (drag-drop installer)
-- Copy macroScript vao usermacros cua Max va reload.
-- Payload (python scripts, skill, icons) nam lai trong thu muc du an.
try
(
    local myDir = getFilenamePath @thisScript
    local src = myDir + "usermacros\\NC_Render_Bridge_v1.mcr"

    if (doesFileExist src) then
    (
        copyFile src ((getDir #usermacros) + "NC_Render_Bridge_v1.mcr")
        macros.reload()
        format "NC-Render: MacroScript v1.0.3 installed OK\n"
        messageBox "NC-Render AI Studio v1.0.3 cai dat thanh cong!\n\nTim dang 'NC-Render' trong:\nCustomize > Customize User Interface > Toolbars\n(tab Custom, category NC-Render AI)" title:"NC-Render Install"
    )
    else
        messageBox ("Khong tim thay macroScript:\n" + src) title:"NC-Render Install FAILED"
)
catch (messageBox ("Loi cai dat: " + (getCurrentException() as string)) title:"NC-Render Install ERROR")
'''

INSTALL_INFO = """\
[Application]
Friendly name=NC-Render AI Studio
Version=1.0
Developer name=Neito
More info URL = https://github.com/Neito112/nc-render-standard
"""


def main():
    src_mcr = PLUGIN_ROOT / "usermacros" / "NC_Render_Bridge_v1.mcr"
    src_uninstall = PLUGIN_ROOT / "usermacros" / "uninstall.ms"
    for p in (src_mcr, src_uninstall):
        if not p.exists():
            print(f"X thieu file: {p}")
            sys.exit(1)

    if OUTPUT.exists():
        OUTPUT.unlink()

    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mzp.run", sanitize(MZR_RUN))
        zf.writestr("install_info.ini", INSTALL_INFO)
        zf.writestr("usermacros/NC_Render_Bridge_v1.mcr", sanitize(read_clean(src_mcr)))
        zf.writestr("usermacros/uninstall.ms", sanitize(read_clean(src_uninstall)))

    # Verify sau khi dong zip: khong BOM, ASCII, khong //, khong PackageContents.xml
    with zipfile.ZipFile(OUTPUT) as zf:
        names = zf.namelist()
        assert "PackageContents.xml" not in names, "Co PackageContents.xml = conflict!"
        assert "mzp.run" in names, "Thieu mzp.run!"
        for n in names:
            b = zf.read(n)
            assert b[:3] != b"\xef\xbb\xbf", f"BOM trong {n}!"
            if n.endswith((".run", ".mcr", ".ms", ".ini")):
                assert sum(1 for x in b if x > 127) == 0, f"non-ASCII trong {n}!"
                assert not any(l.strip().startswith(b"//") for l in b.splitlines()), f"// comment trong {n}!"

    print(f"OK: {OUTPUT}")
    print(f"   {len(names)} files, {OUTPUT.stat().st_size/1024:.0f} KB: {names}")
    print("   Verify: mzp.run root, KHONG PackageContents.xml, khong BOM/ASCII/// comment")
    print("   -> keo tha NC_Render_Standard_v1.mzp vao cua so 3ds Max.")


if __name__ == "__main__":
    main()
