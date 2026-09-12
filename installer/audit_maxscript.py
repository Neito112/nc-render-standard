import re
import sys

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
lines = open(p, encoding="utf-8", errors="replace").read().splitlines()

findings = []

def add(cat, i, txt):
    findings.append((cat, i, txt.strip()[:95]))

# 1. ham/toan tu ma (JS/Python)
GHOST = [r"\btrim\s*\(", r"\btrimString", r"\.startsWith\b", r"\.contains\b",
         r"\bappendIfNotFound\b", r"\bappendIfUnique\b", r"\bmacros\.reload\b",
         r"\bgetExceptionString\b", r"\bignore\s*\(", r"\b\w+\s+contains\s+[\"']",
         r"\.length\b", r"\.push\s*\(", r"\.includes\s*\(", r"===|!==",
         r"\blen\s*\(", r"\bprint\s*\(", r"\bstr\s*\(", r"\brange\s*\(",
         r"\bf\"", r"\.append\s*\(", r"\.split\s*\(", r"\.join\s*\(",
         r"\.strip\s*\(", r"\.upper\s*\(", r"\.lower\s*\(", r"\.replace\s*\("]
for pat in GHOST:
    for i, l in enumerate(lines, 1):
        if l.strip().startswith("--"): continue
        if re.search(pat, l):
            add("GHOST", i, l)

# 2. widget khai bao dang '(expr)' o vi tri text
WIDGET = r'(label|button|checkbox|checkbutton|edittext|radiobuttons|dropdownList|spinner|slider|colorpicker|imagebutton|viewport|groupbox|textbutton|lightbox|curveControl|multiselectlist|listbox|progressBar|hyperLink|quadMenu)'
for i, l in enumerate(lines, 1):
    if re.match(r"^\s*" + WIDGET + r"\s+\w+\s+\(", l):
        add("WIDGET-PAREN", i, l)

# 3. popupMenu / button goi nhu ham (gan '=' truoc no)
for i, l in enumerate(lines, 1):
    if re.search(r"=\s*(button|label|checkbox|edittext|spinner|dropdownList|popupMenu)\s+\w", l):
        add("WIDGET-AS-FUNC", i, l)
    if re.match(r"^\s*popupMenu\s", l):
        add("POPUP-WIDGET", i, l)

# 4. 'on create do' thieu ten rollout
for i, l in enumerate(lines, 1):
    if re.match(r"^\s*on\s+create\s+do\s*$", l):
        add("ON-CREATE-NONAME", i, l)

# 5. case of / comment chen giua case branch
for i, l in enumerate(lines, 1):
    if re.search(r"\bcase\s+of\b", l):
        add("CASE-OF", i, l)
    if re.match(r"^\s*\w+:\s*(--|//)", l):
        add("CASE-COMMENT", i, l)

# 6. noi dung dau \ cuoi dong
for i, l in enumerate(lines, 1):
    if l.rstrip().endswith("\\") and not l.rstrip().endswith("\\\\"):
        add("BACKSLASH-CONT", i, l)

# 7. 'if...do' ma dong ke tiep la 'else' (if-do khong co else)
for i in range(len(lines) - 1):
    cur, nxt = lines[i], lines[i + 1]
    if re.search(r"\bif\b.*\bdo\s*$", cur) and re.match(r"^\s*else\b", nxt):
        add("IFDO-ELSE", i + 1, cur)
    if re.search(r"\bif\b.*\bdo\s*\(\s*$", cur) and re.match(r"^\s*else\b", nxt):
        add("IFDO-ELSE", i + 1, cur)

# 8. widget trung ten
names = {}
for i, l in enumerate(lines, 1):
    m = re.match(r"^\s*" + WIDGET + r"\s+(\w+)\s", l)
    if m:
        names.setdefault(m.group(2), []).append(i)
for nm, locs in names.items():
    if len(locs) > 1:
        add("DUP-WIDGET", locs[0], f"{nm} trung tai {locs}")

# 9. messageBox/queryBox voi buttons:
for i, l in enumerate(lines, 1):
    if re.search(r"(messageBox|queryBox)\b.*\bbuttons\s*:", l):
        add("MSGBOX-BUTTONS", i, l)

# 10. 'then' thieu nhanh (if x then do)
for i, l in enumerate(lines, 1):
    if re.search(r"\bthen\s+do\b", l):
        add("THEN-DO", i, l)

# in bao cao
from collections import Counter
cats = Counter(f[0] for f in findings)
print("=== AUDIT:", p.split(chr(92))[-1], "===")
for c, n in cats.most_common():
    print(f"  {c}: {n}")
print()
for cat, i, t in findings:
    print(f"[{cat}] L{i}: {t}")
