-- run_install.ms -- NC-Render AI Studio v1.5.2 installer
-- Chay sau khi mzp.run giai nen archive vao $temp\NCRender_install
-- QUY TAC: chi dung messageBox/queryBox, duong dan dau / (khong backslash trong
-- string), newline viet escape \n (2 ky tu).
-- GUAN AN TOAN: fileIn/evaluate se CHAY THAT toan bo script nay; quiet mode tu
-- dong tra 'Yes' cho moi queryBox -> purge xoa de tro. MOI test compile phai dat
--   global NCRenderDryRun = true   TRUOC khi fileIn (khong bao gio fileIn tran).

if NCRenderDryRun != true then
(
    -- Helper tu viet, chi dung ham da kiem chung ton tai:
    -- findItem / append / getFiles / doesFileExist / copyFile / deleteFile /
    -- deleteDirectory / matchPattern / openFile / eof / readLine / close /
    -- getDir / filenameFromPath / getFilenamePath / getThisScriptFilename /
    -- messageBox / queryBox / macros.load / macros.run
    fn addUnique arr val =
    (
        if ((findItem arr val) == 0) do append arr val
    )

    local thisDir = getFilenamePath (getThisScriptFilename())
    local srcMcr = thisDir + "usermacros/NC_Render_Bridge_v1.mcr"
    local umDir = getDir #usermacros
    local dstMcr = umDir + "/NC_Render_Bridge_v1.mcr"
    local regMcr = umDir + "/NC_Render AI-NCRenderSmartBridge_v1.mcr"

    fn doInstall srcPath =
    (
        if (doesFileExist srcPath) then
        (
            -- 2 file macroScript: ban duong + ban dang ky theo ten
            -- "<Category>-<MacroName>.mcr" (Max luong ten nay khi quet usermacros
            -- luc khoi dong; thieu no = plugin mat sau restart!)
            copyFile srcPath dstMcr
            copyFile srcPath regMcr
            -- copy icons (package co usericons/)
            local icSrc = thisDir + "usericons"
            if (doesFileExist (icSrc + "/")) then
            (
                local icDst = getDir #userIcons
                for icf in (getFiles (icSrc + "/*.png")) do
                    copyFile icf (icDst + "/" + (filenameFromPath icf))
            )
            macros.load dstMcr
            local opened = try ( macros.run "NC-Render AI" "NCRenderSmartBridge_v1"; true ) catch ( false )
            if opened then
                messageBox "NC-Render AI Studio v1.5.2 cai dat thanh cong!\n\nCua so NC-Render dang mo.\n\nLan sau: Customize > Customize User Interface > Toolbars\n> tab Custom, category NC-Render AI > keo button 'NC-Render v1'\nra toolbar, hoac chay: macros.run \"NC-Render AI\" \"NCRenderSmartBridge_v1\"" title:"NC-Render Install"
            else
                messageBox "Da cai dat xong, nhung khong tu mo duoc cua so.\n\nMo thu:\n1. Customize > Customize User Interface > Toolbars\n2. tab Custom, category 'NC-Render AI'\n3. keo button 'NC-Render v1' ra toolbar roi bam.\n\nHoac go vao Listener (F11):\nmacros.run \"NC-Render AI\" \"NCRenderSmartBridge_v1\"" title:"NC-Render Install"
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

    -- ===== QUET BAN CU (truy tuyen: KHONG quet vao ten dang ky macro!) =====
    local foundOld = #()

    -- chi xo ban Bridge cu, GIU file dang ky 'NC_Render AI-*' (no la plugin dang chay)
    for f in (getFiles (umDir + "/NC_Render_Bridge*.mcr")) do addUnique foundOld f
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
    if (foundOld.count == 0) then
    (
        doInstall srcMcr
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
            doInstall srcMcr
        )
        else
        (
            messageBox ("Gi nguyen " + (foundOld.count as string) + " thanh phan cu. Cai dat da bi huy.") title:"NC-Render"
        )
    )
)
