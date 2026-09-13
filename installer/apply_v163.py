# -*- coding: utf-8 -*-
"""Phoi hop toan bo thu dung v1.6.3 len file v1.6.2 (sau khi bi checkout lui):
1) goa statement rollout-level bat hop phap (local isCorona/isVray, local referenceImage)
2) widget params dung bien runtime -> literal; gia tri that gan trong on create
3) wrap 'on open' try/catch tung buoc (den bao OPEN_FAIL)
4) DOI THU TU: moi rollout-fn dat SAU toan bo widget declaration, theo dependency
"""
import pathlib, re

P = pathlib.Path("usermacros/NC_Render_Bridge_v1.mcr")
s = P.read_text(encoding="utf-8", errors="replace")

# ---------- 1+2: statement bat hop phap + params ----------
assert "        local isCorona = coronaInstalled == \"true\"" in s
s = s.replace("""        local isCorona = coronaInstalled == "true"
        local isVray = vrayInstalled == "true"
        checkbox chkCorona "Corona" pos:[16, 72] width:80 height:18 checked:isCorona enabled:(isCorona or hasCUDA == "true")
        checkbox chkVray "V-Ray" pos:[100, 72] width:80 height:18 checked:isVray enabled:(isVray or hasCUDA == "true")""",
"""        checkbox chkCorona "Corona" pos:[16, 72] width:80 height:18 checked:false
        checkbox chkVray "V-Ray" pos:[100, 72] width:80 height:18 checked:false""")

# btnDefaults dung isCorona/isVray -> inline bieu thuc (handler scope hop le)
s = s.replace("            if isCorona then", "            if coronaInstalled == \"true\" then")
s = s.replace("            else if isVray then", "            else if vrayInstalled == \"true\" then")

# spinner enabled:(renderMethod == ...) -> bo (updateUIForMethod quyet trong open)
s = re.sub(r' enabled:\(renderMethod == "Corona GPU" or renderMethod == "V-Ray GPU"\)', '', s)

# editText text:apiKey -> literal
s = s.replace(' text:apiKey', ' text:""')
s = s.replace(' visible:false passwordChar:"*"', ' visible:false passwordChar:"*"')

# local referenceImage = undefined (rollout-level!) -> global truoc rollout, doi ten dung moi
assert "        local referenceImage = undefined" in s
s = s.replace("\n        local referenceImage = undefined", "")
s = s.replace("\n    rollout rltNCRenderPro_v1", "\n    global ncReferenceImage = undefined\n    rollout rltNCRenderPro_v1")
s = re.sub(r'\breferenceImage\b', 'ncReferenceImage', s)
s = s.replace("global ncncReferenceImage", "global ncReferenceImage")

# ---------- 3: wrap on open ----------
import io
_lines_all = s.splitlines()
_o = next(i for i, l in enumerate(_lines_all) if l.strip() == "on rltNCRenderPro_v1 open do")
# tim dong ')' dong deu indent ket thuc block open
_d = 0; _e = None
for j in range(_o, len(_lines_all)):
    _d += _lines_all[j].count("(") - _lines_all[j].count(")")
    if j > _o and _lines_all[j] == "        )" and _d <= 0:
        _e = j; break
