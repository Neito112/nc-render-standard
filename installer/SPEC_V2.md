# SPEC v2 — NC-Render AI Studio: FIX MECHANISM + COMPACT UI + API CONFIG ROW

Project root (ALWAYS use absolute paths): `D:/Program/setup 3dsmax/Plugins/NC_Render_Standard`
Files you may edit:
- `usermacros/NC_Render_Bridge_v1.mcr`  (main macroScript — UI + all handlers)
- `scripts/sd_generate.py`              (local CUDA wrapper)
- NEW file `scripts/api_render.py`      (OpenRouter + Gemini HTTP client)
Reference (read-only): `installer/current_ui_block.txt` = UI declaration block as-is.

## 0. PRODUCT PURPOSE (core features this plugin MUST keep working)

NC-Render AI Studio = bridge inside 3ds Max 2024 to generate concept renders:
1. **Corona GPU / V-Ray GPU test render** (25% scale) shown in preview bitmap.
2. **Local SD (CUDA)** — calls `pythonBin scripts/sd_generate.py` (Stable Diffusion 1.5, RTX 3050).
3. **Cloud API render** — ONLY two providers now: **OpenRouter** and **Gemini** (replaces the old
   fake "External API (FLUX/Google/MJ)" path which only shows a messageBox and does nothing real).
4. Camera/frame tools, scene-prompt builder from selected objects+materials, material scan listbox,
   reference image (img2img for local; omitted for API), prompt presets save/load,
   plugin self-update via `scripts/github_update.py` (DO NOT TOUCH the update section),
   status bar. Preview column with bitmap uiPreview + Refresh/Full-Capture/Save-PNG buttons.

## 1. BROKEN MECHANISM — FACTS FOUND IN CODE (fix all)

1. **API config hidden behind inputBox**: today the key only changes via `on btnAPIKey pressed`
   → `inputBox` popup (line ~569). Requirement (user): when `ddlRenderMethod` selection is an
   API mode, a **persistent inline row** appears inside `grpRenderMethod` containing:
   `dropdownList ddlApiProvider (OpenRouter | Gemini)` + `editText txtApiKey (passwordChar:'*')`
   + `editText txtApiModel` + `button btnSaveApiCfg "💾 Save"`.
   - Row visible ONLY in API modes (`grpApi.visible = (method is API)`), hidden otherwise
     (MaxScript: use `groupBox grpApi ... ` containing the 4 widgets; toggle `.visible`).
   - `btnSaveApiCfg` writes to config (see §3) and status bar confirms; no popup dialogs.
   - `btnAPIKey` popup is REMOVED entirely.
2. **`txtPromptMaterial` is UNDEFINED** (line ~575) — dead widget reference, throws at runtime.
   Delete/replace with `lblStatus.text`.
3. **sd_generate.py flags mismatch**: macro passes `--detail`, `--tile`, `--upscale <int>` but the
   argparse defines NONE of `--detail/--tile` and `--upscale` is `action="store_true"` (no value).
   → Every Local SD generate crashes argparse. FIX: add `--detail` and `--tile`
   (`action="store_true"`, may be no-ops stored to args, forward to child tool if supported) and
   change `--upscale` to `type=int, default=1` (1 = off; 2/4 = factor). Keep `--upscale` mode call
   path working for btnRender2.
4. **`shellLaunch cmd` fire-and-forget**: Max cannot see errors/results. Replace generate paths
   (Local SD + new API) with a helper `fn ncRunPython cmdArgs, outFile` that runs:
   `dotNet Class System.Diagnostics.Process` StartInfo (FileName pythonBin, Arguments cmdArgs,
   UseShellExecute:false, CreateNoWindow:true, RedirectStandardOutput/Error) → Waitforexit(timeout
   180000 ms API / 900000 ms local SD) → returns exit code + stderr tail. On success, macro reads
   `outFile` (JSON written by python: `{"ok":true,"image":"path","message":"..."}`) and loads the
   PNG into `uiPreview.bitmap` via `openBitmap`. On failure show stderr tail in `lblStatus`
   (NO modal boxes). This helper replaces all 3 render buttons' python invocation (btnRender1 local
   branch, btnRender2 upscale branch, btnRender3 batch branch: batch keeps writing multiple files,
   status line lists count).
   - Keep Corona/V-Ray branches as direct `render()` calls (they run in-engine; do not convert).
5. **Corona/V-Ray button text map** still references removed 4th method string — update all
   `case renderMethod of` maps to the new method strings (§2).

## 2. RENDER METHOD — NEW MODEL

`ddlRenderMethod` items EXACTLY:
`#("Corona GPU (mặc định)", "V-Ray GPU", "Local SD (CUDA)", "OpenRouter API", "Gemini API")`
`renderMethod` global stores the selected STRING (no "Apply" button needed):
- Make `ddlRenderMethod` fire `on ddlRenderMethod selected idx do (...)` directly:
  set renderMethod, toggle grpApi visibility, updateUIForMethod(), save config line 1.
- Keep `btnDefaults` (auto-pick installed renderer else OpenRouter). DELETE `btnApplyMethod`
  (widget + handler) — selection is now live. Keep btnRender1/2/3 (texts updated per method):
  1/2/3 = Test render | Upscale/Ref pass | Batch/Full pass as today's Local-SD labels.
- API branches call: `pythonBin scripts/api_render.py --provider openrouter|gemini --model <txtApiModel.text> --key-from-config --prompt <escaped> --width --height --output-json <tmp>`
  (key read by api_render.py from the shared config file, NOT command line → never leaks in ps list).
- Model dropdown default per provider: OpenRouter → `google/gemini-2.5-flash-image-preview`;
  Gemini → `gemini-2.5-flash-image` ; user can edit.

