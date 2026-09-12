import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
lines = open(p, encoding="utf-8", errors="replace").read().splitlines()

# Lay moi widget: name, type, pos, width, height (neu co)
pat = re.compile(r'^\s*(groupBox|label|button|checkbutton|checkbox|edittext|radiobuttons|dropdownList|spinner|slider|colorpicker|imagebutton|viewport|lightbox|multiselectlist|listbox|progressBar|hyperLink|curveControl|textbutton|dotNetControl)\s+(\w+)\s+"[^"]*"(.*$)')
widgets = []
for i, l in enumerate(lines, 1):
    m = pat.match(l)
    if not m:
        continue
    typ, name, rest = m.groups()
    pos = re.search(r"pos:\[\s*(\d+)\s*,\s*(\d+)\s*\]", rest)
    w = re.search(r"width:\s*(\d+)", rest)
    h = re.search(r"height:\s*(\d+)", rest)
    if pos:
        widgets.append((i, typ, name, int(pos.group(1)), int(pos.group(2)),
                        int(w.group(1)) if w else 0, int(h.group(1)) if h else 0))

print(f"{len(widgets)} widgets co pos")
# phat hien overlap theo truc Y trong cung cot (x < 360 = cot trai)
left = [w for w in widgets if w[3] < 360]
left.sort(key=lambda w: w[4])
print("\n--- COT TRAI theo Y ---")
prev = None
for i, typ, name, x, y, w, h in left:
    hh = h if h else (18 if typ in ("label", "checkbox", "checkbutton") else (24 if typ == "edittext" else (5 if typ == "dropdownList" else 0)))
    bottom = y + hh if hh else None
    flag = ""
    if prev and bottom:
        py, pb, pn = prev
        if y < pb:
            flag = f"  << CHONG voi {pn} (ket thuc y={pb})"
    print(f"  y={y:4d} x={x:3d} {typ:12s} {name:22s} w={w:4d} h={h:3d}{flag}")
    if bottom:
        prev = (y, bottom, name)
