import json, os, re, sys, tempfile, subprocess, time, zipfile
from urllib.request import Request, urlopen

from app._build_version import CURRENT_VERSION

OWNER = "Crankerer"
REPO = "cs2_chat_translation_bot"
APP_EXE_NAME = "CS2ChatTranslationBot.exe"
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
    headers = _gh_headers(accept_json=True)
    req = Request(url, headers=headers)
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
    return sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0])

def _pick_asset(release):
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

def _extract_update_from_zip(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        members = z.namelist()
        exes = [m for m in members if m.lower().endswith(".exe")]
        if not exes:
            return None, None

        # Prefer the exact app EXE by name, fall back to largest
        app_name_lower = APP_EXE_NAME.lower()
        named = [m for m in exes if os.path.basename(m).lower() == app_name_lower]
        pick = named[0] if named else sorted(exes, key=lambda m: z.getinfo(m).file_size, reverse=True)[0]

        out_dir = tempfile.mkdtemp()
        z.extractall(out_dir)

        new_exe = os.path.normpath(os.path.join(out_dir, pick))
        update_root = os.path.dirname(new_exe)
        return update_root, new_exe

def maybe_update(prereleases=False):
    try:
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases"
        rel_data = _http_json(url)

        if isinstance(rel_data, list):
            if not rel_data:
                print("[Updater] No releases found.")
                return False
            if prereleases:
                rel = rel_data[0]
            else:
                rel = next(
                    (r for r in rel_data
                     if not r.get("draft") and not r.get("prerelease")),
                    rel_data[0]
                )
        elif isinstance(rel_data, dict):
            rel = rel_data
        else:
            print(f"[Updater] Unexpected release type: {type(rel_data)}")
            return False
        
        if not rel or rel.get("draft"):
            print("[Updater] No valid release found.")
            return False

        latest_version_str = rel.get("tag_name") or rel.get("name")
        latest_v = _parse_version(latest_version_str)

        current_v = _parse_version(CURRENT_VERSION)

        print(f"[Updater] Local: {CURRENT_VERSION} | Remote: {latest_version_str}")

        if latest_v <= current_v:
            print("[Updater] Already up to date.")
            return False

        print("[Updater] New version available, downloading...")

        asset, kind = _pick_asset(rel)
        if not asset:
            print("[Updater] No suitable Windows asset found.")
            return False

        fd, tmp_file = tempfile.mkstemp()
        os.close(fd)
        _download(asset["browser_download_url"], tmp_file)

        if kind == "zip":
            update_root, new_exe = _extract_update_from_zip(tmp_file)
            if not new_exe:
                print("[Updater] ZIP contains no executable.")
                return False
        else:
            new_exe = tmp_file
            update_root = os.path.dirname(new_exe)

        target = _app_path()
        install_dir = os.path.dirname(target)
        helper_exe = os.path.join(install_dir, "update_helper.exe")

        if not os.path.isfile(helper_exe):
            print(f"[Updater] update_helper.exe not found in installation folder: {helper_exe}")
            return False

        args_json = json.dumps(sys.argv[1:], ensure_ascii=False)

        cmd = [
            helper_exe,
            "--src-root", update_root,
            "--dst-root", install_dir,
            "--src-exe", os.path.abspath(new_exe),
            "--dst-exe", os.path.abspath(target),
            "--args-json", args_json
        ]

        print("[Updater] Starting update_helper.exe:", cmd)

        subprocess.Popen(cmd, close_fds=True)
        sys.exit(0)

    except Exception as e:
        print(f"[Updater] Update failed: {e}")
        return False
