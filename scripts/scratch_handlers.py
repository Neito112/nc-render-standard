import re

def main():
    mcr_path = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
    with open(mcr_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    start_str = "        on btnRender1 pressed do"
    end_str = "        // ============================================================\n        // UI EVENTS"
    
    start_idx = content.find(start_str)
    end_idx = content.find(end_str)
    
    if start_idx == -1 or end_idx == -1:
        print("Could not find handlers block.")
        return
        
    handlers_code = r"""        on btnRender1 pressed do
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
                        ) else lblStatus.text = "Lỗi: " + res[2]
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
                        ) else lblStatus.text = "Lỗi: " + res[2]
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
"""
    new_content = content[:start_idx] + handlers_code + "\n" + content[end_idx:]
    with open(mcr_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Handlers replacement successful.")

if __name__ == "__main__":
    main()
