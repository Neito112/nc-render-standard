(
    local PROJ = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    local out = createFile (PROJ + "/installer/test_final.txt")
    fn logIt s = ( format "%\n" s to:out; flush out )

    -- Nap thang file zip-copy vao macros system (xoa ban cu trong usermacros truoc khi run)
    local tmpMcr = PROJ + "/installer/_zipcopy.mcr"
    rltNCRenderPro_v1 = undefined
    logIt ("LOAD: " + (try ( macros.load tmpMcr; "ok" ) catch ("EXC: " + (getCurrentException() as string))))

    -- Chay body macro
    logIt ("RUN: " + (try ( macros.run "NC-Render AI" "NCRenderSmartBridge_v1"; "ok" ) catch ("EXC: " + (getCurrentException() as string))))
    logIt ("GLOBAL: " + (try ( classOf rltNCRenderPro_v1 as string ) catch ("EXC")))

    -- Neu van undefined: thu doString toan bo body cua macro (bo qua registry)
    if rltNCRenderPro_v1 == undefined then
    (
        local f = openFile tmpMcr mode:"r"
        local code = ""
        while not (eof f) do code += readLine f + "\n"
        close f
        -- tach phan trong ngoac lon cua macroScript: tu '(' dau sau header den ')' cuoi
        logIt ("DOSTRING: " + (try ( doString code; "ok" ) catch ("EXC: " + (getCurrentException() as string))))
        logIt ("GLOBAL2: " + (try ( classOf rltNCRenderPro_v1 as string ) catch ("EXC")))
    )

    logIt "FINAL_DONE"
    close out
)
