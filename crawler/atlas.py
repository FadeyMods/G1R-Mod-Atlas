"""G1R Mod Atlas - findet und aktualisiert alle Gen1Recomp-Mods.

  python crawler/atlas.py seed     # einmalig: Startbestand aus seed/ übernehmen
  python crawler/atlas.py crawl    # Quellen durchsuchen und alle Mods aktualisieren

Mit Umgebungsvariable GITHUB_TOKEN (in GitHub Actions automatisch vorhanden) wird die
GitHub-API genutzt (Suche, Code-Suche, GraphQL). Ohne Token gibt es einen langsameren
Fallback über die GitHub-Webseite und "git ls-remote".
"""
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from classify import CATEGORIES, compute_status, guess_categories, guess_gens  # noqa: E402
from organize import game_feed, organize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "crawler" / "config.json").read_text(encoding="utf-8"))
DB_PATH = ROOT / "docs" / "data" / "mods.json"
CHANGES_PATH = ROOT / "docs" / "data" / "changes.json"
GAME_FEED_PATH = ROOT / "docs" / "data" / "index.json"   # im Spiel unter MODS als zusätzlicher Index nutzbar
STATE_PATH = ROOT / "crawler" / "state.json"
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
DISCORD_GUILD = "1019387038820216882"
UA = "g1r-mod-atlas (+https://github.com)"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
TODAY = NOW[:10]


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


# ---------------------------------------------------------------- HTTP

def http(url, data=None, headers=None, method=None, raw=False, retries=3):
    h = {"User-Agent": UA}
    if TOKEN and ("api.github.com" in url):
        h["Authorization"] = f"Bearer {TOKEN}"
    h.update(headers or {})
    body = json.dumps(data).encode() if data is not None else None
    if body:
        h["Content-Type"] = "application/json"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers=h, method=method)
            with urllib.request.urlopen(req, timeout=40) as r:
                content = r.read()
                return content if raw else json.loads(content.decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and attempt < retries - 1:
                wait = int(e.headers.get("Retry-After") or 0) or 30 * (attempt + 1)
                reset = e.headers.get("X-RateLimit-Reset")
                if e.headers.get("X-RateLimit-Remaining") == "0" and reset:
                    wait = max(wait, int(reset) - int(time.time()) + 2)
                if wait > 900:
                    raise
                log(f"  Rate-Limit ({e.code}), warte {wait}s ...")
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise


def gh_rest(path, **params):
    q = ("?" + urllib.parse.urlencode(params)) if params else ""
    return http(f"https://api.github.com/{path.lstrip('/')}{q}")



# ---------------------------------------------------------------- DB

def load_db():
    if DB_PATH.exists():
        data = json.loads(DB_PATH.read_text(encoding="utf-8"))
        return {m["id"]: m for m in data["mods"]}
    return {}


VISIBLE_KINDS = ("mod", "cart", "tool")


def save_db(db):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    for m in db.values():
        m["status"] = compute_status(m, CFG)
    organize(db)
    mods = sorted(db.values(), key=lambda m: m["name"].lower())
    shown = [m for m in mods if m["family"] == m["id"] and m["kind"] in VISIBLE_KINDS]
    stats = {"total": len(mods), "shown": len(shown), "by_status": {}, "by_category": {}, "by_kind": {}}
    for m in mods:
        stats["by_kind"][m["kind"]] = stats["by_kind"].get(m["kind"], 0) + 1
    for m in shown:
        stats["by_status"][m["status"]] = stats["by_status"].get(m["status"], 0) + 1
        stats["by_category"][m["categories"][0]] = stats["by_category"].get(m["categories"][0], 0) + 1
    out = {"generated_at": NOW, "stats": stats, "mods": mods}
    DB_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    feed = game_feed(db, NOW)
    GAME_FEED_PATH.write_text(json.dumps(feed, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"Gespeichert: {len(mods)} Einträge, {len(shown)} sichtbare Mods, {feed['count']} im Spiel-Feed")


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"seen_prs": [], "rejected_repos": []}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=1), encoding="utf-8")


