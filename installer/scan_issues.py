import re

lines = open(r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr", encoding="utf-8", errors="replace").read().splitlines()

# 1. on-handler thieu 'do'
bad = []
for i, l in enumerate(lines, 1):
    s = l.strip()
    if re.match(r"on\s+\w", s) and not s.endswith("do") and " do" not in s:
        bad.append((i, s[:100]))
print("on thieu do:", len(bad))
for i, s in bad[:15]:
    print(f"  L{i}: {s}")

# 2. noi chuoi bang dau \ cuoi dong (MaxScript khong ho tro nhu Python)
bs = []
for i, l in enumerate(lines, 1):
    if l.rstrip().endswith("\\"):
        bs.append((i, l.strip()[:100]))
print("noi dung \\ cuoi dong:", len(bs))
for i, s in bs[:15]:
    print(f"  L{i}: {s}")

# 3. in ngu canh quanh dong 74-80 cua zip copy (noi fileIn bao loi tai '(' expected do)
print("--- ngu canh L70..L92 ---")
for i in range(69, min(92, len(lines))):
    print(f"L{i+1}: {lines[i][:110]}")
