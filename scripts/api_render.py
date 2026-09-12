import argparse
import sys
import os
import json
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

def get_config_values(config_path):
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8", errors="replace") as f:
        lines = [line.strip() for line in f.readlines()]
    # renderMethod | apiProvider | apiKey | apiModel
    return {
        "apiProvider": lines[1] if len(lines) > 1 else "",
        "apiKey": lines[2] if len(lines) > 2 else "",
        "apiModel": lines[3] if len(lines) > 3 else ""
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["openrouter", "gemini"])
    parser.add_argument("--model", type=str)
    parser.add_argument("--prompt", type=str, required=True)
    parser.add_argument("--negative", type=str, default="")
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--output", type=str, default=os.path.join(os.environ.get("TEMP", "."), "nc_api_render.png"))
    parser.add_argument("--output-json", type=str)
    parser.add_argument("--key-from-config", action="store_true")
    parser.add_argument("--config", type=str, default=os.path.join(os.environ.get("TEMP", "."), "nc_render_config.txt"))
    parser.add_argument("--key", type=str)

    args = parser.parse_args()

    provider = args.provider
    model = args.model
    api_key = args.key

    if args.key_from_config:
        cfg = get_config_values(args.config)
        if not provider:
            provider = cfg.get("apiProvider") or "openrouter"
        if not api_key:
            api_key = cfg.get("apiKey")
        if not model:
            model = cfg.get("apiModel")
            if not model:
                model = "google/gemini-2.5-flash-image-preview" if provider == "openrouter" else "gemini-2.5-flash-image"

    if not api_key:
        print("Missing API key", file=sys.stderr)
        if args.output_json:
            with open(args.output_json, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "message": "Missing API key"}, f)
        sys.exit(1)

    try:
        if provider == "openrouter":
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "messages": [{"role": "user", "content": args.prompt + " — image size 1024 style architectural render"}],
                "modalities": ["image", "text"]
            }
            req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                
                try:
                    b64_data = res_json["choices"][0]["message"]["images"][0]["image_url"]["url"]
                except (KeyError, IndexError):
                    b64_data = res_json["choices"][0]["message"]["content"]
                
                if b64_data.startswith("data:image"):
                    b64_data = b64_data.split(",", 1)[1]
                
                import base64
                img_data = base64.b64decode(b64_data)
                
        elif provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }
            data = {
                "contents": [{"parts": [{"text": args.prompt}]}]
            }
            req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                
                try:
                    b64_data = res_json["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                except (KeyError, IndexError):
                    b64_data = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    
                if b64_data.startswith("data:image"):
                    b64_data = b64_data.split(",", 1)[1]
                
                import base64
                img_data = base64.b64decode(b64_data)
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Write image
        out_path = os.path.abspath(args.output)
        with open(out_path, "wb") as f:
            f.write(img_data)

        msg = "Success"
        if args.output_json:
            with open(args.output_json, "w", encoding="utf-8") as f:
                json.dump({"ok": True, "image": out_path, "provider": provider, "model": model, "message": msg}, f)

        print("Done.")
        sys.exit(0)

    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP Error: {e.code} - {err_body}", file=sys.stderr)
        if args.output_json:
            with open(args.output_json, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "message": f"HTTP {e.code}: {err_body}"}, f)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.output_json:
            with open(args.output_json, "w", encoding="utf-8") as f:
                json.dump({"ok": False, "message": str(e)}, f)
        sys.exit(1)

if __name__ == "__main__":
    main()
