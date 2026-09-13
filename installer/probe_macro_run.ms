(
    local out = "D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/installer/mp2.txt"
    local f = createFile out
    local r1 = try ( fileIn @"D:\Program\setup 3dsmax\Plugins\NC_Render_Standard\installer\probe_macro.ms"; "OK" ) catch ("EXC:" + (getCurrentException() as string))
    format "fileIn=% gNCFP1=%\n" r1 (try (gNCFP1 as string) catch "UNDEF") to:f; flush f
    local r2 = try ( macros.run "NC-Test" "NCFormatProbe"; "OK" ) catch ("EXC:" + (getCurrentException() as string))
    format "macros.run=% gNCFP1=%\n" r2 (try (gNCFP1 as string) catch "UNDEF") to:f; flush f
    format "gNCFP2=%\n" (try (gNCFP2 as string) catch "UNDEF") to:f; flush f
    close f
)
