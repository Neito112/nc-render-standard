# -*- coding: utf-8 -*-
"""Bao 'on open' hien hoanh + format dong loi that de Max tu khai."""
import pathlib

src = pathlib.Path("usermacros/NC_Render_Bridge_v1.mcr")
s = src.read_text(encoding="utf-8", errors="replace")

old_open = '''        on rltNCRenderPro_v1 open do
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
        )'''
assert old_open in s, "open block not found (file da doi?)"

new_open = '''        on rltNCRenderPro_v1 open do
        (
            local ocStep = "init"
            try
            (
                ocStep = "refreshCamList"
                refreshCamList()
                ocStep = "spnWidth"
                spnWidth.value = (if renderWidth == undefined then 1920 else renderWidth)
                ocStep = "spnHeight"
                spnHeight.value = (if renderHeight == undefined then 1080 else renderHeight)
                ocStep = "txtApiKey"
                txtApiKey.text = (if apiKey == undefined then "" else apiKey as string)
                ocStep = "txtApiModel"
                txtApiModel.text = (if apiModel == undefined then "" else apiModel as string)
                ocStep = "ddlApiProvider"
                ddlApiProvider.selection = (if apiProvider == "gemini" then 2 else 1)
                ocStep = "spnRatio"
                spnRatio.value = ((if renderWidth == undefined then 1920 else renderWidth) as float) / ((if renderHeight == undefined then 1080 else renderHeight) as float)
                ocStep = "scanMaterialsInScene"
                scanMaterialsInScene()
                ocStep = "updateUIForMethod"
                updateUIForMethod()
                ocStep = "refreshPreviewDisplay"
                refreshPreviewDisplay()
                lblStatus.text = "Plugin v1.0 loaded. " + renderMethod + " | " + gpuName
            )
            catch
            (
                format "OPEN_FAIL step=% ex=% src=%\\n" ocStep (getCurrentException()) (try (getCurrentException 2) catch "?")
                try ( lblStatus.text = "Open loi [" + ocStep + "]: " + (getCurrentException() as string) ) catch()
            )
        )'''

s = s.replace(old_open, new_open)
src.write_text(s, encoding="utf-8", newline="\n")
print("open handler wrapped with per-step try/catch")
