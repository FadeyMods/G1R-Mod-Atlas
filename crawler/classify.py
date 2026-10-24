"""Kategorien, Gens und Status aus Name/Beschreibung ableiten."""
import re
from datetime import datetime, timezone

CATEGORIES = ["VOXEL", "QOL", "UI", "GAMEPLAY", "CONTENT", "BALANCE", "ART", "AUDIO",
              "TRANSLATION", "TOTAL_CONVERSION", "LIBRARY", "TOOL", "CART", "OTHER"]

# Reihenfolge = Vorrang bei der Erkennung
_RULES = [
    ("VOXEL", r"voxel|diorama|\b3d\b|first.person|third.person|dramatic.?shape|dramaless|terrarium|stadium model|camera"),
    ("TRANSLATION", r"translat|traduç|traduc|übersetz|deutsch|german|español|italian|french|portugu|pt-br|finnish|norweg|chinese|japanese|korean|polish|dutch|russian|turkish|thai|vietnam|indonesi"),
    ("CART", r"\bcart\b|custom cart"),
    ("TOTAL_CONVERSION", r"total conversion|rom.?hack|randomizer|ironmon|kaizo|remake|port of"),
    ("LIBRARY", r"\blib\b|library|framework|dependency|api for"),
    ("TOOL", r"editor|tool|converter|exporter|importer|viewer|maker|generator|debug|cheat|launcher|index"),
    ("AUDIO", r"music|sound|audio|\bost\b|cries|\bcry\b|sfx|soundtrack"),
    ("UI", r"\bui\b|hud|menu|font|interface|screen|overlay|widescreen|layout"),
    ("QOL", r"\bqol\b|quality of life|autosave|hotkey|fast|instant|skip|speed|reusable|convenien|shortcut|fix"),
    ("BALANCE", r"balanc|level cap|difficult|scaling|stat|nerf|buff"),
    ("ART", r"sprite|palette|graphic|texture|art\b|skin|shader|portrait|backsprite|icon"),
    ("CONTENT", r"quest|event|region|new pok|pokedex|dex|area|map|story|npc|trainer|gym|mega|shiny|follower"),
    ("GAMEPLAY", r"battle|mechanic|mode|catch|encounter|online|multiplayer|co-op|nuzlocke|evolution|mount|bike|fishing"),
]

_GEN_RULES = [
    (1, r"\bgen ?1\b|red|blue|yellow|kanto|rby\b"),
    (2, r"\bgen ?2\b|gold|silver|crystal|johto|gsc\b"),
    (3, r"\bgen ?3\b|firered|fire red|leafgreen|leaf green|ruby|sapphire|emerald|hoenn|frlg\b|rse\b"),
]

INDEX_CATEGORY_MAP = {c: c for c in CATEGORIES}


def guess_categories(text):
    t = (text or "").lower()
    for cat, rx in _RULES:
        if re.search(rx, t):
            return [cat]
    return ["OTHER"]


def guess_gens(text):
    t = (text or "").lower()
    gens = [g for g, rx in _GEN_RULES if re.search(rx, t)]
    return gens or [1]


def _days_since(iso):
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - dt).days


def compute_status(mod, cfg):
    """deleted > archived > abandoned > wip > inactive > active"""
    if mod.get("deleted"):
        return "deleted"
    if mod.get("archived"):
        return "archived"
    text = f"{mod.get('name', '')} {mod.get('summary', '')}".lower()
    if any(w in text for w in cfg["abandoned_words"]):
        return "abandoned"
    days = _days_since(mod.get("last_activity"))
    if days is not None and days > cfg["abandoned_after_days"]:
        return "abandoned"
    if mod.get("wip") or not (mod.get("latest") or {}).get("url"):
        return "wip"
    if days is not None and days > cfg["inactive_after_days"]:
        return "inactive"
    return "active"
