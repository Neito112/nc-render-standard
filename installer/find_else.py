import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
lines = open(p, encoding="utf-8", errors="replace").read().splitlines()

# Tim moi dong 'else if' / 'else' dang sau mot 'do' block => MaxScript invalid
# Chuyen 'X do (' -> 'X then (' khi no co 'else' theo sau o cung cap long
report = []
for i, l in enumerate(lines):
    s = l.strip()
    if re.match(r"else\b", s):
        report.append((i + 1, s[:90]))
print(f"so dong bat dau bang 'else': {len(report)}")
for i, s in report:
    print(f"  L{i}: {s}")
