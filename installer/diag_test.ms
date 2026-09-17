(
    fileIn @"C:\Users\HOMIE\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\usermacros\NC_Render AI-NCRenderSmartBridge_v1.mcr"
    format "TEST_START\n"
    try (
        macros.run "NC-Render AI" "NCRenderSmartBridge_v1"
        format "MACRO_RUN_OK\n"
    ) catch (
        format "MACRO_RUN_FAIL: %\n" (getCurrentException() as string)
    )
    
    -- Giả lập nhấn nút render
    try (
        rltNCRenderPro_v1.ddlRenderMethod.selection = 1  -- Corona GPU
        format "SET_METHOD_OK\n"
    ) catch (
        format "SET_METHOD_FAIL: %\n" (getCurrentException() as string)
    )
    
    try (
        rltNCRenderPro_v1.btnRender1.pressed()
        format "BUTTON_CLICK_OK\n"
    ) catch (
        format "BUTTON_CLICK_FAIL: %\n" (getCurrentException() as string)
    )
)