(
    local PROJ = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    local ENU  = @"C:/Users/HOMIE/AppData/Local/Autodesk/3dsMax/2024 - 64bit/ENU"
    local out = createFile (PROJ + "/installer/test_body.txt")
    fn logIt s = ( format "%
" s to:out; flush out )
    NCRenderDryRun = true
    rltNCRenderPro_v1 = undefined

    -- doc body macroScript (bo header macroScript/category/tooltip/buttonText/icon)
    local f = openFile (ENU + "/usermacros/NC_Render AI-NCRenderSmartBridge_v1.mcr") mode:"r"
    local code = ""
    while not (eof f) do code += readLine f + "
"
    close f

    -- tach body: tu '(' dau tien sau header den ')' cuoi
    local s1 = findString code "
(
"
    logIt ("BODY_START_FOUND: " + ((s1 != undefined) as string))
    local body = substring code (s1 + 2) ((code.count - s1) - 2)
    -- bo ')' cuoi neu con dua
    while body.count > 0 and body[body.count] != ")" do body = substring body 1 (body.count - 1)
    body = substring body 1 (body.count - 1)
    logIt ("BODY_LEN: " + (body.count as string))

    logIt ("DOSTRING: " + (try ( doString body; "ran" ) catch ("EXC: " + (getCurrentException() as string))))
    logIt ("ROLLOUT_CLASS: " + (try ( classOf rltNCRenderPro_v1 as string ) catch ("EXC")))
    NCRenderDryRun = false
    logIt "BODY_TEST_DONE"
    close out
)