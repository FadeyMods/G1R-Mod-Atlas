"""Duplikate zusammenfassen, Nicht-Mods erkennen und den Feed im Format des Spiels erzeugen.

Jeder Eintrag bekommt:
  kind     mod | cart | tool | collection | index | port | discussion
  family   id des Haupteintrags seiner Gruppe (bei sich selbst = eigene id)
  variants (nur Haupteintrag) Liste der zusammengefassten Einträge
  merged_by (nur Varianten) warum zusammengefasst wurde

Zusammengefasst wird in dieser Reihenfolge (harte Regeln zuerst):
  1. gleiches echtes Repo (Umbenennungen/Umzüge auf GitHub)
  2. gleiche Mod-ID aus manifest.json (für das Spiel derselbe Mod)
  3. identische Download-Datei
  4. Hand-Entscheidungen aus overrides.json ("same")
  5. Fork ohne eigene Release -> zum Original
  6. Discord-/GameBanana-Eintrag mit sehr ähnlichem Namen -> zum GitHub-/Index-Eintrag
  7. gleicher Name und (gleicher Autor oder einer ist Spiegel/Archiv/gelöscht)
Regeln 6 und 7 werden durch overrides.json ("different") abgeschaltet.
"""
import difflib
import json
import re
from collections import defaultdict
from pathlib import Path

OVERRIDES = json.loads((Path(__file__).parent / "overrides.json").read_text(encoding="utf-8"))
ALIAS = {k.lower(): v.lower() for k, v in OVERRIDES.get("author_alias", {}).items()}
GENERIC_IDS = set(OVERRIDES.get("generic_manifest_ids", []))

_STOP = (r"\b(gen1recomp\+*|gen2recomp|g1r|recomp|mod|mods|for|the|v?\d+(\.\d+)*|beta|alpha|wip|fork|edit|version|"
         r"released?|update[ds]?|archive|backup|mirror|test|latest|old|new|unofficial|official|discontinued|outdated|"
         r"retired|dropped|now|pokemon|pokémon|release)\b")


def norm(name):
    """Name ohne Füllwörter. Gen-Angaben bleiben als Suffix: Gen-Varianten sind eigene Mods."""
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name or "")          # CamelCase trennen
    s = s.lower().replace("-", " ").replace("_", " ")
    gens = "".join(sorted(set(re.findall(r"gen ?([123])\b", s))))
    s = re.sub(r"gen ?[123]\b", " ", s)
    s = re.sub(r"\(.*?\)|\[.*?\]", " ", s)
    s = re.sub(_STOP, " ", s)
    s = re.sub(r"[^a-z0-9]+", "", s)
    return f"{s}#g{gens}" if s and gens else s


def author_key(m):
    a = (m.get("author") or (m.get("repo") or "/").split("/")[0] or "").lower()
    a = re.sub(r"\s*#.*$|\s*\[.*?\]$", "", a).strip()
    return ALIAS.get(a, a)


def detect_kind(m):
    name = (m.get("name") or "").lower()
    repo = (m.get("canonical_repo") or m.get("repo") or "").lower().split("/")[-1]
    text = f"{name} {repo} {(m.get('summary') or '').lower()[:200]}"
    cat = m["categories"][0]
    if m["id"].startswith("dc:") and re.search(r"\?|request|help|anyone|please|looking for|suggestion|wanted|^test$|^ee$|guide|tutorial|assets for", name):
        return "discussion"
    if re.search(r"mod-?index|^index$|-index$|personal index", repo) or re.search(r"\bmod index\b", name):
        return "index"
    if re.search(r"^(gen[123]-?recomp-?mods?|mods|recomp-mods|.*-mod-releases|.*carts_and_mods|monorepo|gen[123]recomp|g1recompmods|pokemon-mods)$", repo):
        return "collection"
    if re.search(r"\b(port|trimui|vita|psp|3ds port|ios|switch|android|linux|rpm|pwa|flatpak|apk|love-nx|mac[- ]fix|installer)\b", text) and cat in ("OTHER", "TOOL"):
        return "port"
    if cat == "CART":
        return "cart"
    if cat == "TOOL":
        return "tool"
    return "mod"


