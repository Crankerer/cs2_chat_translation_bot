import argparse
import json
import os
import shutil
import sys
import time


def copytree_merge(src: str, dst: str) -> None:
    if not os.path.exists(src):
        return

    os.makedirs(dst, exist_ok=True)

    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        target_root = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(target_root, exist_ok=True)

        for d in dirs:
            os.makedirs(os.path.join(target_root, d), exist_ok=True)

        for f in files:
            src_file = os.path.join(root, f)
            dst_file = os.path.join(target_root, f)
            shutil.copy2(src_file, dst_file)


def main():
    parser = argparse.ArgumentParser(
        description="Helper for replacing EXE + lang + _internal + VERSION.txt and restarting."
    )
    parser.add_argument("--src-root", required=True, help="Root folder of the new version")
    parser.add_argument("--dst-root", required=True, help="Installation folder of the running app")
    parser.add_argument("--src-exe", required=True, help="Path to the new EXE")
    parser.add_argument("--dst-exe", required=True, help="Path to the running EXE to be replaced")
    parser.add_argument(
        "--args-json",
        default="[]",
        help="JSON encoded list of command-line arguments for restart",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=40,
        help="Maximum wait time until the old EXE is unlocked",
    )
    args = parser.parse_args()

    src_root = os.path.abspath(args.src_root)
    dst_root = os.path.abspath(args.dst_root)
    src_exe = os.path.abspath(args.src_exe)
    dst_exe = os.path.abspath(args.dst_exe)

    try:
        restart_args = json.loads(args.args_json)
        if not isinstance(restart_args, list):
            restart_args = []
    except Exception:
        restart_args = []

    time.sleep(0.5)

    deadline = time.time() + args.wait_seconds
    last_error = None

    while time.time() < deadline:
        try:
            print(f"[update_helper] Copying EXE: {src_exe} -> {dst_exe}")
            os.makedirs(os.path.dirname(dst_exe), exist_ok=True)
            shutil.copy2(src_exe, dst_exe)
            last_error = None
            break
        except PermissionError as e:
            last_error = e
            time.sleep(0.25)
        except FileNotFoundError as e:
            last_error = e
            break
        except OSError as e:
            last_error = e
            time.sleep(0.25)

    if last_error is not None:
        print(f"[update_helper] Failed to replace EXE: {last_error}")
        sys.exit(1)

    # Copy all files/folders from src_root to dst_root, except config.json
    # (user settings must be preserved across updates).
    # This handles both Nuitka (flat layout) and PyInstaller (_internal/ subfolder).
    print(f"[update_helper] Updating dist files: {src_root} -> {dst_root}")
    for item in os.listdir(src_root):
        if item.lower() == "config.json":
            print("[update_helper] Skipping config.json (preserving user settings)")
            continue
        src_item = os.path.join(src_root, item)
        dst_item = os.path.join(dst_root, item)
        if os.path.isdir(src_item):
            copytree_merge(src_item, dst_item)
        else:
            try:
                shutil.copy2(src_item, dst_item)
            except OSError as e:
                print(f"[update_helper] Failed to copy {item}: {e}")

    cmd = [dst_exe] + restart_args
    print(f"[update_helper] Restarting application: {cmd}")
    os.execv(dst_exe, cmd)


if __name__ == "__main__":
    main()
