# updater.py
# Simple self-updater for Windows, using GitHub Releases only (no hash/signature).
import json, os, re, sys, tempfile, subprocess, time, zipfile
from urllib.request import Request, urlopen

from app._build_version import CURRENT_VERSION

OWNER = "Crankerer"
REPO = "cs2_chat_translation_bot"
APP_EXE_NAME = "cs2_chat_translation_bot.exe"
UA = f"{REPO}-updater/1.0"

def _gh_headers(accept_json=False):
    hdr = {"User-Agent": UA}
    if accept_json:
        hdr["Accept"] = "application/vnd.github+json"
    token = os.getenv("GITHUB_TOKEN")
    if token:
        hdr["Authorization"] = f"Bearer {token}"
        hdr["X-GitHub-Api-Version"] = "2022-11-28"
    return hdr

def _http_json(url):
    req = Request(url, headers=_gh_headers(accept_json=True))
    with urlopen(req, timeout=15) as r:
        return json.load(r)

def _download(url, dest):
    req = Request(url, headers={**_gh_headers(), "Accept": "application/octet-stream"})
    with urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)

def _parse_version(s):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", s or "")
    return tuple(map(int, m.groups())) if m else (0, 0, 0)

def _app_path():
    # For PyInstaller, sys.executable is the .exe file
    return sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0])

def _pick_asset(release):
    """Pick the best Windows asset (.exe preferred, .zip fallback)."""
    assets = release.get("assets", [])
    exe_pref = [a for a in assets
                if a["name"].lower().endswith(".exe")
                and any(x in a["name"].lower() for x in ("win", "windows", "x64", "amd64"))]
    if exe_pref:
        return exe_pref[0], "exe"
    exe_any = [a for a in assets if a["name"].lower().endswith(".exe")]
    if exe_any:
        return exe_any[0], "exe"
    zip_pref = [a for a in assets
                if a["name"].lower().endswith(".zip")
                and any(x in a["name"].lower() for x in ("win", "windows", "x64", "amd64"))]
    if zip_pref:
        return zip_pref[0], "zip"
    zip_any = [a for a in assets if a["name"].lower().endswith(".zip")]
    if zip_any:
        return zip_any[0], "zip"
    return None, None

def _extract_exe_from_zip(zip_path):
    """Extract the correct .exe from a ZIP file."""
    with zipfile.ZipFile(zip_path) as z:
        members = z.namelist()
        exes = [m for m in members if m.lower().endswith(".exe")]
        if not exes:
            return None
        if APP_EXE_NAME:
            match = [m for m in exes if os.path.basename(m).lower() == APP_EXE_NAME.lower()]
            pick = match[0] if match else None
        else:
            exes.sort(key=lambda m: z.getinfo(m).file_size, reverse=True)
            pick = exes[0]
        out_dir = tempfile.mkdtemp()
        z.extract(pick, out_dir)
        return os.path.join(out_dir, pick)

def _replace_self_windows(new_exe):
    """Spawn a helper to replace the running EXE, then relaunch."""
    target = _app_path()
    args = sys.argv[1:]
    helper_code = f"""import os, shutil, sys, time
src=r'''{new_exe}'''; dst=r'''{target}'''; args={args!r}
time.sleep(0.5)
for _ in range(160):
    try:
        shutil.copyfile(src, dst)
        break
    except PermissionError:
        time.sleep(0.25)
os.execv(dst, [dst] + args)
"""
    tmp_py = os.path.join(tempfile.gettempdir(), f"{REPO}_upd_helper.py")
    with open(tmp_py, "w", encoding="utf-8") as f:
        f.write(helper_code)
    subprocess.Popen([sys.executable, tmp_py], close_fds=True)
    sys.exit(0)

def maybe_update(prereleases=False):
    """Check GitHub for a new version, and self-update if found."""
    try:
        rel = (_http_json(f"https://api.github.com/repos/{OWNER}/{REPO}/releases")[0]
               if prereleases else
               _http_json(f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"))
        if not rel or rel.get("draft"):
            return False
        latest_v = _parse_version(rel.get("tag_name") or rel.get("name"))
        current_v = _parse_version(CURRENT_VERSION)
        if latest_v <= current_v:
            return False

        asset, kind = _pick_asset(rel)
        if not asset:
            print("[Updater] No suitable Windows asset found.")
            return False

        fd, tmp = tempfile.mkstemp()
        os.close(fd)
        _download(asset["browser_download_url"], tmp)

        new_exe = _extract_exe_from_zip(tmp) if kind == "zip" else tmp
        if not new_exe:
            print("[Updater] No .exe found in ZIP.")
            return False

        _replace_self_windows(new_exe)
        return True
    except Exception as e:
        print(f"[Updater] Update check failed: {e}")
        return False
