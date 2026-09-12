#!/usr/bin/env python3
"""mscheck.py — quick MaxScript sanity checker: parens balance, line-2 style risk.

Usage: python3 mscheck.py <file.ms|file.mzp>   (mzp: checks run_install.ms inside)
"""
import re
import sys
import zipfile
from pathlib import Path

KEYWORDS = {"fn","do","then","on","in","of","case","with","return","exit","true","false","undefined","global","local","if","else","and","or","not"}


def check(name, code):
    problems = []
    # 1. reserved word used as loop/local var
    for kw in KEYWORDS:
        if re.search(r"\bfor\s+" + re.escape(kw) + r"\s+in\b", code):
            problems.append(f"'{kw}' used as for-loop variable")
        if re.search(r"\blocal\s+" + re.escape(kw) + r"\s*=", code):
            problems.append(f"'{kw}' used as local variable")
        # "name value" missing colon (label foo bar vs label foo:"bar") — heuristic on rollout lines
    # 2. paren balance outside strings/comments
    stripped = []
    for line in code.splitlines():
        s = line.strip()
        if s.startswith("--"):
            continue
        s = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', s)
        s = re.sub(r"'(?:[^'\\\n]|\\.)*'", "''", s)
        stripped.append(s)
    j = "\n".join(stripped)
    op, cl = j.count("("), j.count(")")
    if op != cl:
        problems.append(f"paren unbalanced: {op} vs {cl}")
    # 2b. goi ten built-in "ho" da gay undefined trong thuc te (bo qua dong comment)
    code_nc = "\n".join(l for l in code.splitlines() if not l.strip().startswith("--"))
    for ghost in [r"appendIfNotFound", r"appendIfUnique", r"appendUnique", r"macros\.reload",
                  r"\btrim\s*\(", r"trimString", r"\.startsWith\b", r"\.contains\b", r"\bignore\s*\("]:
        if re.search(ghost, code_nc):
            problems.append(f"goi '{ghost}' — ham ma da kiem chung bang 3dsmaxbatch, khong duoc ton tai")
    # 2c. widget khai bao dang '(expr)' o vi tri text -> rollout clause syntax error
    for i, line in enumerate(code.splitlines(), 1):
        if re.match(r'\s*(label|button|checkbox|checkbutton|edittext|radiobuttons|dropdownList|spinner|slider|colorpicker|imagebutton|viewport|groupbox|textbutton|lightbox|curveControl|multiselectlist|listbox|progressBar|hyperLink)\s+\w+\s+\(', line):
            problems.append(f"L{i}: widget 'name (expr)' o vi tri text — rollout clause can string literal, gan .text trong on create")
    # 3. fn defined AFTER first use at execution level? (rough: fn X vs bare X call)
    defs = set(re.findall(r"\bfn\s+(\w+)", code))
    for d in defs:
        m_def = code.index("fn " + d)
        # find a bare call pattern "  name arg" before def inside same script — skip; too noisy
        pass
    # 4. rollout label lines with 3 tokens (likely missing colon)
    for i, line in enumerate(code.splitlines(), 1):
        s = line.strip()
        if re.match(r"(label|button|checkbox|edittext)\s+\w+\s+\w+\s*$", s):
            problems.append(f"L{i}: possible missing ':' -> {s}")
    # 5. tab char (Max tolerant, just FYI)
    if "\t" in code:
        pass

    print(f"=== {name} ===")
    if problems:
        for p in problems:
            print(f"  !! {p}")
    else:
        print("  OK (parens balanced, no reserved-word vars, no colon-less widget lines)")
    return not problems


def main():
    path = Path(sys.argv[1])
    ok = True
    if path.suffix.lower() == ".mzp":
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if n.endswith((".ms", ".mcr", ".run")):
                    ok &= check(n, z.read(n).decode("utf-8", errors="replace"))
    else:
        ok &= check(path.name, path.read_text(encoding="utf-8", errors="replace"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
