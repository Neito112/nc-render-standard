(
    local PROJ = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    local out = createFile (PROJ + "/installer/test_final.txt")
    fn logIt s = ( format "%\n" s to:out; flush out )

    -- Nap ban .mcr TU ZIP MOI bang macros.load (dung API that, giong installer)
    local tmpMcr = PROJ + "/installer/_zipcopy.mcr"
    logIt ("LOAD_zipcopy: " + (try ( macros.load tmpMcr; "PASS" ) catch ("FAIL: " + (getCurrentException() as string))))

    -- Chay macroScript (bam nut): bao gom toan bo rollout + createDialog
    logIt ("RUN_macro: " + (try
    (
        macros.run "NC-Render AI" "NCRenderSmartBridge_v1"
        "PASS - khong exception"
    ) catch ("EXCEPTION: " + (getCurrentException() as string))))

    -- Neu dialog ton tai sau khi run => giao dien da mo duoc
    logIt ("DIALOG_STATE: " + (try
    (
        if rltNCRenderPro_v1 == undefined then "undefined"
        else "class: " + (classOf rltNCRenderPro_v1 as string)
    ) catch ("EXC: " + (getCurrentException() as string))))

    logIt "FINAL_DONE"
    close out
)