def gh_id(repo):
    return f"gh:{repo.strip().strip('/').lower()}"


def new_mod(mid, name, **kw):
    m = {
        "id": mid, "name": name, "author": "", "summary": "", "categories": ["OTHER"], "gens": [1],
        "repo": None, "sources": {}, "latest": {}, "stars": None, "archived": False, "deleted": False,
        "fork": False, "wip": False, "in_index": False, "last_activity": None,
        "first_seen": TODAY, "last_checked": None, "status": "active",
    }
    m.update(kw)
    return m


def upsert(db, mid, name, changes, **fields):
    """Mod anlegen oder Felder ergänzen. Neue Mods landen im Änderungsprotokoll."""
    if mid not in db:
        db[mid] = new_mod(mid, name)
        changes["new"].append(mid)
    m = db[mid]
    for k, v in fields.items():
        if k == "sources":
            m["sources"].update({sk: sv for sk, sv in v.items() if sv})
        elif v not in (None, "", [], {}):
            m[k] = v
    if not m.get("name") or m["name"] == m["id"]:
        m["name"] = name
    return m


# ---------------------------------------------------------------- Quellen

def source_index(db, changes):
    log("Quelle: offizieller Mod-Index")
    idx = http(CFG["index_url"])
    seen = set()
    for kind, items in (("mod", idx.get("mods", [])), ("cart", idx.get("carts", []))):
        for e in items:
            repo = e.get("github") or ""
            mid = gh_id(repo) if repo else f"idx:{e['id']}"
            seen.add(mid)
            cats = [c for c in (e.get("categories") or []) if c in CATEGORIES] or guess_categories(e.get("title"))
            if kind == "cart":
                cats = ["CART"] + [c for c in cats if c != "CART"]
            lat = e.get("latest") or {}
            text = f"{e.get('title', '')} {e.get('summary', '')}"
            old = (db.get(mid) or {}).get("latest") or {}
            idx_latest = {"version": lat.get("tag") or e.get("version"), "date": lat.get("published_at"),
                          "url": (lat.get("zip") or {}).get("url")}
            # Der Index hinkt manchmal hinterher: neuere Version von GitHub nicht überschreiben
            if old.get("date") and idx_latest["date"] and old["date"] > idx_latest["date"]:
                idx_latest = old
            entry = upsert(db, mid, e.get("title") or repo, changes,
                   author=e.get("author"), summary=e.get("summary"), repo=repo or None,
                   categories=cats, gens=guess_gens(text), in_index=True,
                   sources={"index": f"https://bryanthaboi.github.io/gen1recomp-mod-index/#{e.get('folder', '')}",
                            "github": f"https://github.com/{repo}" if repo else None},
                   latest=idx_latest,
                   downloads=(e.get("downloads") or {}).get("total"),
                   last_activity=lat.get("published_at"), manifest_id=e.get("id"),
                   games=e.get("games") or None,
                   thumbnail=f"https://bryanthaboi.github.io/gen1recomp-mod-index/{e['thumbnail']}" if e.get("thumbnail") else None)
            if e.get("title"):
                entry["name"] = e["title"]
    for mid, m in db.items():
        if m.get("in_index") and mid not in seen:
            m["in_index"] = False
            m.setdefault("notes", []).append(f"{TODAY}: aus dem offiziellen Index entfernt")
    log(f"  {len(seen)} Einträge im Index")


