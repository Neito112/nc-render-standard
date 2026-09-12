import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
raw = open(p, "rb").read().decode("utf-8", errors="replace")

# Liệt kê mọi sequence backslash bat thường
seqs = {}
for m in re.finditer(r"\\.", raw):
    seqs[m.group(0)] = seqs.get(m.group(0), 0) + 1
print("cac escape co trong file:")
for k, v in sorted(seqs.items(), key=lambda x: -x[1]):
    print(f"  {k!r}: {v}")

# Sua \\\" -> \" (escape long hong)
n1 = raw.count('\\\\\\"')
fixed = raw.replace('\\\\\\"', '\\"')
print("doi \\\" -> \":", n1)

open(p, "w", encoding="utf-8", newline="\r\n").write(fixed)

# verify
seqs2 = {}
for m in re.finditer(r"\\.", fixed):
    seqs2[m.group(0)] = seqs2.get(m.group(0), 0) + 1
print("escape con lai:", {k: v for k, v in seqs2.items() if k not in ('\\"', "\\n", "\\t")})
