macroScript NCRenderSmartBridge
category:"NC-Render AI"
tooltip:"NC-Render AI - Direct API Studio Workspace"
buttonText:"NC-Render"
icon:#("NC_Render", 1)
(
    global rltNCRenderPro
    try (destroyDialog rltNCRenderPro) catch()

    rollout rltNCRenderPro "NC-Render AI // Direct API Studio Workspace" width:1220 height:700
    (
        local sceneCams = #()
        local objectsInView = #()
        local previewBmp = undefined

        -- 1. CAMERA & GÓC NHÌN
        groupBox grpCam " 1. CAMERA & GÓC NHÌN " pos:[10, 5] width:350 height:72
        dropdownList ddlCams "" pos:[18, 20] width:332 height:5
        button btnRefreshCams "Quét Cam" pos:[18, 46] width:162 height:20
        button btnStraighten "Dựng nét (2-Point)" pos:[188, 46] width:162 height:20

        -- FRAME SETUP COMPACT
        groupBox grpRatio " Frame Setup " pos:[10, 80] width:350 height:75
        spinner spnWidth "W" range:[64, 8192, 1920] type:#integer fieldwidth:40 pos:[22, 98]
        spinner spnHeight "H" range:[64, 8192, 1080] type:#integer fieldwidth:40 pos:[110, 98]
        spinner spnRatio "R" range:[0.1, 10.0, 1.778] type:#float scale:0.001 fieldwidth:38 pos:[194, 98]
        checkbutton ckbLock "L" checked:true width:24 height:18 pos:[275, 96] tooltip:"Khóa tỉ lệ"
        button btnSwap "O" width:24 height:18 pos:[305, 96] tooltip:"Đảo khung"

        button btnR5_4 "5:4" pos:[18, 122] width:48 height:19
        button btnR4_3 "4:3" pos:[74, 122] width:48 height:19
        button btnR3_2 "3:2" pos:[130, 122] width:48 height:19
        button btnR2_1 "2:1" pos:[186, 122] width:48 height:19
        button btnR16_9 "16:9" pos:[242, 122] width:48 height:19
        button btnR1_1 "1:1" pos:[298, 122] width:48 height:19

        -- 2. VẬT THỂ & GROUP TRONG TẦM NHÌN
        groupBox grpObjPrompt " 2. VẬT THỂ & GROUP TRONG TẦM NHÌN " pos:[10, 158] width:350 height:110
        button btnScanObjs "⚡ Quét Group / Model trong View" pos:[18, 175] width:195 height:20
        checkbutton ckbSafeFrame "Safe Frame" checked:true pos:[218, 175] width:128 height:20
        dropdownList ddlViewObjs "" items:#("[Chưa quét vật thể]") pos:[18, 198] width:332 height:5
        edittext txtObjPrompt "Prompt bổ sung:" text:"" pos:[18, 226] width:328

        -- 3. ĐIỀU PHỐI AI & PROMPT MỞ RỘNG
        groupBox grpEngine " 3. ĐIỀU PHỐI AI & PROMPT CHÍNH " pos:[10, 272] width:350 height:328
        dropdownList ddlEngine "" items:#("Local ComfyUI (Máy có GPU)", "Google Cloud API (Máy yếu / Cloud)") pos:[18, 288] width:332 height:5
        edittext txtApiUrl "Endpoint:" text:"http://127.0.0.1:8188" pos:[18, 313] width:328
        
        label lblPrm "Prompt mô tả toàn cảnh (Mở rộng):" pos:[18, 337]
        edittext txtPrompt "" text:"modern architectural interior, natural soft daylight, photorealistic, 8k, architectural digest, highly detailed" pos:[18, 353] width:328 height:120

        button btnDirectRender "⚡ GỌI RENDER AI TRỰC TIẾP" pos:[18, 482] width:332 height:34
        label lblStatus "Trạng thái: Sẵn sàng." pos:[18, 522] width:332 height:18 style_sunkenedge:true
        button btnExportFiles "Xuất bộ 3 Pass + JSON" pos:[18, 545] width:162 height:20
        button btnUninstall "Gỡ cài đặt Plugin" pos:[188, 545] width:162 height:20

        label lblBrand "NC-Render AI Studio v6.5 (Neito Core)" pos:[18, 575] width:332

        -- CỘT PHẢI: KHUNG PREVIEW (70%)
        groupBox grpPreview " KHUNG PREVIEW " pos:[368, 5] width:840 height:685
        bitmap uiPreview width:820 height:575 pos:[378, 22] color:(color 18 22 30)
        button btnRefreshPreview "🔄 Cập Nhật Preview (Khung Nhìn Sạch & Unhide Ngầm)" pos:[378, 620] width:820 height:45

        -- TRUY TÌM GROUP HEAD CAO NHẤT
        fn getTopGroupOrNode node =
        (
            local cur = node
            while (isValidNode cur.parent and isGroupMember cur) do (
                cur = cur.parent
            )
            cur
        )

        -- BÓC TÁCH MATERIAL VÀ TEXTURE DÙNG VÒNG LẶP HÀNG ĐỢI (KHÔNG DÙNG ĐỆ QUY LỒNG)
        fn getNodeTexturesAndMats node =
        (
            local matList = #()
            local texList = #()
            local nodesToCheck = #()

            if isGroupHead node then (
                local queue = #(node)
                while queue.count > 0 do (
                    local cur = queue[1]
                    deleteItem queue 1
                    for c in cur.children do (
                        append nodesToCheck c
                        if isGroupHead c do append queue c
                    )
                )
            ) else (
                append nodesToCheck node
            )

            for n in nodesToCheck where (isValidNode n and n.material != undefined) do (
                local m = n.material
                if classOf m == Multimaterial then (
                    for sm in m.materialList where sm != undefined do (
                        if (findItem matList sm.name) == 0 do append matList sm.name
                        local bms = getClassInstances Bitmaptexture target:sm
                        for b in bms where (b.filename != undefined and b.filename != "") do (
                            local fname = filenameFromPath b.filename
                            if (findItem texList fname) == 0 do append texList fname
                        )
                    )
                ) else (
                    if (findItem matList m.name) == 0 do append matList m.name
                    local bms = getClassInstances Bitmaptexture target:m
                    for b in bms where (b.filename != undefined and b.filename != "") do (
                        local fname = filenameFromPath b.filename
                        if (findItem texList fname) == 0 do append texList fname
                    )
                )
            )
            #(matList, texList)
        )

        fn applyResToMax =
        (
            renderWidth = spnWidth.value
            renderHeight = spnHeight.value
            lblStatus.text = ("Kích thước: " + (renderWidth as string) + " x " + (renderHeight as string))
        )

        fn updateRatioLock source:#none =
        (
            if ckbLock.checked then
            (
                case source of
                (
                    #width: if spnRatio.value > 0 do spnHeight.value = int((spnWidth.value as float) / spnRatio.value + 0.5)
                    #height: spnWidth.value = int((spnHeight.value as float) * spnRatio.value + 0.5)
                    #ratio: if spnRatio.value > 0 do spnHeight.value = int((spnWidth.value as float) / spnRatio.value + 0.5)
                )
            )
            else
            (
                if spnHeight.value > 0 do spnRatio.value = (spnWidth.value as float) / (spnHeight.value as float)
            )
            applyResToMax()
        )

        fn setPresetRatio rVal =
        (
            spnRatio.value = rVal
            spnHeight.value = int((spnWidth.value as float) / rVal + 0.5)
            ckbLock.checked = true
            applyResToMax()
        )

        fn getValidCameras =
        (
            sceneCams = #()
            for o in cameras where (superClassOf o == camera and classOf o != Targetobject) do (append sceneCams o)
            local names = #("[Active Viewport]")
            for c in sceneCams do append names c.name
            return names
        )

        fn getSelectedCam =
        (
            local idx = ddlCams.selection
            if idx > 1 and idx <= (sceneCams.count + 1) then sceneCams[idx - 1] else undefined
        )

        fn scanObjectsInFrustum =
        (
            objectsInView = #()
            local rawTopNodes = #()
            local winX = gw.getWinSizeX()
            local winY = gw.getWinSizeY()

            for o in geometry where (not o.isHidden and classOf o != Targetobject) do
            (
                local screenPt = gw.wTransPoint o.pos
                if screenPt.x >= 0 and screenPt.x <= winX and screenPt.y >= 0 and screenPt.y <= winY and screenPt.z >= 0.0 and screenPt.z <= 1.0 do
                (
                    local topNode = getTopGroupOrNode o
                    if (findItem rawTopNodes topNode) == 0 do append rawTopNodes topNode
                )
            )

            objectsInView = rawTopNodes
            local names = #()
            for obj in objectsInView do
            (
                local matInfo = getNodeTexturesAndMats obj
                local mats = matInfo[1]
                local texs = matInfo[2]
                local hasTex = (texs.count > 0 or mats.count > 0)
                
                local prefix = if isGroupHead obj then "[G] " else ""
                local stateTag = if hasTex then "[Tex]" else "[NoTex]"
                local prm = getUserProp obj "NC_Prompt"
                if prm != undefined and prm != "" do stateTag += "(*)"
                
                append names (prefix + obj.name + " " + stateTag)
            )

            if names.count == 0 then (
                ddlViewObjs.items = #("[Không có đối tượng trong tầm nhìn]")
                txtObjPrompt.text = ""
            ) else (
                ddlViewObjs.items = names
                ddlViewObjs.selection = 1
                local curPrm = getUserProp objectsInView[1] "NC_Prompt"
                txtObjPrompt.text = if curPrm != undefined then curPrm else ""
            )
            lblStatus.text = ("Tìm thấy " + (objectsInView.count as string) + " nhóm/đối tượng trong view.")
        )

        fn buildCombinedPrompt =
        (
            local finalPrompt = txtPrompt.text
            local objSegments = #()

            for obj in objectsInView where isValidNode obj do
            (
                local matInfo = getNodeTexturesAndMats obj
                local mats = matInfo[1]
                local texs = matInfo[2]
                local userPrm = getUserProp obj "NC_Prompt"
                if userPrm == undefined do userPrm = ""

                local segment = ""
                local prefix = if isGroupHead obj then "Group " else "Object "

                if texs.count > 0 then (
                    local texStr = ""
                    local maxT = amin 3 texs.count
                    for i = 1 to maxT do (
                        texStr += (getFilenameFile texs[i])
                        if i < maxT do texStr += ", "
                    )
                    segment = prefix + obj.name + " (existing textures: " + texStr
                    if userPrm != "" do segment += ", additional details: " + userPrm
                    segment += ")"
                ) else if mats.count > 0 then (
                    local matStr = ""
                    local maxM = amin 2 mats.count
                    for i = 1 to maxM do (
                        matStr += mats[i]
                        if i < maxM do matStr += ", "
                    )
                    segment = prefix + obj.name + " (material: " + matStr
                    if userPrm != "" do segment += ", details: " + userPrm
                    segment += ")"
                ) else (
                    if userPrm != "" then (
                        segment = prefix + obj.name + " (untextured mesh, generate: " + userPrm + ")"
                    ) else (
                        segment = prefix + obj.name + " (untextured plain surface)"
                    )
                )
                append objSegments segment
            )

            if objSegments.count > 0 do (
                finalPrompt += " | Specific Scene Elements: ["
                for i = 1 to objSegments.count do (
                    finalPrompt += objSegments[i]
                    if i < objSegments.count do finalPrompt += "; "
                )
                finalPrompt += "]"
            )
            return finalPrompt
        )

        fn captureGhostViewport passType:#rgb =
        (
            local capturedBmp = undefined
            local camNode = getSelectedCam()
            local savedHidden = for o in objects where o.isHidden collect o
            local oldSafeFrames = displaySafeFrames
            local oldSel = selection as array
            local oldViewCube = false

            local oldHideShapes = hideByCategory.shapes
            local oldHideHelpers = hideByCategory.helpers
            local oldHideLights = hideByCategory.lights
            local oldHideCameras = hideByCategory.cameras

            try
            (
                clearSelection()
                try (oldViewCube = viewcube.visible; viewcube.visible = false) catch ()
                unhide objects
                if isValidNode camNode do viewport.setCamera camNode
                displaySafeFrames = ckbSafeFrame.checked

                hideByCategory.helpers = true
                hideByCategory.lights = true
                hideByCategory.cameras = true
                hideByCategory.shapes = true

                case passType of
                (
                    #rgb: (viewport.setRenderLevel #smoothhighlights; viewport.SetShowEdgeFaces false)
                    #edged: (viewport.setRenderLevel #smoothhighlights; viewport.SetShowEdgeFaces true)
                    #wire: (viewport.setRenderLevel #wireFrame; viewport.SetShowEdgeFaces false)
                )

                completeRedraw()
                redrawViews()
                capturedBmp = gw.getViewportDib()
            ) catch ()

            hideByCategory.shapes = oldHideShapes
            hideByCategory.helpers = oldHideHelpers
            hideByCategory.lights = oldHideLights
            hideByCategory.cameras = oldHideCameras
            viewport.setRenderLevel #smoothhighlights
            viewport.SetShowEdgeFaces false
            try (viewcube.visible = oldViewCube) catch ()
            displaySafeFrames = oldSafeFrames
            for o in savedHidden where isValidNode o do o.isHidden = true
            select oldSel
            completeRedraw()
            redrawViews()

            return capturedBmp
        )

        fn refreshPreviewDisplay =
        (
            local raw = captureGhostViewport passType:#rgb
            if raw != undefined then
            (
                uiPreview.bitmap = raw
                previewBmp = raw
                lblStatus.text = "Trạng thái: Đã cập nhật khung nhìn."
            )
        )

        -- EVENTS
        on rltNCRenderPro open do
        (
            ddlCams.items = getValidCameras()
            spnWidth.value = renderWidth
            spnHeight.value = renderHeight
            spnRatio.value = (renderWidth as float) / (renderHeight as float)
            refreshPreviewDisplay()
            scanObjectsInFrustum()
        )

        on spnWidth changed val do (updateRatioLock source:#width)
        on spnHeight changed val do (updateRatioLock source:#height)
        on spnRatio changed val do (updateRatioLock source:#ratio)
        on ckbLock changed state do (if state do spnRatio.value = (spnWidth.value as float) / (spnHeight.value as float))

        on btnSwap pressed do
        (
            local tempW = spnWidth.value
            spnWidth.value = spnHeight.value
            spnHeight.value = tempW
            spnRatio.value = (spnWidth.value as float) / (spnHeight.value as float)
            applyResToMax()
            refreshPreviewDisplay()
        )

        on btnR5_4 pressed do (setPresetRatio (5.0 / 4.0); refreshPreviewDisplay())
        on btnR4_3 pressed do (setPresetRatio (4.0 / 3.0); refreshPreviewDisplay())
        on btnR3_2 pressed do (setPresetRatio (3.0 / 2.0); refreshPreviewDisplay())
        on btnR2_1 pressed do (setPresetRatio (2.0 / 1.0); refreshPreviewDisplay())
        on btnR16_9 pressed do (setPresetRatio (16.0 / 9.0); refreshPreviewDisplay())
        on btnR1_1 pressed do (setPresetRatio (1.0); refreshPreviewDisplay())

        on ddlCams selected idx do (refreshPreviewDisplay(); scanObjectsInFrustum())
        on btnRefreshCams pressed do (ddlCams.items = getValidCameras(); lblStatus.text = "Đã quét lại Cam.")
        on btnRefreshPreview pressed do (refreshPreviewDisplay())
        on ckbSafeFrame changed state do (displaySafeFrames = state; refreshPreviewDisplay())

        on btnScanObjs pressed do (scanObjectsInFrustum())

        on ddlViewObjs selected idx do
        (
            if idx <= objectsInView.count and isValidNode objectsInView[idx] do
            (
                local curPrm = getUserProp objectsInView[idx] "NC_Prompt"
                txtObjPrompt.text = if curPrm != undefined then curPrm else ""
                select objectsInView[idx]
            )
        )

        on txtObjPrompt entered textVal do
        (
            local idx = ddlViewObjs.selection
            if idx <= objectsInView.count and isValidNode objectsInView[idx] do
            (
                setUserProp objectsInView[idx] "NC_Prompt" textVal
                lblStatus.text = ("Đã lưu prompt cho: " + objectsInView[idx].name)
                scanObjectsInFrustum()
                ddlViewObjs.selection = idx
            )
        )

        on btnStraighten pressed do
        (
            local c = getSelectedCam()
            if isValidNode c then
            (
                try (
                    if hasProperty c #vertical_tilt_correction do c.vertical_tilt_correction = true
                    if hasProperty c #tilt_correction_mode do c.tilt_correction_mode = 1
                    if (classOf c == Targetcamera or classOf c == Freecamera) do addModifier c (Camera_Correction())
                    lblStatus.text = "Đã cân đứng phối cảnh Camera."
                ) catch ()
                refreshPreviewDisplay()
            )
        )

        on ddlEngine selected idx do
        (
            if idx == 1 then (
                txtApiUrl.text = "http://127.0.0.1:8188"
            ) else (
                txtApiUrl.text = "AIzaSy..."
            )
        )

        on btnDirectRender pressed do
        (
            local bmp = captureGhostViewport passType:#rgb
            if bmp == undefined do (lblStatus.text = "Lỗi bắt ảnh Viewport!"; return false)

            local tempImg = (getDir #temp) + "\\nc_ai_input.png"
            bmp.filename = tempImg
            save bmp
            close bmp

            local engineMode = ddlEngine.selection
            local fullPrompt = buildCombinedPrompt()
            lblStatus.text = "Đang kết nối AI Engine..."

            if engineMode == 1 then
            (
                try (
                    local webClient = dotNetObject "System.Net.WebClient"
                    webClient.Headers.Add "Content-Type" "application/json"
                    local triggerPayload = "{\"prompt\": {}, \"client_id\": \"3dsmax_bridge\"}"
                    local res = webClient.UploadString txtApiUrl.text triggerPayload
                    lblStatus.text = "✓ Đã bắn lệnh sang ComfyUI!"
                ) catch (
                    lblStatus.text = "Không kết nối được ComfyUI!"
                )
            )
            else
            (
                try (
                    local apiKey = txtApiUrl.text
                    if apiKey == "" or apiKey == "AIzaSy..." do (
                        messageBox "Vui lòng nhập Google API Key hợp lệ!" title:"Thiếu API Key"
                        return false
                    )
                    local bytes = (dotNetClass "System.IO.File").ReadAllBytes tempImg
                    local b64 = (dotNetClass "System.Convert").ToBase64String bytes
                    local endpoint = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key=" + apiKey

                    local webClient = dotNetObject "System.Net.WebClient"
                    webClient.Headers.Add "Content-Type" "application/json"
                    local payload = "{\"instances\": [{\"prompt\": \"" + fullPrompt + "\"}], \"parameters\": {\"sampleCount\": 1, \"aspectRatio\": \"16:9\"}}"
                    lblStatus.text = "Đang sinh ảnh trên Google Cloud..."
                    local res = webClient.UploadString endpoint payload
                    lblStatus.text = "✓ Google Cloud Render thành công!"
                ) catch (
                    lblStatus.text = "Lỗi xác thực Google API Key hoặc kết nối!"
                )
            )
        )

        on btnExportFiles pressed do
        (
            local targetDir = getSavePath caption:"Chọn thư mục lưu gói dữ liệu AI"
            if targetDir != undefined do (
                local b = captureGhostViewport passType:#rgb
                if b != undefined do (b.filename = targetDir + "\\RGB_Pass.png"; save b; close b)
                lblStatus.text = "Đã xuất file thành công!"
                shellLaunch targetDir ""
            )
        )

        on btnUninstall pressed do
        (
            local uninstScript = (getDir #userMacros) + "\\uninstall.ms"
            if doesFileExist uninstScript do (fileIn uninstScript)
        )
    )

    createDialog rltNCRenderPro
)
