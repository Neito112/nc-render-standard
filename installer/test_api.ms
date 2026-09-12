(
    local PROJ = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    local out = createFile (PROJ + "/installer/test_api.txt")
    fn logIt s = ( format "%\n" s to:out; flush out )
    local names = #("trim", "trimString", "contains", "startsWith", "cam", "f", "here", "tan", "int", "goc", "prompt", "render", "viewport", "config", "variations", "completeRedraw", "coronaStartInteractiveRender", "vrayStartInteractiveRender", "getViewportDib", "redrawViews", "clearSelection", "generate", "started", "starts", "finally", "getExceptionString", "timeStamp", "makeDir", "classOf", "command")
    for nm in names do
    (
        local res = try
        (
            local v = (execute nm)
            if v == undefined then "MISSING" else ("OK: " + (classOf v as string))
        )
        catch ("EXEC-FAIL: " + (getCurrentException() as string))
        logIt (nm + ": " + res)
    )
    logIt "API_DONE"
    close out
)
