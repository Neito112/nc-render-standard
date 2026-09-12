-- test_funcs.ms — kiem tra tung ham trong danh nghi
(
    local PROJ = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    local out = createFile (PROJ + "\\installer\\test_funcs.txt")
    fn logIt s = ( format "%\n" s to:out; flush out )

    logIt ("trim:        " + (try ( ignore (trim " x "); "TON TAI") catch ("HAM MA: " + (getCurrentException() as string))))
    logIt ("trimString:  " + (try ( ignore (trimString " x "); "TON TAI") catch ("HAM MA: " + (getCurrentException() as string))))
    logIt ("filterString:" + (try ( ignore (filterString "a:b" ":"); "TON TAI") catch ("HAM MA: " + (getCurrentException() as string))))
    logIt ("str.contains:" + (try ( ignore (("abc" as string).contains "a"); "TON TAI") catch ("HAM MA: " + (getCurrentException() as string))))
    logIt ("findString:  " + (try ( ignore (findString "abc" "b"); "TON TAI") catch ("HAM MA: " + (getCurrentException() as string))))
    logIt ("matchPattern:" + (try ( ignore (matchPattern "abc" pattern:"a*"); "TON TAI") catch ("HAM MA: " + (getCurrentException() as string))))
    logIt ("toLower:     " + (try ( ignore (toLower "ABC"); "TON TAI") catch ("HAM MA: " + (getCurrentException() as string))))
    logIt ("substring:   " + (try ( ignore (substring "abc" 1 2); "TON TAI") catch ("HAM MA: " + (getCurrentException() as string))))
    logIt ("strLen:      " + (try ( ignore ("abc".count); "TON TAI") catch ("HAM MA: " + (getCurrentException() as string))))
    logIt ("getFilenameFile: " + (try ( ignore (getFilenameFile @"C:\a.txt"); "TON TAI") catch ("HAM MA: " + (getCurrentException() as string))))
    logIt ("matchPattern fn: " + (try ( ignore (matchPattern "x" pattern:"x"); "TON TAI") catch ("HAM MA: " + (getCurrentException() as string))))
    logIt "FUNCS_DONE"
    close out
)
