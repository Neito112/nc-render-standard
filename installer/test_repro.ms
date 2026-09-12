-- test_repro.ms — tai hien loi bam nut mo giao dien, bat exception day du
(
    local PROJ = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    local out = createFile (PROJ + "\\installer\\test_repro.txt")
    if out == undefined then exit
    fn logIt s = ( format "%\n" s to:out; flush out )

    -- 1. macros.run (giong bam nut)
    logIt ("RUN: " + (try
    (
        macros.run "NC-Render AI" "NCRenderSmartBridge_v1"
        "PASS - khong exception"
    ) catch ("EXCEPTION: " + (getCurrentException() as string))))

    -- 2. doi tuong dialog co ton tai sau do?
    logIt ("DIALOG: " + (try
    (
        if rltNCRenderPro_v1 == undefined then "undefined (khong tao duoc)"
        else "class OK: " + (classOf rltNCRenderPro_v1 as string)
    ) catch ("EXCEPTION: " + (getCurrentException() as string))))

    -- 3. createDialog truc tiep tren rollout class (noi crash thuong lo dien)
    logIt ("CREATE: " + (try
    (
        local cd = createDialog rltNCRenderPro_v1
        if cd == undefined then "FAIL: undefined" else "PASS: handle OK"
    ) catch ("EXCEPTION: " + (getCurrentException() as string))))

    -- 4. doc config nhu macroScript lam (kha nang ham ma 'trim')
    logIt ("CONFIG_READ: " + (try
    (
        local cfg = #()
        local f = openFile (PROJ + "\\installer\\dummy_cfg.txt") mode:"w"
        format "test\n" to:f
        close f
        local f2 = openFile (PROJ + "\\installer\\dummy_cfg.txt")
        while not (eof f2) do append cfg (trim (readLine f2))
        close f2
        deleteFile (PROJ + "\\installer\\dummy_cfg.txt")
        "PASS: trim() ton tai, count=" + (cfg.count as string)
    ) catch ("EXCEPTION: " + (getCurrentException() as string))))

    -- 5. icon reference khi file icon KHONG ton tai (nghi van: installer khong copy icons)
    logIt ("ICON_CHECK: " + (try
    (
        local icFiles = (getFiles ((getDir #userIcons) + "\\NC_Render*.*")).count
        "so file icon NC_Render trong userIcons: " + (icFiles as string)
    ) catch ("EXCEPTION: " + (getCurrentException() as string))))

    logIt "REPRO_DONE"
    close out
)
