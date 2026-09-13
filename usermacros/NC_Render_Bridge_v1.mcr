-- NC_Render_Bridge_v1.mcr — NC-Render AI Studio
--
-- CUDA render test, API key, material detection đa renderer,
-- camera consistency, upscale, reference image
--
-- Cài đặt trực tiếp vào userMacros directory
-- Paths relative to MZP package extraction
macroScript NCRenderSmartBridge_v1
category:"NC-Render AI"
tooltip:"NC-Render AI Studio v1.4 — CUDA + API + Multi-Renderer"
buttonText:"NC-Render v1"
icon:#("NC_Render", 1)
(
    global rltNCRenderPro_v1
    -- Helper tu viet, thay ham ma da duoc 3dsmaxbatch kiem chung:
    --   trim / trimString : KHONG ton tai trong MaxScript
    --   "abc".startsWith() / .contains() : kieu JS, KHONG ton tai
    global ncTrim
    global ncStartsWith
    global ncContains
    global ncHas
    fn ncTrim s =
    (
        local t = s as string
        while t.count > 0 and (t[1] == " " or t[1] == "\t") do t = substring t 2 -1
        while t.count > 0 and (t[t.count] == " " or t[t.count] == "\t") do t = substring t 1 (t.count - 1)
        t
    )
    fn ncStartsWith s pre =
    (
        local a = s as string
        local b = pre as string
        if a.count < b.count then false else ((substring a 1 b.count) == b)
    )
    fn ncContains s sub =
    (
        (findString (s as string) (sub as string)) != undefined
    )
    fn ncHas s sub =
    (
        (findString (s as string) (sub as string)) != undefined
    )
    try (destroyDialog rltNCRenderPro_v1) catch()
        -- ============================================================
        -- CONFIG — loaded from config file if exists
        -- ============================================================
    global configFile = (getDir #temp) + "/nc_render_config.txt"
    local config = #()
    if doesFileExist configFile then
    (
        local f = openFile configFile
        while not eof f do append config (ncTrim (readLine f))
        close f
    )
    
    global renderMethod = if config.count > 0 then config[1] else "Corona GPU"
    global apiProvider = if config.count > 1 then config[2] else "openrouter"
    global apiKey = if config.count > 2 then config[3] else ""
    global apiModel = if config.count > 3 then config[4] else "google/gemini-2.5-flash-image-preview"
    global gpuName = if config.count > 4 then config[5] else "Unknown"
    global gpuMemory = if config.count > 5 then config[6] else "0"
    global hasCUDA = if config.count > 6 then config[7] else "false"
    global coronaInstalled = if config.count > 7 then config[8] else "false"
    global vrayInstalled = if config.count > 8 then config[9] else "false"
    global pytorchCUDA = if config.count > 9 then config[10] else "false"
    global renderWidth = 1920
    global renderHeight = 1080
        -- Python interpreter có CUDA — trỏ tới venv Hermes Agent
    global pythonBin = "C:/Users/HOMIE/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe"
    -- Duong dan project goc (giu toan bo payload trong thu muc du an)
    global ncPluginRoot = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    global ncScriptsDir = ncPluginRoot + "/scripts/"
        -- ============================================================
        -- UI — Main rollout
        -- ============================================================
    rollout rltNCRenderPro_v1 "NC-Render AI Studio v1.0 — CUDA + API + Multi-Renderer" width:1120 height:760
    (
        -- Gan text dong sau khi tao widget (rollout clause can string literal)

        -- ===== HELPERS hoisted TRUOC handler dau tien: fn phai duoc dinh nghia
        --        truoc khi on open/pressed chay (clause order = execution order) =====

        fn updateUIForMethod =
        (
        -- Enable/disable controls based on render method
            local isRenderEngine = (renderMethod == "Corona GPU" or renderMethod == "V-Ray GPU")
            local isAIConcept = (renderMethod == "Local SD (CUDA)" or renderMethod == "OpenRouter API" or renderMethod == "Gemini API")
            
            spnWidth.enabled = isRenderEngine
            spnHeight.enabled = isRenderEngine
            spnRatio.enabled = isRenderEngine
            ckbLock.enabled = isRenderEngine
            
            if grpApi != undefined do
            (
                local isApi = (renderMethod == "OpenRouter API" or renderMethod == "Gemini API")
                grpApi.visible = isApi
                ddlApiProvider.visible = isApi
                txtApiKey.visible = isApi
                txtApiModel.visible = isApi
                btnSaveApiCfg.visible = isApi
            )
        -- Update button texts
            btnRender1.text = case true of
            (
                (renderMethod == "Corona GPU"): "⚡ Render Test (Corona GPU)"
                (renderMethod == "V-Ray GPU"): "⚡ Render Test (V-Ray GPU)"
                (renderMethod == "Local SD (CUDA)"): "⚡ Generate from Prompt (CUDA)"
                (renderMethod == "OpenRouter API" or renderMethod == "Gemini API"): "⚡ Generate via API"
            )
            btnRender2.text = case true of
            (
                (renderMethod == "Corona GPU"): "🔄 Corona Interactive"
                (renderMethod == "V-Ray GPU"): "🔄 V-Ray Interactive"
                (renderMethod == "Local SD (CUDA)"): "🔄 Generate + Upscale"
                (renderMethod == "OpenRouter API" or renderMethod == "Gemini API"): "🔄 Generate with Reference"
            )
            btnRender3.text = case true of
            (
                (renderMethod == "Corona GPU"): "🚀 Full Render (Corona)"
                (renderMethod == "V-Ray GPU"): "🚀 Full Render (V-Ray)"
                (renderMethod == "Local SD (CUDA)"): "🚀 Batch Generate"
                (renderMethod == "OpenRouter API" or renderMethod == "Gemini API"): "🚀 Upscale Result"
            )
            
            lblStatus.text = "Render method: " + renderMethod
        )

        fn scanMaterialsInScene =
        (
            local allMats = #()
        -- Detect Corona materials
            try
            (
                for m in getClassInstances CoronaMaterial where isValidNode m do
                (
                    local info = #("Corona", m.name, m)
                    append allMats info
                )
            ) catch ()
        -- Detect V-Ray materials
            try
            (
                for m in getClassInstances VRayMtl where isValidNode m do
                (
                    local info = #("V-Ray", m.name, m)
                    append allMats info
                )
            ) catch ()
        -- Detect standard materials
            for m in objects where isValidNode m and classOf m == Material do
            (
                local className = classOf(m) as string
                if className == "Standard" or className == "PhysicalMaterial" or className == "Multimaterial" then
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
            if idx > 1 then
            (
                local camName = ddlCams.items[idx]
                if camName != "[Active Viewport]" then
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

        fn applyResToMax =
        (
            global renderWidth = spnWidth.value as integer
            global renderHeight = spnHeight.value as integer
            lblStatus.text = ("Kích thước: " + (renderWidth as string) + " x " + (renderHeight as string))
        )

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
            local camNames = #("[Active Viewport]")
            for c in cameras where classOf c != Targetobject do append camNames c.name
            ddlCams.items = camNames
            ddlCams.selection = 1
            lblStatus.text = "Đã quét lại cameras"
        )

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

        fn buildScenePrompt =
        (
            local sceneDesc = ""
        -- Count objects in scene
            local objCount = 0
            for o in geometry where not o.isHidden do objCount += 1
            
            if objCount > 0 then
            (
                sceneDesc += (objCount as string) + " objects in scene"
            )
        -- Detect materials
            local matInfo = scanMaterialsInScene()
            if matInfo.count > 0 then
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
        -- Camera info
            local cam = getRenderCamera()
            if cam != undefined then
            (
                local fov = if isValidNode cam then cam.fov else 63.0
                local focal = 18.0 / (tan (fov / 2.0))
                sceneDesc += " | Camera: " + (focal as string) + "mm lens"
            )
            
            return sceneDesc
        )

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
        on rltNCRenderPro_v1 create do
        (
            lblGPUInfo.text = "GPU: " + gpuName
            lblGPUMemory.text = "VRAM: " + gpuMemory + " MB"
            lblCUDAStatus.text = "CUDA: " + (if hasCUDA == "true" then "Active" else "Not available")
            -- btnRender texts gan trong open (updateUIForMethod)
        )
        -- --- COLUMN LEFT: CONTROL PANEL ---
        -- SECTION 1: GPU & RENDERER STATUS
        groupBox grpSystem " Hệ thống & Renderer " pos:[8, 8] width:196 height:96
        label lblGPUInfo "GPU: -" pos:[16, 24] width:180
        label lblGPUMemory "VRAM: -" pos:[16, 40] width:180
        label lblCUDAStatus "CUDA: -" pos:[16, 56] width:180
        
        local isCorona = coronaInstalled == "true"
        local isVray = vrayInstalled == "true"
        checkbox chkCorona "Corona" pos:[16, 72] width:80 height:18 checked:isCorona enabled:(isCorona or hasCUDA == "true")
        checkbox chkVray "V-Ray" pos:[100, 72] width:80 height:18 checked:isVray enabled:(isVray or hasCUDA == "true")
        -- SECTION UPDATE: Kiểm tra cập nhật plugin
        groupBox grpUpdate " Plugin Update " pos:[212, 8] width:196 height:96
        label lblUpdateInfo "Phiên bản hiện tại: v1.0.0" pos:[220, 24] width:180
        button btnCheckUpdate "🔍 Kiểm tra" pos:[220, 42] width:88 height:24
        button btnDoUpdate "⬇ Tải & Cài" pos:[312, 42] width:88 height:24 enabled:false
        label lblUpdateStatus "" pos:[220, 72] width:180 height:18 style_sunkenedge:true

        on btnDoUpdate pressed do
        (
            lblUpdateStatus.text = "Đang tải bản cập nhật..."
            btnDoUpdate.enabled = false
            btnCheckUpdate.enabled = false
            try
            (
                local statusFile = (getDir #temp) + "/nc_update_status.txt"
                local pyScript = ncScriptsDir + "github_update.py"
                local userMacros = (getDir #userMacros)
                local cmd = (pythonBin + " \"" + pyScript + "\" --download --current-version v1.0.0 --user-macros \"" + userMacros + "\" > \"" + statusFile + "\"")
                shellLaunch cmd
                -- Đợi cấp tải xong (up to 60s)
                local waited = 0
                while not doesFileExist statusFile and waited < 60 do
                (
                    sleep 1
                    waited += 1
                )
                if doesFileExist statusFile then
                (
                    local f = openFile statusFile
                    local content = ""
                    while not eof f do content += (readLine f) + "\n"
                    close f
                    if ncHas content "updated" and ncHas content "true" then
                    (
                        lblUpdateStatus.text = "✅ Cập nhật thành công — khởi động lại 3ds Max để áp dụng"
                        btnDoUpdate.enabled = false
                        btnCheckUpdate.enabled = false
                    )
                    else if ncHas content "error" then
                    (
                        lblUpdateStatus.text = "❌ Lỗi cập nhật — xem log"
                        btnCheckUpdate.enabled = true
                    )
                    else if ncHas content "up_to_date" then
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
                lblUpdateStatus.text = "Lỗi: " + (getCurrentException() as string)
                btnCheckUpdate.enabled = true
            )
        )

        on btnCheckUpdate pressed do
        (
            lblUpdateStatus.text = "Đang kiểm tra..."
            btnDoUpdate.enabled = false
            try
            (
                local statusFile = (getDir #temp) + "/nc_update_status.txt"
                local pyScript = ncScriptsDir + "github_update.py"
                -- Gọi Python, redirect output ra file
                local cmd = (pythonBin + " \"" + pyScript + "\" --check-only --current-version v1.0.0 --json > \"" + statusFile + "\"")
                shellLaunch cmd
                -- Đợi process kết thúc (timeout 15s)
                local waited = 0
                while not doesFileExist statusFile and waited < 15 do
                (
                    sleep 1
                    waited += 1
                )
                if doesFileExist statusFile then
                (
                    local f = openFile statusFile
                    local content = ""
                    while not eof f do content += (readLine f) + "\n"
                    close f
                    -- Parse simple: kiểm tra keywords trong output JSON
                    if ncHas content "up_to_date" and ncHas content "true" then
                    (
                        lblUpdateStatus.text = "✅ Bạn đang dùng phiên bản mới nhất"
                        btnDoUpdate.enabled = false
                    )
                    else if ncHas content "update_available" and ncHas content "true" then
                    (
                        lblUpdateStatus.text = "📦 CÓ bản cập nhật — nhấn \"Tải & Cài đặt\""
                        btnDoUpdate.enabled = true
                    )
                    else if ncHas content "error" then
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
                lblUpdateStatus.text = "Lỗi: " + (getCurrentException() as string)
                btnDoUpdate.enabled = false
            )
        )
        -- SECTION 2: CAMERA & FRAME
        groupBox grpCam " Camera & Frame " pos:[8, 112] width:400 height:118
        dropdownList ddlCams "" pos:[16, 128] width:384 height:6
        
        button btnQuickCam "+ Quick Cam" pos:[16, 152] width:92 height:24
        button btnRefreshCams "🔄 Refresh" pos:[112, 152] width:92 height:24
        button btn2Point "2-Point Perp" pos:[208, 152] width:92 height:24
        button btnResetCam "Reset Cam" pos:[304, 152] width:96 height:24

        on btnQuickCam pressed do
        (
            -- Tao camera ngay tai goc nhin viewport hien tai (viewPos/viewDir/viewUp: bien toan cuc Max)
            local n = 1
            while (getNodeByName ("NC_Cam" + (n as string))) != undefined do n += 1
            local cam = FreeCamera pos:viewPos name:("NC_Cam" + (n as string))
            cam.dir = viewDir
            max.viewCamera = cam
            refreshCamList()
            lblStatus.text = "Camera: " + cam.name
        )
        
        on btnResetCam pressed do
        (
            -- Bo camera gan vao viewport, tra ve goc nhin tu do
            try ( viewport.setCamera undefined ) catch()
            refreshCamList()
            lblStatus.text = "Da reset ve viewport hien tai"
        )
        
        spinner spnWidth "W" range:[64, 7680, 1920] type:#integer fieldwidth:40 pos:[16, 184] enabled:(renderMethod == "Corona GPU" or renderMethod == "V-Ray GPU")
        spinner spnHeight "H" range:[64, 7680, 1080] type:#integer fieldwidth:40 pos:[120, 184] enabled:(renderMethod == "Corona GPU" or renderMethod == "V-Ray GPU")
        spinner spnRatio "R" range:[0.1, 10.0, 1.778] type:#float scale:0.001 fieldwidth:36 pos:[220, 184] enabled:(renderMethod == "Corona GPU" or renderMethod == "V-Ray GPU")
        checkbutton ckbLock "🔒 L" checked:true width:24 height:20 pos:[308, 182] tooltip:"Khóa tỉ lệ khung hình"
        dropdownList ddlRatio "" pos:[336, 182] width:64 height:5 items:#("16:9", "4:3", "5:4", "3:2", "2:1", "1:1", "9:16")
        
        on ddlRatio selected idx do
        (
            local item = ddlRatio.items[idx]
            local parts = (filterString item ":")
            if parts.count == 2 then
            (
                local w = (parts[1] as integer) as float
                local h = (parts[2] as integer) as float
                spnRatio.value = w / h
                spnHeight.value = int((spnWidth.value as float) / spnRatio.value + 0.5)
            )
        )
        -- SECTION 3: RENDER METHOD SELECTION
        groupBox grpRenderMethod " Render Method " pos:[8, 238] width:400 height:132
        label lblMethod "Chọn phương án render:" pos:[16, 254] width:384 height:18
        dropdownList ddlRenderMethod "" pos:[16, 274] width:316 height:6 items:#("Corona GPU (mặc định)", "V-Ray GPU", "Local SD (CUDA)", "OpenRouter API", "Gemini API")
        button btnDefaults "Default" pos:[340, 274] width:60 height:21
        
        groupBox grpApi " API Configuration " pos:[16, 304] width:384 height:54 visible:false
        dropdownList ddlApiProvider "" pos:[24, 324] width:96 height:5 items:#("openrouter", "gemini") visible:false
        editText txtApiKey "" pos:[124, 324] width:150 height:18 visible:false passwordChar:"*" text:apiKey
        editText txtApiModel "" pos:[278, 324] width:114 height:18 visible:false
        button btnSaveApiCfg "💾 Save" pos:[16, 304] width:60 height:24 visible:false
        
        on ddlRenderMethod selected idx do
        (
            case idx of
            (
                1: renderMethod = "Corona GPU"
                2: renderMethod = "V-Ray GPU"
                3: renderMethod = "Local SD (CUDA)"
                4: renderMethod = "OpenRouter API"
                5: renderMethod = "Gemini API"
            )
            lblStatus.text = "Render method: " + renderMethod
            updateUIForMethod()
            if saveNcConfig != undefined do saveNcConfig()
        )
        
        on btnDefaults pressed do
        (
            if isCorona then
            (
                renderMethod = "Corona GPU"
                ddlRenderMethod.selection = 1
            )
            else if isVray then
            (
                renderMethod = "V-Ray GPU"
                ddlRenderMethod.selection = 2
            )
            else
            (
                renderMethod = "OpenRouter API"
                ddlRenderMethod.selection = 4
                updateUIForMethod()
            )
            lblStatus.text = "Render method: " + renderMethod
            updateUIForMethod()
            if saveNcConfig != undefined do saveNcConfig()
        )
        
        on btnSaveApiCfg pressed do
        (
            apiKey = txtApiKey.text
            if saveNcConfig != undefined do saveNcConfig()
            lblStatus.text = "API Key and config saved."
        )
        
        on ddlApiProvider selected idx do
        (
            if idx == 1 then txtApiModel.text = "google/gemini-2.5-flash-image-preview"
            else txtApiModel.text = "gemini-2.5-flash-image"
        )
        -- SECTION 4: PROMPT & MATERIALS
        groupBox grpPrompt " Prompt & Materials " pos:[8, 378] width:400 height:200
        edittext txtPrompt "" text:"modern architectural interior, natural soft daylight, photorealistic, 8k, architectural digest" pos:[16, 394] width:384 height:70
        
        button btnSavePrompt "💾 Save Preset" pos:[16, 470] width:188 height:24
        button btnLoadPreset "📂 Load Preset" pos:[212, 470] width:188 height:24
        
        button btnDetectMaterial "🔍 Quét Materials" pos:[16, 502] width:188 height:24
        button btnRefreshMat "🔄 Refresh" pos:[212, 502] width:188 height:24
        listbox lstMaterials "" pos:[16, 532] width:384 height:3
        
        on btnDetectMaterial pressed do
        (
            local mats = scanMaterialsInScene()
            if mats.count > 0 then
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
        
        on btnRefreshMat pressed do
        (
            local mats = scanMaterialsInScene()
            if mats.count > 0 then
            (
                lstMaterials.items = for m in mats collect m.name
                lstMaterials.selection = 1
                lblStatus.text = "Refreshed: " + (mats.count as string) + " materials"
            )
            else
            (
                lstMaterials.items = #("(khong co material trong scene)")
                lblStatus.text = "No materials detected"
            )
        )
        
        on btnSavePrompt pressed do
        (
            local name = inputBox "Preset name:" "Save prompt preset" "my_prompt"
            if name != undefined and name != "" then
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
            if files.count > 0 then
            (
                local selected = getOpenFileName caption:"Select prompt preset" types:"Prompt Presets|*.txt|" filename:(files[1])
                if selected != undefined then
                (
                    local f = openFile selected
                    txtPrompt.text = readLine f
                    local methodLine = readLine f
                    if methodLine != "" then
                    (
                        case (ncTrim methodLine) of
                        (
                            "Corona GPU": ddlRenderMethod.selection = 1
                            "V-Ray GPU": ddlRenderMethod.selection = 2
                            "Local SD (CUDA)": ddlRenderMethod.selection = 3
                            "OpenRouter API": ddlRenderMethod.selection = 4
                            "Gemini API": ddlRenderMethod.selection = 5
                        )
                        renderMethod = ncTrim methodLine
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
        -- SECTION 5: RENDER BUTTONS
        groupBox grpRender " Render & Generate " pos:[8, 586] width:400 height:60
        button btnRender1 "Render" pos:[16, 606] width:125 height:28
        button btnRender2 "Render" pos:[145, 606] width:125 height:28
        button btnRender3 "Render" pos:[274, 606] width:125 height:28
        -- SECTION 6: QUALITY & UPSCALE
        groupBox grpQuality " Quality & Upscale " pos:[8, 654] width:400 height:56
        label lblUpscale "Upscale:" pos:[16, 674] width:48 height:18
        dropdownList ddlUpscale "" pos:[64, 672] width:96 height:5 items:#("1x (không)", "2x", "4x", "8x")
        checkbutton chkDetail "Tối ưu chi tiết" checked:true pos:[168, 670] width:112 height:24
        checkbutton chkTile "Tile-based" checked:true pos:[288, 670] width:112 height:24
        -- --- COLUMN RIGHT: PREVIEW ---
        groupBox grpPreview " KHUNG PREVIEW " pos:[416, 8] width:696 height:720
        bitmap uiPreview width:680 height:590 pos:[424, 24] color:(color 18 22 30)
        button btnRefreshPreview "🔄 Cập Nhật Viewport" pos:[424, 622] width:220 height:24
        button btnFullPreview "📷 Capture Viewport" pos:[652, 622] width:220 height:24
        button btnSavePreview "💾 Save Preview" pos:[880, 622] width:224 height:24
        
        label lblReference "Reference (tham chiếu):" pos:[424, 660] width:160 height:18
        button btnLoadRef "📁 Load ref" pos:[424, 680] width:100 height:24
        button btnClearRef "🗑 Clear" pos:[528, 680] width:100 height:24
        local referenceImage = undefined
        
        on btnLoadRef pressed do
        (
            local fname = getOpenFileName caption:"Select reference image" types:"Image Files|*.png;*.jpg;*.jpeg;*.bmp;*.tga|All Files|*.*|"
            if fname != undefined then
            (
                referenceImage = open fname
                lblStatus.text = "Reference loaded: " + (filenameFromPath fname)
            )
        )
        
        on btnClearRef pressed do
        (
            if referenceImage != undefined then
            (
                close referenceImage
                referenceImage = undefined
                lblStatus.text = "Reference cleared"
            )
        )
        -- SECTION 7: STATUS
        label lblStatus "Trạng thái: Sẵn sàng." pos:[8, 736] width:1096 height:18 style_sunkenedge:true
        -- ============================================================
        -- HELPER FUNCTIONS
        -- ============================================================
        
        fn saveNcConfig =
        (
            try
            (
                local cfgPath = (getDir #temp) + "/nc_render_config.txt"
                local f = createFile cfgPath
                writeLine f (renderMethod as string)
                writeLine f (if ddlApiProvider != undefined and ddlApiProvider.selection == 2 then "gemini" else "openrouter")
                writeLine f (apiKey as string)
                writeLine f (if txtApiModel != undefined then txtApiModel.text else apiModel)
                writeLine f (gpuName as string)
                writeLine f (gpuMemory as string)
                writeLine f (hasCUDA as string)
                writeLine f (coronaInstalled as string)
                writeLine f (vrayInstalled as string)
                writeLine f (pytorchCUDA as string)
                close f
            ) catch()
        )

        fn ncJsonImage jPath =
        (
            -- Doc JSON 1 dong {.."image":"..."}, tra ve duong dan PNG hoac undefined
            try
            (
                local f = openFile jPath
                local j = ""
                while not eof f do j += readLine f
                close f
                local key = "\"image\": \""
                local p1 = findString j key
                if p1 == undefined then ( key = "\"image\":\""; p1 = findString j key )
                if p1 == undefined then undefined
                else (
                    p1 += key.count
                    local p2 = findString (substring j p1 -1) "\""
                    if p2 == undefined then undefined else (substring j p1 (p2 - 1))
                )
            ) catch undefined
        )
        
        fn ncRunPython cmdArgs outFile =
        (
            -- Sync python chay co timeout; xu ly het pipe TRUOC WaitForExit de tranh pipe deadlock.
            -- tra ve #(exitCode, errTail)
            local psi = dotNetObject "System.Diagnostics.ProcessStartInfo"
            psi.FileName = pythonBin
            psi.Arguments = cmdArgs
            psi.UseShellExecute = false
            psi.CreateNoWindow = true
            psi.RedirectStandardOutput = true
            psi.RedirectStandardError = true
            local ps = dotNetClass "System.Diagnostics.Process"
            local proc = ps.Start psi
            local deadline = (dotNetClass "System.DateTime").Now.AddMilliseconds (if renderMethod == "Local SD (CUDA)" then 900000.0 else 180000.0)
            local outSb = dotNetObject "System.Text.StringBuilder"
            local errSb = dotNetObject "System.Text.StringBuilder"
            local drained = false
            while not drained do
            (
                local so = proc.StandardOutput
                local se = proc.StandardError
                local c1 = so.Read()
                local c2 = se.Read()
                if c1 >= 0 do outSb.Append ((dotNetClass "System.Char").ConvertFromInt32 c1)
                if c2 >= 0 do errSb.Append ((dotNetClass "System.Char").ConvertFromInt32 c2)
                if c1 < 0 and c2 < 0 then
                (
                    if proc.WaitForExit 100 then drained = true
                    if (dotNetClass "System.DateTime").Now > deadline do
                    (
                        try ( proc.Kill() ) catch()
                        drained = true
                    )
                )
            )
            local code = -1
            try ( code = proc.ExitCode ) catch ( code = -2 )
            local err = errSb.ToString()
            local out = outSb.ToString()
            if code != 0 and err != undefined and err.count < 3 do err = out
            if err == undefined do err = ""
            local tail = if err.count > 300 then (substring err (err.count - 299) 300) else err
            return #(code, tail)
        )
        -- ============================================================
        -- RENDER HANDLERS
        -- ============================================================
        
        on btnRender1 pressed do
        (
            lblStatus.text = "Đang xử lý render..."
            
            case renderMethod of
            (
                "Corona GPU":
                (
                    try
                    (
                        local testScale = 0.25
                        local w = int(spnWidth.value * testScale)
                        local h = int(spnHeight.value * testScale)
                        renderOutputWidth = w
                        renderOutputHeight = h
                        renderOutputResolution = [w, h]
                        
                        renderers.current = renderers.Corona
                        
                        lblStatus.text = "Đang render (Corona GPU)..."
                        local startTime = timeStamp()
                        local img = render()
                        local elapsed = (timeStamp() - startTime) / 1000.0
                        
                        if img != undefined then
                        (
                            uiPreview.bitmap = img
                            lblStatus.text = ("Render xong: " + (w as string) + "x" + (h as string) + " — " + (elapsed as string) + "s")
                            local savePath = (getDir #temp) + "/nc_render_test.png"
                            img.filename = savePath
                            save img
                            close img
                        )
                        else lblStatus.text = "Render thất bại! Kiểm tra Corona cài chưa?"
                    )
                    catch (lblStatus.text = "Lỗi render: " + (getCurrentException() as string))
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
                        
                        if img != undefined then
                        (
                            uiPreview.bitmap = img
                            lblStatus.text = ("Render xong: " + (w as string) + "x" + (h as string) + " — " + (elapsed as string) + "s")
                            local savePath = (getDir #temp) + "/nc_render_test.png"
                            img.filename = savePath
                            save img
                            close img
                        )
                        else lblStatus.text = "Render thất bại! Kiểm tra V-Ray cài chưa?"
                    )
                    catch (lblStatus.text = "Lỗi render: " + (getCurrentException() as string))
                )
                
                "Local SD (CUDA)":
                (
                    try
                    (
                        lblStatus.text = "Đang generate từ prompt (CUDA)..."
                        local scenePrompt = buildScenePrompt()
                        local finalPrompt = txtPrompt.text + " | " + scenePrompt
                        
                        local pyScript = ncScriptsDir + "sd_generate.py"
                        local outFile = (getDir #temp) + "/nc_local_render.json"
                        local cmdArgs = ("\"" + pyScript + "\" --prompt \"" + finalPrompt + "\" --width " + (spnWidth.value as string) + " --height " + (spnHeight.value as string) + " --output-json \"" + outFile + "\"")
                        
                        if referenceImage != undefined then
                        (
                            local refPath = (getDir #temp) + "/nc_reference.png"
                            copy referenceImage filename:refPath
                            cmdArgs += " --reference \"" + refPath + "\""
                        )
                        
                        if chkDetail.checked do cmdArgs += " --detail"
                        if chkTile.checked do cmdArgs += " --tile"
                        if ddlUpscale.selection > 1 do cmdArgs += " --upscale " + (ddlUpscale.selection as string)
                        
                        local res = ncRunPython cmdArgs outFile
                        if res[1] == 0 then
                        (
                            local pth = ncJsonImage outFile
                            if pth != undefined and doesFileExist pth then
                            (
                                uiPreview.bitmap = openBitmap pth
                                lblStatus.text = "Generate xong: " + pth
                            )
                            else lblStatus.text = "Xong nhung khong doc duoc anh tu JSON"
                        ) else lblStatus.text = "Loi: " + res[2]
                    )
                    catch (lblStatus.text = "Lỗi generation: " + (getCurrentException() as string))
                )
                
                "OpenRouter API":
                (
                    try
                    (
                        lblStatus.text = "Đang gửi request đến OpenRouter API..."
                        local finalPrompt = txtPrompt.text + " | " + buildScenePrompt()
                        local pyScript = ncScriptsDir + "api_render.py"
                        local outFile = (getDir #temp) + "/nc_api_result.json"
                        local outImg = (getDir #temp) + "/nc_api_render.png"
                        local cmdArgs = ("\"" + pyScript + "\" --provider openrouter --key-from-config --prompt \"" + finalPrompt + "\" --width " + (spnWidth.value as string) + " --height " + (spnHeight.value as string) + " --output-json \"" + outFile + "\" --output \"" + outImg + "\"")
                        local res = ncRunPython cmdArgs outFile
                        if res[1] == 0 then
                        (
                            try ( uiPreview.bitmap = openBitmap outImg; lblStatus.text = "API Render xong." ) catch()
                        ) else lblStatus.text = "API Lỗi: " + res[2]
                    )
                    catch (lblStatus.text = "Lỗi API call: " + (getCurrentException() as string))
                )
                
                "Gemini API":
                (
                    try
                    (
                        lblStatus.text = "Đang gửi request đến Gemini API..."
                        local finalPrompt = txtPrompt.text + " | " + buildScenePrompt()
                        local pyScript = ncScriptsDir + "api_render.py"
                        local outFile = (getDir #temp) + "/nc_api_result.json"
                        local outImg = (getDir #temp) + "/nc_api_render.png"
                        local cmdArgs = ("\"" + pyScript + "\" --provider gemini --key-from-config --prompt \"" + finalPrompt + "\" --width " + (spnWidth.value as string) + " --height " + (spnHeight.value as string) + " --output-json \"" + outFile + "\" --output \"" + outImg + "\"")
                        local res = ncRunPython cmdArgs outFile
                        if res[1] == 0 then
                        (
                            try ( uiPreview.bitmap = openBitmap outImg; lblStatus.text = "API Render xong." ) catch()
                        ) else lblStatus.text = "API Lỗi: " + res[2]
                    )
                    catch (lblStatus.text = "Lỗi API call: " + (getCurrentException() as string))
                )
            )
        )
        
        on btnRender2 pressed do
        (
            lblStatus.text = "Đang xử lý render nhanh..."
            case renderMethod of
            (
                "Corona GPU":
                (
                    try
                    (
                        if (getCommand CoronaRenderer "coronaStartInteractiveRender") != undefined then coronaStartInteractiveRender()
                        else
                        (
                            renderOutputWidth = int(spnWidth.value * 0.5)
                            renderOutputHeight = int(spnHeight.value * 0.5)
                            renderers.current = renderers.Corona
                            local img = render()
                            if img != undefined do (uiPreview.bitmap = img; lblStatus.text = "Corona Interactive preview")
                        )
                    ) catch (lblStatus.text = "Corona IR không khả dụng")
                )
                "V-Ray GPU":
                (
                    try
                    (
                        if (getCommand VRayRenderer "vrayStartInteractiveRender") != undefined then vrayStartInteractiveRender()
                        else
                        (
                            renderOutputWidth = int(spnWidth.value * 0.5)
                            renderOutputHeight = int(spnHeight.value * 0.5)
                            renderers.current = renderers.VRay
                            local img = render()
                            if img != undefined do (uiPreview.bitmap = img; lblStatus.text = "V-Ray Interactive preview")
                        )
                    ) catch (lblStatus.text = "V-Ray Interactive không khả dụng")
                )
                "Local SD (CUDA)":
                (
                    try
                    (
                        lblStatus.text = "Generate + Upscale..."
                        local finalPrompt = txtPrompt.text + " | " + buildScenePrompt()
                        local pyScript = ncScriptsDir + "sd_generate.py"
                        local outFile = (getDir #temp) + "/nc_local_render.json"
                        local cmdArgs = ("\"" + pyScript + "\" --prompt \"" + finalPrompt + "\" --width " + (spnWidth.value as string) + " --height " + (spnHeight.value as string) + " --upscale " + (ddlUpscale.selection as string) + " --output-json \"" + outFile + "\"")
                        
                        if chkDetail.checked do cmdArgs += " --detail"
                        if referenceImage != undefined then
                        (
                            local refPath = (getDir #temp) + "/nc_reference.png"
                            copy referenceImage filename:refPath
                            cmdArgs += " --reference \"" + refPath + "\""
                        )
                        local res = ncRunPython cmdArgs outFile
                        if res[1] == 0 then
                        (
                            local pth = ncJsonImage outFile
                            if pth != undefined and doesFileExist pth then
                            (
                                uiPreview.bitmap = openBitmap pth
                                lblStatus.text = "Upscale xong: " + pth
                            )
                            else lblStatus.text = "Xong nhung khong doc duoc anh tu JSON"
                        ) else lblStatus.text = "Loi: " + res[2]
                    ) catch (lblStatus.text = "Lỗi: " + (getCurrentException() as string))
                )
                "OpenRouter API":
                (
                    lblStatus.text = "OpenRouter: Không hỗ trợ upscale trực tiếp qua API."
                )
                "Gemini API":
                (
                    lblStatus.text = "Gemini: Không hỗ trợ upscale trực tiếp qua API."
                )
            )
        )
        
        on btnRender3 pressed do
        (
            lblStatus.text = "Đang xử lý render đầy đủ..."
            case renderMethod of
            (
                "Corona GPU":
                (
                    try
                    (
                        local w = spnWidth.value
                        local h = spnHeight.value
                        renderOutputWidth = w
                        renderOutputHeight = h
                        renderOutputResolution = [w, h]
                        renderers.current = renderers.Corona
                        
                        lblStatus.text = "Đang render toàn cảnh..."
                        local startTime = timeStamp()
                        local img = render()
                        local elapsed = (timeStamp() - startTime) / 1000.0
                        
                        if img != undefined then
                        (
                            uiPreview.bitmap = img
                            lblStatus.text = ("Full render xong: " + (elapsed as string) + "s")
                            local saveDir = getSavePath caption:"Save render result?" types:"PNG|*.png"
                            if saveDir != undefined do
                            (
                                img.filename = saveDir + "/nc_render_full.png"
                                save img
                                close img
                            )
                        ) else lblStatus.text = "Render thất bại"
                    ) catch (lblStatus.text = "Lỗi: " + (getCurrentException() as string))
                )
                "V-Ray GPU":
                (
                    try
                    (
                        local w = spnWidth.value
                        local h = spnHeight.value
                        renderOutputWidth = w
                        renderOutputHeight = h
                        renderers.current = renderers.VRay
                        local img = render()
                        
                        if img != undefined then
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
                    ) catch (lblStatus.text = "Lỗi: " + (getCurrentException() as string))
                )
                "Local SD (CUDA)":
                (
                    try
                    (
                        lblStatus.text = "Batch generate (CUDA)..."
                        local scenePrompt = buildScenePrompt()
                        local variations = #()
                        append variations (txtPrompt.text + " | " + scenePrompt)
                        append variations (txtPrompt.text + " | cinematic lighting | " + scenePrompt)
                        append variations (txtPrompt.text + " | studio lighting | " + scenePrompt)
                        append variations (txtPrompt.text + " | golden hour | " + scenePrompt)
                        
                        local pyScript = ncScriptsDir + "sd_generate.py"
                        local outFile = (getDir #temp) + "/nc_batch_out.json"
                        local cmdArgs = ("\"" + pyScript + "\" --prompts \"" + (arrayToCSV variations) + "\"")
                        
                        if referenceImage != undefined then
                        (
                            local refPath = (getDir #temp) + "/nc_reference.png"
                            copy referenceImage filename:refPath
                            cmdArgs += " --reference \"" + refPath + "\""
                        )
                        local res = ncRunPython cmdArgs outFile
                        if res[1] == 0 then lblStatus.text = "Batch done." else lblStatus.text = "Lỗi batch: " + res[2]
                    ) catch (lblStatus.text = "Lỗi batch: " + (getCurrentException() as string))
                )
                "OpenRouter API":
                (
                    lblStatus.text = "OpenRouter: Không hỗ trợ batch."
                )
                "Gemini API":
                (
                    lblStatus.text = "Gemini: Không hỗ trợ batch."
                )
            )
        )
        -- ============================================================
        -- UI EVENTS
        -- ============================================================
        
        on rltNCRenderPro_v1 open do
        (
        -- Load cameras
            refreshCamList()
        -- Load last width/height (renderWidth/renderHeight do applyResToMax giu trong lan chay truoc)
            spnWidth.value = (if renderWidth == undefined then 1920 else renderWidth)
            spnHeight.value = (if renderHeight == undefined then 1080 else renderHeight)
            txtApiKey.text = apiKey
            txtApiModel.text = apiModel
            ddlApiProvider.selection = (if apiProvider == "gemini" then 2 else 1)
            spnRatio.value = (renderWidth as float) / (renderHeight as float)
        -- Detect materials in scene
            scanMaterialsInScene()
        -- Update UI for current method
            updateUIForMethod()
        -- Capture initial preview
            refreshPreviewDisplay()
            
            lblStatus.text = "Plugin v1.0 loaded. " + renderMethod + " | " + gpuName
        )
        
        on ddlCams selected idx do
        (
            refreshPreviewDisplay()
            if idx > 1 then
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
            if cam != undefined then
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
            if bmp != undefined then
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
            if savePath != undefined then
            (
                local bmp = uiPreview.bitmap
                if bmp != undefined then
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
        -- ============================================================
        -- HELPER: apply resolution to 3ds Max
        -- ============================================================
        -- ============================================================
        -- HELPER: refresh preview
        -- ============================================================
        -- ============================================================
        -- HELPER: capture viewport (ghost)
        -- ============================================================
        -- ============================================================
        -- HELPER: build scene prompt from object detection
        -- ============================================================
        -- ============================================================
        -- HELPER: array to CSV
        -- ============================================================
    )
    
    on execute do
    (
        try
        (
            if rltNCRenderPro_v1 == undefined then
                throw "NC_Render rollout class missing (reload the .mcr)"
            createDialog rltNCRenderPro_v1
        )
        catch
        (
            format "NC-Render dialog FAILED: %\n" (getCurrentException())
            messageBox ("NC-Render AI cannot open: " + (getCurrentException() as string)) title:"NC-Render AI"
        )
    )
)
