(
    local out = "D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/installer/dbg_load.txt"
    local f = createFile out
    local r = try ( fileIn @"C:\Users\HOMIE\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\usermacros\NC_Render AI-NCRenderSmartBridge_v1.mcr"; "FILEIN-OK" ) catch ("FILEIN-EXC:" + (getCurrentException() as string))
    format "step1 %\n" r to:f; flush f
    format "step2 corona=%\n" (try (coronaInstalled as string) catch "UNDEF") to:f; flush f
    format "step3 vray=%\n" (try (vrayInstalled as string) catch "UNDEF") to:f; flush f
    format "step4 fnT=%\n" (try (ncRendererPresentT "*Corona*" as string) catch "UNDEF/EXC") to:f; flush f
    close f
)
