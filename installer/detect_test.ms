(
    local out = "D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/installer/detect_test.txt"
    local f = createFile out
    fileIn @"C:\Users\HOMIE\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\usermacros\NC_Render AI-NCRenderSmartBridge_v1.mcr"
    local runRes = try ( macros.run "NC-Render AI" "NCRenderSmartBridge_v1" ) catch ("RUNEXC:" + (getCurrentException() as string))
    format "RUN = %\n" (runRes as string) to:f; flush f
    format "CORONA_INSTALLED = %\n" (try (coronaInstalled as string) catch "UNDEF") to:f; flush f
    format "VRAY_INSTALLED = %\n" (try (vrayInstalled as string) catch "UNDEF") to:f; flush f
    local rp = try (
        local hit = for rr in RendererClass.classes where matchPattern (rr as string) pattern:"*Corona*" collect rr
        hit.count as string
    ) catch ("EXC:" + (getCurrentException() as string))
    format "RE-CHECK corona hits = %\n" rp to:f; flush f
    close f
)