def _score(m):
    """Höher = besserer Haupteintrag: verfügbar, echte Release, NEUESTE Version, dann Index/echtes Repo."""
    lat = m.get("latest") or {}
    return (
        m.get("status") != "deleted",
        bool(lat.get("url")),
        "/releases/download/" in (lat.get("url") or "") or "gamebanana" in (lat.get("url") or ""),
        (lat.get("date") or "")[:10],
        bool(m.get("in_index")),
        not m["id"].startswith(("dc:", "gb:")),
        not m.get("fork", False),
        m.get("stars") or 0,
    )


def _is_mirror(x):
    if x["id"].startswith(("dc:", "gb:")):
        return True
    if x.get("status") in ("deleted", "archived"):
        return True
    if x.get("fork") and not (x.get("latest") or {}).get("release_url"):
        return True
    return bool(re.search(r"archive|backup|mirror|test|copy|-latest$", (x.get("repo") or "").lower()))


def _similar(a, b):
    na, nb = norm(a["name"]), norm(b["name"])
    if not na or not nb or na.split("#")[1:] != nb.split("#")[1:]:
        return 0.0
    ka, kb = na.split("#")[0], nb.split("#")[0]
    if len(ka) < 4 or len(kb) < 4:
        return 0.0
    if ka == kb:
        return 1.0
    if (ka in kb or kb in ka) and min(len(ka), len(kb)) >= 6:
        return 0.9
    return difflib.SequenceMatcher(None, ka, kb).ratio()


def organize(db):
    mods = list(db.values())
    for m in mods:
        m["kind"] = detect_kind(m)
        m.pop("variants", None)
        m.pop("merged_by", None)
        m["family"] = m["id"]
    ids = {m["id"] for m in mods}
    different = {frozenset(p) for p in OVERRIDES.get("different", []) if len(p) == 2}

    parent = {m["id"]: m["id"] for m in mods}
    reason = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b, why, soft=False):
        if soft and frozenset((a, b)) in different:
            return
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
            reason.setdefault(b, why)

    def group_by(keyfn, why):
        seen = {}
        for m in mods:
            k = keyfn(m)
            if not k:
                continue
            if k in seen:
                union(seen[k], m["id"], why)
            else:
                seen[k] = m["id"]

    # 1-3: harte Merkmale
    group_by(lambda m: (m.get("canonical_repo") or m.get("repo") or "").lower() or None, "gleiches Repo")
    group_by(lambda m: (m.get("manifest_id") or "").lower() if (m.get("manifest_id") or "").lower() not in GENERIC_IDS else None, "gleiche Mod-ID")
    group_by(lambda m: (m.get("latest") or {}).get("url") if "/releases/download/" in ((m.get("latest") or {}).get("url") or "") else None, "gleicher Download")
    # 4: Hand-Entscheidungen
    for a, b in OVERRIDES.get("same", []):
        if a in ids and b in ids:
            union(a, b, "Hand-Entscheidung")
    # 5: Forks ohne eigene Release
    by_repo = {(m.get("canonical_repo") or m.get("repo") or "").lower(): m for m in mods if m.get("repo")}
    for m in mods:
        p = (m.get("parent_repo") or "").lower()
        if m.get("fork") and p in by_repo and not (m.get("latest") or {}).get("release_url"):
            union(by_repo[p]["id"], m["id"], "Fork ohne eigene Release")
    # 6: Discord/GameBanana -> GitHub/Index per Namensähnlichkeit
    real = [m for m in mods if m["kind"] != "discussion" and not m["id"].startswith(("dc:", "gb:"))]
    for m in mods:
        if not m["id"].startswith(("dc:", "gb:")) or m["kind"] == "discussion":
            continue
        best, best_s = None, 0.0
        for r in real:
            s = _similar(m, r)
            if s > best_s or (s == best_s and best and _score(r) > _score(best)):
                best, best_s = r, s
        if best and best_s >= 0.86:
            union(best["id"], m["id"], f"Discord/GameBanana-Eintrag zu {best.get('repo') or best['id']}", soft=True)
    # 7: gleicher Name + Spiegel oder gleicher Autor
    groups = defaultdict(list)
    for m in mods:
        if m["kind"] == "discussion":
            continue
        k = norm(m["name"])
        if len(k.split("#")[0]) >= 4:
            groups[k].append(m)
    for members in groups.values():
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                if _is_mirror(a) or _is_mirror(b) or author_key(a) == author_key(b):
                    union(a["id"], b["id"], "gleicher Name (Spiegel/gleicher Autor)", soft=True)

    fam = defaultdict(list)
    for m in mods:
        fam[find(m["id"])].append(m)
    for members in fam.values():
        best = max(members, key=_score)
        for m in members:
            m["family"] = best["id"]
        if len(members) > 1:
            best["variants"] = sorted(m["id"] for m in members if m is not best)
            for m in members:
                if m is not best:
                    m["merged_by"] = reason.get(m["id"]) or reason.get(best["id"]) or "Gruppe"
                for k, v in (m.get("sources") or {}).items():
                    best["sources"].setdefault(k, v)
                if m.get("in_index"):
                    best["in_index"] = True
                if m.get("downloads") and not best.get("downloads"):
                    best["downloads"] = m["downloads"]
                if m.get("thumbnail") and not best.get("thumbnail"):
                    best["thumbnail"] = m["thumbnail"]
            # Kind des Haupteintrags: wenn irgendein Mitglied ein echter Mod ist, ist es ein Mod
            kinds = {m["kind"] for m in members}
            if best["kind"] in ("discussion", "index", "collection", "port") and kinds & {"mod", "tool", "cart"}:
                best["kind"] = next(k for k in ("mod", "cart", "tool") if k in kinds)
    return len(fam)


