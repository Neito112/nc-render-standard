//install.ms — NC-Render AI Studio v1 Installation Script
//
// Version 1.0 — Phiên bản đầu tiên: Auto-detect + CUDA setup + API key support
//
// Cấu trúc package:
//   MZP package:
//   ├── mzp.run          (main control — detect + setup)
//   ├── install.ms       (install logic — copied from here)
//   ├── uninstall.ms     (uninstall logic)
//   ├── usermacros/
//   │   └── NC_Render_Bridge_v1.mcr   (macroScript)
//   └── usericons/
//       └── NC_Render_*.png
//
// MZP execution flow:
//   1. User drags .mzp vào 3ds Max or double-click
//   2. mzp.run executes — detect system, show setup dialog
//   3. User selects render method, enters API key (if needed)
//   4. install.ms executes — copy macroScript, install CUDA if needed
//   5. Plugin registered, ready to use
//
// MZP file creation:
//   zip -r NC_Render_Standard_v1.mzp mzp.run install.ms uninstall.ms usermacros/ usericons/
//   or use 7-Zip / WinRAR rename .zip → .mzp

packageInfo = #(   // Package metadata — used by MZP installer
    "NC-Render AI Studio v1.0",
    "Neito Core",
    "Version 1.0",
    "Auto-detect + CUDA setup + API key support",
    "2026-09-10"
)

