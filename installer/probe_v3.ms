(
    local ENU = @"C:/Users/HOMIE/AppData/Local/Autodesk/3dsMax/2024 - 64bit/ENU"
    format "SANITY: 1280x1050 -> %
" (try ( createDialog bigRlt ) catch ("EXC:" + (getCurrentException())))
    rollout bigRlt "Big" width:1280 height:1050 ( label l1 "x" pos:[10,10] )
    local r = try ( createDialog bigRlt ) catch ( "EXC:" + (getCurrentException()) )
    format "SANITY_BIG: %
" (if r == undefined then "undefined" else (classof r))
    destroyDialog bigRlt

    local reg = ENU + "/usermacros/NC_Render AI-NCRenderSmartBridge_v1.mcr"
    fileIn reg
    local rr = try ( macros.run "NC-Render AI" "NCRenderSmartBridge_v1" ) catch ( "RUNEXC:" + getCurrentException() )
    format "MACROS_RUN_RETURN: %
" (if rr == undefined then "undefined" else (classof rr))
    format "GLOBAL_CLASS: %
" (classof rltNCRenderPro_v1)
    if rltNCRenderPro_v1 != undefined do format "HWND: %
" (windows.getMaxHWND rltNCRenderPro_v1)
    format "DONE
"
)