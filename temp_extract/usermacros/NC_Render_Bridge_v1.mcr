-- NC_Render_Bridge_v1.mcr - NC-Render AI Studio
--
-- CUDA render test, API key, material detection da renderer,
-- camera consistency, upscale, reference image
--
-- Cai dat truc tiep vao userMacros directory
-- Paths relative to MZP package extraction
macroScript NCRenderSmartBridge_v1
category:"NC-Render AI"
tooltip:"NC-Render AI Studio v1.4 - CUDA + API + Multi-Renderer"
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
        -- CONFIG - loaded from config file if exists
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
    global apiKey = if config.count > 1 then config[2] else ""
    global gpuName = if config.count > 2 then config[3] else "Unknown"
    global gpuMemory = if config.count > 3 then config[4] else "0"
    global hasCUDA = if config.count > 4 then config[5] else "false"
    global coronaInstalled = if config.count > 5 then config[6] else "false"
    global vrayInstalled = if config.count > 6 then config[7] else "false"
    global pytorchCUDA = if config.count > 7 then config[8] else "false"
        -- Python interpreter co CUDA - tro toi venv Hermes Agent
    global pythonBin = "C:/Users/HOMIE/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe"
    -- Duong dan project goc (giu toan bo payload trong thu muc du an)
    global ncPluginRoot = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    global ncScriptsDir = ncPluginRoot + "/scripts/"
        -- ============================================================
        -- UI - Main rollout
        -- ============================================================
    rollout rltNCRenderPro_v1 "NC-Render AI Studio v1.0 - CUDA + API + Multi-Renderer" width:1120 height:760
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
                (renderMethod == "Corona GPU"): "[FAST] Render Test (Corona GPU)"
                (renderMethod == "V-Ray GPU"): "[FAST] Render Test (V-Ray GPU)"
                (renderMethod == "Local SD (CUDA)"): "[FAST] Generate from Prompt (CUDA)"
                (renderMethod == "OpenRouter API" or renderMethod == "Gemini API"): "[FAST] Generate via API"
            )
            btnRender2.text = case true of
            (
                (renderMethod == "Corona GPU"): "[LOOP] Corona Interactive"
                (renderMethod == "V-Ray GPU"): "[LOOP] V-Ray Interactive"
                (renderMethod == "Local SD (CUDA)"): "[LOOP] Generate + Upscale"
                (renderMethod == "OpenRouter API" or renderMethod == "Gemini API"): "[LOOP] Generate with Reference"
            )
            btnRender3.text = case true of
            (
                (renderMethod == "Corona GPU"): "[FULL] Full Render (Corona)"
                (renderMethod == "V-Ray GPU"): "[FULL] Full Render (V-Ray)"
                (renderMethod == "Local SD (CUDA)"): "[FULL] Batch Generate"
                (renderMethod == "OpenRouter API" or renderMethod == "Gemini API"): "[FULL] Upscale Result"
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
            renderWidth = spnWidth.value
            renderHeight = spnHeight.value
            lblStatus.text = ("Kich thuoc: " + (renderWidth as string) + " x " + (renderHeight as string))
        )

        fn refreshPreviewDisplay =
        (
            local raw = captureGhostViewport passType:#rgb
            if raw != undefined then
            (
                uiPreview.bitmap = raw
                lblStatus.text = "Da cap nhat khung nhin"
            )
        )

        fn refreshCamList =
        (
            local camNames = #("[Active Viewport]")
            for c in cameras where classOf c != Targetobject do append camNames c.name
            ddlCams.items = camNames
            ddlCams.selection = 1
            lblStatus.text = "Da quet lai cameras"
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
            lblRendererInfo.text = "Renderer: " + renderMethod
            btnRender1.text = renderButtons[1]
            btnRender2.text = renderButtons[2]
            btnRender3.text = renderButtons[3]
        )
        -- --- COLUMN LEFT: CONTROL PANEL ---
        -- SECTION 1: GPU & RENDERER STATUS
        groupBox grpSystem " He thong & Renderer " pos:[8, 8] width:196 height:96
        label lblGPUInfo "GPU: -" pos:[16, 24] width:180
        label lblGPUMemory "VRAM: -" pos:[16, 40] width:180
        label lblCUDAStatus "CUDA: -" pos:[16, 56] width:180
        
        local isCorona = coronaInstalled == "true"
        local isVray = vrayInstalled == "true"
        checkbox chkCorona "Corona" pos:[16, 72] width:80 height:18 checked:isCorona enabled:(isCorona or hasCUDA == "true")
        checkbox chkVray "V-Ray" pos:[100, 72] width:80 height:18 checked:isVray enabled:(isVray or hasCUDA == "true")
        -- SECTION UPDATE: Kiem tra cap nhat plugin
        groupBox grpUpdate " Plugin Update " pos:[212, 8] width:196 height:96
        label lblUpdateInfo "Phien ban hien tai: v1.0.0" pos:[220, 24] width:180
        button btnCheckUpdate "[SEARCH] Kiem tra" pos:[220, 42] width:88 height:24
        button btnDoUpdate "[v] Tai & Cai" pos:[312, 42] width:88 height:24 enabled:false
        label lblUpdateStatus "" pos:[220, 72] width:180 height:18 style_sunkenedge:true
        -- SECTION 2: CAMERA & FRAME
        groupBox grpCam " Camera & Frame " pos:[8, 112] width:400 height:118
        dropdownList ddlCams "" pos:[16, 128] width:384 height:6
        
        button btnQuickCam "+ Quick Cam" pos:[16, 152] width:92 height:24
        button btnRefreshCams "[LOOP] Refresh" pos:[112, 152] width:92 height:24
        button btn2Point "2-Point Perp" pos:[208, 152] width:92 height:24
        button btnResetCam "Reset Cam" pos:[304, 152] width:96 height:24
        
        spinner spnWidth "W" range:[64, 7680, 1920] type:#integer fieldwidth:40 pos:[16, 184] enabled:(renderMethod == "Corona GPU" or renderMethod == "V-Ray GPU")
        spinner spnHeight "H" range:[64, 7680, 1080] type:#integer fieldwidth:40 pos:[120, 184] enabled:(renderMethod == "Corona GPU" or renderMethod == "V-Ray GPU")
        spinner spnRatio "R" range:[0.1, 10.0, 1.778] type:#float scale:0.001 fieldwidth:36 pos:[220, 184] enabled:(renderMethod == "Corona GPU" or renderMethod == "V-Ray GPU")
        checkbutton ckbLock "[LOCK] L" checked:true width:24 height:20 pos:[308, 182] tooltip:"Khoa ti le khung hinh"
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
        label lblMethod "Chon phuong an render:" pos:[16, 254] width:384 height:18
        dropdownList ddlRenderMethod "" pos:[16, 274] width:316 height:6 items:#("Corona GPU (mac dinh)", "V-Ray GPU", "Local SD (CUDA)", "OpenRouter API", "Gemini API")
        button btnDefaults "Default" pos:[340, 274] width:60 height:21
        
        groupBox grpApi " API Configuration " pos:[16, 304] width:384 height:54 visible:false
        dropdownList ddlApiProvider "" pos:[24, 324] width:96 height:5 items:#("openrouter", "gemini") visible:false
        editText txtApiKey "" pos:[124, 324] width:150 height:18 visible:false passwordChar:"*" text:apiKey
        editText txtApiModel "" pos:[278, 324] width:114 height:18 visible:false
        button btnSaveApiCfg "[SAVE] Save" pos:[16, 304] width:60 height:24 visible:false
        
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
        
        button btnSavePrompt "[SAVE] Save Preset" pos:[16, 470] width:188 height:24
        button btnLoadPreset "[DIR] Load Preset" pos:[212, 470] width:188 height:24
        
        button btnDetectMaterial "[SEARCH] Quet Materials" pos:[16, 502] width:188 height:24
        button btnRefreshMat "[LOOP] Refresh" pos:[212, 502] width:188 height:24
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
        dropdownList ddlUpscale "" pos:[64, 672] width:96 height:5 items:#("1x (khong)", "2x", "4x", "8x")
        checkbutton chkDetail "Toi uu chi tiet" checked:true pos:[168, 670] width:112 height:24
        checkbutton chkTile "Tile-based" checked:true pos:[288, 670] width:112 height:24
        -- --- COLUMN RIGHT: PREVIEW ---
        groupBox grpPreview " KHUNG PREVIEW " pos:[416, 8] width:696 height:720
        bitmap uiPreview width:680 height:590 pos:[424, 24] color:(color 18 22 30)
        button btnRefreshPreview "[LOOP] Cap Nhat Viewport" pos:[424, 622] width:220 height:24
        button btnFullPreview "[CAM] Capture Viewport" pos:[652, 622] width:220 height:24
        button btnSavePreview "[SAVE] Save Preview" pos:[880, 622] width:224 height:24
        
        label lblReference "Reference (tham chieu):" pos:[424, 660] width:160 height:18
        button btnLoadRef "[DIR] Load ref" pos:[424, 680] width:100 height:24
        button btnClearRef "[DEL] Clear" pos:[528, 680] width:100 height:24
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
        label lblStatus "Trang thai: San sang." pos:[8, 736] width:1096 height:18 style_sunkenedge:true
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
                writeLine f (if ddlApiProvider != undefined then ddlApiProvider.selected else "openrouter")
                writeLine f (apiKey as string)
                writeLine f (if txtApiModel != undefined then txtApiModel.text else "google/gemini-2.5-flash-image-preview")
                writeLine f (gpuName as string)
                writeLine f (gpuMemory as string)
                writeLine f (hasCUDA as string)
                writeLine f (coronaInstalled as string)
                writeLine f (vrayInstalled as string)
                writeLine f (pytorchCUDA as string)
                close f
            ) catch()
        )

        fn ncRunPython cmdArgs outFile =
        (
            local psInfo = dotNetObject "System.Diagnostics.ProcessStartInfo" pythonBin
            psInfo.Arguments = cmdArgs
            psInfo.UseShellExecute = false
            psInfo.CreateNoWindow = true
            psInfo.RedirectStandardOutput = true
            psInfo.RedirectStandardError = true
            
            local ps = dotNetObject "System.Diagnostics.Process"
            ps.StartInfo = psInfo
            ps.Start()
            
            local timeout = if renderMethod == "Local SD (CUDA)" then 900000 else 180000
            ps.WaitForExit timeout
            
            local exitCode = -1
            try (exitCode = ps.ExitCode) catch()
            local errTail = ""
            if not ps.HasExited then
            (
                ps.Kill()
                errTail = "Process timeout"
            )
            else
            (
                local errText = ps.StandardError.ReadToEnd()
                if errText != undefined do errTail = (errText as string)
                if errTail.count > 100 do errTail = substring errTail (errTail.count - 100) 100
            )
            return #(exitCode, errTail)
        )
        -- ============================================================
        -- RENDER HANDLERS
        -- ============================================================
        
        on btnRender1 pressed do
        (
            lblStatus.text = "Dang xu ly render..."
            
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
                        
                        lblStatus.text = "Dang render (Corona GPU)..."
                        local startTime = timeStamp()
                        local img = render()
                        local elapsed = (timeStamp() - startTime) / 1000.0
                        
                        if img != undefined then
                        (
                            uiPreview.bitmap = img
                            lblStatus.text = ("Render xong: " + (w as string) + "x" + (h as string) + " - " + (elapsed as string) + "s")
                            local savePath = (getDir #temp) + "/nc_render_test.png"
                            img.filename = savePath
                            save img
                            close img
                        )
                        else lblStatus.text = "Render that bai! Kiem tra Corona cai chua?"
                    )
                    catch (lblStatus.text = "Loi render: " + (getCurrentException() as string))
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
                        
                        lblStatus.text = "Dang render (V-Ray GPU)..."
                        local startTime = timeStamp()
                        local img = render()
                        local elapsed = (timeStamp() - startTime) / 1000.0
                        
                        if img != undefined then
                        (
                            uiPreview.bitmap = img
                            lblStatus.text = ("Render xong: " + (w as string) + "x" + (h as string) + " - " + (elapsed as string) + "s")
                            local savePath = (getDir #temp) + "/nc_render_test.png"
                            img.filename = savePath
                            save img
                            close img
                        )
                        else lblStatus.text = "Render that bai! Kiem tra V-Ray cai chua?"
                    )
                    catch (lblStatus.text = "Loi render: " + (getCurrentException() as string))
                )
                
                "Local SD (CUDA)":
                (
                    try
                    (
                        lblStatus.text = "Dang generate tu prompt (CUDA)..."
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
                            try (
                                local f = openFile outFile
                                local j = readLine f
                                close f
                                local p1 = findString j "\"image\":\""
                                if p1 != undefined then (
                                    p1 += 9
                                    local p2 = findString (substring j p1 -1) "\""
                                    local pth = substring j p1 (p2-1)
                                    uiPreview.bitmap = openBitmap pth
                                    lblStatus.text = "Generate xong."
                                )
                            ) catch(lblStatus.text = "Generate done, but image load failed.")
                        ) else lblStatus.text = "Loi: " + res[2]
                    )
                    catch (lblStatus.text = "Loi generation: " + (getCurrentException() as string))
                )
                
                "OpenRouter API":
                (
                    try
                    (
                        lblStatus.text = "Dang gui request den OpenRouter API..."
                        local finalPrompt = txtPrompt.text + " | " + buildScenePrompt()
                        local pyScript = ncScriptsDir + "api_render.py"
                        local outFile = (getDir #temp) + "/nc_api_result.json"
                        local outImg = (getDir #temp) + "/nc_api_render.png"
                        local cmdArgs = ("\"" + pyScript + "\" --provider openrouter --key-from-config --prompt \"" + finalPrompt + "\" --width " + (spnWidth.value as string) + " --height " + (spnHeight.value as string) + " --output-json \"" + outFile + "\" --output \"" + outImg + "\"")
                        local res = ncRunPython cmdArgs outFile
                        if res[1] == 0 then
                        (
                            try ( uiPreview.bitmap = openBitmap outImg; lblStatus.text = "API Render xong." ) catch()
                        ) else lblStatus.text = "API Loi: " + res[2]
                    )
                    catch (lblStatus.text = "Loi API call: " + (getCurrentException() as string))
                )
                
                "Gemini API":
                (
                    try
                    (
                        lblStatus.text = "Dang gui request den Gemini API..."
                        local finalPrompt = txtPrompt.text + " | " + buildScenePrompt()
                        local pyScript = ncScriptsDir + "api_render.py"
                        local outFile = (getDir #temp) + "/nc_api_result.json"
                        local outImg = (getDir #temp) + "/nc_api_render.png"
                        local cmdArgs = ("\"" + pyScript + "\" --provider gemini --key-from-config --prompt \"" + finalPrompt + "\" --width " + (spnWidth.value as string) + " --height " + (spnHeight.value as string) + " --output-json \"" + outFile + "\" --output \"" + outImg + "\"")
                        local res = ncRunPython cmdArgs outFile
                        if res[1] == 0 then
                        (
                            try ( uiPreview.bitmap = openBitmap outImg; lblStatus.text = "API Render xong." ) catch()
                        ) else lblStatus.text = "API Loi: " + res[2]
                    )
                    catch (lblStatus.text = "Loi API call: " + (getCurrentException() as string))
                )
            )
        )
        
        on btnRender2 pressed do
        (
            lblStatus.text = "Dang xu ly render nhanh..."
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
                    ) catch (lblStatus.text = "Corona IR khong kha dung")
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
                    ) catch (lblStatus.text = "V-Ray Interactive khong kha dung")
                )
                "Local SD (CUDA)":
                (
                    try
                    (
                        lblStatus.text = "Generate + Upscale..."
                        local finalPrompt = txtPrompt.text + " | " + buildScenePrompt()
                        local pyScript = ncScriptsDir + "sd_generate.py"
                        local outFile = (getDir #temp) + "/nc_local_render.json"
                        local cmdArgs = ("\"" + pyScript + "\" --prompt \"" + finalPrompt + "\" --upscale " + (ddlUpscale.selection as string) + " --output-json \"" + outFile + "\"")
                        
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
                            try (
                                local f = openFile outFile; local j = readLine f; close f
                                local p1 = findString j "\"image\":\""
                                if p1 != undefined do (
                                    p1 += 9; local p2 = findString (substring j p1 -1) "\""
                                    uiPreview.bitmap = openBitmap (substring j p1 (p2-1))
                                    lblStatus.text = "Upscale xong."
                                )
                            ) catch()
                        ) else lblStatus.text = "Loi: " + res[2]
                    ) catch (lblStatus.text = "Loi: " + (getCurrentException() as string))
                )
                "OpenRouter API":
                (
                    lblStatus.text = "OpenRouter: Khong ho tro upscale truc tiep qua API."
                )
                "Gemini API":
                (
                    lblStatus.text = "Gemini: Khong ho tro upscale truc tiep qua API."
                )
            )
        )
        
        on btnRender3 pressed do
        (
            lblStatus.text = "Dang xu ly render day du..."
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
                        
                        lblStatus.text = "Dang render toan canh..."
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
                        ) else lblStatus.text = "Render that bai"
                    ) catch (lblStatus.text = "Loi: " + (getCurrentException() as string))
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
                    ) catch (lblStatus.text = "Loi: " + (getCurrentException() as string))
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
                        if res[1] == 0 then lblStatus.text = "Batch done." else lblStatus.text = "Loi batch: " + res[2]
                    ) catch (lblStatus.text = "Loi batch: " + (getCurrentException() as string))
                )
                "OpenRouter API":
                (
                    lblStatus.text = "OpenRouter: Khong ho tro batch."
                )
                "Gemini API":
                (
                    lblStatus.text = "Gemini: Khong ho tro batch."
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
        -- Load last width/height
            spnWidth.value = renderWidth
            spnHeight.value = renderHeight
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
                    lblStatus.text = "Da ap dung 2-Point Perspective"
                )
                catch (lblStatus.text = "Khong the ap dung 2-Point")
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
                lblStatus.text = "Khong the capture viewport"
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
            dlgNCRenderHwnd = (try (windows.getMaxHWND rltNCRenderPro_v1) catch undefined)
            if dlgNCRenderHwnd == undefined do
                format "NC-Render: createDialog ran but no window handle.
"
        )
        catch
        (
            format "NC-Render dialog FAILED: %\n" (getCurrentException())
            messageBox ("NC-Render AI cannot open:\n" + getCurrentException()) title:"NC-Render AI"
        )
    )
)
