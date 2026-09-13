(
    local out = "D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/installer/renderer_assign.txt"
    local f = createFile out
    local r

    r = try ( matchPattern "V_Ray_6__update_2_1" "*V_Ray*" ) catch ("EXC:" + (getCurrentException() as string))
    format "1 matchPattern src-first = %\n" r to:f; flush f

    r = try ( matchPattern pattern:"*V_Ray*" "V_Ray_6__update_2_1" ) catch ("EXC:" + (getCurrentException() as string))
    format "2 matchPattern named = %\n" r to:f; flush f

    r = try ( classOf Corona ) catch ("EXC:" + (getCurrentException() as string))
    format "3 Corona symbol = %\n" r to:f; flush f

    r = try ( classOf (Corona()) ) catch ("EXC:" + (getCurrentException() as string))
    format "4 Corona() instance = %\n" r to:f; flush f

    r = try ( renderers.current = Corona; classOf renderers.current ) catch ("EXC:" + (getCurrentException() as string))
    format "5 assign current=Corona class = %\n" r to:f; flush f

    r = try ( renderers.current = Corona(); classOf renderers.current ) catch ("EXC:" + (getCurrentException() as string))
    format "6 assign current=Corona() inst = %\n" r to:f; flush f

    r = try ( local hit = for rr in RendererClass.classes where matchPattern (rr as string) pattern:"*V_Ray*" collect rr
              if hit.count > 0 then ( renderers.current = hit[1](); classOf renderers.current ) else "no-hit" ) catch ("EXC:" + (getCurrentException() as string))
    format "7 setRenderer-style = %\n" r to:f; flush f

    close f
)
