#!/usr/bin/env python3
r"""
build_mzp.py — Build NC_Render_Standard_v1.mzp theo ĐÚNG format drag-drop thật.

BÀI HỌC LỚN (từ 4 .mzp mẫu chạy được trên máy: PruneScene, CollectAsset,
Dabarti, PasteRefImage):  mzp.run KHÔNG PHẢI MaxScript! Nó là file DIRECTIVE
dạng text thuần để Max Engine parse:

    name "..."              <- bắt buộc
    version ...             <- bắt buộc
    description "..."
    extract to "$temp\\MyPlugin"   <- giải nén cả archive vào đây
    drop "run_installer.ms"        <- file mzp không coi là script rơi
    run "run_installer.ms"         <- chạy script cài đặt (MaxScript THẬT)
    clear temp on MAX exit

Mọi logic (dialog setup, detect bản cũ, gỡ/cài) nằm trong run_install.ms.

File zip:
    mzp.run                              (root, directives)
    run_install.ms                       (root, MaxScript installer)
    usermacros/NC_Render_Bridge_v1.mcr   (payload sanitized)

KHÔNG chứa PackageContents.xml (conflict 2 loader).
KHÔNG copy gì vào thư mục Max ngoài ý người dùng — installer chỉ hỏi,
người dùng bấm mới ghi.

Chạy:  python3 build_mzp.py
Cài :  kéo NC_Render_Standard_v1.mzp thả vào cửa sổ 3ds Max.
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


def sanitize_ms(text: str) -> str:
    """MaxScript: // -> --, ASCII-fold, CRLF, khong BOM."""
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


# ============ mzp.run — DIRECTIVES, khong phai MaxScript ============
# QUAN TRONG: "version" la SO (number token), KHONG duoc co 2 dau cham.
# "1.0.4" lam parser Max abort toan bo file -> "Failed to load .mzp".
# Cac .mzp mau chay duoc chi dung: khong co version (PruneScene), hoac
# 1 dau cham (Dabarti "0.901", CollectAsset "2.099"). Dung "1.4" o day.
MZR_RUN = """name "NC-Render AI Studio"
version 1.4
description "CUDA concept render for 3ds Max 2024"
extract to "$temp\\NCRender_install"
drop "run_install.ms"
run "run_install.ms"
clear temp on MAX exit
"""

# ============ run_install.ms — installer MaxScript that ============
RUN_INSTALL = r'''
-- run_install.ms — NC-Render AI Studio v1.4 installer
-- Chay sau khi mzp.run giai nen archive vao $temp\NCRender_install
-- Chi dung messageBox/queryBox (khong dung createDialog -> khong co cua de crash syntax).

(
    local thisDir = getFilenamePath (getThisScriptFilename())
    local srcMcr = thisDir + "usermacros\NC_Render_Bridge_v1.mcr"
    local umDir = getDir #usermacros

    -- ===== Ham cai macroScript =====
    fn doInstall srcPath dstPath =
    (
        if (doesFileExist srcPath) then
        (
            copyFile srcPath dstPath
            macros.reload()
            messageBox "NC-Render AI Studio v1.4 cai dat thanh cong!\n\nMo: Customize > Customize User Interface > Toolbars\n> tab Custom, category NC-Render AI\n> keo button 'NC-Render v1' ra toolbar." title:"NC-Render Install"
            true
        )
        else
        (
            messageBox ("Khong tim thay macroScript trong package:\n" + srcPath) title:"NC-Render Install FAILED"
            false
        )
    )

    -- ===== Ham go sach danh sach cu =====
    fn purgeOld lst =
    (
        for f in lst do
        (
            if (doesFileExist (f + "\")) then (try (deleteDirectory f) catch())
            else (try (deleteFile f) catch())
        )
        macros.reload()
    )

    -- ===== 1. QUET BAN CU =====
    local foundOld = #()

    for f in (getFiles (umDir + "\NC_Render*.mcr")) do appendIfNotFound foundOld f
    for f in (getFiles (umDir + "\NC_Render*.ms"))  do appendIfNotFound foundOld f
    for f in (getFiles (umDir + "\_render_feedback*")) do appendIfNotFound foundOld f

    local uninstFile = umDir + "\uninstall.ms"
    if (doesFileExist uninstFile) then
    (
        local fh = openFile uninstFile mode:"r"
        if fh != undefined then
        (
            local txt = ""
            while not (eof fh) do txt += readLine fh + "\n"
            close fh
            if (matchPattern txt pattern:"*NC-Render*") or (matchPattern txt pattern:"*NCRender*") then
                appendIfNotFound foundOld uninstFile
        )
    )

    local us = getDir #userScripts
    for f in (getFiles (us + "\sd_generate.py"))       do appendIfNotFound foundOld f
    for f in (getFiles (us + "\sd_batch.py"))          do appendIfNotFound foundOld f
    for f in (getFiles (us + "\cuda_auto_install.py")) do appendIfNotFound foundOld f
    for f in (getFiles (us + "\nc_cuda_render.py"))    do appendIfNotFound foundOld f
    for f in (getFiles (us + "\github_update.py"))     do appendIfNotFound foundOld f
    for f in (getFiles (us + "\_setup_download.py"))   do appendIfNotFound foundOld f

    local ncFolder = us + "\NC-Render"
    if (doesFileExist (ncFolder + "\")) do appendIfNotFound foundOld ncFolder

    for f in (getFiles ((getDir #userIcons) + "\NC_Render_*.*")) do appendIfNotFound foundOld f

    local apDir = @"C:\ProgramData\Autodesk\ApplicationPlugins\NC_Render_Standard"
    if (doesFileExist (apDir + "\")) do appendIfNotFound foundOld apDir

    -- ===== 2. QUYET DINH =====
    if (foundOld.count == 0) then
    (
        doInstall srcMcr (umDir + "\NC_Render_Bridge_v1.mcr")
    )
    else
    (
        local msgOld = "Phat hien " + (foundOld.count as string) + " thanh phan cu:\n\n"
        for f in foundOld do msgOld += f + "\n"
        msgOld += "\nBam [Co] = Go cu + Cai lai.\nBam [Khong] = Chi go, chua cai.\nBam Huy o goc tren = giu nguyen."

        local doRemove = queryBox msgOld title:"NC-Render - Phat hien ban cu"
        if doRemove then
        (
            purgeOld foundOld
            doInstall srcMcr (umDir + "\NC_Render_Bridge_v1.mcr")
        )
        else
        (
            messageBox ("Da go " + (foundOld.count as string) + " thanh phan cu.\nChua cai ban moi.") title:"NC-Render - Da go"
        )
    )
)
'''


