# cuda-render-style — Tool-Driven Local Render Skill

## Tổng quan

Skill này cung cấp **tool sẵn sàng chiến** cho agent render ảnh local trên GPU NVIDIA mà không cần API key, không tốn tiền, không cần code từ đầu.

**Philosophy:** Agent gọi tool là xong — tool tự detect hardware, tự chọn model, tự xử lý lỗi, tự download model nếu cần.

## Cấu trúc

```
cuda-render-style/
├── SKILL.md                  # Documentation này
├── cuda_render_tool.py       # Main tool (render + fix + detect + clean)
├── cuda_fix_tool.py          # Standalone fix tool
└── scripts/
    ├── detect_gpu.py         # Hardware detection module
    ├── model_manager.py      # Model management (check, download, auto-select)
    └── error_handler.py      # Error handling (OOM, CUDA, missing model)
```

## Tool chính

### 1. Render Tool (`cuda_render_tool.py render`)

Sinh ảnh từ prompt local GPU. Tool tự làm tất cả.

```bash
# Cơ bản — tool tự detect, tự chọn model local, tự xử lý
python3 cuda_render_tool.py render --prompt "modern architectural interior, photorealistic, 8k"

# Cấu hình chi tiết
python3 cuda_render_tool.py render \
    --prompt "interior design" \
    --model sd15 \
    --width 512 \
    --height 512 \
    --steps 20 \
    --guidance 7.5 \
    --seed 42 \
    --output "render.png"

# Image-to-image với reference (khu vực đang phát triển)
python3 cuda_render_tool.py render \
    --prompt "architectural interior" \
    --reference "reference.png" \
    --strength 0.7 \
    --output "output.png"
```

**Tool làm gì tự động:**
- Detect hardware (GPU, VRAM, CUDA, PyTorch)
- Chọn model phù hợp theo VRAM — SD1.5 (4GB), SDXL (6GB), FLUX (8GB)
- Load model từ local cache hoặc download nếu thiếu
- Generate ảnh với settings tối ưu, xử lý OOM tự động (reduce res, retry)
- Cleanup VRAM sau generation
- Lưu metadata vào `cuda_render_config.json`

**Model đang có local (RTX 3050 8GB):**
| Model | VRAM | Status |
|-------|------|--------|
| SD 1.5 | 2.6 GB | ✅ Local Ready |
| SDXL Base | ~6 GB | ❌ Chưa tải |
| FLUX.1-schnell | ~8 GB | ❌ Chưa tải |
| FLUX.1-dev | ~8 GB | ❌ Chưa tải |

### 2. Fix Tool (`cuda_render_tool.py fix` hoặc `cuda_render_tool.py fix fix-issue <issue>`)

Chẩn đoán lỗi, kiểm tra môi trường, đưa ra command fix cụ thể.

```bash
# Chẩn đoán toàn diện
python3 cuda_render_tool.py fix diagnose

# Hoặc chạy rút gọn
python3 cuda_render_tool.py fix

# Fix specific issue
python3 cuda_render_tool.py fix fix-issue cuda     # Fix CUDA issues
python3 cuda_render_tool.py fix fix-issue oom      # Fix OOM issues
python3 cuda_render_tool.py fix fix-issue model    # Fix model issues
python3 cuda_render_tool.py fix fix-issue quality  # Fix quality issues
python3 cuda_render_tool.py fix fix-issue disk     # Fix disk space issues
```

**Tested on Neito's machine (2026-09-10):**
- GPU: NVIDIA GeForce RTX 3050 (8.0 GB VRAM)
- CUDA: v12.8 ✅
- PyTorch: 2.11.0+cu128 ✅
- Model SD1.5 local: 2617 MB ✅
- Render test: 512x512, 20 steps, 4.4s ✅

### 3. Detect Tool (`cuda_render_tool.py detect`)

Kiểm tra hardware nhanh.

```bash
python3 cuda_render_tool.py detect
```

### 4. Clean VRAM (`cuda_render_tool.py clean`)

```bash
python3 cuda_render_tool.py clean
```

## Thông số Model

| Model | Repo | VRAM Min | Đã tải local | Quality | Speed |
|-------|------|----------|--------------|---------|-------|
| SD 1.5 | `runwayml/stable-diffusion-v1-5` | 4GB | ✅ 2.6GB | Cơ bản | Nhanh (~4s/512x512) |
| SDXL Base | `stabilityai/stable-diffusion-xl-base-1.0` | 6GB | ❌ | Cao | Trung bình |
| FLUX.1-schnell | `black-forest-labs/FLUX.1-schnell` | 8GB | ❌ | Rất cao | Nhanh |
| FLUX.1-dev | `black-forest-labs/FLUX.1-dev` | 8GB | ❌ | Cao nhất | Chậm |

