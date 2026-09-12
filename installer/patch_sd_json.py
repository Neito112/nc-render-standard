# -*- coding: utf-8 -*-
"""Patch sd_generate.py: gui JSON ket qua cho macro 3ds Max doc."""
import re
from pathlib import Path

p = Path("scripts/sd_generate.py")
s = p.read_text(encoding="utf-8")

helper = '''
def _write_output_json(args, ok, image, message=""):
    """Ghi JSON ket qua de macro 3ds Max doc duoc (field 'image' la uoc mo)."""
    if not getattr(args, "output_json", None):
        return
    import json
    try:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump({"ok": bool(ok), "image": image or "", "message": message}, f)
        print("[output-json] " + str(args.output_json))
    except Exception as e:
        print("warn: cannot write output-json: " + str(e))


def _default_output_path(args):
    """Mac dinh PNG vao Temp de macro luon biet duong dan ket qua."""
    if not args.output:
        import tempfile
        import time as _t
        args.output = str(Path(tempfile.gettempdir()) / ("nc_sd_" + str(int(_t.time() * 1000)) + ".png"))
    return args.output

'''

anchor = "def cmd_generate(args):"
assert anchor in s, "anchor cmd_generate"
s = s.replace(anchor, helper.lstrip("\n") + anchor, 1)

s = s.replace("    has_cuda, pt_ver = detect_pytorch_cuda()",
              "    _default_output_path(args)\n    has_cuda, pt_ver = detect_pytorch_cuda()", 1)

old1 = '''        result = subprocess.run(render_cmd, cwd=str(SKILL_DIR),
                                capture_output=True, text=True, timeout=600)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode'''
new1 = '''        result = subprocess.run(render_cmd, cwd=str(SKILL_DIR),
                                capture_output=True, text=True, timeout=600)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        ok = result.returncode == 0 and Path(args.output).exists()
        _write_output_json(args, ok, args.output if ok else "",
                           (result.stdout[-500:] if ok else (result.stderr or "")[-500:]))
        return 0 if ok else 1'''
assert old1 in s, "case1 block"; s = s.replace(old1, new1, 1)

old3 = '''        result = subprocess.run(render_cmd, cwd=str(PLUGIN_ROOT / "scripts"),
                                capture_output=True, text=True, timeout=900)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode'''
new3 = '''        result = subprocess.run(render_cmd, cwd=str(PLUGIN_ROOT / "scripts"),
                                capture_output=True, text=True, timeout=900)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        ok = result.returncode == 0 and Path(args.output).exists()
        _write_output_json(args, ok, args.output if ok else "",
                           (result.stdout[-500:] if ok else (result.stderr or "")[-500:]))
        return 0 if ok else 1'''
assert old3 in s, "case3 block"; s = s.replace(old3, new3, 1)

old4 = 'print("  G\u1eef v\u1ec1 External API ho\u1eb7c c\u00e0i PyTorch CUDA:")'
s2 = s.replace(old4, 'print("  Gi\u1eef v\u1ec1 External API ho\u1eb7c c\u00e0i PyTorch CUDA:")')
old4b = '    print("  python3 -m pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128")\n    return 1'
new4b = '    print("  python3 -m pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128")\n    _write_output_json(args, False, "", "No CUDA / PyTorch CUDA not installed")\n    return 1'
assert old4b in s, "case4 block"; s = s.replace(old4b, new4b, 1)

oldb = '''    print(f"\\nBatch done \u2014 output dir: {output_dir}")
    return 0'''
newb = '''    print(f"\\nBatch done \u2014 output dir: {output_dir}")
    pngs = sorted(str(x) for x in Path(output_dir).glob("batch_*.png"))
    _write_output_json(args, len(pngs) > 0, pngs[0] if pngs else "",
                       str(len(pngs)) + "/" + str(len(prompts)) + " images in " + output_dir)
    return 0 if pngs else 1'''
assert oldb in s, "batch block"; s = s.replace(oldb, newb, 1)

olds = '''    if not args.reference:
        print("\u274c C\u1ea7n reference image \u0111\u1ec3 upscale")
        return 1'''
news = '''    if not args.reference:
        print("\u274c C\u1ea7n reference image \u0111\u1ec3 upscale")
        _write_output_json(args, False, "", "Can reference image de upscale")
        return 1'''
assert olds in s, "upscale block"; s = s.replace(olds, news, 1)

p.write_text(s, encoding="utf-8", newline="\n")
import ast
ast.parse(s)
print("sd_generate.py patched + syntax OK")
