import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
lines = open(p, encoding="utf-8", errors="replace").read().splitlines()

# 1. on create do -> on <rollout> create do
fixed_on = 0
for i, l in enumerate(lines):
    if re.match(r"^\s*on create do\s*$", l):
        indent = l[: len(l) - len(l.lstrip())]
        lines[i] = indent + "on rltNCRenderPro_v1 create do"
        fixed_on += 1
print("on create fixed:", fixed_on)

# 2. ghep noi dung dau \ cuoi dong (MaxScript khong ho tro line continuation)
joined = []
buf = None
joined_count = 0
for l in lines:
    if buf is not None:
        l = buf + " " + l.strip()
        buf = None
        joined_count += 1
    if l.rstrip().endswith("\\") and not l.rstrip().endswith("\\\\"):
        buf = l.rstrip()[:-1]
        continue
    joined.append(l)
if buf is not None:
    joined.append(buf)
print("noi dong sau dau \\:", joined_count)

open(p, "w", encoding="utf-8", newline="\r\n").write("\n".join(joined) + "\n")

# verify
src = "\n".join(joined)
print("con \\ cuoi dong:", sum(1 for l in joined if l.rstrip().endswith("\\")))
print("con 'on create do':", len(re.findall(r"on create do", src)))
