-- clean_nc_old.ms — NC-Render AI Studio: don ve plugin cu trong 3ds Max
-- Chay doc lap, KHONG thuoc package, dung khi ban cai cu lam Max "mo khung".
-- Cach dung: 3ds Max -> Scripting > Run Script -> chon file nay

(
    fn addUnique arr val =
    (
        if ((findItem arr val) == 0) do append arr val
    )

    local found = #()

    -- 1. usermacros: macroScript + rac install cu
    local umDir = getDir #usermacros
    for f in (getFiles (umDir + "/NC_Render*.mcr")) do addUnique found f
    for f in (getFiles (umDir + "/NC_Render*.ms"))  do addUnique found f
    for f in (getFiles (umDir + "/_render_feedback*")) do addUnique found f

    -- uninstall.ms: chi go neu la cua NC-Render (doc noi dung kiem tra)
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
                addUnique found uninstFile
        )
    )

    -- 2. scripts: python cua install cu
    local scrDir = getDir #userScripts
    for f in (getFiles (scrDir + "/sd_generate.py"))      do addUnique found f
    for f in (getFiles (scrDir + "/sd_batch.py"))         do addUnique found f
    for f in (getFiles (scrDir + "/cuda_auto_install.py")) do addUnique found f
    for f in (getFiles (scrDir + "/nc_cuda_render.py"))   do addUnique found f
    for f in (getFiles (scrDir + "/github_update.py"))    do addUnique found f
    for f in (getFiles (scrDir + "/_setup_download.py"))  do addUnique found f

    -- 3. folder rac scripts/NC-Render
    local ncFolder = scrDir + "/NC-Render"
    if (doesFileExist (ncFolder + "/")) do addUnique found ncFolder

    -- 4. usericons
    for f in (getFiles ((getDir #userIcons) + "/NC_Render_*.*")) do addUnique found f

    -- 5. ApplicationPlugins package cu
    local apDir = @"C:\ProgramData\Autodesk\ApplicationPlugins\NC_Render_Standard"
    if (doesFileExist (apDir + "/")) do addUnique found apDir
    local apDir2 = @"C:\ProgramData\Autodesk\ApplicationPlugins\nc_render_standard"
    if (apDir2 != apDir and (doesFileExist (apDir2 + "/"))) do addUnique found apDir2

    -- Ket luan
    if found.count == 0 then
        messageBox "Khong phat hien ban cu nao cua NC-Render trong 3ds Max.\n\nSach se - an tam cai ban moi." title:"NC-Render Cleanup"
    else
    (
        local msg = "Phat hien " + (found.count as string) + " thanh phan cu:\n\n"
        for f in found do msg += "  " + f + "\n"
        msg += "\nGo sach tat ca?"
        if (queryBox msg title:"NC-Render Cleanup") then
        (
            local okCount = 0
            for f in found do
            (
                local ok = false
                if (doesFileExist (f + "/")) then
                    ok = deleteDirectory f
                else
                    ok = deleteFile f
                if ok do okCount += 1
            )
            macros.reload()
            messageBox ("Da go " + (okCount as string) + "/" + (found.count as string) + " thanh phan.\n\nRestart 3ds Max lan nua roi cai ban moi.") title:"NC-Render Cleanup"
        )
    )
)
