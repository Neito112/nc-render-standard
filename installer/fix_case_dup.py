import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
src = open(p, encoding="utf-8", errors="replace").read()
lines = src.splitlines()

# 1. doi ten widget trung lap o dong 102 -> lblRendererInfo
out = []
for i, l in enumerate(lines, 1):
    if i == 102:
        l = l.replace("label lblStatus ", "label lblRendererInfo ")
    if i == 81:
        l = l.replace("lblStatus.text", "lblRendererInfo.text")
    out.append(l)
src = "\n".join(out)
print("doi ten lblStatus L102 -> lblRendererInfo")

# 2. 'case of' -> 'case true of'
n = len(re.findall(r"\bcase of\b", src))
src = re.sub(r"\bcase of\b", "case true of", src)
print("case of -> case true of:", n)

open(p, "w", encoding="utf-8", newline="\r\n").write(src + "\n")

# verify
print("con 'case of':", len(re.findall(r"\bcase of\b", src)))
print("con lblStatus trung:", src.count("label lblStatus"))
