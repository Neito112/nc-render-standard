(
    fileIn @"C:\Users\HOMIE\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\usermacros\NC_Render AI-NCRenderSmartBridge_v1.mcr"
    format "P3_CLASS: %\n" (classof rltNCRenderPro_v1)
    local hwnd = createDialog rltNCRenderPro_v1
    format "P3_HWND: %\n" (hwnd as string)
    format "P3_OPEN: %\n" ((try (windows.isDialogOpen rltNCRenderPro_v1) catch "n/a") as string)
    destroyDialog rltNCRenderPro_v1
    format "P3_DONE\n"
)
