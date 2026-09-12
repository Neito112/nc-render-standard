import re

def main():
    mcr_path = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
    with open(mcr_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_ui = """        // --- COLUMN LEFT: CONTROL PANEL ---
        
        // SECTION 1: GPU & RENDERER STATUS
        groupBox grpSystem " Hệ thống & Renderer " pos:[8, 8] width:196 height:96
        label lblGPUInfo "GPU: -" pos:[16, 24] width:180
        label lblGPUMemory "VRAM: -" pos:[16, 40] width:180
        label lblCUDAStatus "CUDA: -" pos:[16, 56] width:180
        
        local isCorona = coronaInstalled == "true"
        local isVray = vrayInstalled == "true"
        checkbox chkCorona "Corona" pos:[16, 72] width:80 height:18 checked:isCorona enabled:(isCorona or hasCUDA == "true")
        checkbox chkVray "V-Ray" pos:[100, 72] width:80 height:18 checked:isVray enabled:(isVray or hasCUDA == "true")
        
        // SECTION UPDATE: Kiểm tra cập nhật plugin
        groupBox grpUpdate " Plugin Update " pos:[212, 8] width:196 height:96
        label lblUpdateInfo "Phiên bản hiện tại: v1.0.0" pos:[220, 24] width:180
        button btnCheckUpdate "🔍 Kiểm tra" pos:[220, 42] width:88 height:24
        button btnDoUpdate "⬇ Tải & Cài" pos:[312, 42] width:88 height:24 enabled:false
        label lblUpdateStatus "" pos:[220, 72] width:180 height:18 style_sunkenedge:true
        
        // SECTION 2: CAMERA & FRAME
        groupBox grpCam " Camera & Frame " pos:[8, 112] width:400 height:118
        dropdownList ddlCams "" pos:[16, 128] width:384 height:6
        
        button btnQuickCam "+ Quick Cam" pos:[16, 152] width:92 height:24
        button btnRefreshCams "🔄 Refresh" pos:[112, 152] width:92 height:24
        button btn2Point "2-Point Perp" pos:[208, 152] width:92 height:24
        button btnResetCam "Reset Cam" pos:[304, 152] width:96 height:24
        
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
        
        // SECTION 3: RENDER METHOD SELECTION
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
        
        // SECTION 4: PROMPT & MATERIALS
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
        
        // SECTION 5: RENDER BUTTONS
        groupBox grpRender " Render & Generate " pos:[8, 586] width:400 height:60
        button btnRender1 "Render" pos:[16, 606] width:125 height:28
        button btnRender2 "Render" pos:[145, 606] width:125 height:28
        button btnRender3 "Render" pos:[274, 606] width:125 height:28
        
        // SECTION 6: QUALITY & UPSCALE
        groupBox grpQuality " Quality & Upscale " pos:[8, 654] width:400 height:56
        label lblUpscale "Upscale:" pos:[16, 674] width:48 height:18
        dropdownList ddlUpscale "" pos:[64, 672] width:96 height:5 items:#("1x (không)", "2x", "4x", "8x")
        checkbutton chkDetail "Tối ưu chi tiết" checked:true pos:[168, 670] width:112 height:24
        checkbutton chkTile "Tile-based" checked:true pos:[288, 670] width:112 height:24
        
        // --- COLUMN RIGHT: PREVIEW ---
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
        
        // SECTION 7: STATUS
        label lblStatus "Trạng thái: Sẵn sàng." pos:[8, 736] width:1096 height:18 style_sunkenedge:true
"""

    # Replace from "// --- COLUMN LEFT: CONTROL PANEL ---" to "// SECTION 7: STATUS" block inclusive
    import re
    # We will match the start marker up to just before // ============================================================
    # // HELPER FUNCTIONS
    
    start_str = "// --- COLUMN LEFT: CONTROL PANEL ---"
    end_str = "// ============================================================\n        // HELPER FUNCTIONS"
    
    start_idx = content.find(start_str)
    end_idx = content.find(end_str)
    
    if start_idx != -1 and end_idx != -1:
        new_content = content[:start_idx] + new_ui + "\n        " + content[end_idx:]
        with open(mcr_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("UI Replacement successful.")
    else:
        print("Markers not found.")
        print(f"Start found: {start_idx != -1}, End found: {end_idx != -1}")

if __name__ == "__main__":
    main()
