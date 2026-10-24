"""Prüfbericht: Was wurde zusammengefasst, und welche sichtbaren Mods sehen sich noch ähnlich?

  python crawler/audit.py            -> Bericht auf der Konsole
  python crawler/audit.py --md FILE  -> zusätzlich als Markdown-Datei
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from organize import _similar, author_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
d = json.loads((ROOT / "docs" / "data" / "mods.json").read_text(encoding="utf-8"))
mods = d["mods"]
by = {m["id"]: m for m in mods}
visible = [m for m in mods if m["family"] == m["id"] and m["kind"] in ("mod", "cart", "tool")]

lines = []
p = lines.append
p(f"# Duplikat-Prüfbericht ({d['generated_at'][:10]})\n")
p(f"- Einträge gesamt: {len(mods)}")
p(f"- Sichtbare Mods (ein Eintrag je Mod): {len(visible)}")
merged = [m for m in mods if m["family"] != m["id"]]
p(f"- Zusammengefasste Duplikate: {len(merged)}")
for why, n in Counter(m.get("merged_by", "?").split(" zu ")[0] for m in merged).most_common():
    p(f"  - {why}: {n}")
kinds = Counter(m["kind"] for m in mods if m["family"] == m["id"] and m["kind"] not in ("mod", "cart", "tool"))
p(f"- Ausgeblendet (keine Mods): {dict(kinds)}")

# Gleiche Mod-ID / gleiches Repo dürfen unter den sichtbaren nicht mehrfach vorkommen
for label, key in (("Mod-ID", lambda m: (m.get("manifest_id") or "").lower()),
                   ("Repo", lambda m: (m.get("canonical_repo") or m.get("repo") or "").lower())):
    c = Counter(key(m) for m in visible if key(m))
    dup = [k for k, n in c.items() if n > 1]
    p(f"- Sichtbar doppelte {label}: {len(dup)} {dup[:10] if dup else ''}")

p("\n## Noch ähnliche sichtbare Mods (bitte prüfen)\n")
sus = []
for i, a in enumerate(visible):
    for b in visible[i + 1:]:
        s = _similar(a, b)
        if s >= 0.8:
            sus.append((s, a, b))
sus.sort(key=lambda x: -x[0])
for s, a, b in sus:
    same_author = "gleicher Autor" if author_key(a) == author_key(b) else "andere Autoren"
    p(f"- {s:.2f} | {a['name']} [{a.get('repo') or a['id']}] <> {b['name']} [{b.get('repo') or b['id']}] | {same_author}")
p(f"\n{len(sus)} Paare")

text = "\n".join(lines)
print(text)
if "--md" in sys.argv:
    Path(sys.argv[sys.argv.index("--md") + 1]).write_text(text, encoding="utf-8")
