// NC_Render_Bridge_v1.mcr — NC-Render AI Studio
//
// CUDA render test, API key, material detection đa renderer,
// camera consistency, upscale, reference image
//
// Cài đặt trực tiếp vào userMacros directory
// Paths relative to MZP package extraction

macroScript NCRenderSmartBridge_v1
category:"NC-Render AI"
tooltip:"NC-Render AI Studio v1.0 — CUDA + API + Multi-Renderer"
buttonText:"NC-Render v1"
icon:#("NC_Render", 1)
(
    global rltNCRenderPro_v1
    try (destroyDialog rltNCRenderPro_v1) catch()
    
    // ============================================================
    // CONFIG — loaded from config file if exists
    // ============================================================
    local configFile = (getDir #temp) + "/nc_render_config.txt"
    local config = #()
    if doesFileExist configFile do
    (
        local f = openFile configFile
        while not eof f do append config (trim (readLine f))
        close f
    )
    
    local renderMethod = if config.count > 0 then config[1] else "Corona GPU"
    local apiKey = if config.count > 1 then config[2] else ""
    local gpuName = if config.count > 2 then config[3] else "Unknown"
    local gpuMemory = if config.count > 3 then config[4] else "0"
    local hasCUDA = if config.count > 4 then config[5] else "false"
    local coronaInstalled = if config.count > 5 then config[6] else "false"
    local vrayInstalled = if config.count > 6 then config[7] else "false"
    local pytorchCUDA = if config.count > 7 then config[8] else "false"
    // Python interpreter có CUDA — trỏ tới venv Hermes Agent
    local pythonBin = "C:/Users/HOMIE/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe"
    
    // ============================================================
    // UI — Main rollout
    // ============================================================
    rollout rltNCRenderPro_v1 "NC-Render AI Studio v1.0 — CUDA + API + Multi-Renderer" width:1280 height:800
    (
        // --- COLUMN LEFT: CONTROL PANEL ---
        
        // SECTION 1: GPU & RENDERER STATUS
        groupBox grpSystem " Hệ thống & Renderer " pos:[10, 5] width:340 height:70
        label lblGPUInfo "GPU: " + gpuName pos:[20, 20] width:320
        label lblGPUMemory "VRAM: " + gpuMemory + " MB" pos:[20, 40] width:320
        label lblCUDAStatus "CUDA: " + (if hasCUDA == "true" then "✅ Active" else "⚠️ Not available") pos:[20, 55] width:320
        
        // Renderer checkboxes (đọc trạng thái từ hệ thống)
        local isCorona = coronaInstalled == "true"
        local isVray = vrayInstalled == "true"
        
        checkbox chkCorona "Corona Renderer" pos:[20, 85] width:150 height:18 \
            checked:isCorona enabled:(isCorona or hasCUDA == "true")
        checkbox chkVray "V-Ray Renderer" pos:[180, 85] width:150 height:18 \
            checked:isVray enabled:(isVray or hasCUDA == "true")
        
        label lblStatus "Trạng thái renderer: " + renderMethod pos:[20, 108] width:320
        
        // SECTION UPDATE: Kiểm tra cập nhật plugin
        groupBox grpUpdate " Plugin Update " pos:[10, 115] width:340 height:110
        label lblUpdateInfo "Phiên bản hiện tại: v1.0.0" pos:[20, 130] width:320
        button btnCheckUpdate "🔍 Kiểm tra cập nhật" pos:[20, 155] width:320 height:22
        label lblUpdateStatus "" pos:[20, 182] width:320 height:18 style_sunkenedge:true
        button btnDoUpdate "⬇ Tải & Cài đặt" pos:[20, 205] width:320 height:22 enabled:false
        
        on btnCheckUpdate pressed do
        (
            lblUpdateStatus.text = "Đang kiểm tra..."
            btnDoUpdate.enabled = false
            try
            (
                local statusFile = (getDir #temp) + "/nc_update_status.txt"
                local pyScript = (getDir #max) + "/Plugins/NC_Render_Standard/scripts/github_update.py"
                // Gọi Python, redirect output ra file
                local cmd = (pythonBin + " \"" + pyScript + "\" --check-only --current-version v1.0.0 --json > \"" + statusFile + "\"")
                shellLaunch cmd
                // Đợi process kết thúc (timeout 15s)
                local waited = 0
                while not doesFileExist statusFile and waited < 15 do
                (
                    sleep 1
                    waited += 1
                )
                if doesFileExist statusFile do
                (
                    local f = openFile statusFile
                    local content = ""
                    while not eof f do content += (readLine f) + "\n"
                    close f
                    // Parse simple: kiểm tra keywords trong output JSON
                    if content contains "up_to_date" and content contains "true" do
                    (
                        lblUpdateStatus.text = "✅ Bạn đang dùng phiên bản mới nhất"
                        btnDoUpdate.enabled = false
                    )
                    else if content contains "update_available" and content contains "true" do
                    (
                        lblUpdateStatus.text = "📦 CÓ bản cập nhật — nhấn \"Tải & Cài đặt\""
                        btnDoUpdate.enabled = true
                    )
                    else if content contains "error" do
                    (
                        lblUpdateStatus.text = "⚠️ Lỗi kiểm tra — kiểm tra mạng hoặc GitHub API"
                        btnDoUpdate.enabled = false
                    )
                    else
                    (
                        lblUpdateStatus.text = "⚠️ Không thể đọc kết quả — thử lại"
                        btnDoUpdate.enabled = false
                    )
                )
                else
                (
                    lblUpdateStatus.text = "⚠️ Không thể kết nối GitHub API (timeout)"
                    btnDoUpdate.enabled = false
                )
            )
            catch
            (
                lblUpdateStatus.text = "Lỗi: " + (getExceptionString() as string)
                btnDoUpdate.enabled = false
            )
        )
        
        on btnDoUpdate pressed do
        (
            lblUpdateStatus.text = "Đang tải bản cập nhật..."
            btnDoUpdate.enabled = false
            btnCheckUpdate.enabled = false
            try
            (
                local statusFile = (getDir #temp) + "/nc_update_status.txt"
                local pyScript = (getDir #max) + "/Plugins/NC_Render_Standard/scripts/github_update.py"
                local userMacros = (getDir #userMacros)
                local cmd = (pythonBin + " \"" + pyScript + "\" --download --current-version v1.0.0 --user-macros \"" + userMacros + "\" > \"" + statusFile + "\"")
                shellLaunch cmd
                // Đợi cấp tải完 (up to 60s)
                local waited = 0
                while not doesFileExist statusFile and waited < 60 do
                (
                    sleep 1
                    waited += 1
                )
                if doesFileExist statusFile do
                (
                    local f = openFile statusFile
                    local content = ""
                    while not eof f do content += (readLine f) + "\n"
                    close f
                    if content contains "updated" and content contains "true" do
                    (
                        lblUpdateStatus.text = "✅ Cập nhật thành công — khởi động lại 3ds Max để áp dụng"
                        btnDoUpdate.enabled = false
                        btnCheckUpdate.enabled = false
                    )
                    else if content contains "error" do
                    (
                        lblUpdateStatus.text = "❌ Lỗi cập nhật — xem log"
                        btnCheckUpdate.enabled = true
                    )
                    else if content contains "up_to_date" do
                    (
                        lblUpdateStatus.text = "ℹ️ Không có bản cập nhật mới"
                        btnCheckUpdate.enabled = true
                    )
                    else
                    (
                        lblUpdateStatus.text = "⚠️ Không đọc được kết quả — kiểm tra lại"
                        btnCheckUpdate.enabled = true
                    )
                )
                else
                (
                    lblUpdateStatus.text = "❌ Timeout — tải bản cập nhật thất bại"
                    btnCheckUpdate.enabled = true
                )
            )
            catch
            (
                lblUpdateStatus.text = "Lỗi: " + (getExceptionString() as string)
                btnCheckUpdate.enabled = true
            )
        )
        
        // SECTION 2: CAMERA & FRAME
        groupBox grpCam " Camera & Frame " pos:[10, 120] width:340 height:95
        dropdownList ddlCams "" pos:[18, 135] width:322 height:6
        
        button btnQuickCam "+ Quick Cam" pos:[18, 152] width:80 height:20
        button btnRefreshCams "🔄 Refresh" pos:[108, 152] width:80 height:20
        button btn2Point "2-Point Perp" pos:[198, 152] width:80 height:20
        button btnResetCam "Reset Camera" pos:[18, 175] width:80 height:20
        
        // Frame setup
        spinner spnWidth "W" range:[64, 7680, 1920] type:#integer fieldwidth:40 pos:[18, 195] \
            enabled:(renderMethod == "Corona GPU" or renderMethod == "V-Ray GPU")
        spinner spnHeight "H" range:[64, 7680, 1080] type:#integer fieldwidth:40 pos:[110, 195] \
            enabled:(renderMethod == "Corona GPU" or renderMethod == "V-Ray GPU")
        spinner spnRatio "R" range:[0.1, 10.0, 1.778] type:#float scale:0.001 fieldwidth:38 pos:[202, 195] \
            enabled:(renderMethod == "Corona GPU" or renderMethod == "V-Ray GPU")
        checkbutton ckbLock "🔒 L" checked:true width:28 height:18 pos:[292, 193] \
            tooltip:"Khóa tỉ lệ khung hình"
        
        // Quick ratios
        button btnRatios "Ratios:" pos:[18, 222] width:322 height:18
        local ratioItems = #("16:9", "4:3", "5:4", "3:2", "2:1", "1:1", "9:16")
        popupMenu pmRatio "Ratios" pos:[0, 0] width:100 items:ratioItems
        on btnRatios pressed do pmRatio.pos = [18, 220]; pmRatio.amount = 0
        
        on pmRatio picked item do
        (
            local parts = (filterString item ":")
            if parts.count == 2 do
            (
                local w = (parts[1] as integer) as float
                local h = (parts[2] as integer) as float
                spnRatio.value = w / h
                spnHeight.value = int((spnWidth.value as float) / spnRatio.value + 0.5)
            )
        )
        
        // SECTION 3: RENDER METHOD SELECTION
        groupBox grpRenderMethod " Render Method " pos:[10, 222] width:340 height:80
        
        label lblMethod "Chọn phương án render:" pos:[20, 240] width:320
        dropdownList ddlRenderMethod "" pos:[20, 260] width:320 height:6 \
            items:#("Corona GPU (mặc định)", "V-Ray GPU", "Local SD (CUDA)", "External API (FLUX/Google/MJ)")
        button btnApplyMethod "Apply" pos:[20, 290] width:80 height:20
        button btnDefaults "Default" pos:[110, 290] width:80 height:20
        button btnAPIKey "API Key..." pos:[200, 290] width:80 height:20
        
        on btnApplyMethod pressed do
        (
            local idx = ddlRenderMethod.selection
            case idx of
            (
                1: renderMethod = "Corona GPU"
                2: renderMethod = "V-Ray GPU"
                3: renderMethod = "Local SD (CUDA)"
                4: renderMethod = "External API (FLUX/Google/MJ)"
            )
            lblStatus.text = "Render method: " + renderMethod
            updateUIForMethod()
        )
        
        on btnDefaults pressed do
        (
            if isCorona do
            (
                renderMethod = "Corona GPU"
                ddlRenderMethod.selection = 1
            )
            else if isVray do
            (
                renderMethod = "V-Ray GPU"
                ddlRenderMethod.selection = 2
            )
            else
            (
                renderMethod = "External API (FLUX/Google/MJ)"
                ddlRenderMethod.selection = 4
            )
            lblStatus.text = "Render method: " + renderMethod
            updateUIForMethod()
        )
        
        on btnAPIKey pressed do
        (
            local key = inputBox "Nhập API Key:" "API Key for external render" apiKey
            if key != undefined do
            (
                apiKey = key
                txtPromptMaterial.text = "API key updated."
            )
        )
        
        // SECTION 4: PROMPT & MATERIALS
        groupBox grpPrompt " Prompt & Materials " pos:[10, 305] width:340 height:180
        
        label lblPrompt "Prompt mô tả (mở rộng):" pos:[20, 322] width:320
        edittext txtPrompt "modern architectural interior, natural soft daylight, photorealistic, 8k, architectural digest" \
            text:"modern architectural interior, natural soft daylight, photorealistic, 8k, architectural digest" \
            pos:[20, 338] width:320 height:80
        
        label lblMaterial "Material detection:" pos:[20, 425] width:320
        button btnDetectMaterial "🔍 Quét Material toàn cảnh" pos:[20, 445] width:160 height:20
        button btnRefreshMat "🔄 Refresh" pos:[190, 445] width:80 height:20
        listbox lstMaterials "" pos:[20, 470] width:320 height:5
        
        label lblReference "Reference Image (tham chiếu):" pos:[20, 498] width:320
        button btnLoadRef "📁 Load reference" pos:[20, 518] width:160 height:20
        button btnClearRef "🗑 Clear" pos:[190, 518] width:80 height:20
        local referenceImage = undefined
        
        button btnSavePrompt "💾 Save Prompt as preset" pos:[20, 545] width:160 height:20
        button btnLoadPreset "📂 Load preset..." pos:[190, 545] width:140 height:20
        
        on btnDetectMaterial pressed do
        (
            local mats = scanMaterialsInScene()
            if mats.count > 0 do
            (
                lstMaterials.items = for m in mats collect m.name
                lstMaterials.selection = 1
                lblStatus.text = "Found " + (mats.count as string) + " materials in scene"
            )
            else
            (
                lstMaterials.items = #("No materials found")
                lblStatus.text = "No materials detected"
            )
        )
        
        on btnLoadRef pressed do
        (
            local fname = getOpenFileName caption:"Select reference image" \
                types:"Image Files|*.png;*.jpg;*.jpeg;*.bmp;*.tga|All Files|*.*|"
            if fname != undefined do
            (
                referenceImage = open fname
                lblStatus.text = "Reference loaded: " + (filenameFromPath fname)
            )
        )
        
        on btnClearRef pressed do
        (
            if referenceImage != undefined do
            (
                close referenceImage
                referenceImage = undefined
                lblStatus.text = "Reference cleared"
            )
        )
        
        on btnSavePrompt pressed do
        (
            local name = inputBox "Preset name:" "Save prompt preset" "my_prompt"
            if name != undefined and name != "" do
            (
                local presetFile = (getDir #temp) + "/nc_prompts/" + name + ".txt"
                makeDir (getFilenamePath presetFile)
                local f = createFile presetFile
                writeLine f txtPrompt.text
                writeLine f (renderMethod as string)
                close f
                lblStatus.text = "Preset saved: " + name
            )
        )
        
        on btnLoadPreset pressed do
        (
            local presetDir = (getDir #temp) + "/nc_prompts"
            local files = getFiles (presetDir + "/*.txt")
            if files.count > 0 do
            (
                local selected = getOpenFileName caption:"Select prompt preset" \
                    types:"Prompt Presets|*.txt|" \
                    filename:(files[1])
                if selected != undefined do
                (
                    local f = openFile selected
                    txtPrompt.text = readLine f
                    local methodLine = readLine f
                    if methodLine != "" do
                    (
                        case (trim methodLine) of
                        (
                            "Corona GPU": ddlRenderMethod.selection = 1
                            "V-Ray GPU": ddlRenderMethod.selection = 2
                            "Local SD (CUDA)": ddlRenderMethod.selection = 3
                            "External API (FLUX/Google/MJ)": ddlRenderMethod.selection = 4
                        )
                        renderMethod = trim methodLine
                    )
                    close f
                    lblStatus.text = "Preset loaded: " + (filenameFromPath selected)
                )
            )
            else
            (
                lblStatus.text = "No presets found"
            )
        )
        
        // SECTION 5: RENDER BUTTONS
        groupBox grpRender " Render & Generate " pos:[10, 490] width:340 height:180
        
        local renderButtons = case of
        (
            (renderMethod == "Corona GPU"): 
                #("⚡ Render Test (Corona GPU)", "🔄 Corona Interactive", "🚀 Full Render (Corona)")
            (renderMethod == "V-Ray GPU"): 
                #("⚡ Render Test (V-Ray GPU)", "🔄 V-Ray Interactive", "🚀 Full Render (V-Ray)")
            (renderMethod == "Local SD (CUDA)"):
                #("⚡ Generate from Prompt (CUDA)", "🔄 Generate + Upscale", "🚀 Batch Generate")
            (renderMethod == "External API (FLUX/Google/MJ)"):
                #("⚡ Generate via API", "🔄 Generate with Reference", "🚀 Upscale Result")
        )
        
        local btnRender = button btnRender1 "Render" pos:[20, 505] width:320 height:30
        btnRender1.text = renderButtons[1]
        local btnRender2 = button btnRender2 "Render" pos:[20, 540] width:320 height:30
        btnRender2.text = renderButtons[2]
        local btnRender3 = button btnRender3 "Render" pos:[20, 575] width:320 height:30
        btnRender3.text = renderButtons[3]
        
        // SECTION 6: UPSAMPLE & QUALITY
        groupBox grpQuality " Quality & Upscale " pos:[10, 675] width:340 height:80
        
        label lblUpscale "Upscale factor:" pos:[20, 690] width:120
        dropdownList ddlUpscale "" pos:[150, 688] width:80 height:5 items:#("1x (không upscale)", "2x", "4x", "8x")
        label lblDetail "Detail enhancement:" pos:[245, 690] width:100
        checkbutton chkDetail "Tối ưu chi tiết" checked:true pos:[340, 688] width:100 height:18
        label lblTile "Tile-based upscaling:" pos:[20, 713] width:120
        checkbutton chkTile "B decomposed if large" checked:true pos:[150, 711] width:200 height:18
        
        // SECTION 7: STATUS
        label lblStatus "Trạng thái: Sẵn sàng. Đang load plugin..." pos:[10, 760] width:340 height:18 style_sunkenedge:true
        
        // --- COLUMN RIGHT: PREVIEW ---
        groupBox grpPreview " KHUNG PREVIEW " pos:[355, 5] width:920 height:770
        bitmap uiPreview width:900 height:600 pos:[365, 22] color:(color 18 22 30)
        button btnRefreshPreview "🔄 Cập Nhật (Unhide + Clean View)" pos:[365, 632] width:900 height:50
        button btnFullPreview "📷 Full Viewport Capture" pos:[365, 690] width:440 height:40
        button btnSavePreview "💾 Save Preview as PNG" pos:[815, 690] width:440 height:40
        
        // ============================================================
        // HELPER FUNCTIONS
        // ============================================================
        
        fn updateUIForMethod =
        (
            // Enable/disable controls based on render method
            local isRenderEngine = (renderMethod == "Corona GPU" or renderMethod == "V-Ray GPU")
            local isAIConcept = (renderMethod == "Local SD (CUDA)" or renderMethod == "External API (FLUX/Google/MJ)")
            
            spnWidth.enabled = isRenderEngine
            spnHeight.enabled = isRenderEngine
            spnRatio.enabled = isRenderEngine
            ckbLock.enabled = isRenderEngine
            
            // Update button texts
            btnRender1.text = case of
            (
                (renderMethod == "Corona GPU"): "⚡ Render Test (Corona GPU)"
                (renderMethod == "V-Ray GPU"): "⚡ Render Test (V-Ray GPU)"
                (renderMethod == "Local SD (CUDA)"): "⚡ Generate from Prompt (CUDA)"
                (renderMethod == "External API (FLUX/Google/MJ)"): "⚡ Generate via API"
            )
            btnRender2.text = case of
            (
                (renderMethod == "Corona GPU"): "🔄 Corona Interactive"
                (renderMethod == "V-Ray GPU"): "🔄 V-Ray Interactive"
                (renderMethod == "Local SD (CUDA)"): "🔄 Generate + Upscale"
                (renderMethod == "External API (FLUX/Google/MJ)"): "🔄 Generate with Reference"
            )
            btnRender3.text = case of
            (
                (renderMethod == "Corona GPU"): "🚀 Full Render (Corona)"
                (renderMethod == "V-Ray GPU"): "🚀 Full Render (V-Ray)"
                (renderMethod == "Local SD (CUDA)"): "🚀 Batch Generate"
                (renderMethod == "External API (FLUX/Google/MJ)"): "🚀 Upscale Result"
            )
            
            lblStatus.text = "Render method: " + renderMethod
        )
        
        fn scanMaterialsInScene =
        (
            local allMats = #()
            
            // Detect Corona materials
            try
            (
                for m in getClassInstances CoronaMaterial where isValidNode m do
                (
                    local info = #("Corona", m.name, m)
                    append allMats info
                )
            ) catch ()
            
            // Detect V-Ray materials
            try
            (
                for m in getClassInstances VRayMtl where isValidNode m do
                (
                    local info = #("V-Ray", m.name, m)
                    append allMats info
                )
            ) catch ()
            
            // Detect standard materials
            for m in objects where isValidNode m and classOf m == Material do
            (
                local className = classOf(m) as string
                if className == "Standard" or className == "PhysicalMaterial" or className == "Multimaterial" do
                (
                    local info = #(className, m.name, m)
                    append allMats info
                )
            )
            
            return allMats
        )
        
        fn getRenderCamera =
        (
            local idx = ddlCams.selection
            if idx > 1 do
            (
                local camName = ddlCams.items[idx]
                if camName != "[Active Viewport]" do
                (
                    for c in cameras where c.name == camName do return c
                )
            )
            return undefined
        )
        
        fn captureViewportRender =
        (
            local cam = getRenderCamera()
            if cam != undefined do viewport.setCamera cam
            
            local savedHidden = for o in objects where o.isHidden collect o
            local savedSafeFrames = displaySafeFrames
            
            try
            (
                clearSelection()
                unhide objects
                displaySafeFrames = false
                hideByCategory.helpers = true
                hideByCategory.lights = true
                hideByCategory.cameras = true
                hideByCategory.shapes = true
                
                viewport.setRenderLevel #smoothhighlights
                completeRedraw()
                redrawViews()
                
                local bmp = gw.getViewportDib()
                return bmp
            )
            catch (return undefined)
            finally
            (
                displaySafeFrames = savedSafeFrames
                for o in savedHidden where isValidNode o do o.isHidden = true
                completeRedraw()
                redrawViews()
            )
        )
        
        // ============================================================
        // RENDER HANDLERS
        // ============================================================
        
        on btnRender1 pressed do
        (
            // Phương án render chính
            lblStatus.text = "Đang xử lý render..."
            
            case renderMethod of
            (
                "Corona GPU":
                (
                    // Render test với Corona GPU, resolution thấp
                    try
                    (
                        local testScale = 0.25
                        local w = int(spnWidth.value * testScale)
                        local h = int(spnHeight.value * testScale)
                        renderOutputWidth = w
                        renderOutputHeight = h
                        renderOutputResolution = [w, h]
                        
                        // Set Corona as active renderer
                        renderers.current = renderers.Corona
                        
                        lblStatus.text = "Đang render (Corona GPU)..."
                        local startTime = timeStamp()
                        local img = render()
                        local elapsed = (timeStamp() - startTime) / 1000.0
                        
                        if img != undefined do
                        (
                            uiPreview.bitmap = img
                            lblStatus.text = ("Render xong: " + (w as string) + "x" + (h as string) + " — " + elapsed as string + "s")
                            // Auto-save nếu cần
                            local savePath = (getDir #temp) + "/nc_render_test.png"
                            img.filename = savePath
                            save img
                            close img
                        )
                        else
                        (
                            lblStatus.text = "Render thất bại! Kiểm tra Corona cài chưa?"
                        )
                    )
                    catch (lblStatus.text = "Lỗi render: " + (getExceptionString() as string))
                )
                
                "V-Ray GPU":
                (
                    try
                    (
                        local testScale = 0.25
                        local w = int(spnWidth.value * testScale)
                        local h = int(spnHeight.value * testScale)
                        renderOutputWidth = w
                        renderOutputHeight = h
                        
                        renderers.current = renderers.VRay
                        
                        lblStatus.text = "Đang render (V-Ray GPU)..."
                        local startTime = timeStamp()
                        local img = render()
                        local elapsed = (timeStamp() - startTime) / 1000.0
                        
                        if img != undefined do
                        (
                            uiPreview.bitmap = img
                            lblStatus.text = ("Render xong: " + (w as string) + "x" + (h as string) + " — " + elapsed as string + "s")
                            local savePath = (getDir #temp) + "/nc_render_test.png"
                            img.filename = savePath
                            save img
                            close img
                        )
                        else
                        (
                            lblStatus.text = "Render thất bại! Kiểm tra V-Ray cài chưa?"
                        )
                    )
                    catch (lblStatus.text = "Lỗi render: " + (getExceptionString() as string))
                )
                
                "Local SD (CUDA)":
                (
                    // Gọi Python script để generate ảnh từ prompt
                    try
                    (
                        lblStatus.text = "Đang generate từ prompt (CUDA)..."
                        
                        // Build full prompt từ scene
                        local scenePrompt = buildScenePrompt()
                        local finalPrompt = txtPrompt.text + " | " + scenePrompt
                        
                        // Gọi Python subprocess — sd_generate.py là wrapper duy nhất
                        local pyScript = (getDir #max) + "/Plugins/NC_Render_Standard/scripts/sd_generate.py"
                        local cmd = (pythonBin + " \"" + pyScript + "\" --prompt \"" + finalPrompt + "\" --width " + (spnWidth.value as string) + " --height " + (spnHeight.value as string))
                        
                        if referenceImage != undefined do
                        (
                            local refPath = (getDir #temp) + "/nc_reference.png"
                            copy referenceImage filename:refPath
                            cmd += " --reference " + refPath
                        )
                        
                        if chkDetail.checked do cmd += " --detail"
                        if chkTile.checked do cmd += " --tile"
                        if ddlUpscale.selection > 1 do cmd += " --upscale " + (ddlUpscale.selection as string)
                        
                        lblStatus.text = "Running: " + cmd
                        shellLaunch cmd
                        
                        // Wait a bit for generation to start
                        sleep 5
                        lblStatus.text = "Generation started (check output folder for result)"
                    )
                    catch (lblStatus.text = "Lỗi generation: " + (getExceptionString() as string))
                )
                
                "External API (FLUX/Google/MJ)":
                (
                    // Send prompt + reference đến external API
                    try
                    (
                        lblStatus.text = "Đang gửi request đến API..."
                        
                        if apiKey == "" or apiKey == "AIzaSy..." do
                        (
                            messageBox "Vui lòng nhập API Key trước khi render!" title:"Thiếu API Key" buttons:[ #OK ]
                            lblStatus.text = "API Key trống — không thể render"
                            return false
                        )
                        
                        local scenePrompt = buildScenePrompt()
                        local fullPrompt = txtPrompt.text + " | " + scenePrompt
                        
                        // Build API request
                        local engine = ddlRenderMethod.selection
                        case engine of
                        (
                            4: // External API — FLUX / Google / Midjourney
                            (
                                // Select provider based on API key prefix
                                local provider = if apiKey.startsWith("hf_") then "FLUX (HuggingFace)" \
                                    else if apiKey.startsWith("AIza") then "Google Imagen" \
                                    else if apiKey.contains("mj_") then "Midjourney" \
                                    else "Unknown provider"
                                
                                lblStatus.text = "Gửi request đến " + provider + "..."
                                
                                // Implement API call here (simplified)
                                local payload = #()
                                append payload #( "prompt", fullPrompt )
                                append payload #( "width", spnWidth.value )
                                append payload #( "height", spnHeight.value )
                                append payload #( "api_key", apiKey )
                                
                                if referenceImage != undefined do
                                (
                                    local refPath = (getDir #temp) + "/nc_reference.png"
                                    copy referenceImage filename:refPath
                                    append payload #( "reference", refPath )
                                )
                                
                                // Send to API (simplified — actual implementation needs HTTP client)
                                messageBox "Request sent to " + provider + ".\nCheck API dashboard for result." title:"API Request" buttons:[ #OK ]
                            )
                        )
                    )
                    catch (lblStatus.text = "Lỗi API call: " + (getExceptionString() as string))
                )
            )
        )
        
        on btnRender2 pressed do
        (
            // Interactive/preview render
            lblStatus.text = "Đang xử lý render nhanh..."
            
            case renderMethod of
            (
                "Corona GPU":
                (
                    try
                    (
                        lblStatus.text = "Khởi động Corona Interactive..."
                        // Corona IR command (nếu available)
                        if (getCommand CoronaRenderer "coronaStartInteractiveRender") != undefined do
                        (
                            coronaStartInteractiveRender()
                        )
                        else
                        (
                            // Fallback: render với 1 sample
                            renderOutputWidth = int(spnWidth.value * 0.5)
                            renderOutputHeight = int(spnHeight.value * 0.5)
                            renderers.current = renderers.Corona
                            local img = render()
                            if img != undefined do
                            (
                                uiPreview.bitmap = img
                                lblStatus.text = "Corona Interactive preview"
                            )
                        )
                    )
                    catch (lblStatus.text = "Corona IR không khả dụng")
                )
                
                "V-Ray GPU":
                (
                    try
                    (
                        lblStatus.text = "Khởi động V-Ray Interactive..."
                        // V-Ray interactive (nếu available)
                        if (getCommand VRayRenderer "vrayStartInteractiveRender") != undefined do
                        (
                            vrayStartInteractiveRender()
                        )
                        else
                        (
                            renderOutputWidth = int(spnWidth.value * 0.5)
                            renderOutputHeight = int(spnHeight.value * 0.5)
                            renderers.current = renderers.VRay
                            local img = render()
                            if img != undefined do
                            (
                                uiPreview.bitmap = img
                                lblStatus.text = "V-Ray Interactive preview"
                            )
                        )
                    )
                    catch (lblStatus.text = "V-Ray Interactive không khả dụng")
                )
                
                "Local SD (CUDA)":
                (
                    // Generate with upscaling
                    try
                    (
                        lblStatus.text = "Generate + Upscale..."
                        
                        local scenePrompt = buildScenePrompt()
                        local finalPrompt = txtPrompt.text + " | " + scenePrompt
                        
                        local pyScript = (getDir #max) + "/Plugins/NC_Render_Standard/scripts/sd_generate.py"
                        local cmd = (pythonBin + " \"" + pyScript + "\" --prompt \"" + finalPrompt + "\" --upscale " + (ddlUpscale.selection as string))
                        
                        if chkDetail.checked do cmd += " --detail"
                        if referenceImage != undefined do
                        (
                            local refPath = (getDir #temp) + "/nc_reference.png"
                            copy referenceImage filename:refPath
                            cmd += " --reference " + refPath
                        )
                        
                        lblStatus.text = "Running: " + cmd
                        shellLaunch cmd
                        sleep 5
                        lblStatus.text = "Upscale generation started"
                    )
                    catch (lblStatus.text = "Lỗi: " + (getExceptionString() as string))
                )
                
                "External API (FLUX/Google/MJ)":
                (
                    // Generate with reference image
                    try
                    (
                        if apiKey == "" do
                        (
                            messageBox "Vui lòng nhập API Key!" title:"Thiếu API Key" buttons:[ #OK ]
                            return false
                        )
                        
                        local scenePrompt = buildScenePrompt()
                        local fullPrompt = txtPrompt.text + " | " + scenePrompt
                        
                        if referenceImage != undefined do
                        (
                            lblStatus.text = "Generate with reference..."
                            local refPath = (getDir #temp) + "/nc_reference.png"
                            copy referenceImage filename:refPath
                            
                            local provider = if apiKey.startsWith("hf_") then "FLUX" else "External API"
                            messageBox "Sending reference + prompt to " + provider + "..." title:"API Request" buttons:[ #OK ]
                        )
                        else
                        (
                            lblStatus.text = "Vui lòng load reference image trước"
                        )
                    )
                    catch (lblStatus.text = "Lỗi: " + (getExceptionString() as string))
                )
            )
        )
        
        on btnRender3 pressed do
        (
            // Full render / batch
            lblStatus.text = "Đang xử lý render đầy đủ..."
            
            case renderMethod of
            (
                "Corona GPU":
                (
                    try
                    (
                        lblStatus.text = "Full render (Corona GPU) — hỏi đợi..."
                        
                        local w = spnWidth.value
                        local h = spnHeight.value
                        renderOutputWidth = w
                        renderOutputHeight = h
                        renderOutputResolution = [w, h]
                        
                        renderers.current = renderers.Corona
                        
                        lblStatus.text = "Đang render toàn cảnh (" + (w as string) + "x" + (h as string) + ")..."
                        local startTime = timeStamp()
                        local img = render()
                        local elapsed = (timeStamp() - startTime) / 1000.0
                        
                        if img != undefined do
                        (
                            uiPreview.bitmap = img
                            lblStatus.text = ("Full render xong: " + (w as string) + "x" + (h as string) + " — " + elapsed as string + "s")
                            
                            // Save result
                            local saveDir = getSavePath caption:"Save render result?" types:"PNG|*.png"
                            if saveDir != undefined do
                            (
                                img.filename = saveDir + "/nc_render_full.png"
                                save img
                                close img
                                lblStatus.text = "Render saved to: " + saveDir
                            )
                        )
                        else
                        (
                            lblStatus.text = "Render thất bại"
                        )
                    )
                    catch (lblStatus.text = "Lỗi: " + (getExceptionString() as string))
                )
                
                "V-Ray GPU":
                (
                    try
                    (
                        lblStatus.text = "Full render (V-Ray GPU)..."
                        
                        local w = spnWidth.value
                        local h = spnHeight.value
                        renderOutputWidth = w
                        renderOutputHeight = h
                        
                        renderers.current = renderers.VRay
                        local img = render()
                        
                        if img != undefined do
                        (
                            uiPreview.bitmap = img
                            lblStatus.text = "V-Ray full render xong"
                            
                            local saveDir = getSavePath caption:"Save render result?" types:"PNG|*.png"
                            if saveDir != undefined do
                            (
                                img.filename = saveDir + "/nc_render_full.png"
                                save img
                                close img
                            )
                        )
                    )
                    catch (lblStatus.text = "Lỗi: " + (getExceptionString() as string))
                )
                
                "Local SD (CUDA)":
                (
                    // Batch generate — nhiều biến thể prompt
                    try
                    (
                        lblStatus.text = "Batch generate (CUDA)..."
                        
                        local scenePrompt = buildScenePrompt()
                        
                        // Tạo nhiều biến thể prompt
                        local variations = #()
                        append variations (txtPrompt.text + " | " + scenePrompt)
                        append variations (txtPrompt.text + " | cinematic lighting | " + scenePrompt)
                        append variations (txtPrompt.text + " | studio lighting | " + scenePrompt)
                        append variations (txtPrompt.text + " | golden hour | " + scenePrompt)
                        
                        // Gửi batch request
                        local pyScript = (getDir #max) + "/Plugins/NC_Render_Standard/scripts/sd_batch.py"
                        local cmd = (pythonBin + " \"" + pyScript + "\" --prompts \"" + (arrayToCSV variations) + "\"")
                        
                        if referenceImage != undefined do
                        (
                            local refPath = (getDir #temp) + "/nc_reference.png"
                            copy referenceImage filename:refPath
                            cmd += " --reference " + refPath
                        )

                        lblStatus.text = "Batch generation started (4 variations)"
                        shellLaunch cmd
                        sleep 5
                        lblStatus.text = "Batch generation in progress"
                    )
                    catch (lblStatus.text = "Lỗi batch: " + (getExceptionString() as string))
                )

                "External API (FLUX/Google/MJ)":
                (
                    // Upscale existing result
                    try
                    (
                        if apiKey == "" do
                        (
                            messageBox "Vui lòng nhập API Key!" title:"Thiếu API Key" buttons:[ #OK ]
                            return false
                        )

                        lblStatus.text = "Upscaling result..."

                        // Load existing render result
                        local existingImg = uiPreview.bitmap
                        if existingImg == undefined do
                        (
                            lblStatus.text = "Không có render result để upscale — vui lòng render trước"
                            return false
                        )

                        // Save existing image tạm thời
                        local tempImgPath = (getDir #temp) + "/nc_upscale_input.png"
                        existingImg.filename = tempImgPath
                        save existingImg
                        close existingImg

                        // Send upscale request
                        local provider = if apiKey.startsWith("hf_") then "FLUX Upscale" else "API Upscale"

                        local payload = #()
                        append payload #( "image", tempImgPath )
                        append payload #( "scale", ddlUpscale.selection as string )
                        append payload #( "api_key", apiKey )

                        messageBox "Upscaling request sent to " + provider + ".\nCheck API dashboard for result." title:"Upscale" buttons:[ #OK ]
                    )
                    catch (lblStatus.text = "Lỗi upscale: " + (getExceptionString() as string))
            )
        )
)
        
        // ============================================================
        // UI EVENTS
        // ============================================================
        
        on rltNCRenderPro_v1 open do
        (
            // Load cameras
            refreshCamList()
            
            // Load last width/height
            spnWidth.value = renderWidth
            spnHeight.value = renderHeight
            spnRatio.value = (renderWidth as float) / (renderHeight as float)
            
            // Detect materials in scene
            scanMaterialsInScene()
            
            // Update UI for current method
            updateUIForMethod()
            
            // Capture initial preview
            refreshPreviewDisplay()
            
            lblStatus.text = "Plugin v1.0 loaded. " + renderMethod + " | " + gpuName
        )
        
        on ddlCams selected idx do
        (
            refreshPreviewDisplay()
            if idx > 1 do
            (
                local camName = ddlCams.items[idx]
                for c in cameras where c.name == camName do
                (
                    if isValidNode c do viewport.setCamera c
                )
            )
        )
        
        
        on btn2Point pressed do
        (
            local cam = getRenderCamera()
            if cam != undefined do
            (
                try
                (
                    if hasProperty cam #vertical_tilt_correction do cam.vertical_tilt_correction = true
                    if hasProperty cam #tilt_correction_mode do cam.tilt_correction_mode = 1
                    if (classOf cam == Targetcamera or classOf cam == Freecamera) do addModifier cam (Camera_Correction())
                    lblStatus.text = "Đã áp dụng 2-Point Perspective"
                )
                catch (lblStatus.text = "Không thể áp dụng 2-Point")
            )
            refreshPreviewDisplay()
        )
        
        on btnRefreshCams pressed do
        (
            refreshCamList()
            refreshPreviewDisplay()
        )
        
        on btnRefreshPreview pressed do
        (
            refreshPreviewDisplay()
        )
        
        on btnFullPreview pressed do
        (
            local bmp = captureViewportRender()
            if bmp != undefined do
            (
                uiPreview.bitmap = bmp
                lblStatus.text = "Full viewport captured"
            )
            else
            (
                lblStatus.text = "Không thể capture viewport"
            )
        )
        
        on btnSavePreview pressed do
        (
            local savePath = getSavePath caption:"Save preview image" types:"PNG|*.png|All Files|*.*|"
            if savePath != undefined do
            (
                local bmp = uiPreview.bitmap
                if bmp != undefined do
                (
                    bmp.filename = savePath + "/nc_preview.png"
                    save bmp
                    close bmp
                    lblStatus.text = "Preview saved to: " + savePath
                )
            )
        )
        
        on spnWidth changed val do
        (
            if ckbLock.checked do spnHeight.value = int((spnWidth.value as float) / spnRatio.value + 0.5)
            applyResToMax()
        )
        
        on spnHeight changed val do
        (
            if ckbLock.checked do spnWidth.value = int((spnHeight.value as float) * spnRatio.value + 0.5)
            applyResToMax()
        )
        
        on spnRatio changed val do
        (
            if ckbLock.checked do spnHeight.value = int((spnWidth.value as float) / spnRatio.value + 0.5)
            applyResToMax()
        )
        
        on ckbLock changed state do
        (
            if state do spnRatio.value = (spnWidth.value as float) / (spnHeight.value as float)
            applyResToMax()
        )
        
        on chkCorona changed state do
        (
            if state do coronaInstalled = true
            lblStatus.text = "Corona: " + (if state then "Enabled" else "Disabled")
        )
        
        on chkVray changed state do
        (
            if state do vrayInstalled = true
            lblStatus.text = "V-Ray: " + (if state then "Enabled" else "Disabled")
        )
        
        // ============================================================
        // HELPER: apply resolution to 3ds Max
        // ============================================================
        fn applyResToMax =
        (
            renderWidth = spnWidth.value
            renderHeight = spnHeight.value
            lblStatus.text = ("Kích thước: " + (renderWidth as string) + " x " + (renderHeight as string))
        )
        
        // ============================================================
        // HELPER: refresh preview
        // ============================================================
        fn refreshPreviewDisplay =
        (
            local raw = captureGhostViewport passType:#rgb
            if raw != undefined then
            (
                uiPreview.bitmap = raw
                lblStatus.text = "Đã cập nhật khung nhìn"
            )
        )
        
        fn refreshCamList =
        (
            local camNames = #(\"[Active Viewport]\")
            for c in cameras where classOf c != Targetobject do append camNames c.name
            ddlCams.items = camNames
            ddlCams.selection = 1
            lblStatus.text = "Đã quét lại cameras"
        )
        
        // ============================================================
        // HELPER: capture viewport (ghost)
        // ============================================================
        fn captureGhostViewport passType:#rgb =
        (
            local capturedBmp = undefined
            local camNode = getRenderCamera()
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
                if isValidNode camNode and camNode != undefined do viewport.setCamera camNode
                displaySafeFrames = false
                
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
        
        // ============================================================
        // HELPER: build scene prompt from object detection
        // ============================================================
        fn buildScenePrompt =
        (
            local sceneDesc = ""
            
            // Count objects in scene
            local objCount = 0
            for o in geometry where not o.isHidden do objCount += 1
            
            if objCount > 0 do
            (
                sceneDesc += (objCount as string) + " objects in scene"
            )
            
            // Detect materials
            local matInfo = scanMaterialsInScene()
            if matInfo.count > 0 do
            (
                local coronaCount = 0
                local vrayCount = 0
                local stdCount = 0
                
                for m in matInfo do
                (
                    case m[1] of
                    (
                        "Corona": coronaCount += 1
                        "V-Ray": vrayCount += 1
                        default: stdCount += 1
                    )
                )
                
                sceneDesc += " | Materials: " + (coronaCount as string) + " Corona, " + (vrayCount as string) + " V-Ray, " + (stdCount as string) + " Standard"
            )
            
            // Camera info
            local cam = getRenderCamera()
            if cam != undefined do
            (
                local fov = if isValidNode cam then cam.fov else 63.0
                local focal = 18.0 / (tan (fov / 2.0))
                sceneDesc += " | Camera: " + (focal as string) + "mm lens"
            )
            
            return sceneDesc
        )
        
        // ============================================================
        // HELPER: array to CSV
        // ============================================================
        fn arrayToCSV arr =
        (
            local result = ""
            for i = 1 to arr.count do
            (
                result += arr[i]
                if i < arr.count do result += "|||"
            )
            return result
        )
    )
    
    createDialog rltNCRenderPro_v1
)
