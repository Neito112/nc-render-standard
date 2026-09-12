-- run_install.ms -- NC-Render AI Studio v1.4 installer
-- Chay sau khi mzp.run giai nen archive vao $temp\NCRender_install
-- QUY TAC: chi dung messageBox/queryBox, duong dan dau / (khong backslash
-- trong string), newline trong chuoi viet bang escape \n (2 ky tu).

(
    -- Helper tu viet: KHONG tin vao built-in nho ten (da co 2 ten ho gay
    -- 'got: undefined'). chi dung findItem/append — co trong moi ban Max.
    fn addUnique arr val =
    (
        if ((findItem arr val) == 0) do append arr val
    )

    local thisDir = getFilenamePath (getThisScriptFilename())
    local srcMcr = thisDir + "usermacros/NC_Render_Bridge_v1.mcr"
    local umDir = getDir #usermacros

    fn doInstall srcPath dstPath =
    (
        if (doesFileExist srcPath) then
        (
            copyFile srcPath dstPath
            -- copy icons (neu package co usericons/)
            local icSrc = thisDir + "usericons"
            if (doesFileExist (icSrc + "/")) then
            (
                local icDst = getDir #userIcons
                for icf in (getFiles (icSrc + "/*.png")) do
                    copyFile icf (icDst + "/" + (filenameFromPath icf))
            )
            macros.load dstPath
            -- Mo ngay giao dung: macros.run la ham THAT cua struct macros
            local opened = try (macros.run "NC-Render AI" "NCRenderSmartBridge_v1"; true) catch (false)
            if opened then
                messageBox "NC-Render AI Studio v1.4 cai dat thanh cong!\n\nCua so NC-Render dang mo.\n\nLan sau: Customize > Customize User Interface > Toolbars\n> tab Custom, category NC-Render AI > keo button 'NC-Render v1' ra toolbar,\nhoac chay: macros.run \"NC-Render AI\" \"NCRenderSmartBridge_v1\"" title:"NC-Render Install"
            else
                messageBox "Da cai dat xong, nhung khong tu mo duoc cua so.\n\nMo thu bang cach:\n1. Customize > Customize User Interface > Toolbars\n2. tab Custom, category 'NC-Render AI'\n3. keo button 'NC-Render v1' ra toolbar roi bam.\n\nHoac go vao Listener (F11):\nmacros.run \"NC-Render AI\" \"NCRenderSmartBridge_v1\"" title:"NC-Render Install"
            true
        )
        else
        (
            messageBox ("Khong tim thay macroScript trong package:\n" + srcPath) title:"NC-Render Install FAILED"
            false
        )
    )

    fn purgeOld lst =
    (
        for f in lst do
        (
            if (doesFileExist (f + "/")) then (try (deleteDirectory f) catch())
            else (try (deleteFile f) catch())
        )
    )

    -- ===== QUET BAN CU =====
    local foundOld = #()

    for f in (getFiles (umDir + "/NC_Render*.mcr")) do addUnique foundOld f
    for f in (getFiles (umDir + "/NC_Render*.ms")) do addUnique foundOld f
    for f in (getFiles (umDir + "/_render_feedback*")) do addUnique foundOld f

    local uninstFile = umDir + "/uninstall.ms"
    if (doesFileExist uninstFile) then
    (
        local fh = openFile uninstFile mode:"r"
        if fh != undefined then
        (
            local txt = ""
            while not (eof fh) do txt += readLine fh + "\n"
            close fh
            if (matchPattern txt pattern:"*NC-Render*") or (matchPattern txt pattern:"*NCRender*") then
                addUnique foundOld uninstFile
        )
    )

    local us = getDir #userScripts
    for f in (getFiles (us + "/sd_generate.py")) do addUnique foundOld f
    for f in (getFiles (us + "/sd_batch.py")) do addUnique foundOld f
    for f in (getFiles (us + "/cuda_auto_install.py")) do addUnique foundOld f
    for f in (getFiles (us + "/nc_cuda_render.py")) do addUnique foundOld f
    for f in (getFiles (us + "/github_update.py")) do addUnique foundOld f
    for f in (getFiles (us + "/_setup_download.py")) do addUnique foundOld f

    local ncFolder = us + "/NC-Render"
    if (doesFileExist (ncFolder + "/")) do addUnique foundOld ncFolder

    for f in (getFiles ((getDir #userIcons) + "/NC_Render_*.*")) do addUnique foundOld f

    local apDir = "C:/ProgramData/Autodesk/ApplicationPlugins/NC_Render_Standard"
    if (doesFileExist (apDir + "/")) do addUnique foundOld apDir

    -- ===== QUYET DINH =====
    local dstMcr = umDir + "/NC_Render_Bridge_v1.mcr"

    if (foundOld.count == 0) then
    (
        doInstall srcMcr dstMcr
    )
    else
    (
        local msgOld = "Phat hien " + (foundOld.count as string) + " thanh phan cu:\n\n"
        for f in foundOld do msgOld += f + "\n"
        msgOld += "\nBam [Co] = Go cu + Cai lai.\nBam [Khong] = Chi go, chua cai.\nBam nut Huy tren cua so = giu nguyen."

        local doRemove = queryBox msgOld title:"NC-Render - Phat hien ban cu"
        if doRemove then
        (
            purgeOld foundOld
            doInstall srcMcr dstMcr
        )
        else
        (
            messageBox ("Gi nguyen " + (foundOld.count as string) + " thanh phan cu. Cai dat da bi huy.") title:"NC-Render"
        )
    )
)
