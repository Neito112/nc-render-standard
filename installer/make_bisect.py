# -*- coding: utf-8 -*-
"""Cay marker vao cac buoc cua rollout de tim noi 'items in undefined' xay ra."""
import re, pathlib

src = pathlib.Path("usermacros/NC_Render_Bridge_v1.mcr")
s = src.read_text(encoding="utf-8", errors="replace")

# 1) marker dau on create / on open
s = s.replace("        on rltNCRenderPro_v1 create do\n        (",
              "        on rltNCRenderPro_v1 create do\n        (\n            format \"B_CREATE\\n\"")
s = s.replace("        on rltNCRenderPro_v1 open do\n        (",
              "        on rltNCRenderPro_v1 open do\n        (\n            format \"B_OPEN\\n\"")

# 2) marker tung buoc trong open handler
calls = [
    ("refreshCamList()", "B_OPEN_CAMLIST"),
    ("txtApiKey.text = apiKey", "B_OPEN_APIKEY"),
    ("ddlApiProvider.selection", "B_OPEN_APisel"),
    ("scanMaterialsInScene()", "B_OPEN_SCAN"),
    ("updateUIForMethod()", "B_OPEN_UPDUI"),
    ("refreshPreviewDisplay()", "B_OPEN_PREV"),
]
for frag, tag in calls:
    # chen format NGAY TRUOC dong goi (chi trong block open: tim dong chua frag sau 'open do')
    def before(m):
        indent = m.group(1)
        return f"{indent}format \"{tag}\\n\"\n{m.group(0)}"
    s = re.sub(r'( *)' + re.escape(frag), before, s, count=1,
               flags=re.M) if f"format \"{tag}" not in s else s

# 3) marker trong fn refreshCamList truoc dong .items
s = s.replace("            ddlCams.items = camNames",
              "            format \"B_SET_ITEMS ddlCams=%\\n\" (classof ddlCams)\n            ddlCams.items = camNames")
# 4) marker dau cac fn
for fnname, tag in [("fn scanMaterialsInScene", "B_FN_SCAN"), ("fn updateUIForMethod", "B_FN_UPDUI"),
                    ("fn refreshPreviewDisplay", "B_FN_PREV"), ("fn captureGhostViewport", "B_FN_GHOST"),
                    ("fn getRenderCamera", "B_FN_GETCAM")]:
    i = s.index(fnname)
    j = s.index("(", i)
    s = s[:j+1] + "\n            format \"" + tag + "\\n\"" + s[j+1:]

out = pathlib.Path("installer/bisect.ms")
out.write_text(s, encoding="utf-8", newline="\n")
print("bisect.ms written, markers:", sum(1 for l in s.splitlines() if "B_" in l))