GEN_GAMES = {1: ["red", "blue", "yellow"], 2: ["gold", "silver", "crystal"],
             3: ["firered", "leafgreen", "ruby", "sapphire", "emerald"]}


def installable(m):
    url = (m.get("latest") or {}).get("url") or ""
    return bool(re.search(r"/releases/download/|gamebanana\.com/dl/|gamebanana\.com/mmdl/", url)) and m.get("status") != "deleted"


def game_feed(db, now, index_raw=None):
    """Feed im Format von bryanthaboi/gen1recomp-mod-index (schema_version 1).

    Enthält nur Mods, die NICHT im offiziellen Index sind (sonst doppelt im Spiel),
    nur Haupteinträge und nur Mods mit installierbarer Release-Zip.
    """
    out = []
    for m in sorted(db.values(), key=lambda x: x["name"].lower()):
        if m["family"] != m["id"] or m.get("in_index") or m["kind"] not in ("mod", "tool") or not installable(m):
            continue
        lat = m["latest"]
        mid = m.get("manifest_id") or re.sub(r"[^a-z0-9_]+", "_", (m.get("repo") or m["id"]).split("/")[-1].lower()).strip("_")
        entry = {
            "folder": f"{m.get('author') or 'unknown'}@{mid}",
            "id": mid,
            "title": m["name"],
            "author": m.get("author") or "",
            "version": (lat.get("version") or "").lstrip("vV"),
            "categories": [c for c in m["categories"] if c not in ("VOXEL",)] or ["ART"],
            "tags": (["voxel"] if "VOXEL" in m["categories"] else []) + ["unlisted"],
            "summary": (m.get("summary") or "")[:300],
            "latest": {
                "version": (lat.get("version") or "").lstrip("vV"),
                "tag": lat.get("version"),
                "name": lat.get("version"),
                "prerelease": False,
                "published_at": lat.get("date"),
                "zip": {"name": lat["url"].rsplit("/", 1)[-1], "url": lat["url"]},
            },
            "update_check": "ok",
            "last_release": lat.get("date"),
        }
        if m.get("games"):
            entry["games"] = m["games"]
        if m.get("repo"):
            entry["repo"] = f"https://github.com/{m.get('canonical_repo') or m['repo']}"
            entry["github"] = m.get("canonical_repo") or m["repo"]
        out.append(entry)
    return {"schema_version": 1, "generated_at": now, "count": len(out), "mods": out, "carts": []}
