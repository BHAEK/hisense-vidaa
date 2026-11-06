"""Generate the integration icons (requires Pillow; not needed at runtime or in CI).

The artwork is a generic television symbol drawn from scratch: it deliberately does not
reuse any manufacturer or platform logo.

Usage:
    python tools/generate_brand.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUTPUT = Path(__file__).resolve().parent.parent / "custom_components" / "hisense_vidaa" / "brand"
SUPERSAMPLE = 4
LIGHT = (11, 110, 153, 255)  # for white backgrounds
DARK = (143, 211, 244, 255)  # for dark backgrounds


def draw_icon(size: int, colour: tuple[int, int, int, int]) -> Image.Image:
    """A television with a play symbol, trimmed to the canvas (no padding)."""
    big = size * SUPERSAMPLE
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    stroke = big // 14
    screen_bottom = int(big * 0.80)
    pen.rounded_rectangle(
        (stroke // 2, stroke // 2, big - stroke // 2, screen_bottom),
        radius=big // 9,
        outline=colour,
        width=stroke,
    )
    # stand
    pen.rounded_rectangle(
        (int(big * 0.34), int(big * 0.88), int(big * 0.66), big - stroke // 2),
        radius=stroke // 2,
        fill=colour,
    )
    pen.rectangle((int(big * 0.46), screen_bottom, int(big * 0.54), int(big * 0.90)), fill=colour)
    # play symbol
    cx, cy = big // 2, int(big * 0.41)
    half_h, half_w = int(big * 0.17), int(big * 0.15)
    pen.polygon(
        [(cx - half_w, cy - half_h), (cx - half_w, cy + half_h), (cx + half_w + stroke // 2, cy)],
        fill=colour,
    )
    return image.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for prefix, colour in (("", LIGHT), ("dark_", DARK)):
        draw_icon(256, colour).save(OUTPUT / f"{prefix}icon.png", optimize=True)
        draw_icon(512, colour).save(OUTPUT / f"{prefix}icon@2x.png", optimize=True)
    print(f"written to {OUTPUT}")


if __name__ == "__main__":
    main()