def main():
    src_mcr = PLUGIN_ROOT / "usermacros" / "NC_Render_Bridge_v1.mcr"
    if not src_mcr.exists():
        print(f"X thieu {src_mcr}")
        sys.exit(1)

    if OUTPUT.exists():
        OUTPUT.unlink()

    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mzp.run", MZR_RUN.replace("\n", "\r\n"))          # directives thuan
        zf.writestr("run_install.ms", sanitize_ms(RUN_INSTALL))         # MaxScript sanitized
        zf.writestr("usermacros/NC_Render_Bridge_v1.mcr", sanitize_ms(read_clean(src_mcr)))

    # Verify
    with zipfile.ZipFile(OUTPUT) as zf:
        names = zf.namelist()
        assert "PackageContents.xml" not in names
        assert names[0] == "mzp.run", "mzp.run phai la entry dau tien"
        run = zf.read("mzp.run")
        assert run[:3] != b"\xef\xbb\xbf", "mzp.run co BOM!"
        assert run.startswith(b'name "'), f"mzp.run phai bat dau bang directive name: {run[:20]!r}"
        for kw in [b"extract to", b"drop", b"run "]:
            assert kw in run, f"mzp.run thieu directive {kw!r}"
        # "version" phai la so voi TOI DA 1 dau cham (Max parser doc nhu number literal)
        import re as _re
        vm = _re.search(rb"version\s+(\S+)", run)
        if vm:
            vtok = vm.group(1).decode()
            assert vtok.count(".") <= 1, f"mzp.run 'version {vtok}' co qua 1 dau cham -> Max parser abort (Failed to load .mzp)!"
            assert _re.fullmatch(r"[0-9]+(\.[0-9]+)?", vtok), f"mzp.run 'version {vtok}' khong phai so hop le!"
        ri = zf.read("run_install.ms")
        assert ri[:3] != b"\xef\xbb\xbf" and sum(1 for x in ri if x > 127) == 0, "run_install.ms BOM/non-ASCII!"
        assert not any(l.strip().startswith(b"//") for l in ri.splitlines()), "run_install.ms co // comment!"
        # 'fn' la keyword dinh nghia ham cua MaxScript — dung lam bien vong lap = syntax crash ca file
        _ri = ri.decode()
        for _kw in ["fn", "do", "then", "on", "in", "of", "case", "with", "return", "exit", "true", "false", "undefined"]:
            import re as _re2
            assert not _re2.search(r"\bfor\s+" + _kw + r"\s+in\b", _ri), f"run_install.ms dung keyword '{_kw}' lam bien for-loop -> MaxScript syntax error!"
            assert not _re2.search(r"\blocal\s+" + _kw + r"\s*=", _ri), f"run_install.ms dung keyword '{_kw}' lam bien local -> MaxScript syntax error!"
        mc = zf.read("usermacros/NC_Render_Bridge_v1.mcr")
        assert mc[:3] != b"\xef\xbb\xbf" and sum(1 for x in mc if x > 127) == 0, ".mcr BOM/non-ASCII!"
        assert not any(l.strip().startswith(b"//") for l in mc.splitlines()), ".mcr co // comment!"

    print(f"OK: {OUTPUT}")
    print(f"   {len(names)} files, {OUTPUT.stat().st_size/1024:.0f} KB: {names}")
    print("   mzp.run = DIRECTIVES (name/extract/drop/run) — khop dinh dang 4 .mzp mau")
    print("   Verify: entry dau = mzp.run, khong BOM, ASCII, -- comments, khong PackageContents.xml")
    print("   -> keo tha file .mzp vao cua so 3ds Max.")


if __name__ == "__main__":
    main()