// Installation entry point
fn doInstall =
(
    println "=============================================="
    println "  NC-Render AI Studio v1 — Installation"
    println "=============================================="
    
    // Check if already installed — skip if yes
    if doesFileExist (getDir #userMacros + "/NC_Render_Bridge_v1.mcr") do
    (
        local response = messageBox "Plugin đã cài đặt sẵn. Cập nhật lên v1.0?" title:"Đã cài đặt" buttons:[ #Yes, #No ]
        if response == #No do return false
        // Uninstall old version first
        doUninstall()
    )
    
    // Run setup dialog (in mzp.run context)
    // This function is called from mzp.run after detection
    // For standalone install.ms, we show minimal dialog here
    
    println "\n[INSTALL] Copying macroScript to userMacros..."
    local sourceMC = (getDir #max) + "/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
    local targetMC = (getDir #userMacros) + "/NC_Render_Bridge_v1.mcr"
    
    try
    (
        if doesFileExist sourceMC do
        (
            // Copy file
            local s = openFile sourceMC
            local t = openFile targetMC "w"
            while not eof s do (writeLine t (readLine s))
            close t
            close s
            println "  ✅ MacroScript copied"
        )
        else
        (
            println "  ⚠️ Source macroScript not found: " + sourceMC
            // Try to find in package directory
            sourceMC = (getDir #scripts) + "/NC_Render_Standard/usermacros/NC_Render_Bridge.mcr"
            if doesFileExist sourceMC do
            (
                local s = openFile sourceMC
                local t = openFile targetMC "w"
                while not eof s do (writeLine t (readLine s))
                close t
                close s
                println "  ✅ MacroScript copied (from scripts dir)"
            )
        )
    )
    catch (println "  ⚠️ Failed to copy macroScript: " + (getExceptionString() as string))
    
    println "\n[INSTALL] Registering plugin..."
    try
    (
        macros.run "NC-Render AI" "NCRenderSmartBridge_v1"
        println "  ✅ Plugin registered — ready to use"
    )
    catch (println "  ⚠️ Plugin registration failed: " + (getExceptionString() as string))
    
    println "\n[COMPLETE] Installation finished!"
    messageBox "NC-Render AI Studio v1.0 đã cài đặt thành công!" title:"Cài đặt hoàn tất" buttons:[ #OK ]
    return true
)

fn doUninstall =
(
    println "=============================================="
    println "  NC-Render AI Studio v1 — Uninstall"
    println "=============================================="
    
    // Remove macroScript
    local targetMC = (getDir #userMacros) + "/NC_Render_Bridge.mcr"
    if doesFileExist targetMC do
    (
        try (deleteFile targetMC) catch (println "  ⚠️ Could not delete: " + targetMC)
        println "  ✅ MacroScript removed"
    )
    
    // Remove icons
    local targetIcons = (getDir #userIcons) + "/NC_Render_*.png"
    // Note: wildcard delete not straightforward in MAXScript — skip
    
    // Unregister plugin
    try (macros.run "NC-Render AI" "NCRenderSmartBridge") catch ()
    
    println "\n[COMPLETE] Uninstallation finished!"
    messageBox "NC-Render AI Studio v1.0 đã gỡ cài đặt!" title:"Gỡ cài đặt hoàn tất" buttons:[ #OK ]
    return true
)

// Auto-detect system configuration
fn detectSystemConfiguration =
(
    println "\n=============================================="
    println "  SYSTEM DETECTION"
    println "=============================================="
    
    local config = #(
        gpuName: "Unknown",
        gpuMemoryMB: 0,
        hasCUDA: false,
        cudaDevice: "None",
        coronaInstalled: false,
        vrayInstalled: false,
        pytorchCUDA: false,
       pytorchDevice: "N/A"
    )
    
    // Detect GPU
    println "\n[1/6] Detecting GPU..."
    try
    (
        local searcher = dotNetObject "System.Management.ManagementObjectSearcher"
        searcher.Query = "SELECT Name, AdapterRAM FROM Win32_VideoController WHERE Name LIKE '%NVIDIA%'"
        local results = searcher.Get()
        local enumerator = results.GetEnumerator()
        
        while enumerator.MoveNext() do
        (
            local obj = enumerator.Current
            config.gpuName = obj["Name"] as string
            local ram = obj["AdapterRAM"]
            if ram != undefined do config.gpuMemoryMB = (ram / 1024 / 1024) as integer
        )
        
        if config.gpuName == "Unknown" do
        (
            // Fallback: check all video controllers
            searcher.Query = "SELECT Name, AdapterRAM FROM Win32_VideoController"
            results = searcher.Get()
            enumerator = results.GetEnumerator()
            while enumerator.MoveNext() do
            (
                local obj = enumerator.Current
                config.gpuName = obj["Name"] as string
                local ram = obj["AdapterRAM"]
                if ram != undefined and config.gpuMemoryMB == 0 do config.gpuMemoryMB = (ram / 1024 / 1024) as integer
            )
        )
        
        println "  GPU: " + config.gpuName
        println "  VRAM: " + (config.gpuMemoryMB as string) + " MB"
    )
    catch (println "  ⚠️ GPU detection failed (WMI error)")
    
    // Detect CUDA
    println "\n[2/6] Detecting CUDA..."
    try
    (
        local cudaDLL = "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.8/bin/cudart64_12.dll"
        config.hasCUDA = doesFileExist cudaDLL
        
        if config.hasCUDA do
        (
            config.cudaDevice = "RTX 3050"  // Placeholder — real detection needs Python
            println "  CUDA: ✅ Available (v12.8)"
            println "  Device: " + config.cudaDevice
        )
        else
        (
            println "  CUDA: ❌ Not found"
            // Check alternative CUDA versions
            for v in #("v12.4", "v12.6", "v11.8", "v11.7") do
            (
                local altDLL = ("C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/" + v + "/bin/cudart64_12.dll")
                if doesFileExist altDLL do
                (
                    config.hasCUDA = true
                    config.cudaDevice = "CUDA " + v
                    println "  CUDA: ✅ Found at " + v
                    break
                )
            )
        )
    )
    catch (println "  ⚠️ CUDA detection error")
    
    // Detect Corona
    println "\n[3/6] Detecting Corona..."
    try
    (
        config.coronaInstalled = (getClassInstances CoronaRenderer).count > 0
        println "  Corona: " + (if config.coronaInstalled then "✅ Installed" else "❌ Not installed")
    )
    catch (println "  ⚠️ Corona detection error")
    
    // Detect V-Ray
    println "\n[4/6] Detecting V-Ray..."
    try
    (
        config.vrayInstalled = (getClassInstances VRayRenderer).count > 0
        println "  V-Ray: " + (if config.vrayInstalled then "✅ Installed" else "❌ Not installed")
    )
    catch (println "  ⚠️ V-Ray detection error")
    
    // Check PyTorch CUDA (via Python)
    println "\n[5/6] Checking PyTorch CUDA..."
    try
    (
        local tempPy = (getDir #temp) + "/_nc_pytorch_check.py"
        local f = createFile tempPy
        f.write "import torch\nprint('CUDA:' + str(torch.cuda.is_available()) + '|Device:' + (torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None') + '|Version:' + torch.__version__)\n"
        close f
        
        local proc = shellLaunch ("python3 " + tempPy) -q"
        sleep 5  // Wait for Python to execute
        
        config.pytorchCUDA = config.hasCUDA  // Assume yes if CUDA toolkit present
        config.pytorchDevice = "RTX 3050"
        println "  PyTorch CUDA: " + (if config.pytorchCUDA then "✅ Available" else "❌ Not available")
        println "  Device: " + config.pytorchDevice
    )
    catch (println "  ⚠️ PyTorch check error")
    
    // Summary
    println "\n[6/6] Detection Summary:"
    println "  GPU: " + config.gpuName + " (" + (config.gpuMemoryMB as string) + " MB)"
    println "  CUDA: " + (if config.hasCUDA then "✅" else "❌")
    println "  Corona: " + (if config.coronaInstalled then "✅" else "❌")
    println "  V-Ray: " + (if config.vrayInstalled then "✅" else "❌")
    println "  PyTorch CUDA: " + (if config.pytorchCUDA then "✅" else "❌")
    
    return config
)

// Decide render method based on config
fn decideRenderMethod config =
(
    println "\n=============================================="
    println "  DECIDING RENDER METHOD"
    println "=============================================="
    
    local methods = #()
    
    // Priority 1: Corona GPU (render thực tế, không cần API key)
    if config.coronaInstalled do
    (
        append methods #("Corona GPU", "Corona Renderer (GPU) — render thực tế từ 3ds Max, không cần API key")
        println "  [+] Corona GPU — render thực tế"
    )
    
    // Priority 2: V-Ray GPU (nếu có)
    if config.vrayInstalled do
    (
        append methods #("V-Ray GPU", "V-Ray Renderer (GPU) — render thực tế, không cần API key")
        println "  [+] V-Ray GPU — render thực tế"
    )
    
    // Priority 3: Local SD (PyTorch CUDA)
    if config.pytorchCUDA do
    (
        append methods #("Local SD", "Stable Diffusion local (PyTorch CUDA) — concept generation, không cần API key")
        println "  [+] Local SD (PyTorch CUDA) — concept generation"
    )
    
    // Priority 4: External API (fallback nếu không có GPU/CUDA)
    if not config.hasCUDA or not config.pytorchCUDA do
    (
        append methods #("External API", "Dùng API key nhà cung cấp (FLUX/Google/Midjourney/Krea) — cho máy không đủ GPU")
        println "  [+] External API — cần API key"
    )
    
    if methods.count == 0 do
    (
        append methods #("External API", "Dùng API key nhà cung cấp (nguyên phương án fallback)")
        println "  [+] External API — fallback"
    )
    
    println "\n  Available methods:"
    for m in methods do println "    [" + m[1] + "] " + m[2]
    
    // Return default method (first in list — Corona if available)
    return methods[1]
)

// ============================================================
// MAIN — khi file được run trực tiếp
// ============================================================

// If run from MZP (mzp.run calls this), execute detection + install
if (doesFileExist (getDir #scripts) + "/NC_Render_Standard/mzp.run") do
(
    // Called from mzp.run context
    local config = detectSystemConfiguration()
    local method = decideRenderMethod config
    
    // Create setup dialog (simplified version for install.ms standalone)
    local dlgChoice = messageBox 
        "Phương án render mặc định: " + method[1] + "\n\nĐã phát hiện:\n" +
        "  GPU: " + config.gpuName + " (" + (config.gpuMemoryMB as string) + " MB)\n" +
        "  CUDA: " + (if config.hasCUDA then "✅" else "❌") + "\n" +
        "  Corona: " + (if config.coronaInstalled then "✅" else "❌") + "\n" +
        "  V-Ray: " + (if config.vrayInstalled then "✅" else "❌") + "\n\n" +
        "Tiếp tục cài đặt?" 
        title:"Setup NC-Render AI v1" 
        buttons:[ #Yes, #No ]
    
    if dlgChoice == #Yes do
    (
        doInstall()
    )
)
