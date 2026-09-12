import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
src = open(p, encoding="utf-8", errors="replace").read()

old = """        local btnRender = button btnRender1 "Render" pos:[20, 505] width:320 height:30
        btnRender1.text = renderButtons[1]
        local btnRender2 = button btnRender2 "Render" pos:[20, 540] width:320 height:30
        btnRender2.text = renderButtons[2]
        local btnRender3 = button btnRender3 "Render" pos:[20, 575] width:320 height:30
        btnRender3.text = renderButtons[3]"""

new = """        button btnRender1 "Render" pos:[20, 505] width:320 height:30
        button btnRender2 "Render" pos:[20, 540] width:320 height:30
        button btnRender3 "Render" pos:[20, 575] width:320 height:30"""

assert old in src, "btn block not found"
src = src.replace(old, new)

# gan text trong on create (da co san handler, chen them 3 dong cuoi)
old_create = """            lblStatus.text = "Renderer: " + renderMethod
        )"""
new_create = """            lblStatus.text = "Renderer: " + renderMethod
            btnRender1.text = renderButtons[1]
            btnRender2.text = renderButtons[2]
            btnRender3.text = renderButtons[3]
        )"""
assert old_create in src, "on create block not found"
src = src.replace(old_create, new_create)

# 'case of' o dong 476-490 la syntax ma -> xem context
for i, l in enumerate(src.splitlines(), 1):
    if "case of" in l:
        print(f"L{i}: {l.strip()[:90]}")

open(p, "w", encoding="utf-8", newline="\r\n").write(src)
print("buttons fixed")
