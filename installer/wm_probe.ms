(
    global tf = createFile "D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/installer/wm_result.txt"
    format "W0_INIT\n" to:tf
)
(
    fileIn @"C:\Users\HOMIE\AppData\Local\Autodesk\3dsMax\2024 - 64bit\ENU\usermacros\NC_Render AI-NCRenderSmartBridge_v1.mcr"
    local rr = try ( (macros.run "NC-Render AI" "NCRenderSmartBridge_v1") as string ) catch ("EXC:" + (getCurrentException() as string))
    format "W1_RUN: %\n" rr to:tf
)
(
    local d = try ( createDialog rltNCRenderPro_v1 ) catch ("EXC:" + (getCurrentException() as string))
    format "W2_CREATE: %\n" (d as string) to:tf
)
(
    local ro = rltNCRenderPro_v1
    local kids = try ( windows.getChildrenHWND 0 ) catch "EXC"
    -- liet ke cua so con co title trung dialog
    local dlgH = undefined
    if kids != undefined and (classof kids) == Array do
    (
        for k in kids where try (matchPattern (k[3] as string) pattern:"*NC-Render AI Studio*") catch false do dlgH = k[1]
    )
    format "W3_DLGH: %\n" (dlgH as string) to:tf
    global dlgHwndG = dlgH
)
(
    local kids = try ( windows.getChildrenHWND dlgHwndG 0 ) catch ("EXC:" + (getCurrentException() as string))
    local combos = #()
    if (classof kids) == Array do ( for k in kids where (k[2] as string) == "#32770" or matchPattern (k[2] as string) pattern:"*ComboBox*" or matchPattern (k[2] as string) pattern:"*Button*" do append combos k )
    format "W4_CHILDREN: total=%\n" (try (kids.count as string) catch (kids as string)) to:tf
    if (classof kids) == Array do ( for k in kids do format "  child: %\n" (k as string) to:tf )
    global kidsG = kids
)
(
    format "W9_DONE\n" to:tf
    close tf
)
