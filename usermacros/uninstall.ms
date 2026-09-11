(
    if (queryBox "Gỡ bỏ hoàn toàn NC-Render AI Studio khỏi 3ds Max?" title:"Xác nhận") do
    (
        try (destroyDialog rltNCRenderPro) catch()
        local mcr = (getDir #userMacros) + "\\NC_Render_Bridge.mcr"
        if doesFileExist mcr do (deleteFile mcr)
        local uninst = (getDir #userMacros) + "\\uninstall.ms"
        if doesFileExist uninst do (deleteFile uninst)
        local iconFiles = getFiles ((getDir #userIcons) + "\\NC_Render_*.*")
        for f in iconFiles do (deleteFile f)
        colorman.reinitIcons()
        messageBox "Đã gỡ bỏ thành công!" title:"NC-Render AI"
    )
)
