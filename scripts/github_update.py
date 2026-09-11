#!/usr/bin/env python3
"""
github_update.py — Kiểm tra GitHub releases và cập nhật plugin tự động.
Gọi từ 3ds Max macroScript qua shellLaunch.

Usage:
    python3 github_update.py --current-version v1.0.0 --user-macros "C:/path/to/usermacros"
    python3 github_update.py --check-only          # Chỉ check, không download
    python3 github_update.py --download             # Check + download + replace
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import zipfile
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

GITHUB_REPO = "Neito112/nc-render-standard"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
USER_AGENT = "NC-Render-Update/1.0"

# Default paths
DEFAULT_PLUGIN_ROOT = Path(r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard")
DEFAULT_USER_MACROSE = Path(r"C:/Users/HOMIE/AppData/Local/Autodesk/3dsMax/2024 - 64bit/ENU/usermacros")


def fetch_latest_release():
    """Fetch latest release từ GitHub API."""
    print(f"Fetching latest release from GitHub: {GITHUB_REPO} ...", flush=True)
    req = urllib.request.Request(GITHUB_API, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                print(f"  ⚠️ GitHub API returned status {resp.status}", flush=True)
                return None
            data = json.loads(resp.read())
            return data
    except urllib.error.URLError as e:
        print(f"  ❌ Network error: {e.reason}", flush=True)
        return None
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON decode error: {e}", flush=True)
        return None
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}", flush=True)
        return None


def check_update(current_version: str, release_data: dict) -> dict:
    """
    So sánh current version với latest release.
    Returns dict với keys: available, latest_version, download_url, asset_name, release_url
    """
    if not release_data:
        return {"available": False, "error": "Cannot fetch release info"}

    latest_tag = release_data.get("tag_name", "unknown")
    release_url = release_data.get("html_url", "")
    assets = release_data.get("assets", [])

    # Parse versions (v1.0.0 → tuple)
    def parse_version(v):
        try:
            return tuple(int(x) for x in v.lstrip("v").split("."))
        except:
            return (0, 0, 0)

    current_parsed = parse_version(current_version)
    latest_parsed = parse_version(latest_tag)

    # Tìm .mzp asset
    mzp_asset = None
    for asset in assets:
        if asset["name"].endswith(".mzp"):
            mzp_asset = asset
            break

    # Có bản mới không?
    available = latest_parsed > current_parsed

    result = {
        "available": available,
        "current_version": current_version,
        "latest_version": latest_tag,
        "release_url": release_url,
        "download_url": mzp_asset["browser_download_url"] if mzp_asset else None,
        "asset_name": mzp_asset["name"] if mzp_asset else None,
        "asset_size_mb": round(mzp_asset["size"] / (1024 * 1024), 2) if mzp_asset else 0,
    }

    if not available:
        result["note"] = "Bạn đang dùng phiên bản mới nhất"

    return result


def download_mzp(url: str, dest_dir: Path) -> Path:
    """Download .mzp về temp, trả về path file."""
    print(f"Downloading {url} ...", flush=True)
    tmp_file = dest_dir / f"nc_render_update_{int(datetime.now().timestamp())}.mzp"
    try:
        urllib.request.urlretrieve(url, str(tmp_file))
        size_mb = tmp_file.stat().st_size / (1024 * 1024)
        print(f"  Downloaded: {size_mb:.2f} MB", flush=True)
        return tmp_file
    except Exception as e:
        print(f"  ❌ Download failed: {e}", flush=True)
        if tmp_file.exists():
            tmp_file.unlink()
        raise


def extract_and_copy_mcr(mzp_path: Path, target_dir: Path, verbose=True):
    """
    Extract .mcr từ .mzp và copy vào userMacros directory.
    Trả về list tên file đã copy.
    """
    copied = []
    try:
        with zipfile.ZipFile(mzp_path, "r") as zf:
            mcr_files = [n for n in zf.namelist() if n.endswith(".mcr")]
            if not mcr_files:
                print("  ⚠️ No .mcr found in archive", flush=True)
                return []

            for mcr_path in mcr_files:
                target_name = Path(mcr_path).name
                target_path = target_dir / target_name
                with zf.open(mcr_path) as src:
                    content = src.read()
                    target_path.write_bytes(content)
                    copied.append(target_name)
                    if verbose:
                        print(f"  ✅ Copied: {target_name} → {target_path}", flush=True)
    except Exception as e:
        print(f"  ❌ Extract failed: {e}", flush=True)
        raise

    return copied


def update_plugin(current_version: str, user_macros_dir: Path, check_only=False):
    """
    Main update logic.
    - Check GitHub releases
    - Nếu có bản mới: download .mzp, extract .mcr, copy vào userMacros
    - Trả về status dict
    """
    print("=" * 60, flush=True)
    print("NC-RENDER PLUGIN UPDATER", flush=True)
    print("=" * 60, flush=True)
    print(f"Current version: {current_version}", flush=True)
    print(f"User macros dir: {user_macros_dir}", flush=True)
    print(f"Check only: {check_only}", flush=True)
    print()

    # Step 1: Fetch latest
    release = fetch_latest_release()
    if not release:
        return {
            "success": False,
            "error": "Cannot fetch latest release",
            "action": "retry_later",
        }

    # Step 2: Check update
    result = check_update(current_version, release)
    print(f"Latest version: {result['latest_version']}", flush=True)
    print(f"Update available: {result['available']}", flush=True)
    if result.get("release_url"):
        print(f"Release page: {result['release_url']}", flush=True)
    print()

    if not result["available"]:
        print("✅ Bạn đang dùng phiên bản mới nhất", flush=True)
        return {
            "success": True,
            "up_to_date": True,
            "current_version": current_version,
            "latest_version": result["latest_version"],
        }

    # Step 3: Download + update (nếu không phải check-only)
    if check_only:
        print("⏸  Check-only mode — not downloading", flush=True)
        print(f"Download URL: {result['download_url']}", flush=True)
        print(f"Release page: {result['release_url']}", flush=True)
        return {
            "success": True,
            "update_available": True,
            "latest_version": result["latest_version"],
            "download_url": result["download_url"],
            "release_url": result["release_url"],
            "action": "user_approve",
        }

    # Step 4: Download và cập nhật
    print("-" * 60, flush=True)
    print("DOWNLOADING...", flush=True)

    mzp_path = None
    try:
        mzp_path = download_mzp(result["download_url"], DEFAULT_PLUGIN_ROOT)
        print()
        print("EXTRACTING & COPYING...", flush=True)
        copied = extract_and_copy_mcr(mzp_path, user_macros_dir)
        print()
        if copied:
            print(f"✅ Đã cập nhật {len(copied)} file(.mcr) vào userMacros", flush=True)
            print("⚠️  Khuyến nghị: Restart 3ds Max để load phiên bản mới", flush=True)
            return {
                "success": True,
                "updated": True,
                "files_copied": copied,
                "latest_version": result["latest_version"],
                "restart_recommended": True,
            }
        else:
            print("❌ Không có .mcr nào trong package", flush=True)
            return {
                "success": False,
                "error": "No .mcr found in package",
            }
    except Exception as e:
        print(f"❌ Update failed: {e}", flush=True)
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        if mzp_path and mzp_path.exists():
            mzp_path.unlink()
            print(f"  Đã xóa file tải: {mzp_path.name}", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="NC-Render Plugin Auto-Updater — kiểm tra GitHub releases và cập nhật",
    )
    parser.add_argument(
        "--current-version", "-v",
        default="v1.0.0",
        help="Phiên bản hiện tại (mặc định: v1.0.0)",
    )
    parser.add_argument(
        "--user-macros", "-u",
        type=str,
        default=None,
        help="Đường dẫn userMacros directory của 3ds Max (mặc định: C:/Users/HOMIE/AppData/Local/Autodesk/3dsMax/2024 - 64bit/ENU/usermacros)",
    )
    parser.add_argument(
        "--check-only", "-c",
        action="store_true",
        help="Chỉ kiểm tra, không download/copy",
    )
    parser.add_argument(
        "--download", "-d",
        action="store_true",
        help="Kiểm tra + download + copy (mặc định nếu không chỉ định check-only)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output kết quả dưới dạng JSON",
    )

    args = parser.parse_args()

    # Xác định userMacros dir
    if args.user_macros:
        user_macros_dir = Path(args.user_macros)
    else:
        user_macros_dir = DEFAULT_USER_MACROSE

    # Chạy update
    check_only = args.check_only and not args.download
    result = update_plugin(args.current_version, user_macros_dir, check_only=check_only)

    # Output JSON nếu 요청
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Pretty print summary
        print()
        print("=" * 60, flush=True)
        print("SUMMARY", flush=True)
        print("=" * 60, flush=True)
        if result.get("up_to_date"):
            print("✅ Đang dùng phiên bản mới nhất:", result.get("latest_version"), flush=True)
        elif result.get("updated"):
            print("✅ Đã cập nhật thành công:", result.get("latest_version"), flush=True)
            print("   Files:", result.get("files_copied"), flush=True)
            if result.get("restart_recommended"):
                print("   ⚠️  Restart 3ds Max để áp dụng", flush=True)
        elif result.get("update_available") and result.get("action") == "user_approve":
            print("📦 CÓ bản cập nhật:", result.get("latest_version"), flush=True)
            print("   Download:", result.get("download_url"), flush=True)
            print("   Chạy lại với --download để tự động cập nhật", flush=True)
        else:
            print("❌ Lỗi:", result.get("error", "unknown"), flush=True)

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
