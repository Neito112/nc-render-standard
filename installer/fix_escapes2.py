import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
raw = open(p, encoding="utf-8", errors="replace").read()

# Chi sua backslash ngoai string: #(\"  va  \")
n_open = raw.count('#(\\"')
n_close = raw.count('\\")')
fixed = raw.replace('#(\\"', '#("').replace('\\")', '")')
print("sua #(\":", n_open, " | \"):", n_close)

# kiem tra backslash bat thuong con lai
seqs = {}
for m in re.finditer(r"\\.", fixed):
    seqs[m.group(0)] = seqs.get(m.group(0), 0) + 1
odd = {k: v for k, v in seqs.items() if k not in ('\\"', "\\n", "\\t")}
print("escape la con lai:", odd if odd else "KHONG")

open(p, "w", encoding="utf-8", newline="\r\n").write(fixed)
print("saved")
