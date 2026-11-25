# NC-Render — patch list for the config check (VM pass, 2026-11-25)

Probe built and tested on the VM: `/tmp/nc-config-check/nc_config_check.py`
(stdlib only, own code). Real VM result: `API_ONLY`, no GPU, RAM free
~1 GB, CPU bench 6.5 s. Simulated tiers verified: RTX 3050 8 GB ->
GPU_MID, 12 GB+ -> GPU_HIGH, 6 GB -> GPU_MID, 2 GB -> GPU_TOO_SMALL,
no GPU -> API_ONLY.

## What the probe replaces

The repo's current detection is broken in three ways (read-only audit):
- `skill/cuda-render-style/cuda_render_tool.py` imports
  `detect_gpu`, `model_manager`, `error_handler` from `skill/scripts/`,
  a directory that does not exist in the repo. `detect()` therefore
  crashes on import before it can print anything.
- `mzp.run` / `install.ms` detect CUDA by checking for
  `cudart64_12.dll` and hardcode the GPU name as `"RTX 3050"`.
- `render()` only gates on `torch.cuda.is_available()` and then uses
  fixed defaults (512x512, 20 steps). It never measures speed and
  never scales model/resolution to the PC.

## Patch list (repo files, in order)

1. `skill/cuda-render-style/cuda_render_tool.py`
   - Delete the `from detect_gpu / model_manager / error_handler` import
     block at the top; import the probe instead
     (`skill/cuda-render-style/nc_config_check.py`, copy of the probe).
   - `detect()`: call the probe and print its tier, model, resolution,
     steps and expected time. Do not call the missing `get_recommendation()`.
   - `render()`: gate on `tier["local_gpu"]`, not only on PyTorch CUDA.
     Use the tier's model / width / height / steps as defaults.
     When tier is API_ONLY, print the API path and return 1 with a
     clear message instead of crashing.
   - `_diagnose()`: replace the static issue list with the probe report
     (GPU, VRAM, CUDA toolkit, PyTorch, RAM free, CPU bench).

2. `skill/cuda-render-style/scripts/` (missing — do not recreate as stubs)
   - Do NOT recreate `detect_gpu.py`, `model_manager.py`,
     `error_handler.py` as empty files. Delete all references to them:
     `cuda_render_tool.py`, `sd_generate.py`, and the SKILL.md file list.
     The probe + `scripts/_setup_download.py` (self-contained) cover
     detection and download.

3. `scripts/sd_generate.py`
   - Delete `from scripts.model_manager import ...` in
     `check_model_local()` / `get_model_path_local()`; check the local
     model directory directly with `Path.exists()`.
   - Case 4 (no CUDA): do not just exit 1. Return the probe tier and
     point at the API path (`scripts/api_render.py`).

4. `scripts/nc_cuda_render.py`
   - Remove the hard exit when CUDA is unavailable. Branch: CUDA ->
     GPU path as now; no CUDA -> refuse with the probe tier, or CPU
     opt-in only (float32, attention slicing, explicit flag).
   - Fix `OUTPUT_DIR`: `Path.home() / "AppData/Local/Temp"` creates a
     fake Windows path on Linux. Use `tempfile.gettempdir()`.

5. `scripts/cuda_auto_install.py`, `scripts/_quick_test.py`,
   `skill/cuda-render-style/_test_json_flow.py`,
   `skill/cuda-render-style/cuda_fix_tool.py`
   - Remove `import wmi` and all `C:/Program Files/NVIDIA...` DLL checks.
   - Replace every hardcoded `D:/Program/setup 3dsmax/...` and
     `C:/Users/HOMIE/...` path with a path relative to `__file__`
     (`Path(__file__).parent.parent`).
   - `_quick_test.py` must check for the weights file first and report
     "model weights missing, run _setup_download.py" instead of crashing
     on `.stat()` of a missing file.

6. `usermacros/NC_Render_Bridge_v1.mcr`
   - `pythonBin`: delete the hardcoded Hermes venv path
     (`C:/Users/HOMIE/AppData/Local/hermes/.../python.exe`). Resolve
     Python from a config file / `PATH` first, fall back to asking the user.
   - `ncPluginRoot`: delete the hardcoded `D:/Program/...` path.
     Resolve from the macro file location.
   - On open, run the probe (via a small JSON call) and show the tier +
     expected time in the status label; disable the GPU render buttons
     when tier is API_ONLY instead of letting them fail at render time.

7. `mzp.run`, `install.ms`, `installer/run_install.ms`
   - Delete the hardcoded `"RTX 3050"` device name and the DLL-existence
     CUDA check. Call the probe and show its tier in the setup dialog.

8. New file: `requirements.txt` (repo root, currently missing)
   - `torch`, `diffusers`, `transformers`, `accelerate`, `Pillow`,
     with the CUDA 12.8 index URL noted in a comment. The probe itself
     needs no dependencies.

## NOT verified in this VM pass (needs a GPU PC)

- Real CUDA tier on an NVIDIA GPU (only simulated tiers were tested).
- The `.mcr` / `.ms` installer inside 3ds Max 2024.
- SD 1.5 weights download (~4 GB) and a real render.
- `api_render.py` end-to-end (needs an OpenRouter/Gemini key; none was
  used on the VM).

## Tier table (probe logic)

| VRAM + CUDA | Tier | Model / size | Expected |
|---|---|---|---|
| >= 12 GB | GPU_HIGH | SDXL / FLUX-schnell, 1024 | ~10-20 s |
| 8-12 GB | GPU_MID | SDXL 1024, SD1.5 512 fast | ~20 s / ~4-5 s |
| 6-8 GB | GPU_MID | SDXL 1024, SD1.5 512 fast | ~20 s |
| 4-6 GB | GPU_LOW | SD1.5 512 only | ~4-5 s |
| 1-4 GB | GPU_TOO_SMALL | local GPU OFF, API only | — |
| 0 GB, RAM free >= 4 GB | API_ONLY_CPU_POSSIBLE | API; CPU opt-in only | minutes |
| 0 GB, RAM free < 4 GB | API_ONLY | API only | provider-dependent |
