(
    local PROJ = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    local out = createFile (PROJ + "/installer/test_reg.txt")
    fn logIt s = ( format "%
" s to:out; flush out )

    logIt ("LIST_ALL: " + (try
    (
        local lst = macros.list()
        "class=" + (classOf lst as string) + " count=" + (lst.count as string)
    ) catch ("EXC: " + (getCurrentException() as string))))

    logIt ("LIST_CAT: " + (try
    (
        local lst = macros.list "NC-Render AI"
        local s = "class=" + (classOf lst as string)
        for m in lst do s += " [" + (m as string) + "]"
        s
    ) catch ("EXC: " + (getCurrentException() as string))))

    logIt ("BOGUS_NAME: " + (try ( macros.run "NC-Render AI" "NoSuchMacro_zz"; "NO-THROW (silent no-op!)" ) catch ("THREW: " + (getCurrentException() as string))))
    logIt ("BOGUS_CAT:  " + (try ( macros.run "NoCategory zz" "x"; "NO-THROW (silent no-op!)" ) catch ("THREW: " + (getCurrentException() as string))))

    logIt ("DESKTOP: " + (try ( (desktop.width as string) + "x" + (desktop.height as string) ) catch ("EXC: " + (getCurrentException() as string))))
    logIt "REG_DONE"
    close out
)