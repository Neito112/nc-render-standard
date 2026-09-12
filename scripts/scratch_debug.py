import re
code = open("D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr", encoding="utf-8").read()
stripped = []
for line in code.splitlines():
    s = line.strip()
    if s.startswith("--"): continue
    s = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', s)
    s = re.sub(r"'(?:[^'\\\n]|\\.)*'", "''", s)
    stripped.append(s)

depth = 0
for i, s in enumerate(stripped, 1):
    depth += s.count("(")
    depth -= s.count(")")
    print(f"L{i}: {depth} (op={s.count('(')} cl={s.count(')')}) -> {s}")
