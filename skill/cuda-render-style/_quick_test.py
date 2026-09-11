#!/usr/bin/env python3
"""Quick CUDA + SD1.5 render test — FIXED PATH."""
import torch
import sys
from pathlib import Path

print("=== CUDA REALTIME CHECK ===")
print(f"CUDA available: {torch.cuda.is_available()}")
if not torch.cuda.is_available():
    print("CUDA NOT AVAILABLE")
    sys.exit(1)
print(f"GPU: {torch.cuda.get_device_name(0)}")
props = torch.cuda.get_device_properties(0)
print(f"VRAM: {props.total_memory / 1024**3:.1f} GB")

print()
print("=== SD1.5 MODEL CHECK ===")
MODEL_ROOT = Path(r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/skill/cuda-render-style/models/sd15")
unet_path = MODEL_ROOT / "unet" / "diffusion_pytorch_model.safetensors"
print(f"Model root: {MODEL_ROOT}")
print(f"UNet: {unet_path} ({unet_path.stat().st_size / 1024**2:.0f} MB)")

print()
print("=== RENDER TEST ===")
from diffusers import DiffusionPipeline

pipe = DiffusionPipeline.from_pretrained(
    str(MODEL_ROOT),
    torch_dtype=torch.float16,
    use_safetensors=True,
    safety_checker=None,
)
pipe.to("cuda")

image = pipe(
    prompt="modern architectural interior, photorealistic, soft daylight, floor-to-ceiling windows, 8k, architectural visualization",
    width=512,
    height=512,
    num_inference_steps=20,
    guidance_scale=7.5,
    generator=torch.Generator("cuda").manual_seed(42),
).images[0]

output_path = Path(r"C:/Users/HOMIE/test_cuda_render_neito.png")
image.save(str(output_path))
print(f"✅ Render saved: {output_path} ({output_path.stat().st_size / 1024:.0f} KB)")
print(f"   Size: {image.size[0]}x{image.size[1]}")
