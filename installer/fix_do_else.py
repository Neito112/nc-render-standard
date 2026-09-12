import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
src = open(p, encoding="utf-8", errors="replace").read()
lines = src.splitlines()

out = []
n_do2then = 0
for l in lines:
    s = l.strip()
    # chi doi 'do' -> 'then' tren dong bat dau bang 'if' hoac 'else if'
    m = re.match(r"^(\s*(?:else\s+)?if\b.*?)(\bdo\b)(\s*\(?.*)$", l)
    if m and m.group(3).strip() in ("", "("):
        l = m.group(1) + "then" + m.group(3)
        n_do2then += 1
    out.append(l)
src = "\n".join(out)
print("if...do -> if...then:", n_do2then)

# getExceptionString la ham ma -> getCurrentException
n = len(re.findall(r"getExceptionString\(\)", src))
src = src.replace("getExceptionString()", "getCurrentException()")
print("getExceptionString -> getCurrentException:", n)

# kiem tra 'do' cuoi con sot tren dong if
left = [ (i, l.strip()[:90]) for i, l in enumerate(src.splitlines(), 1)
         if re.match(r"^\s*(else\s+)?if\b", l) and re.search(r"\bdo\b", l) ]
print("dong if con 'do':", len(left))
for i, s in left[:10]:
    print(f"  L{i}: {s}")

open(p, "w", encoding="utf-8", newline="\r\n").write(src + "\n")
print("saved")
