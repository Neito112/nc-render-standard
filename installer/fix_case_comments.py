import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
lines = open(p, encoding="utf-8", errors="replace").read().splitlines()

out = []
n_fixed = 0
for l in lines:
    m = re.match(r"^(\s*)(\d+):\s*((--|//).*)$", l)
    if m:
        indent, idx, comment = m.group(1), m.group(2), m.group(3)
        out.append(indent + comment)
        out.append(indent + idx + ":")
        n_fixed += 1
    else:
        out.append(l)
src = "\n".join(out)
open(p, "w", encoding="utf-8", newline="\r\n").write(src + "\n")
print("tach comment khoi case branch:", n_fixed)
left = [(i, l.strip()[:80]) for i, l in enumerate(src.splitlines(), 1)
        if re.match(r"^\s*\d+:\s*(--|//)", l)]
print("con sot:", len(left))
