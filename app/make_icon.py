"""Erzeugt app/icon.ico (Pokéball) für die EXE."""
from pathlib import Path

from PIL import Image, ImageDraw

S = 256
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
pad, w = 10, 18
d.ellipse([pad, pad, S - pad, S - pad], fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=w)
d.pieslice([pad, pad, S - pad, S - pad], 180, 360, fill=(227, 53, 13, 255), outline=(20, 20, 20, 255), width=w)
d.rectangle([pad, S // 2 - w // 2, S - pad, S // 2 + w // 2], fill=(20, 20, 20, 255))
r = 40
d.ellipse([S // 2 - r, S // 2 - r, S // 2 + r, S // 2 + r], fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=w)
img.save(Path(__file__).with_name("icon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
