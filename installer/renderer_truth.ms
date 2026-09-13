(
    local out = "D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/installer/renderer_truth.txt"
    local f = createFile out
    format "A renderers.count=%\n" (try (renderers.count as string) catch ("EXC:" + (getCurrentException() as string))) to:f
    format "B renderers[5]=%\n" (try (classOf renderers[5] as string) catch ("EXC:" + (getCurrentException() as string))) to:f
    format "C iter for r in renderers: %\n" (try ((for r in renderers collect (classOf r as string)) as string) catch ("EXC:" + (getCurrentException() as string))) to:f
    format "D RendererClass.classes: %\n" (try ((for c in RendererClass.classes collect c) as string) catch ("EXC:" + (getCurrentException() as string))) to:f
    format "E matchPattern direct: % %\n" (matchPattern "Corona" "*Corona*") (matchPattern pattern:"*Corona*" "Corona") to:f
    close f
)
