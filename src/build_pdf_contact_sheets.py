from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build 2x2 contact sheets from rendered PDF pages")
    parser.add_argument("page_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--prefix", default="tmlr-page")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pages = sorted(args.page_dir.glob(f"{args.prefix}-*.png"))
    if not pages:
        raise FileNotFoundError(f"No rendered pages found in {args.page_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=20)
    thumb_width, thumb_height = 440, 570
    margin, label_height = 24, 34
    sheet_width = 2 * thumb_width + 3 * margin
    sheet_height = 2 * (thumb_height + label_height) + 3 * margin
    for group_index in range(0, len(pages), 4):
        group = pages[group_index : group_index + 4]
        sheet = Image.new("RGB", (sheet_width, sheet_height), "white")
        draw = ImageDraw.Draw(sheet)
        for local_index, path in enumerate(group):
            row, column = divmod(local_index, 2)
            x = margin + column * (thumb_width + margin)
            y = margin + row * (thumb_height + label_height + margin)
            with Image.open(path) as page:
                preview = page.convert("RGB")
                preview.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                px = x + (thumb_width - preview.width) // 2
                py = y + label_height + (thumb_height - preview.height) // 2
                sheet.paste(preview, (px, py))
                draw.rectangle(
                    (px - 1, py - 1, px + preview.width, py + preview.height),
                    outline="#777777",
                    width=1,
                )
            draw.text((x, y), f"Page {group_index + local_index + 1}", fill="black", font=font)
        output = args.output_dir / f"contact-{group_index // 4 + 1}.png"
        sheet.save(output)
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
