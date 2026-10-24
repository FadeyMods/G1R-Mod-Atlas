"""G1R Mod Atlas - Desktop-App (Mod-Manager für Gen1Recomp).

Zeigt dieselbe Oberfläche wie die Webseite (docs/) und ergänzt:
installieren, updaten, entfernen, Spiel starten.

Mods landen im Speicherordner des Spiels unter mods/<manifest-id>/ - genau dort,
wo Gen1Recomp sie auch beim "Import mod .zip" ablegt.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import webview

APP_NAME = "G1R Mod Atlas"
UA = "g1r-mod-atlas-app/1.0"
# Online-Liste (GitHub Pages); ohne Verbindung wird die mitgelieferte Liste genutzt. In den Einstellungen änderbar, z. B. für Forks.
DEFAULT_FEED = "https://fadeymods.github.io/G1R-Mod-Atlas/data/mods.json"

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
DOCS = BASE / "docs"
APPDATA = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
SETTINGS_FILE = APPDATA / "settings.json"
INSTALLED_FILE = APPDATA / "installed.json"
CACHE_FILE = APPDATA / "mods-cache.json"
REMOVED_DIR = APPDATA / "entfernt"


def _read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def _fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ---------------------------------------------------------------- Erkennung

def detect_save_dir():
    roaming = Path(os.environ.get("APPDATA", ""))
    candidates = [roaming / "pokemon-love2d", roaming / "LOVE" / "pokemon-love2d"]
    found = [c for c in candidates if (c / "options.lua").exists()]
    if not found:
        return str(candidates[0])
    return str(max(found, key=lambda c: (c / "options.lua").stat().st_mtime))


def detect_game_exe():
    home = Path.home()
    for root in (home / "Desktop", home / "Downloads", home / "Documents", Path("C:/Games"), Path("D:/")):
        if not root.exists():
            continue
        try:
            for p in root.glob("gen1recomp.exe"):
                return str(p)
            for p in root.glob("*/gen1recomp.exe"):
                return str(p)
            for p in root.glob("*/*/gen1recomp.exe"):
                return str(p)
        except OSError:
            continue
    return ""


# ---------------------------------------------------------------- Zip-Installation

def _manifest_dirs(zf):
    """Alle Ordner (als Präfix) mit manifest.json, flachste Ebene zuerst."""
    dirs = []
    for name in zf.namelist():
        p = PurePosixPath(name)
        if p.name == "manifest.json" and len(p.parts) <= 4:
            dirs.append(str(p.parent) if str(p.parent) != "." else "")
    if not dirs:
        return []
    depth = min(d.count("/") + (1 if d else 0) for d in dirs)
    return [d for d in dirs if d.count("/") + (1 if d else 0) == depth]


def _safe_extract(zf, prefix, target):
    target = Path(target).resolve()
    pre = (prefix + "/") if prefix else ""
    for info in zf.infolist():
        if not info.filename.startswith(pre) or info.is_dir():
            continue
        rel = info.filename[len(pre):]
        if not rel:
            continue
        dest = (target / rel).resolve()
        if target not in dest.parents:
            raise ValueError(f"Unsicherer Pfad im Zip: {info.filename}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, open(dest, "wb") as out:
            shutil.copyfileobj(src, out)


class Api:
    def __init__(self):
        self._window = None
        self.lock = threading.Lock()
        s = _read_json(SETTINGS_FILE, {})
        s.setdefault("save_dir", detect_save_dir())
        s.setdefault("game_exe", detect_game_exe())
        s.setdefault("feed_url", DEFAULT_FEED)
        self.settings = s
        _write_json(SETTINGS_FILE, s)

    # ---------- Daten
    def get_data(self):
        url = (self.settings.get("feed_url") or "").strip()
        if url:
            try:
                if not url.endswith(".json"):
                    url = url.rstrip("/") + "/data/mods.json"
                data = json.loads(_fetch(url))
                _write_json(CACHE_FILE, data)
                return data
            except Exception:
                cached = _read_json(CACHE_FILE, None)
                if cached:
                    return cached
        return _read_json(DOCS / "data" / "mods.json", {"mods": [], "generated_at": datetime.utcnow().isoformat()})

    def get_changes(self):
        url = (self.settings.get("feed_url") or "").strip()
        if url:
            try:
                base = url.rsplit("/", 1)[0] if url.endswith(".json") else url.rstrip("/") + "/data"
                return json.loads(_fetch(base + "/changes.json"))
            except Exception:
                pass
        return _read_json(DOCS / "data" / "changes.json", [])

    def mods_dir(self):
        return Path(self.settings["save_dir"]) / "mods"

    def get_state(self):
        installed = {}
        mdir = self.mods_dir()
        if mdir.exists():
            for d in mdir.iterdir():
                man = _read_json(d / "manifest.json", None) if d.is_dir() else None
                if man and man.get("id"):
                    installed["manifest:" + str(man["id"])] = {"version": man.get("version"), "path": str(d)}
        records = _read_json(INSTALLED_FILE, {})
        for atlas_id, rec in records.items():
            if all(Path(p).exists() for p in rec.get("paths", [])) and rec.get("paths"):
                installed[atlas_id] = rec
        return {"installed": installed, "settings": self.settings}

    # ---------- Aktionen
    def install(self, mod):
        url = (mod.get("latest") or {}).get("url")
        if not url:
            return {"ok": False, "error": "Kein Download vorhanden"}
        with self.lock:
            tmp = None
            try:
                data = _fetch(url, timeout=300)
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
                tmp.write(data)
                tmp.close()
                with zipfile.ZipFile(tmp.name) as zf:
                    prefixes = _manifest_dirs(zf)
                    if not prefixes:
                        return {"ok": False, "error": "Im Download ist keine manifest.json - kein installierbarer Mod"}
                    paths, ids = [], []
                    mdir = self.mods_dir()
                    mdir.mkdir(parents=True, exist_ok=True)
                    for pre in prefixes:
                        man = json.loads(zf.read((pre + "/" if pre else "") + "manifest.json").decode("utf-8-sig"))
                        mid = str(man.get("id") or PurePosixPath(pre).name or mod["id"].split("/")[-1])
                        target = mdir / mid
                        if target.exists():
                            self._move_to_removed(target, keep=False)
                        _safe_extract(zf, pre, target)
                        paths.append(str(target))
                        ids.append(mid)
                records = _read_json(INSTALLED_FILE, {})
                records[mod["id"]] = {"version": (mod.get("latest") or {}).get("version"), "manifest_ids": ids,
                                      "paths": paths, "installed_at": datetime.now().isoformat(timespec="seconds"),
                                      "name": mod.get("name")}
                _write_json(INSTALLED_FILE, records)
                return {"ok": True, "version": records[mod["id"]]["version"], "paths": paths}
            except Exception as e:
                return {"ok": False, "error": str(e)}
            finally:
                if tmp:
                    try:
                        os.unlink(tmp.name)
                    except OSError:
                        pass

    def _move_to_removed(self, folder, keep=True):
        """Statt endgültig zu löschen: in den App-Ordner 'entfernt' verschieben (wiederherstellbar)."""
        if keep:
            REMOVED_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(folder), str(REMOVED_DIR / f"{Path(folder).name}-{int(time.time())}"))
        else:
            old = REMOVED_DIR / "alte-versionen" / f"{Path(folder).name}-{int(time.time())}"
            old.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(folder), str(old))
            # nur die letzten 3 alten Versionen je Mod behalten
            same = sorted(old.parent.glob(f"{Path(folder).name}-*"))
            for p in same[:-3]:
                shutil.rmtree(p, ignore_errors=True)

    def uninstall(self, mod):
        records = _read_json(INSTALLED_FILE, {})
        rec = records.get(mod["id"])
        paths = rec["paths"] if rec else []
        if not paths and mod.get("manifest_id"):
            p = self.mods_dir() / mod["manifest_id"]
            if p.exists():
                paths = [str(p)]
        try:
            for p in paths:
                if Path(p).exists():
                    self._move_to_removed(p)
            records.pop(mod["id"], None)
            _write_json(INSTALLED_FILE, records)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def open_folder(self, mod):
        rec = _read_json(INSTALLED_FILE, {}).get(mod["id"])
        path = rec["paths"][0] if rec and rec.get("paths") else str(self.mods_dir())
        os.startfile(path)
        return True

    def launch(self):
        exe = self.settings.get("game_exe")
        if not exe or not Path(exe).exists():
            return {"ok": False}
        subprocess.Popen([exe], cwd=str(Path(exe).parent))
        return {"ok": True}

    # ---------- Einstellungen
    def pick_folder(self):
        r = self._window.create_file_dialog(webview.FileDialog.FOLDER, directory=self.settings.get("save_dir") or "")
        return r[0] if r else None

    def pick_exe(self):
        r = self._window.create_file_dialog(webview.FileDialog.OPEN, file_types=("Gen1Recomp (*.exe)",))
        return r[0] if r else None

    def save_settings(self, s):
        for k in ("save_dir", "game_exe", "feed_url"):
            if k in s:
                self.settings[k] = s[k]
        _write_json(SETTINGS_FILE, self.settings)
        return True


def main():
    api = Api()
    window = webview.create_window(APP_NAME, url=str(DOCS / "index.html"), js_api=api,
                                   width=1320, height=860, min_size=(900, 600), background_color="#0f1218")
    api._window = window
    webview.start(http_server=True, private_mode=False, storage_path=str(APPDATA / "webview"))


if __name__ == "__main__":
    main()
