(
    global tf = createFile "D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/installer/case_gem.txt"
    format "START\n" to:tf
    fileIn @"C:/Users/HOMIE/AppData/Local/Autodesk/3dsMax/2024 - 64bit/ENU/usermacros/NC_Render AI-NCRenderSmartBridge_v1.mcr"
    local rr = try ( (macros.run "NC-Render AI" "NCRenderSmartBridge_v1") as string ) catch ("EXC:" + (getCurrentException() as string))
    format "B1_RUN: %\n" rr to:tf
)
(
    format "B2_CLASS: %\n" (classof rltNCRenderPro_v1) to:tf
    local d = try ( createDialog rltNCRenderPro_v1 ) catch ("EXC:" + (getCurrentException() as string))
    format "B2_CREATE: %\n" (d as string) to:tf
)
(
    local ro = rltNCRenderPro_v1
    format "B3_STATE: method=% sel=% grp=% key=% prov=% model=% save=% spnW=% keyTxt=% modelTxt=%\n" (try (renderMethod as string) catch "U") (try (ro.ddlRenderMethod.selection as string) catch "E") (try (ro.grpApi.visible as string) catch "E") (try (ro.txtApiKey.visible as string) catch "E") (try (ro.ddlApiProvider.visible as string) catch "E") (try (ro.txtApiModel.visible as string) catch "E") (try (ro.btnSaveApiCfg.visible as string) catch "E") (try (ro.spnWidth.enabled as string) catch "E") (try (ro.txtApiKey.text as string) catch "E") (try (ro.txtApiModel.text as string) catch "E") to:tf
    try ( destroyDialog ro ) catch ()
    format "B9_DONE\n" to:tf
    close tf
)