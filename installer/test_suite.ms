-- test_suite.ms — kiem thu That MaxScript engine (3dsmaxbatch), truoc khi ship .mzp
-- Chay: 3dsmaxbatch.exe test_suite.ms
-- Ket qua ghi vao: D:\Program\setup 3dsmax\Plugins\NC_Render_Standard\installer\test_result.txt
-- (format->stdout khong tin cay trong batch; ghi file truc tiep)

(
    local PROJ = @"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard"
    local MCR_SRC = PROJ + "/usermacros/NC_Render_Bridge_v1.mcr"
    local MCR_DST = (getDir #usermacros) + "/NC_Render_Bridge_v1.mcr"
    local outPath = PROJ + "\\installer\\test_result.txt"

    local out = createFile outPath
    if out == undefined then ( format "CANNOT OPEN OUTPUT\n"; exit )

    fn logIt s = ( format "%\n" s to:out; flush out )

    logIt ("MAX version: " + (maxVersion())[1] as string)

    -- TEST 2: copy + macros.load
    logIt ("TEST2_macros_load: " + (try
    (
        copyFile MCR_SRC MCR_DST
        macros.load MCR_DST
        "PASS"
    ) catch ("FAIL: " + (getCurrentException() as string))))

    -- TEST 1: fileIn compile .mcr
    logIt ("TEST1_compile_mcr: " + (try ( fileIn MCR_DST; "PASS" ) catch ("FAIL: " + (getCurrentException() as string))))

    -- TEST 3: macroScript dang ky — kiem tra macros.run khong throw
    -- (khong co macros.list() kieu mang tra ve; kiem nghiem bang chinh macros.run)

    -- TEST 4: macros.run mo giao dien
    logIt ("TEST4_macros_run: " + (try
    (
        macros.run "NC-Render AI" "NCRenderSmartBridge_v1"
        "PASS (khong exception)"
    ) catch ("FAIL: " + (getCurrentException() as string))))

    -- TEST 5: primitives cua installer
    -- TEST 5: primitives cua installer — tach tung cai de dinh vi loi
    fn mk5 name expr = ( try ( expr(); "PASS" ) catch ("FAIL: " + (getCurrentException() as string)) )
    logIt ("TEST5a_findItem: " + (try ( local aa = #("x"); if ((findItem aa "x") != 1) then throw "sai"; "PASS" ) catch ("FAIL: " + (getCurrentException() as string))))
    logIt ("TEST5b_append: " + (try ( local bb = #(); append bb 1; if bb.count != 1 then throw "sai"; "PASS" ) catch ("FAIL: " + (getCurrentException() as string))))
    logIt ("TEST5c_getFiles: " + (try ( local gf = (getFiles ((getDir #usermacros) + "/NC_Render*.mcr")); if gf.count < 1 then throw "khong thay file nao"; "PASS" ) catch ("FAIL: " + (getCurrentException() as string))))
    logIt ("TEST5d_getDir_uscripts: " + (try ( local d = getDir #userScripts; if d == undefined then throw "undefined"; "PASS: " + d ) catch ("FAIL: " + (getCurrentException() as string))))
    logIt ("TEST5e_doesFileExist: " + (try ( if not (doesFileExist MCR_DST) then throw "khong thay file"; "PASS" ) catch ("FAIL: " + (getCurrentException() as string))))
    logIt ("TEST5f_addUnique: " + (try ( fn au arr val = ( if ((findItem arr val) == 0) do append arr val ); local cc = #(); au cc "x"; au cc "x"; au cc "y"; if cc.count != 2 then throw "sai"; "PASS" ) catch ("FAIL: " + (getCurrentException() as string))))

    -- TEST 6: rollout class nam trong scope macroScript — batch khong voi toi, bo qua
    logIt "TEST6_destroy: SKIP (rollout class trong scope macro, batch khong access duoc)"


    -- TEST 7: run_install.ms khong chua ham ma da biet
    logIt ("TEST7_installer_ghost_names: " + (try
    (
        local f = openFile (PROJ + "\\installer\\run_install.ms") mode:"r"
        local code = ""
        while not (eof f) do code += readLine f + "\n"
        close f
        local bad = #("appendIfNotFound", "appendIfUnique", "appendUnique", "macros.reload")
        local hits = 0
        for b in bad do ( if ((findString code b) != undefined) do hits += 1 )
        if hits == 0 then "PASS (sach ham ma)" else ("FAIL: " + (hits as string) + " ham ma con sot")
    ) catch ("FAIL: " + (getCurrentException() as string))))

    logIt "TEST_DONE"
    close out
)
