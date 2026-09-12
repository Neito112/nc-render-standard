import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
raw = open(p, "rb").read().decode("utf-8", errors="replace")

# 1. chuan hoa het: ve \n, roi ep gop dong trang lien tiep thanh 1 \n
raw = raw.replace("\r\n", "\n").replace("\r", "\n")
raw = re.sub(r"\n{2,}", "\n", raw)

# 2. popupMenu-as-function -> dropdownList
old = '''        // Quick ratios — popupMenu la HAM toan cuc, khong phai rollout control
        button btnRatios "Ratios:" pos:[18, 222] width:322 height:18
        on btnRatios pressed do
        (
            local ratioItems = #("16:9", "4:3", "5:4", "3:2", "2:1", "1:1", "9:16")
            local item = popupMenu items:ratioItems
            if item != undefined then
            (
                local parts = (filterString item ":")
                if parts.count == 2 then
                (
                    local w = (parts[1] as integer) as float
                    local h = (parts[2] as integer) as float
                    spnRatio.value = w / h
                    spnHeight.value = int((spnWidth.value as float) / spnRatio.value + 0.5)
                )
            )
        )'''

new = '''        // Quick ratios — dropdownList la rollout control that phuong
        dropdownList ddlRatio "Ratio nhanh:" pos:[18, 222] width:322 height:5 items:#("16:9", "4:3", "5:4", "3:2", "2:1", "1:1", "9:16")
        on ddlRatio selected idx do
        (
            local item = ddlRatio.items[idx]
            local parts = (filterString item ":")
            if parts.count == 2 then
            (
                local w = (parts[1] as integer) as float
                local h = (parts[2] as integer) as float
                spnRatio.value = w / h
                spnHeight.value = int((spnWidth.value as float) / spnRatio.value + 0.5)
            )
        )'''

assert old in raw, "popupMenu block still not found"
raw = raw.replace(old, new)

open(p, "w", encoding="utf-8", newline="\r\n").write(raw)
lines = raw.splitlines()
print("lines:", len(lines), "| popupMenu con:", sum(1 for l in lines if "popupMenu" in l), "| ddlRatio:", sum(1 for l in lines if "ddlRatio" in l))
