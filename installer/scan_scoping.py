import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
lines = open(p, encoding="utf-8", errors="replace").read().splitlines()

# Tinh paren depth (bo qua comment + string) de biet fn nao nam trong rollout nao
depth = 0
rollout_stack = []
targets = {}
for i, l in enumerate(lines, 1):
    s = l.strip()
    if s.startswith("--"):
        continue
    s = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', s)
    # ghi nhan su kien
    m = re.match(r"rollout\s+(\w+)", s)
    if m:
        rollout_stack.append((m.group(1), depth))
    mo = re.match(r"on\s+(\w+)\s+(open|create)\b", s)
    if mo:
        print(f"L{i}: HANDLER on {mo.group(1)} {mo.group(2)} | depth={depth} | rollout={rollout_stack[-1][0] if rollout_stack else '-'}")
    mf = re.match(r"fn\s+(\w+)", s)
    if mf:
        rl = "-"
        for name, d in reversed(rollout_stack):
            if depth > d:
                rl = name
                break
        print(f"L{i}: FN {mf.group(1):28s} depth={depth:3d} | trong rollout: {rl}")
    for c in l:
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            while rollout_stack and depth <= rollout_stack[-1][1]:
                rollout_stack.pop()
