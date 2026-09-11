#!/usr/bin/env python3
r"""
sanitize_maxscript.py — Chuyển file MaxScript sang pure ASCII (Windows-1252 safe).

Lý do: 3ds Max 2024 MaxScript parser dễ fail im lặng khi gặp:
  - UTF-8 BOM (đã biết)
  - Chuỗi non-ASCII dài / dash typesetting (—, ‘’ “”)
File sau sanitize chỉ dùng để DEPLOY, bản gốc giữ nguyên cho dev.
"""
import sys
from pathlib import Path

# Bảng thay thế các ký tự typesetting phổ biến
REPL = {
    "\u2014": "-",    # em dash
    "\u2013": "-",    # en dash
    "\u2018": "'", "\u2019": "'",   # smart quotes
    "\u201c": '"', "\u201f": '"',   # smart double quotes
    "\u2026": "...",  # ellipsis
    "\u00a0": " ",    # NBSP
    "\u2705": "[OK]", "\u274c": "[x]", "\u26a0\ufe0f": "[!]",
}

# Vietnamese: decompose char-by-char sang ASCII gần đúng
VI = {
    "ă": "a", "Â": "A", "â": "a", "Đ": "D", "đ": "d", "ê": "e", "Ê": "E",
    "ô": "o", "Ô": "O", "ơ": "o", "Ơ": "O", "ư": "u", "Ư": "U",
}


def to_ascii(text: str) -> str:
    for k, v in REPL.items():
        text = text.replace(k, v)

    out = []
    for ch in text:
        if ord(ch) < 128:
            out.append(ch)
            continue
        # NFD decompose: "ậ" -> "a" + dots
        import unicodedata
        d = unicodedata.normalize("NFD", ch)
        base = "".join(c for c in d if unicodedata.category(c) != "Mn")
        if base and all(ord(c) < 128 for c in base):
            out.append(base if len(base) == 1 else VI.get(ch, base))
        elif ch in VI:
            out.append(VI[ch])
        else:
            out.append("?")
    return "".join(out)


def sanitize_file(p: Path):
    raw = p.read_bytes()
    if raw[:3] == b"\xef\xbb\xbf":
        raw = raw[3:]
    text = raw.decode("utf-8", errors="replace")
    # MaxScript comment là "--", không phải "//" — chuyển đổi đầu dòng
    lines = []
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("//"):
            indent = line[: len(line) - len(stripped)]
            line = indent + "--" + stripped[2:]
        lines.append(line)
    text = "\n".join(lines)
    # Chuẩn hóa line ending CRLF cho Max
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    clean = to_ascii(text)
    p.write_bytes(clean.encode("ascii", errors="replace"))
    return len(clean)


def main():
    targets = [
        Path(r"C:/ProgramData/Autodesk/ApplicationPlugins/NC_Render_Standard/Contents/usermacros/NC_Render_Bridge_v1.mcr"),
        Path(r"C:/ProgramData/Autodesk/ApplicationPlugins/NC_Render_Standard/Contents/startup/nc_render_startup.ms"),
        Path(r"C:/ProgramData/Autodesk/ApplicationPlugins/NC_Render_Standard/Contents/mzp.run"),
    ]
    for t in targets:
        if t.exists():
            n = sanitize_file(t)
            # verify
            with open(t, "rb") as f:
                data = f.read()
            bad = [b for b in data if b > 127]
            bom = data[:3] == b"\xef\xbb\xbf"
            print(f"{t.name}: {n} chars, non-ASCII={len(bad)}, BOM={bom}")
        else:
            print(f"MISSING: {t}")


if __name__ == "__main__":
    main()
