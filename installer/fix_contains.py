import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
src = open(p, encoding="utf-8", errors="replace").read()

# 1. Them helper ncHas (findString-based) ngay sau ncContains
anchor = """    fn ncContains s sub =
    (
        (findString (s as string) (sub as string)) != undefined
    )"""
assert anchor in src, "anchor not found"
src = src.replace(anchor, anchor + """
    fn ncHas s sub =
    (
        (findString (s as string) (sub as string)) != undefined
    )""")

# 2. Toan tu 'X contains "Y"' -> ncHas X "Y"
before = len(re.findall(r'\b\w+\s+contains\s+"', src))
src = re.sub(r'\b(\w+)\s+contains\s+(")', r'ncHas \1 \2', src)
after = len(re.findall(r'\b\w+\s+contains\s+"', src))
print(f"contains -> ncHas: {before} trc, {after} sau")

# 3. Kiem tra con 'else if' nao dang ngo khong
for i, l in enumerate(src.splitlines(), 1):
    if re.search(r"\belse\s+if\b", l):
        print(f"  L{i}: {l.strip()[:100]}")

open(p, "w", encoding="utf-8", newline="\r\n").write(src)
print("saved")
