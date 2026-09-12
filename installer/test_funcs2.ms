-- test_funcs2.ms — khong dung 'ignore' (ignore cung la ham ma!)
(
    local PROJ = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    local out = createFile (PROJ + "\\installer\\test_funcs2.txt")
    fn logIt s = ( format "%\n" s to:out; flush out )

    local r1 = try ( local v = trim " x "; "TON TAI -> " + v ) catch ("HAM MA: " + (getCurrentException() as string))
    local r2 = try ( local v = trimString " x "; "TON TAI -> " + v ) catch ("HAM MA: " + (getCurrentException() as string))
    local r3 = try ( local v = filterString "a:b:c" ":"; "TON TAI -> count=" + (v.count as string) ) catch ("HAM MA: " + (getCurrentException() as string))
    local r4 = try ( local s2 = "abc"; local v = findString s2 "b"; "TON TAI -> " + (v as string) ) catch ("HAM MA: " + (getCurrentException() as string))
    local r5 = try ( local s2 = "abc"; local v = substring s2 1 2; "TON TAI -> " + v ) catch ("HAM MA: " + (getCurrentException() as string))
    local r6 = try ( local v = matchPattern "abc" pattern:"a*"; "TON TAI -> " + (v as string) ) catch ("HAM MA: " + (getCurrentException() as string))
    local r7 = try ( local s2 = "ABC"; local v = toLower s2; "TON TAI -> " + v ) catch ("HAM MA: " + (getCurrentException() as string))
    local r8 = try ( local s2 = "a_mj_b"; local v = (findString s2 "mj_") != undefined; "findString-based contains -> " + (v as string) ) catch ("HAM MA: " + (getCurrentException() as string))
    local r9 = try ( local s2 = "abc"; local v = s2.count; "string.count -> " + (v as string) ) catch ("HAM MA: " + (getCurrentException() as string))
    local r10 = try ( local s2 = "abc"; local v = s2[1]; "string index -> " + (v as string) ) catch ("HAM MA: " + (getCurrentException() as string))

    logIt ("trim:        " + r1)
    logIt ("trimString:  " + r2)
    logIt ("filterString:" + r3)
    logIt ("findString:  " + r4)
    logIt ("substring:   " + r5)
    logIt ("matchPattern:" + r6)
    logIt ("toLower:     " + r7)
    logIt ("contains via findString: " + r8)
    logIt ("string.count:" + r9)
    logIt ("string index:" + r10)
    logIt "FUNCS2_DONE"
    close out
)
