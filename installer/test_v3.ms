(
    global tf = createFile "D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/installer/test_v3_result.txt"
    format "X0_INIT\n" to:tf
    local cfg = (getDir #temp) + "/nc_render_config.txt"
    global cfgPath = cfg
)
(
    fileIn @"C:\Users\HOMIE\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\usermacros\NC_Render AI-NCRenderSmartBridge_v1.mcr"
    local rr = try ( (macros.run "NC-Render AI" "NCRenderSmartBridge_v1") as string ) catch ("EXC:" + (getCurrentException() as string))
    format "X1_RUN: %\n" rr to:tf
)
-- ==== Case OR: config = OpenRouter API ====
(
    local f2 = createFile cfgPath
    format "%\nopenrouter\nsk-or-TESTKEY\ngemini-pro-img\ntestgpu\n8192\ntrue\ntrue\ntrue\ntrue\n" "OpenRouter API" to:f2
    close f2
    local r = try ( macros.run "NC-Render AI" "NCRenderSmartBridge_v1" ) catch ("EXC:" + (getCurrentException() as string))
    format "X2_OR_run: %\n" (r as string) to:tf
)
(
    local d = try ( createDialog rltNCRenderPro_v1 ) catch ("EXC:" + (getCurrentException() as string))
    format "X2_OR_create: %\n" (d as string) to:tf
)
(
    local ro = rltNCRenderPro_v1
    format "X3_OR: method=% sel=% grp=% key=% model=% save=% prov=% spnW=% keyTxt=%\n" (try (renderMethod as string) catch "U") (try (ro.ddlRenderMethod.selection as string) catch "E") (try (ro.grpApi.visible as string) catch "E") (try (ro.txtApiKey.visible as string) catch "E") (try (ro.txtApiModel.visible as string) catch "E") (try (ro.btnSaveApiCfg.visible as string) catch "E") (try (ro.ddlApiProvider.visible as string) catch "E") (try (ro.spnWidth.enabled as string) catch "E") (try (ro.txtApiKey.text as string) catch "E") to:tf
    destroyDialog ro
)
-- ==== Case V-Ray ====
(
    local f2 = createFile cfgPath
    format "%\nopenrouter\nk\nm\ntestgpu\n8192\ntrue\ntrue\ntrue\ntrue\n" "V-Ray GPU" to:f2
    close f2
    local r = try ( macros.run "NC-Render AI" "NCRenderSmartBridge_v1" ) catch ("EXC:" + (getCurrentException() as string))
    local d = try ( createDialog rltNCRenderPro_v1 ) catch ("EXC:" + (getCurrentException() as string))
    format "X4_VRAY_create: %\n" (d as string) to:tf
)
(
    local ro = rltNCRenderPro_v1
    format "X5_VRAY: method=% sel=% grp=% curRenderer=%\n" (try (renderMethod as string) catch "U") (try (ro.ddlRenderMethod.selection as string) catch "E") (try (ro.grpApi.visible as string) catch "E") (try (classOf renderers.current as string) catch "E") to:tf
    destroyDialog ro
)
-- ==== Case Gemini: provider ddl=2, model tu config ====
(
    local f2 = createFile cfgPath
    format "%\ngemini\nsk-or-GG\nmodel-gg\ntestgpu\n8192\ntrue\ntrue\ntrue\ntrue\n" "Gemini API" to:f2
    close f2
    local r = try ( macros.run "NC-Render AI" "NCRenderSmartBridge_v1" ) catch ("EXC:" + (getCurrentException() as string))
    local d = try ( createDialog rltNCRenderPro_v1 ) catch ("EXC:" + (getCurrentException() as string))
    format "X6_GEM_create: %\n" (d as string) to:tf
)
(
    local ro = rltNCRenderPro_v1
    format "X7_GEM: method=% sel=% grp=% prov=% modelTxt=%\n" (try (renderMethod as string) catch "U") (try (ro.ddlRenderMethod.selection as string) catch "E") (try (ro.grpApi.visible as string) catch "E") (try (ro.ddlApiProvider.selection as string) catch "E") (try (ro.txtApiModel.text as string) catch "E") to:tf
    destroyDialog ro
    close tf
)
