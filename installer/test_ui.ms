(
    local PROJ = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    local ENU  = @"C:/Users/HOMIE/AppData/Local/Autodesk/3dsMax/2024 - 64bit/ENU"
    local out = createFile (PROJ + "/installer/test_ui.txt")
    fn logIt s = ( format "%
" s to:out; flush out )
    NCRenderDryRun = true
    rltNCRenderPro_v1 = undefined

    -- fileIn = thuc thi body macroScript (dong hanh vi bam nut trong Max that)
    logIt ("FILEIN_BODY: " + (try
    (
        fileIn (ENU + "/usermacros/NC_Render AI-NCRenderSmartBridge_v1.mcr")
        "ran"
    ) catch ("EXC: " + (getCurrentException() as string))))
    logIt ("ROLLOUT_CLASS: " + (try ( classOf rltNCRenderPro_v1 as string ) catch ("EXC")))
    NCRenderDryRun = false
    logIt "UI_TEST_DONE"
    close out
)