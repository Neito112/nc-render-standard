(
    local out = "D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/installer/mp_truth.txt"
    local f = createFile out
    local r

    r = try ( matchPattern "V_Ray_6" "*Ray*" ) catch ("EXC:" + (getCurrentException() as string))
    format "A 2-arg = %\n" r to:f; flush f

    r = try ( matchPattern "*Ray*" "V_Ray_6" ) catch ("EXC:" + (getCurrentException() as string))
    format "B reversed = %\n" r to:f; flush f

    r = try ( matchPattern pattern:"*Ray*" matchString:"V_Ray_6" ) catch ("EXC:" + (getCurrentException() as string))
    format "C named both = %\n" r to:f; flush f

    r = try ( matchPattern "V_Ray_6__update_2_1" pattern:"*Ray*" ) catch ("EXC:" + (getCurrentException() as string))
    format "D str+pattern = %\n" r to:f; flush f

    r = try ( "V_Ray_6__update_2_1".match "*Ray*" ) catch ("EXC:" + (getCurrentException() as string))
    format "E dotnet-string = %\n" r to:f; flush f

    r = try ( (findString "V_Ray_6__update_2_1" "Ray") != undefined ) catch ("EXC:" + (getCurrentException() as string))
    format "F findString = %\n" r to:f; flush f

    r = try ( doesFilePatternExist = ok ) catch ("EXC:" + (getCurrentException() as string))
    format "G noop = %\n" r to:f; flush f

    close f
)
