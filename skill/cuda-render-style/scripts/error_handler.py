"""
error_handler.py — Error handling module for cuda_render_tool.py

Xử lý các lỗi phổ biến: OOM, CUDA error, missing model.
Cung cấp hàm safe_generate với retry và fallback.
"""

import torch
import time
from pathlib import Path


def handle_oom_error(error, model_key=None, current_width=512, current_height=512):
    """
    Xử lý Out-Of-Memory error.
    Trả về dict đề xuất các action để recovery.
    """
    suggestions = []

    # Đề xuất 1: Giảm resolution
    new_w = max(256, current_width // 2)
    new_h = max(256, current_height // 2)
    suggestions.append({
        "action": "reduce_resolution",
        "command": f"--width {new_w} --height {new_h}",
        "description": f"Giảm resolution từ {current_width}x{current_height} xuống {new_w}x{new_h}",
    })

    # Đề xuất 2: Chuyển model nhỏ hơn
    if model_key and model_key.startswith("flux"):
        suggestions.append({
            "action": "switch_model",
            "command": "--model sdxl-base",
            "description": "Chuyển từ FLUX sang SDXL Base (nhẹ hơn)",
        })
    elif model_key and model_key.startswith("sdxl"):
        suggestions.append({
            "action": "switch_model",
            "command": "--model sd15",
            "description": "Chuyển từ SDXL sang SD 1.5 (nhẹ hơn)",
        })

    # Đề xuất 3: Cleanup VRAM
    suggestions.append({
        "action": "clean_vram",
        "command": "python3 cuda_render_tool.py clean",
        "description": "Dọn VRAM trước khi retry",
    })

    return {
        "error_type": "OOM",
        "error_message": str(error),
        "suggestions": suggestions,
        "retry_possible": True,
    }


def handle_cuda_error(error):
    """
    Xử lý CUDA error (kernel fail, driver issue, v.v.)
    """
    error_str = str(error).lower()

    if "driver" in error_str or "drv" in error_str:
        return {
            "error_type": "CUDA_DRIVER",
            "error_message": str(error),
            "suggestions": [
                {
                    "action": "update_driver",
                    "command": "Update NVIDIA GPU driver",
                    "description": "Driver NVIDIA có thể đã cũ hoặc hỏng",
                },
                {
                    "action": "reboot",
                    "command": "restart",
                    "description": "Khởi động lại máy để reload driver",
                },
            ],
            "retry_possible": False,
        }

    if "init" in error_str or "cudaInitialize" in error_str or "cuda initialization" in error_str:
        return {
            "error_type": "CUDA_INIT",
            "error_message": str(error),
            "suggestions": [
                {
                    "action": "check_cuda",
                    "command": "python3 cuda_render_tool.py detect",
                    "description": "Kiểm tra lại CUDA availability",
                },
                {
                    "action": "reinstall_pytorch",
                    "command": "python3 -m pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128",
                    "description": "Reinstall PyTorch CUDA",
                },
            ],
            "retry_possible": False,
        }

    return {
        "error_type": "CUDA_ERROR",
        "error_message": str(error),
        "suggestions": [
            {
                "action": "diagnose",
                "command": "python3 cuda_render_tool.py fix",
                "description": "Chạy full diagnosis",
            },
        ],
        "retry_possible": False,
    }


def handle_missing_model(model_key):
    """
    Xử lý missing model error.
    """
    available_models = ["sd15", "sdxl-base", "sdxl-refiner", "flux-schnell", "flux-dev"]

    return {
        "error_type": "MISSING_MODEL",
        "error_message": f"Model '{model_key}' not found locally",
        "model_requested": model_key,
        "available_models": available_models,
        "suggestions": [
            {
                "action": "download",
                "command": f"python3 scripts/model_manager.py {model_key}",
                "description": f"Download model '{model_key}' từ HuggingFace",
            },
            {
                "action": "auto_download",
                "command": "python3 scripts/model_manager.py --auto --download",
                "description": "Auto-select và download model phù hợp với VRAM",
            },
        ],
        "retry_possible": True,
    }


def safe_generate(pipe, prompt, max_retries=2, **kwargs):
    """
    Generate ảnh với retry logic và fallback.

    Args:
        pipe: DiffusionPipeline đã load
        prompt: Prompt text
        max_retries: Số lần retry khi OOM
        **kwargs: Các tham số chuyển vào pipe()

    Returns:
        PIL Image hoặc raise exception
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            result = pipe(prompt=prompt, **kwargs)

            # diffusers trả về DifferentiableDataPicke ou Similar — unwrap
            if hasattr(result, 'images'):
                return result.images[0]
            return result

        except torch.cuda.OutOfMemoryError as e:
            last_error = e
            torch.cuda.empty_cache()
            if attempt < max_retries:
                time.sleep(2)
                # Giảm từ khóa nếu có thể
                if 'height' in kwargs:
                    kwargs['height'] = max(256, kwargs['height'] // 2)
                if 'width' in kwargs:
                    kwargs['width'] = max(256, kwargs['width'] // 2)
                continue
            raise

        except RuntimeError as e:
            error_str = str(e).lower()
            if "cuda" in error_str or "memory" in error_str or "oom" in error_str:
                last_error = e
                torch.cuda.empty_cache()
                if attempt < max_retries:
                    time.sleep(2)
                    continue
            raise

    if last_error:
        raise last_error
    raise RuntimeError("safe_generate failed after all retries")


def classify_error(error):
    """
    Phân loại lỗi tự động.
    """
    error_str = str(error)

    if "OutOfMemory" in error_str or "OOM" in error_str or "out of memory" in error_str.lower():
        return "oom"

    if "cuda" in error_str.lower() or "CUDA" in error_str:
        return "cuda"

    if "checkpoint" in error_str.lower() or "model not found" in error_str.lower() or "not found" in error_str.lower():
        return "missing_model"

    return "unknown"