assert _e is not None, "open block end"
old_open = "\n".join(_lines_all[_o:_e+1])
new_open = '''        on rltNCRenderPro_v1 open do
        (
            local ocStep = "init"
            try
            (
                ocStep = "syncCreate"
                chkCorona.checked = (coronaInstalled == "true")
                chkCorona.enabled = (coronaInstalled == "true" or hasCUDA == "true")
                chkVray.checked = (vrayInstalled == "true")
                chkVray.enabled = (vrayInstalled == "true" or hasCUDA == "true")
                ocStep = "refreshCamList"
                refreshCamList()
                ocStep = "spnWH"
                spnWidth.value = (if renderWidth == undefined then 1920 else renderWidth)
                spnHeight.value = (if renderHeight == undefined then 1080 else renderHeight)
                ocStep = "apiWidgets"
                txtApiKey.text = (if apiKey == undefined then "" else apiKey as string)
                txtApiModel.text = (if apiModel == undefined then "" else apiModel as string)
                ddlApiProvider.selection = (if apiProvider == "gemini" then 2 else 1)
                ocStep = "spnRatio"
                spnRatio.value = ((if renderWidth == undefined then 1920 else renderWidth) as float) / ((if renderHeight == undefined then 1080 else renderHeight) as float)
                ocStep = "scanMaterialsInScene"
                scanMaterialsInScene()
                ocStep = "updateUIForMethod"
                updateUIForMethod()
                ocStep = "refreshPreviewDisplay"
                refreshPreviewDisplay()
                lblStatus.text = "Plugin v1.0 loaded. " + renderMethod + " | " + gpuName
            )
            catch
            (
                format "OPEN_FAIL step=% ex=%\\n" ocStep (getCurrentException())
                try ( lblStatus.text = "Open loi [" + ocStep + "]" ) catch()
            )
        )'''
assert old_open in s, "open block anchor thay doi"
s = s.replace(old_open, new_open)

# ---------- 4: doi thu tu fn ----------
lines = s.splitlines()
def fn_range(ls, i):
    depth = 0
    for j in range(i, len(ls)):
        depth += ls[j].count("(") - ls[j].count(")")
        if j > i and re.match(r'^        \)\s*$', ls[j]) and depth <= 0:
            return i, j
    raise RuntimeError("unclosed fn @" + str(i))

fn_defs = {}
keep = [True]*len(lines)
i = 0
while i < len(lines):
    m = re.match(r'^        fn (\w+)', lines[i])
    if m:
        a, b = fn_range(lines, i)
        fn_defs[m.group(1)] = lines[a:b+1]
        for k in range(a, b+1): keep[k] = False
        i = b + 1
    else:
        i += 1
print("fn tach ra:", sorted(fn_defs))
order = ["getRenderCamera","captureViewportRender","captureGhostViewport","refreshCamList",
         "refreshPreviewDisplay","scanMaterialsInScene","buildScenePrompt","arrayToCSV",
         "applyResToMax","updateUIForMethod","saveNcConfig","ncJsonImage","ncRunPython"]
seq = []
for name in order + [k for k in fn_defs if k not in order]:
    if name in fn_defs: seq += fn_defs[name]
rest = [l for l, k in zip(lines, keep) if k]
rest = [l for l in rest if "HELPERS hoisted" not in l]
pat_last = re.compile(r'^        (?:groupBox|label|button|checkbox|checkbutton|editText|edittext|spinner|dropdownList|imageButton|bitmap|listbox)\s+\w+')
ilw = max(i for i, l in enumerate(rest) if pat_last.match(l))
new_lines = rest[:ilw+1] + ["        -- ==== fn dat SAU widget (scope MaxScript) va theo dependency ==== "] + seq + [""] + rest[ilw+1:]
s = "\n".join(new_lines) + "\n"

# kiem tra cuoi
pat_w = re.compile(r'^        (?:groupBox|label|button|checkbox|checkbutton|editText|edittext|spinner|dropdownList|imageButton|bitmap|listbox)\s+\w+', re.M)
last_widget = max(m.start() for m in pat_w.finditer(s))
for m in re.finditer(r'^        fn (\w+)', s, re.M):
    assert m.start() > last_widget, "fn van truoc widget: " + m.group(1)
assert "local isCorona" not in s and " text:apiKey" not in s and "enabled:(renderMethod" not in s
assert len(re.findall(r'\breferenceImage\b', s)) == 0, "con referenceImage ro"
assert len(re.findall(r'\bncReferenceImage\b', s)) >= 8, "thieu ncReferenceImage"
P.write_text(s, encoding="utf-8", newline="\n")
print("V1.6.3 recipe applied; lines:", s.count("\n"))
