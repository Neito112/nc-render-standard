import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
raw = open(p, encoding="utf-8", errors="replace").read()

# =================== BANG V TRI MOI (cot trai x=10 w=340, gap 8) ===================
POS = {
    # SECTION 1: System
    "grpSystem":        (10, 5, 340, 128),
    "lblGPUInfo":       (20, 22, 320, None),
    "lblGPUMemory":     (20, 40, 320, None),
    "lblCUDAStatus":    (20, 58, 320, None),
    "chkCorona":        (20, 80, 150, 18),
    "chkVray":          (180, 80, 150, 18),
    "lblRendererInfo":  (20, 104, 320, None),
    # SECTION UPDATE
    "grpUpdate":        (10, 141, 340, 112),
    "lblUpdateInfo":    (20, 158, 320, None),
    "btnCheckUpdate":   (20, 178, 320, 22),
    "btnDoUpdate":      (20, 204, 320, 22),
    "lblUpdateStatus":  (20, 230, 320, 18),
    # SECTION 2: Camera & Frame
    "grpCam":           (10, 261, 340, 140),
    "ddlCams":          (18, 278, 322, 6),
    "btnQuickCam":      (18, 296, 80, 20),
    "btnRefreshCams":   (110, 296, 80, 20),
    "btn2Point":        (202, 296, 80, 20),
    "btnResetCam":      (18, 320, 80, 20),
    "spnWidth":         (18, 348, 40, None),
    "spnHeight":        (110, 348, 40, None),
    "spnRatio":         (202, 348, 38, None),
    "ckbLock":          (292, 346, 28, 18),
    "ddlRatio":         (18, 372, 322, 5),
    # SECTION 3: Render Method
    "grpRenderMethod":  (10, 409, 340, 105),
    "lblMethod":        (20, 426, 320, None),
    "ddlRenderMethod":  (20, 444, 320, 6),
    "btnApplyMethod":   (20, 470, 80, 20),
    "btnDefaults":      (110, 470, 80, 20),
    "btnAPIKey":        (200, 470, 80, 20),
    # SECTION 4: Prompt & Materials
    "grpPrompt":        (10, 522, 340, 250),
    "lblPrompt":        (20, 539, 320, None),
    "txtPrompt":        (20, 555, 320, 80),
    "lblReference":     (20, 640, 320, None),
    "btnLoadRef":       (20, 656, 160, 20),
    "btnClearRef":      (190, 656, 80, 20),
    "lblMaterial":      (20, 684, 320, None),
    "btnDetectMaterial":(20, 700, 160, 20),
    "btnRefreshMat":    (190, 700, 80, 20),
    "lstMaterials":     (20, 724, 320, 40),
    # SECTION 5: Render buttons
    "grpRender":        (10, 780, 340, 125),
    "btnRender1":       (20, 797, 320, 30),
    "btnRender2":       (20, 830, 320, 30),
    "btnRender3":       (20, 863, 320, 30),
    # SECTION 6: Quality
    "grpQuality":       (10, 913, 340, 100),
    "lblUpscale":       (20, 930, 120, None),
    "ddlUpscale":       (150, 928, 80, 5),
    "lblDetail":        (20, 952, 120, None),
    "chkDetail":        (150, 950, 150, 18),
    "lblTile":          (20, 974, 120, None),
    "chkTile":          (150, 972, 180, 18),
    # STATUS
    "lblStatus":        (10, 1021, 340, 18),
    # PREVIEW (cot phai)
    "grpPreview":       (355, 5, 920, 1016),
}

n_done = 0
for name, (x, y, w, h) in POS.items():
    # tim dong khai bao widget
    pat = re.compile(r"^(\s*\w+\s+" + re.escape(name) + r"\s+\"[^\"]*\".*?pos:\[)\s*\d+\s*,\s*\d+\s*(\].*)$", re.M)
    def rep(m, x=x, y=y):
        return m.group(1) + f"{x}, {y}" + m.group(2)
    new, k = pat.subn(rep, raw, count=1)
    if k == 0:
        print(f"  !! khong match: {name}")
        continue
    # width/height neu co
    if h is not None:
        line_pat = re.compile(r"^(\s*\w+\s+" + re.escape(name) + r"\b.*)$", re.M)
        mm = line_pat.search(new)
        if mm:
            line = mm.group(1)
            if re.search(r"width:\s*\d+", line):
                line = re.sub(r"width:\s*\d+", f"width:{w}", line, count=1)
            if re.search(r"height:\s*\d+", line):
                line = re.sub(r"height:\s*\d+", f"height:{h}", line, count=1)
            new = new[:mm.start()] + line + new[mm.end():]
    raw = new
    n_done += 1

# doi kich thuoc rollout (createDialog tu dung kich thuoc cua rollout)
raw = raw.replace("width:1280 height:800", "width:1280 height:1050")

open(p, "w", encoding="utf-8", newline="\r\n").write(raw)
print(f"reflow: {n_done}/{len(POS)} widgets")
