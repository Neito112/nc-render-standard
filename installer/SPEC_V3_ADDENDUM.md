# HANDOFF V3 — facts từ batch experiments (bổ sung SPEC_V3, đọc SAU SPEC_V3)

## EVIDENCE LOG (3dsmaxbatch, deployed file = ...ENU/usermacros/NC_Render AI-NCRenderSmartBridge_v1.mcr, md5 6d5cf3fd-era + bản hiện tại)

1. Dialog giờ MỞ ĐƯỢC: macros.run ở block N → block N+1 `classof rltNCRenderPro_v1 = RolloutClass`, createDialog trả OK. (Tối đa hoá file thành nhiều block `(...)` kế tiếp khi test — tên macro chỉ resolve ở block SAU.)
2. Detector trong `on rltNCRenderPro_v1 open` CHẠY ĐÚNG: H6 `corona=true vray=true` với patterns "*Corona*" và "*Ray*" (class THẬT trên máy này: `Corona`, `V_Ray_GPU_6__update_2_1`, `V_Ray_6__update_2_1`, `Arnold`, `ART_Renderer`... qua `RendererClass.classes`). `renderers` struct KHÔNG có .count/.iter — dùng `RendererClass.classes`.
3. `matchPattern` chữ ký đúng là `matchPattern <string> pattern:"<glob>"` (thử sai: `matchPattern "s" "g"` → Argument count error wanted 1 got 2). Đã dùng đúng trong ncRendererPresent/ncSetRenderer.
4. GÁN RENDERER: `renderers.current = Corona` (class) → "Unable to convert: Corona to type: Renderer". ĐÚNG: `renderers.current = Corona()` hoặc `hit[1]()` — ncSetRenderer đã dùng `hit[1]()`.
5. CRITICAL BATCH FACT: gán `rltNCRenderPro_v1.ddlRenderMethod.selection = 4` từ batch KHÔNG fire `on ddlRenderMethod selected` handler → method vẫn "Corona GPU", grpApi.visible=false. Đây là limitation của harness, không phải bằng chứng GUI fail. ĐỂ TEST ĐƯỜNG GUI THẬT, hoặc: (a) gửi Windows message vào HWND dropdown: `local ddlH = windows.getChildHWND 0 ...` (traverse dialog's children — `windows.getChildrenHWND`, tìm theo class "#ComboBox32"), dùng `windows.sendMessage h 0x0143 3 0` (CB_SETCURSEL=0x0143, chọn idx 0-based) HOẶC `0x0111` WM_COMMAND với code CBN_SELCHANGE(1) vào cha của nó; hoặc (b) expose 1 fn macro-scope `ncApplyMethodIdx` CHỨA TOÀN BỘ logic đổi method (validate installed → renderMethod=ncMethodFromIdx → lblStatus → updateUIForMethod → saveNcConfig), handler `on ddlRenderMethod selected` CHỈ GỌI fn đó; fn đặt ở rollout-scope sau widgets THÌ batch không gọi xuyên rollout được — NÊN thay vì fn rollout, đổi 1 GLOBAL fn: khai `global ncApplyMethodIdx` ngay TRƯỚC rollout (fn không tham chiếu widget trực tiếp — nó set `renderMethod` global rồi GỌI `updateUIForMethod` BẰNG CÁCH... updateUIForMethod là rollout fn!). Giải pháp cuối cùng đơn giản NHẤT: `on rltNCRenderPro_v1 open do` + `on ddlRenderMethod selected` đều gọi updateUIForMethod() như hiện tại, VÀ thêm đồng bộ ở đầu updateUIForMethod: TỰ SUY renderMethod TỪ selection (renderMethod = ncMethodFromIdx ddlRenderMethod.selection) thay vì tin global. Khi đó batch test chỉ cần: (1) set .selection trong block, (2) block SAU gọi `destroyDialog rltNCRenderPro_v1` rồi `createDialog rltNCRenderPro_v1` (tái mở = on open → updateUIForMethod đọc selection ĐÚNG), kiểm grpApi.visible + renderMethod. Đây là test contract mới.

## FIX LIST (làm hết, theo thứ tự)

A. updateUIForMethod (dòng ~708): thêm DÒNG ĐẦU `local idx = ddlRenderMethod.selection; if idx != undefined and idx > 0 do renderMethod = ncMethodFromIdx idx` (single source of truth = selection; global renderMethod luôn phản chiếu dropdown). Giữ nguyên visibility/button-text logic bên dưới.
B. on ddlRenderMethod selected: đơn giản thành validate-installed (idx 1/2 cần coronaInstalled/vrayInstalled) rồi updateUIForMethod + saveNcConfig (bỏ case gán renderMethod trùng lặp).
C. btnDefaults: targetIdx theo corona→1/vray→2/else 4; GIỜ VI SAO NÓ "không hoạt động": nó set selection + renderMethod nhưng nếu Corona chưa detect (file config cũ coronaInstalled=false) thì rơi else 4 = OpenRouter — detection đã chạy ở open nên OK. VẤN ĐỀ THẬT: check `on btnDefaults pressed` KHÔNG có guard — đảm bảo nó set selection TRƯỚC rồi updateUIForMethod (A sẽ re-sync từ selection). Thêm `lblStatus.text = "Đã chọn mặc định: " + renderMethod`.
D. V-Ray test-render branch (btnRender1 case "V-Ray GPU" + 2 interactive/full branches): hiện vẫn `renderers.current = renderers.VRay` ở 1 số chỗ? grep `renderers.VRay` và `renderers.Corona` — PHẢI = 0 kết quả; tất cả qua ncSetRenderer("*Ray*")/("*Corona*"), fail → lblStatus + revert selection 3.
E. Config loader guard: dòng 1 config renderMethod có thể lệch dropdown (vd "OpenRouter API" nhưng selection=1 default). Trong on create hoặc open TRƯỚC updateUIForMethod: `ddlRenderMethod.selection = (case renderMethod of (...))` (viết if/else chuỗi) để dialog mở đúng method đã lưu.
F. Bọc TOÀN BỘ on open (đã có) — giữ.

## TEST CONTRACT (cập nhật installer/test_v3.ms theo block-split pattern ĐANG CHẠY ĐƯỢC — xem file hiện tại làm mẫu, mỗi block 1 cặp (...) và tf=open mode:"a" đã create ở block 1)

1. fileIn deployed mcr + macros.run  (block 1)
2. createDialog rltNCRenderPro_v1 (block 2)
3. destroyDialog (block 3)  [đóng để on open không ăn config cũ giữa chừng]
4. set selection=4 (block 4)
5. createDialog (block 5) → doc tf: H renderMethod PHẢI "OpenRouter API", grpApi.visible=true, txtApiKey.visible=true, btnSaveApiCfg.visible=true, spnWidth.enabled=true
6. destroyDialog; set selection=1 (block 6)
7. createDialog (block 7) → grpApi.visible=false; set selection=2 (block 8); destroyDialog; createDialog (block 9) → method "V-Ray GPU", curRenderer classOf chứa "V_Ray"
8. btnDefaults: block — set selection=3; destroyDialog; createDialog; rồi GIẢ LẬP nút defaults bằng windows.sendMessage CBN CLICK? NEU kho: boc logic defaults thanh fn rollout `ncApplyDefaults` va goi... batch voi rollout fn = EXC → CHAP NHAN: kiem tra defaults qua doc code co tu (coronaInstalled→1) HOAC test bang cach mo file config = rỗng trưóc batch (config corona=true sau open; defaults handler set selection=1...). DUOC PHEP: T3_DEFAULTS ghi "PASS-VIA-CODE-PATH (handler reads live globals set by detection in open)".
9. In ket qua + listener khong duoc co "OPEN_FAIL".

## PIPELINE
parencheck → build_mzp → deploy (zip, CRLF→LF) → test_v3.ms (contract tren) → probe_open2.ms sach. Sau đó ghi ket qua test_v3_result.txt vaou log agy in ra.
