# SPEC V3 — FIX 3 BUGS: method-flow / V-Ray error / API row hidden / btnDefaults dead

PROJECT: NC-Render AI Studio v1.6.3 (dialog now opens fine — DO NOT regress that).
FILE: usermacros/NC_Render_Bridge_v1.mcr (rollout rltNCRenderPro_v1, width:1120 height:760).
SCOPE: usermacros/NC_Render_Bridge_v1.mcr ONLY (you may also read installer/* probes).

## ARCHITECTURE RULES ALREADY TRUE — KEEP THEM (violating = dialog silently dies again)
- Inside the rollout body: ALL widget declarations first, then ALL `fn`s (callee-before-caller),
  then `on ... create`, `on ... open`, then other handlers. Never move a fn above a widget decl.
- Widget declaration params = literals only (no runtime vars in checked:/text:/enabled:/visible:).
- No bare `local x = ...` statements at rollout body level between widget declarations.
- No `case ... of (1:"a", 2:"b")` comma single-line syntax. Use if/else.
- `on rltNCRenderPro_v1 open` black-box (ocStep try/catch + OPEN_FAIL format) MUST stay.
- global `ncReferenceImage` is the reference holder (NOT a rollout-local).

## BUG 1 — "đổi render method chưa nhận đúng luồng"

Current: `fn updateUIForMethod` does `spnWidth.enabled = isRenderEngine` (only Corona/V-Ray get W/H/R
enabled). BUT Local SD / OpenRouter / Gemini branches all READ spnWidth.value/spnHeight.value for the
python call — user cannot set size in AI modes = broken flow.
FIX:
1. spnWidth/spnHeight/spnRatio/ckbLock stay ENABLED in ALL methods (delete the .enabled lines
   entirely — resolution is meaningful for every path).
2. `on ddlRenderMethod selected idx` currently sets renderMethod + updateUIForMethod + save — verify
   each branch also syncs API widgets when entering API mode: txtApiKey.text := apiKey (unless user
   already typed — keep simple: always refresh), txtApiModel.text := apiModel, ddlApiProvider from
   apiProvider. Factor that sync into a fn `syncApiWidgets` and call it from updateUIForMethod
   (it already handles visibility) — one place only.
3. ddlRatio handler sets spnHeight from ratio — must respect ckbLock (only auto-adjust height when
   ckbLock.checked).

## BUG 2 — "sang V-Ray báo lỗi"

Current: render branches execute `renderers.current = renderers.VRay` → on machines without V-Ray:
"Unknown property VRay..." surfaces in lblStatus (user sees it as plugin error). Corona path has same
latent risk. ALSO: `coronaInstalled`/`vrayInstalled` are never DETECTED at runtime — they come from
config with default "false", so the system lies both ways.
FIX:
1. Add rollout fn `ncRendererPresent clsPattern` → returns bool:
   `(local hit = for rr in renderers where matchPattern (classOf rr as string) clsPattern collect rr; hit.count > 0)`
   (class name substrings on this machine: Corona → "Corona*", V-Ray → "VRay*"; iterate the real
   `renderers` Map — print the class names of all renderers to your test log once to confirm patterns
   before hardcoding).
2. In `on rltNCRenderPro_v1 create`: run detection and set the globals:
   `global coronaInstalled = (if ncRendererPresent "Corona*" then "true" else "false")` and same for
   vrayInstalled with "VRay*". Then chkCorona.checked/.enabled from them (keep literal-safe: assign
   inside create, not in declaration).
3. Everywhere `renderers.current = renderers.VRay` / `renderers.Corona` appears (3 V-Ray + 2 Corona
   spots incl. interactive branches), replace with guarded resolution helper:
   `fn ncSetRenderer clsPattern = (local hit = for rr in renderers where matchPattern (classOf rr as string) clsPattern collect rr; if hit.count > 0 then (renderers.current = hit[1]; true) else false)`
   If it returns false → set `lblStatus.text = "V-Ray khong duoc cai dat — chuyen qua che do khac"`
   and DO NOT call render(). Also auto-revert ddlRenderMethod.selection to 3 (Local SD) in that case.
4. V-Ray not installed should ALSO be reflected in the dropdown UX: when ddlRenderMethod selection==2
   and vrayInstalled=="false" → immediately warn in status bar and do not keep it as stored default.
   (Do NOT remove the dropdown item — user may install V-Ray later.)

## BUG 3 — "chọn API nhưng dòng key/model không hiện" + btnDefaults chết

3a. API row invisible: updateUIForMethod sets .visible=true on grpApi + 4 children when isApi — user
reports nothing appears. First PROVE/DISPROVE empirically with a batch test (below), then fix with
whichever mechanism actually works in Max 2024 rollout:
   - Candidate A: `groupBox` + children visible toggling DOES work — then find why not (compare string:
     renderMethod exact "OpenRouter API" vs stored config line mismatch e.g. trailing spaces — fix
     with ncTrim on comparison sides).
   - Candidate B: visible toggling unreliable → switch strategy: ALWAYS-visible API row but fully
     `enabled:false` + grayed for non-API modes, and additionally set its `height` trick NO — simplest
     robust: visible toggling on children only if A fails.
   Whatever works, the end user MUST see: provider dropdown + key field + model field + Save button
   under the Render Method group when an API method is selected.
3b. btnDefaults dead: it checks coronaInstalled=="true" — always "false" because detection never ran
(Bug2.2 fixes the data). ALSO its first two branches set .selection but updateUIForMethod is only in
else-branch inside the parens (structural slip). Rewrite handler body: determine target idx
(corona→1, vray→2, else 4), set global renderMethod string accordingly (mirror the same mapping in
ONE fn `ncMethodFromIdx idx` used by both ddl-selected and defaults to kill drift), then ONE call to
updateUIForMethod + saveNcConfig at the end (outside the if-chain). Also sync ddlApiProvider selection
from apiProvider there via syncApiWidgets.

## TEST HARNESS YOU MUST BUILD & RUN (this is the contract, no hand-waving)

Create installer/test_v3.ms (MaxScript) that in 3dsmaxbatch:
1. fileIn the DEPLOYED macro file (path C:/Users/HOMIE/AppData/Local/Autodesk/3dsMax/2024 - 64bit/ENU/usermacros/NC_Render AI-NCRenderSmartBridge_v1.mcr)
2. macros.run "NC-Render AI" "NCRenderSmartBridge_v1"; assert classof rltNCRenderPro_v1 == RolloutClass
   and (try createDialog guard) — dialog must exist: `local dlgHwnd = windows.getChildHWND 0 (title of rltNCRenderPro_v1)`  (title literal "NC-Render AI Studio v1.0 — CUDA + API + Multi-Renderer" — if em-dash breaks matching, use dotNet form or match by prefix; batch dialogs DO create).
3. For idx 1..5: `rltNCRenderPro_v1.ddlRenderMethod.selection = idx` then read back:
   `rltNCRenderPro_v1.txtApiKey.visible`, `...spnWidth.enabled`, and renderMethod global string.
4. Check detection: `(classOf renderers) as string` dump + per-class `matchPattern` results, and
   coronaInstalled/vrayInstalled globals after dialog create.
5. `rltNCRenderPro_v1.btnDefaults.doPress()` (or the MaxScript way: `pressButton` — verify which API
   exists in batch; fallback: call the handler body indirectly by setting selection then re-reading)
   → assert renderMethod becomes the installed renderer (Corona on this machine = class 'Corona' present).
6. Write results line-per-assertion to installer/test_v3_result.txt (forward slashes, `to:` file handle;
   batch stdout is unreliable). Format `T3_<NAME>: PASS|FAIL <detail>`.
Run: "C:/Program Files/Autodesk/3ds Max 2024/3dsmaxbatch.exe" <abs test_v3.ms> ; then read result file.
MUST end with ALL PASS (no OPEN_FAIL line in -listenerlog either). Iterate code fixes until true.

## PIPELINE AFTER GREEN

1. python3 installer/parencheck.py usermacros/NC_Render_Bridge_v1.mcr → final depth=0
2. python3 build_mzp.py
3. deploy: python zipfile → read usermacros/NC_Render_Bridge_v1.mcr from NC_Render_Standard_v1.mzp,
   replace CRLF→LF, write to C:/Users/HOMIE/AppData/Local/Autodesk/3dsMax/2024 - 64bit/ENU/usermacros/NC_Render AI-NCRenderSmartBridge_v1.mcr
4. re-run probe_open2.ms → must keep P2_RUN: OK / P2_CLASS: RolloutClass / P2_CREATE: undefined-ok,
   NO OPEN_FAIL.
5. Re-run test_v3.ms once more on the DEPLOYED file (step 1 of harness uses deployed copy — it already does).

## DELIVERABLE (print at end)
- Which candidate (A/B) fixed API row + exact diff lines
- Renderer class names found on this machine (evidence for matchPattern strings)
- test_v3_result.txt content (all lines)
- probe_open2 final P2 lines
- list of every changed hunk (before→after) — keep the rollout open (no blank line storms).