def source_gamebanana(db, changes):
    log("Quelle: GameBanana")
    page, n = 1, 0
    while True:
        r = http(f"https://gamebanana.com/apiv11/Game/{CFG['gamebanana_game_id']}/Subfeed?_nPage={page}&_csvModelInclusions=Mod")
        recs = r.get("_aRecords") or []
        for rec in recs:
            gid = rec["_idRow"]
            text = rec.get("_sName", "")
            ts = rec.get("_tsDateUpdated") or rec.get("_tsDateAdded")
            date = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None
            mid = f"gb:{gid}"
            m = upsert(db, mid, text, changes, author=(rec.get("_aSubmitter") or {}).get("_sName"),
                       sources={"gamebanana": rec.get("_sProfileUrl") or f"https://gamebanana.com/mods/{gid}"},
                       last_activity=date)
            if mid in changes["new"]:
                m["categories"] = guess_categories(text)
                m["gens"] = guess_gens(text)
            n += 1
        if r.get("_aMetadata", {}).get("_bIsComplete", True) or not recs:
            break
        page += 1
    # Dateien/Version der GameBanana-Mods
    for mid, m in db.items():
        if not mid.startswith("gb:"):
            continue
        try:
            info = http(f"https://gamebanana.com/apiv11/Mod/{mid[3:]}?_csvProperties=_aFiles,_sDescription,_bIsWithheld")
            files = info.get("_aFiles") or []
            if files:
                f = max(files, key=lambda x: x.get("_idRow", 0))
                m["latest"] = {"version": f.get("_sVersion") or f"gb-{f['_idRow']}",
                               "date": datetime.fromtimestamp(f["_tsDateAdded"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                               "url": f.get("_sDownloadUrl")}
                m["last_activity"] = max(filter(None, [m.get("last_activity"), m["latest"]["date"]]))
            if info.get("_sDescription") and not m.get("summary"):
                m["summary"] = info["_sDescription"][:300]
            m["deleted"] = bool(info.get("_bIsWithheld"))
            m["last_checked"] = NOW
        except urllib.error.HTTPError as e:
            if e.code == 404:
                m["deleted"] = True
    log(f"  {n} Mods auf GameBanana")


def _relevant(text):
    t = (text or "").lower()
    if any(x in t for x in CFG["exclude_keywords"]):
        return False
    return any(k in t for k in CFG["relevance_keywords"])


def _candidate(db, state, repo, changes, hint_text="", via=""):
    """Unbekanntes Repo prüfen und ggf. aufnehmen."""
    repo = repo.strip().strip("/")
    key = repo.lower()
    if gh_id(repo) in db or key in state["rejected_repos"] or key in CFG["exclude_repos"]:
        return
    readme = ""
    try:
        readme = http(f"https://raw.githubusercontent.com/{repo}/HEAD/README.md", raw=True).decode("utf-8", "ignore")[:20000]
    except Exception:
        pass
    if not _relevant(hint_text + " " + readme + " " + repo):
        state["rejected_repos"].append(key)
        return
    name = repo.split("/")[1].replace("-", " ").replace("_", " ")
    m = upsert(db, gh_id(repo), name, changes, repo=repo, author=repo.split("/")[0],
               sources={"github": f"https://github.com/{repo}"})
    text = f"{name} {hint_text} {readme[:2000]}"
    m["categories"] = guess_categories(f"{name} {hint_text}") if guess_categories(f"{name} {hint_text}") != ["OTHER"] else guess_categories(text)
    m["gens"] = guess_gens(text)
    m["found_via"] = via
    log(f"  NEU: {repo} ({via})")


def source_github_search(db, state, changes):
    if not TOKEN:
        log("Quelle: GitHub-Suche übersprungen (kein GITHUB_TOKEN)")
        return
    log("Quelle: GitHub-Repo-Suche")
    for q in CFG["github_repo_queries"]:
        for page in range(1, 11):
            try:
                r = gh_rest("search/repositories", q=q, per_page=100, page=page, sort="updated")
            except urllib.error.HTTPError as e:
                log(f"  Suche '{q}' Fehler {e.code}")
                break
            for it in r.get("items", []):
                if it.get("fork"):
                    continue
                _candidate(db, state, it["full_name"], changes, f"{it.get('description') or ''} {' '.join(it.get('topics') or [])}", f"Suche: {q}")
            if len(r.get("items", [])) < 100:
                break
            time.sleep(2.5)
        time.sleep(2.5)
    log("Quelle: GitHub-Code-Suche")
    for q in CFG["github_code_queries"]:
        for page in range(1, 6):
            try:
                r = gh_rest("search/code", q=q, per_page=100, page=page)
            except urllib.error.HTTPError as e:
                log(f"  Code-Suche '{q}' Fehler {e.code}")
                break
            for it in r.get("items", []):
                repo = it["repository"]
                if not repo.get("fork"):
                    _candidate(db, state, repo["full_name"], changes, repo.get("description") or "", f"Code-Suche: {q}")
            if len(r.get("items", [])) < 100:
                break
            time.sleep(7)
        time.sleep(7)


def source_index_prs(db, state, changes):
    if not TOKEN:
        log("Quelle: Index-Pull-Requests übersprungen (kein GITHUB_TOKEN)")
        return
    log("Quelle: Pull Requests des Mod-Index")
    seen = set(state["seen_prs"])
    for page in range(1, 30):
        prs = gh_rest(f"repos/{CFG['index_repo']}/pulls", state="all", per_page=100, page=page)
        if not prs:
            break
        for pr in prs:
            if pr["number"] in seen:
                continue
            repos = set(re.findall(r"github\.com/([\w.-]+/[\w.-]+)", f"{pr.get('title', '')} {pr.get('body') or ''}"))
            try:
                for f in gh_rest(f"repos/{CFG['index_repo']}/pulls/{pr['number']}/files", per_page=100):
                    if f["filename"].endswith("meta.json") and f.get("raw_url"):
                        meta = json.loads(http(f["raw_url"], raw=True).decode("utf-8", "ignore"))
                        if meta.get("repo"):
                            repos.update(re.findall(r"github\.com/([\w.-]+/[\w.-]+)", meta["repo"]))
            except Exception as e:
                log(f"  PR #{pr['number']}: {e}")
            for repo in repos:
                repo = re.sub(r"\.git$", "", repo)
                _candidate(db, state, repo, changes, pr.get("title", ""), f"Index-PR #{pr['number']}")
            seen.add(pr["number"])
        if len(prs) < 100:
            break
    state["seen_prs"] = sorted(seen)


# ---------------------------------------------------------------- GitHub-Status aktualisieren

GQL_FIELDS = """
  nameWithOwner description stargazerCount isArchived isFork pushedAt url
  owner { login }
  parent { nameWithOwner }
  openGraphImageUrl usesCustomOpenGraphImage
  latestRelease { tagName publishedAt url releaseAssets(first: 10) { nodes { name downloadUrl } } }
  defaultBranchRef { target { ... on Commit { oid committedDate } } }
"""


def _apply_repo(m, d):
    if d is None:
        if not m.get("deleted"):
            m.setdefault("notes", []).append(f"{TODAY}: Repo nicht mehr erreichbar")
        m["deleted"] = True
        return
    m["deleted"] = False
    m["repo"] = d["nameWithOwner"]
    m["sources"]["github"] = d["url"]
    m["stars"] = d["stargazerCount"]
    m["archived"] = d["isArchived"]
    m["fork"] = d["isFork"]
    m["parent_repo"] = (d.get("parent") or {}).get("nameWithOwner")
    if d.get("usesCustomOpenGraphImage") and not m.get("thumbnail"):
        m["thumbnail"] = d["openGraphImageUrl"]
    if d.get("description") and not m.get("summary"):
        m["summary"] = d["description"]
    if not m.get("author"):
        m["author"] = d["owner"]["login"]
    commit = ((d.get("defaultBranchRef") or {}).get("target") or {})
    rel = d.get("latestRelease")
    if rel:
        zips = [a["downloadUrl"] for a in rel["releaseAssets"]["nodes"] if re.search(r"\.(zip|7z|love)$", a["name"], re.I)]
        m["latest"] = {"version": rel["tagName"], "date": rel["publishedAt"],
                       "url": zips[0] if zips else f"https://github.com/{d['nameWithOwner']}/archive/refs/tags/{rel['tagName']}.zip",
                       "release_url": rel["url"]}
    elif commit.get("oid") and not m.get("in_index"):
        m["latest"] = {"version": f"commit-{commit['oid'][:7]}", "date": commit.get("committedDate"),
                       "url": f"https://github.com/{d['nameWithOwner']}/archive/{commit['oid']}.zip"}
    m["last_activity"] = max(filter(None, [commit.get("committedDate"), (rel or {}).get("publishedAt"), d.get("pushedAt")]), default=None)


def refresh_github_graphql(db):
    mods = [m for m in db.values() if m.get("repo")]
    log(f"GitHub-Status (GraphQL) für {len(mods)} Repos")
    for i in range(0, len(mods), 40):
        chunk = mods[i:i + 40]
        parts = []
        for j, m in enumerate(chunk):
            owner, name = m["repo"].split("/", 1)
            parts.append(f'r{j}: repository(owner: {json.dumps(owner)}, name: {json.dumps(name)}) {{ {GQL_FIELDS} }}')
        r = http("https://api.github.com/graphql", data={"query": "query {" + "\n".join(parts) + "}"})
        data = r.get("data") or {}
        for j, m in enumerate(chunk):
            _apply_repo(m, data.get(f"r{j}"))
            m["last_checked"] = NOW
        time.sleep(1)


def _atom_entries(url):
    """Einträge eines GitHub-Atom-Feeds als (id, link, updated). None = Repo existiert nicht."""
    try:
        xml = http(url, raw=True).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    out = []
    for entry in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        eid = re.search(r"<id>(.*?)</id>", entry)
        link = re.search(r'<link[^>]*href="([^"]+)"', entry)
        upd = re.search(r"<updated>(.*?)</updated>", entry)
        out.append((eid.group(1) if eid else "", link.group(1) if link else "", upd.group(1) if upd else None))
    return out


def _release_asset(repo, tag):
    """Erste .zip-Datei einer Release über die Webseite (ohne API)."""
    try:
        html = http(f"https://github.com/{repo}/releases/expanded_assets/{urllib.parse.quote(tag, safe='')}", raw=True).decode("utf-8", "ignore")
    except Exception:
        return None
    for href in re.findall(r'href="(/[^"]+/releases/download/[^"]+)"', html):
        if re.search(r"\.(zip|7z|love)$", href, re.I):
            return "https://github.com" + href
    return None


MANIFEST_PATHS = ["manifest.json", "{name}/manifest.json", "mod/manifest.json", "src/manifest.json", "mods/{name}/manifest.json"]


def resolve_identity(db, force=False):
    """Echten (ggf. umbenannten) Repo-Namen und die Mod-ID aus manifest.json ermitteln.

    Das sind die stärksten Merkmale gegen Duplikate: zwei Einträge mit demselben echten Repo
    oder derselben Mod-ID sind für das Spiel derselbe Mod.
    """
    todo = [m for m in db.values() if m.get("repo") and not m.get("deleted") and (force or not m.get("resolved"))]
    log(f"Identität (echter Repo-Name, Mod-ID) für {len(todo)} Repos")
    for n, m in enumerate(todo, 1):
        repo = m["repo"]
        try:
            xml = http(f"https://github.com/{repo}/commits.atom", raw=True).decode("utf-8", "ignore")
            link = re.search(r'<link[^>]*href="https://github\.com/([\w.-]+/[\w.-]+)/commits', xml)
            if link:
                m["canonical_repo"] = link.group(1)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                m["deleted"] = True
                continue
        except Exception:
            continue
        canon = m.get("canonical_repo") or repo
        name = canon.split("/")[1]
        for p in MANIFEST_PATHS:
            try:
                raw = http(f"https://raw.githubusercontent.com/{canon}/HEAD/{p.format(name=name)}", raw=True)
                man = json.loads(raw.decode("utf-8-sig", "ignore"))
                if isinstance(man, dict) and man.get("id"):
                    m["manifest_id"] = m.get("manifest_id") or str(man["id"])
                    if man.get("games") and not m.get("games"):
                        m["games"] = man["games"]
                    break
            except Exception:
                continue
        m["resolved"] = TODAY
        if n % 100 == 0:
            log(f"  {n}/{len(todo)}")


def refresh_github_fallback(db, limit=None):
    """Ohne Token: öffentliche Atom-Feeds (Releases + Commits), kein API-Limit, aber keine Sterne/Archiv-Info."""
    mods = [m for m in db.values() if m.get("repo")]
    if limit:
        mods = mods[:limit]
    log(f"GitHub-Status (ohne Token, Atom-Feeds) für {len(mods)} Repos")
    for n, m in enumerate(mods, 1):
        repo = m["repo"]
        try:
            commits = _atom_entries(f"https://github.com/{repo}/commits.atom")
            if commits is None:
                _apply_repo(m, None)
            else:
                m["deleted"] = False
                releases = _atom_entries(f"https://github.com/{repo}/releases.atom") or []
                commit_date = commits[0][2] if commits else None
                sha = commits[0][0].rsplit("/", 1)[-1] if commits else None
                if releases:
                    _, link, rdate = releases[0]
                    tag = urllib.parse.unquote(link.rsplit("/tag/", 1)[1]) if "/tag/" in link else None
                    if tag:
                        old = m.get("latest") or {}
                        url = old.get("url") if old.get("version") == tag and "/releases/download/" in (old.get("url") or "") else None
                        url = url or _release_asset(repo, tag) or f"https://github.com/{repo}/archive/refs/tags/{urllib.parse.quote(tag)}.zip"
                        m["latest"] = {"version": tag, "date": rdate, "release_url": link, "url": url}
                elif sha and not m.get("in_index"):
                    m["latest"] = {"version": f"commit-{sha[:7]}", "date": commit_date,
                                   "url": f"https://github.com/{repo}/archive/{sha}.zip"}
                m["last_activity"] = max(filter(None, [commit_date, (m.get("latest") or {}).get("date")]), default=None)
            m["last_checked"] = NOW
        except Exception as e:
            log(f"  {repo}: {e}")
        if n % 100 == 0:
            log(f"  {n}/{len(mods)}")


# ---------------------------------------------------------------- Seed

def seed():
    db, changes = load_db(), {"new": []}
    seed_dir = ROOT / "seed"
    # 1. Funde aus GitHub-/Web-Suche
    with open(seed_dir / "web-found.tsv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if re.search(r"spam|re-?upload", r.get("note", ""), re.I):
                continue
            cat = (r.get("category") or "OTHER").strip().upper()
            cat = cat if cat in CATEGORIES else "OTHER"
            repo = (r.get("github_repo_or_empty") or "").strip()
            gb = re.search(r"gamebanana\.com/mods/(\d+)", r.get("source_url", ""))
            if repo:
                m = upsert(db, gh_id(repo), r["name"], changes, repo=repo, author=repo.split("/")[0],
                           categories=[cat], gens=guess_gens(f"{r['name']} {r.get('note', '')}"),
                           sources={"github": f"https://github.com/{repo}"}, found_via="Web-/GitHub-Suche")
            elif gb:
                m = upsert(db, f"gb:{gb.group(1)}", r["name"], changes, categories=[cat],
                           gens=guess_gens(r["name"]), sources={"gamebanana": r["source_url"]}, found_via="GameBanana")
            else:
                continue
            if r.get("note"):
                m["seed_note"] = r["note"][:300]
    # 2. Ergänzte Mods (Discord-Funde, Voxel-Extras) inkl. Kategorie
    extra = json.loads((seed_dir / "extra-mods.json").read_text(encoding="utf-8-sig"))
    for x in extra["mods"]:
        if x.get("repo"):
            upsert(db, gh_id(x["repo"]), x["name"], changes, repo=x["repo"], categories=[x["category"]],
                   gens=guess_gens(x["name"]), sources={"github": f"https://github.com/{x['repo']}"})
    for repo in extra.get("voxel_ids_from_index", []):
        upsert(db, gh_id(repo), repo, changes, repo=repo, categories=["VOXEL"])
    # 3. Discord-Threads
    for line in (seed_dir / "discord-threads.txt").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        tid, forum, repo, title = line.split("|", 3)
        url = f"https://discord.com/channels/{DISCORD_GUILD}/{tid}"
        if repo:
            mid = gh_id(repo)
            if mid in db:
                db[mid]["sources"]["discord"] = url
                continue
            m = upsert(db, mid, title, changes, repo=repo, author=repo.split("/")[0], sources={"github": f"https://github.com/{repo}", "discord": url})
        else:
            m = upsert(db, f"dc:{tid}", title, changes, sources={"discord": url}, wip=(forum == "wip"))
            m["discord_only"] = True
        if m["categories"] == ["OTHER"]:
            m["categories"] = ["CART"] if forum == "carts" else guess_categories(title)
            m["gens"] = guess_gens(title)
        if forum == "wip":
            m["wip"] = True
    # 4. Bekannte gelöschte Repos
    for line in (seed_dir / "dead-and-manual.txt").read_text(encoding="utf-8-sig").splitlines():
        mm = re.match(r"- (.+?): https://github\.com/([\w.-]+/[\w.-]+)$", line.strip())
        if mm:
            m = upsert(db, gh_id(mm.group(2)), mm.group(1), changes, repo=mm.group(2), author=mm.group(2).split("/")[0],
                       sources={"github": f"https://github.com/{mm.group(2)}"})
            m["deleted"] = True
    for m in db.values():
        m["status"] = compute_status(m, CFG)
    save_db(db)
    log(f"Seed fertig: {len(changes['new'])} Einträge übernommen")


# ---------------------------------------------------------------- Crawl

def crawl(limit=None):
    db, state = load_db(), load_state()
    before = {mid: ((m.get("latest") or {}).get("version"), m.get("status")) for mid, m in db.items()}
    changes = {"new": []}
    for step in (lambda: source_index(db, changes),
                 lambda: source_gamebanana(db, changes),
                 lambda: source_index_prs(db, state, changes),
                 lambda: source_github_search(db, state, changes)):
        try:
            step()
        except Exception as e:
            log(f"  Quelle fehlgeschlagen: {e}")
        save_state(state)
    if TOKEN:
        refresh_github_graphql(db)
    else:
        refresh_github_fallback(db, limit)
    updated, status_changed = [], []
    for mid, m in db.items():
        m["status"] = compute_status(m, CFG)
        old_ver, old_status = before.get(mid, (None, None))
        new_ver = (m.get("latest") or {}).get("version")
        if mid in before and new_ver and old_ver and new_ver.lstrip("vV") != old_ver.lstrip("vV"):
            updated.append({"id": mid, "name": m["name"], "from": old_ver, "to": new_ver})
        if mid in before and old_status and old_status != m["status"]:
            status_changed.append({"id": mid, "name": m["name"], "from": old_status, "to": m["status"]})
    save_db(db)
    save_state(state)
    hist = json.loads(CHANGES_PATH.read_text(encoding="utf-8")) if CHANGES_PATH.exists() else []
    entry = {"date": NOW, "new": [{"id": i, "name": db[i]["name"]} for i in changes["new"]],
             "updated": updated, "status_changed": status_changed}
    hist = ([entry] + hist)[:90]
    CHANGES_PATH.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"Fertig: {len(changes['new'])} neu, {len(updated)} Updates, {len(status_changed)} Statuswechsel")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "crawl"
    if cmd == "seed":
        seed()
    elif cmd == "organize":
        save_db(load_db())
    elif cmd == "resolve":
        _db = load_db()
        resolve_identity(_db, force="--force" in sys.argv)
        save_db(_db)
    elif cmd == "quick":   # nur Index + GameBanana, ohne alle Repos abzufragen
        _db, _ch = load_db(), {"new": []}
        source_index(_db, _ch)
        source_gamebanana(_db, _ch)
        for _m in _db.values():
            _m["status"] = compute_status(_m, CFG)
        save_db(_db)
    elif cmd == "crawl":
        lim = int(sys.argv[2]) if len(sys.argv) > 2 else None
        crawl(lim)
    else:
        print(__doc__)