## 3. CONFIG PERSISTENCE

Config stays `(getDir #temp) + "/nc_render_config.txt"` line format (order MUST stay compatible
with loader at lines ~44-65): `renderMethod | apiProvider | apiKey | apiModel | gpuName | gpuMemory
| hasCUDA | coronaInstalled | vrayInstalled | pytorchCUDA`.
Write a `fn saveNcConfig = (...)` that dumps ALL globals in that order; call it from:
method change, API save, resolution change, upscale change. Loader: extend with guards so missing
lines fall back to defaults (it already uses config.count checks — keep, add lines 2/3/4 for
provider/key/model, apiProvider default "openrouter", apiModel default per provider).
API key stored plain in temp config is ACCEPTABLE for this internal tool (note it in code comment).

## 4. scripts/api_render.py — NEW, REAL IMPLEMENTATION (stdlib urllib only, no pip deps)

CLI: `--provider {openrouter,gemini} --model STR --prompt STR [--negative STR] --width INT
--height INT [--output PATH] [--output-json PATH] [--key-from-config] [--config PATH]`
- Reads key from config file (line 3 = key, line 2 = provider, line 4 = model; if
  --key-from-config not passed, require --key).
- OpenRouter: POST `https://openrouter.ai/api/v1/chat/completions`, header
  `Authorization: Bearer <key>`, body: model + `messages:[{role:user, content: prompt +
  " — image size 1024 style architectural render"}]`, plus `"modalities":["image","text"]` —
  parse `choices[0].message.images[0].image_url.url` (base64 data URI) OR fall back to text
  content b64. 30s read timeout, on HTTP error print body to stderr + exit 1.
- Gemini: POST `https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent`
  with `?key=<key>` header `x-goog-api-key`, body `{"contents":[{"parts":[{"text": prompt}]}]}` —
  parse `candidates[0].content.parts[]` for inlineData.data (base64 png).
- Write PNG bytes to `--output` (default temp `nc_api_render.png`), write
  `--output-json` `{"ok":true,"image":"<abs path>","provider":...,"model":...,"message":"..."}`
  (on error: `{"ok":false,...,"message":<err>}` exit 1). ASCII-safe print, UTF-8 file read
  `encoding utf-8 errors replace`.
- `build_payload_from_scene` NOT needed here — prompt arrives fully built from Max.
- MUST run with `C:/Users/HOMIE/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe`
  (stdlib only → works anywhere). Self-test: `--provider openrouter` with fake key must fail
  GRACEFULLY with json ok:false (test by running it after writing, show output).

## 5. UI COMPACTNESS PASS 2 (user: "vẫn loãng")

Target: `rollout width:1120 height:760`, no dead space, 8px grid.
- Left rail 400px: grpSystem+grpUpdate side-by-side row1 (each 196w × 96h);
  grpCam (h 118: dropdown full-row, 4 small buttons one row 96w each, W/H/R spinners one row);
  grpRenderMethod (h 132: method dropdown full row 372w + btnDefaults 60w SAME row; grpApi row
  inside it: provider ddl 96w + key 150w + model 126w + save 60w SAME row; lblMethod small above);
  grpPrompt (h 200: prompt edittext 70h full-row; preset save/load 2 buttons row; material: detect
  + refresh + listbox 3 rows h ~56);
  grpRender (h 60, 3 buttons one row equal 125w); grpQuality (h 56: upscale ddl + 2 checkbuttons
  one row).
- Right preview 704w × 724h at x=416: bitmap uiPreview 688×520, toolbar 3 buttons one row under it,
  reference section INSIDE preview group (Load/Clear + path label) at group bottom.
- lblStatus full width y=736 h:18.
- Every widget keeps its EXISTING variable name (grpApi and the 4 api widgets are the ONLY new
  ones: grpApi, ddlApiProvider, txtApiKey, txtApiModel, btnSaveApiCfg; btnAPIKey and btnApplyMethod
  are the ONLY removals — also remove their handlers).
- All `on <widget>` handlers, all `fn` helpers: geometry edit must NOT break them; new handlers
  allowed for ddlApiProvider/txtApiKey/... and for ddlRenderMethod selected.

## 6. HARD CONSTRAINTS

- MaxScript only; widget captions are string literals on ONE line each; no `//` comments in NEW
  lines you write (use `--`); file UTF-8 no BOM, LF; keep `case true of` style; never name a
  variable `log`, `contains`, `trim`, or `fn`. `dropdownList` needs `items:#(...)` in declaration
  or set in handler; `editText` supports `passwordChar:"*"`.
- After editing run: `python3 installer/parencheck.py usermacros/NC_Render_Bridge_v1.mcr`
  (expect `final depth=0`) and `python3 mscheck.py` if present — fix until clean.
- Then run `python3 build_mzp.py` and deploy: copy the sanitized `usermacros/NC_Render_Bridge_v1.mcr`
  from the freshly built `.mzp` (zip entry `usermacros/NC_Render_Bridge_v1.mcr`) over
  `C:/Users/HOMIE/AppData/Local/Autodesk/3dsMax/2024 - 64bit/ENU/usermacros/NC_Render AI-NCRenderSmartBridge_v1.mcr`
  (strip \r, no BOM). Report md5.
- DO NOT touch: github_update.py, installer/, the `on execute` block at file end, the update
  section handlers btnCheckUpdate/btnDoUpdate, clean scripts.
- Keep total macroScript under 1400 lines.

## 7. DELIVERABLE SUMMARY (print at end)

5 lines: new rollout size; grpApi row spec; what replaced shellLaunch; sd_generate.py flag fix;
parencheck + build + deploy md5 result.
