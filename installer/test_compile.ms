(
    local PROJ = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    local out = createFile (PROJ + "/installer/test_final.txt")
    fn logIt s = ( format "%\n" s to:out; flush out )

    local tmpMcr = PROJ + "/installer/_zipcopy.mcr"
    logIt ("FILEIN: " + (try ( fileIn tmpMcr; "PASS - compile OK" ) catch ("FAIL: " + (getCurrentException() as string))))

    logIt "FINAL_DONE"
    close out
)
