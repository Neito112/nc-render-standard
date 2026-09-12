import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
src = open(p, encoding="utf-8", errors="replace").read()

old = """        // Quick ratios
        button btnRatios "Ratios:" pos:[18, 222] width:322 height:18
        local ratioItems = #("16:9", "4:3", "5:4", "3:2", "2:1", "1:1", "9:16")
        popupMenu pmRatio "Ratios" pos:[0, 0] width:100 items:ratioItems
        on btnRatios pressed do pmRatio.pos = [18, 220]; pmRatio.amount = 0
        
        on pmRatio picked item do
        (
            local parts = (filterString item ":")
            if parts.count == 2 then
            (
                local w = (parts[1] as integer) as float
                local h = (parts[2] as integer) as float
                spnRatio.value = w / h
                spnHeight.value = int((spnWidth.value as float) / spnRatio.value + 0.5)
            )
        )"""

new = """        // Quick ratios — popupMenu la HAM toan cuc, khong phai rollout control
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
        )"""

assert old in src, "block not found"
src = src.replace(old, new)
open(p, "w", encoding="utf-8", newline="\r\n").write(src)
print("popupMenu widget -> ham toan cuc: OK")