## Test Result (2026-09-10)

- **Render:** `test_render_v9.png` — modern architectural interior, 512x512, 20 steps, seed 42, 4.4s
- **Quality:** Photorealistic, natural soft daylight, minimalist furniture, warm oak wood ✅
- **System:** RTX 3050, CUDA 12.8, PyTorch 2.11.0+cu128, SD1.5 local ✅
- **Pipeline:** cuda_render_tool.py → detect_gpu → model_manager → error_handler → diffusers DiffusionPipeline → PNG output

### 4. Model Management (`scripts/model_manager.py`)

Quản lý model: check, download, auto-select.

```bash
# List models
python3 scripts/model_manager.py --list

# Check model
python3 scripts/model_manager.py --check sd15

# Download model
python3 scripts/model_manager.py sd15

# Auto-select và download
python3 scripts/model_manager.py --auto --download
```

### 5. VRAM Monitor (`scripts/vram_monitor.py`)

Monitor VRAM realtime.

```bash
# Check current VRAM
python3 scripts/vram_monitor.py

# Monitor for 30s
python3 scripts/vram_monitor.py --monitor

# Continuous watch
python3 scripts/vram_monitor.py --watch
```

## Thông số Model

|| Model | Repo | VRAM Minimum | Quality | Speed |
|-------|------|--------------|---------|-------|
| SD 1.5 | `runwayml/stable-diffusion-v1-5` | 4GB | Cơ bản | Nhanh (~5s/512x512) |
| SDXL Base | `stabilityai/stable-diffusion-xl-base-1.0` | 6GB | Cao | Trung bình (~20s/1024x1024) — chưa tải local |
| FLUX.1-schnell | `black-forest-labs/FLUX.1-schnell` | 8GB | Rất cao | Nhanh (~10s/1024x1024) — chưa tải local |
| FLUX.1-dev | `black-forest-labs/FLUX.1-dev` | 8GB | Cao nhất | Chậm (~40s/1024x1024) — chưa tải local |

## Prompt Library

Xem `templates/prompt_library.md` để biết prompt templates cho architecture/interior.

## Error Handling

Tool tự xử lý các lỗi phổ biến:

| Lỗi | Tool xử lý |
|-----|-----------|
| OOM (Out of Memory) | Giảm resolution, chuyển model nhỏ hơn, clean VRAM |
| CUDA not available | Báo lỗi, hướng dẫn cài PyTorch CUDA |
| Model not found | Báo lỗi, hướng dẫn download model |
| Bad quality | Gợi ý tăng steps, tăng guidance, đổi model |

## Config

Tool lưu config tại `./cuda_render_config.json`:
- GPU info, VRAM, CUDA, PyTorch
- Model path, default settings
- Last render info

## Quick Start

```bash
# 1. Chạy detect để biết môi trường
python3 cuda_render_tool.py detect

# 2. Render ảnh (tool tự làm tất cả)
python3 cuda_render_tool.py render --prompt "modern architectural interior, photorealistic, 8k"

# 3. Nếu gặp lỗi, chạy fix
python3 cuda_render_tool.py fix
```

## Agent Workflow

```
1. User yêu cầu render ảnh
2. Agent kiểm tra môi trường: python3 cuda_render_tool.py detect
3. Agent chọn model (có thể để tool tự chọn)
4. Agent build prompt (từ scene data hoặc user request)
5. Agent gọi render: python3 cuda_render_tool.py render --prompt "..."
6. Tool sinh ảnh, lưu file
7. Agent deliver ảnh cho user

Nếu lỗi:
1. Agent gọi: python3 cuda_render_tool.py fix
2. Tool hiện lỗi + command fix
3. Agent chạy command fix
4. Agent retry render
```

## Lưu ý

- Tool hoạt động trên bất kỳ NVIDIA GPU nào (không hardcode tên card).
- Tool tự chọn model theoVRAMreal.
- Tool tự download model nếu thiếu (cần internet).
- Tool xử lý OOM tự động (giảm resolution, chuyển model).
- Không cần API key — mọi thứ local, miễn phí.
- Agent không cần code từ đầu — chỉ gọi tool với args.

## File trong Skill

| File | Mô tả |
|------|-------|
| `SKILL.md` | Documentation skill |
| `cuda_render_tool.py` | Main tool (render + fix + detect + clean) |
| `cuda_fix_tool.py` | Standalone fix tool |
| `scripts/detect_gpu.py` | Hardware detection module |
| `scripts/model_manager.py` | Model management module |
| `scripts/error_handler.py` | Error handling module |
| `scripts/vram_monitor.py` | VRAM monitoring utility |
| `scripts/prompt_builder.py` | Prompt engineering helper |
| `templates/prompt_library.md` | Prompt templates cho architecture/interior |
