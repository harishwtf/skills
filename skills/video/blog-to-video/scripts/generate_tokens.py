#!/usr/bin/env python3
"""
Generate tokens.ts and fonts.ts from a brand-config.json

Usage:
  python3 generate_tokens.py --brand brands/zuddl/brand-config.json --output brands/zuddl/
  python3 generate_tokens.py --brand brands/zuddl/brand-config.json --output my-project/src/

Generates:
  - tokens.ts (COLORS, GRADIENTS, SPACING, RADIUS, SHADOWS)
  - fonts.ts (Google Font loading)
"""

import json
import argparse
from pathlib import Path


def generate_tokens_ts(config: dict) -> str:
    c = config["colors"]
    g = config["gradients"]
    s = config["shadows"]
    sp = config["spacing"]
    r = config["radius"]
    brand = config["brand_name"]

    angle = g["brand_angle"]
    g_start = g["brand_start"]
    g_end = g["brand_end"]
    radial_rgb = g["bg_radial_color"]
    radial_op = g["bg_radial_opacity"]
    base_rgb = s["base_rgb"]
    prim_rgb = s["primary_rgb"]

    return f"""// Design tokens — {brand}
// Auto-generated from brand-config.json — do not edit manually

export const COLORS = {{
  BG: '{c["bg"]}',
  BG_SOFT: '{c["bg_soft"]}',
  SURFACE: '{c["surface"]}',
  SURFACE_SOFT: '{c["surface_soft"]}',
  HEADING: '{c["heading"]}',
  BODY: '{c["body"]}',
  MUTED: '{c["muted"]}',
  PRIMARY: '{c["primary"]}',
  PRIMARY_DARK: '{c["primary_dark"]}',
  BORDER_SOFT: '{c["border_soft"]}',
  BORDER: '{c["border"]}',
  WHITE: '{c["white"]}',
}} as const;

export const GRADIENTS = {{
  BRAND: 'linear-gradient({angle}deg, {g_start} 0%, {g_end} 100%)',
  BRAND_SOFT: 'linear-gradient({angle}deg, rgba({prim_rgb},0.12) 0%, rgba({int(g_end[1:3],16)},{int(g_end[3:5],16)},{int(g_end[5:7],16)},0.12) 100%)',
  BG_RADIAL: 'radial-gradient(ellipse at 20% 50%, rgba({radial_rgb},{radial_op}) 0%, transparent 60%)',
  CARD_BORDER: 'linear-gradient({angle}deg, rgba({prim_rgb},0.3), rgba({int(g_end[1:3],16)},{int(g_end[3:5],16)},{int(g_end[5:7],16)},0.15))',
}} as const;

export const SPACING = {{
  BASE: 8,
  XS: {sp["xs"]},
  SM: {sp["sm"]},
  MD: {sp["md"]},
  LG: {sp["lg"]},
  XL: {sp["xl"]},
  XXL: {sp["xxl"]},
  SECTION_X: {sp["section_x"]},
  SECTION_Y: {sp["section_y"]},
}} as const;

export const RADIUS = {{
  XS: {r["xs"]},
  SM: {r["sm"]},
  MD: {r["md"]},
  LG: {r["lg"]},
  XL: {r["xl"]},
  XXL: {r["xxl"]},
  PILL: {r["pill"]},
}} as const;

export const SHADOWS = {{
  CARD: '0 2px 8px rgba({base_rgb},0.08), 0 1px 2px rgba({base_rgb},0.04)',
  CARD_ELEVATED: '0 8px 32px rgba({base_rgb},0.12), 0 2px 8px rgba({base_rgb},0.06)',
  ICON_TILE: '0 4px 16px rgba({prim_rgb},0.28), 0 1px 4px rgba({prim_rgb},0.16)',
  BUTTON: '0 4px 16px rgba({prim_rgb},0.35)',
}} as const;
"""


def generate_fonts_ts(config: dict) -> str:
    f = config["font"]
    font_id = f["google_font_id"]
    import_path = f["import_path"]
    weights = ", ".join(f'"{w}"' for w in f["weights"])
    subsets = ", ".join(f'"{s}"' for s in f["subsets"])

    return f"""import {{ loadFont }} from "{import_path}";

const {{ fontFamily }} = loadFont("normal", {{
  weights: [{weights}],
  subsets: [{subsets}],
}});

export {{ fontFamily }};
"""


def main():
    parser = argparse.ArgumentParser(description="Generate tokens.ts and fonts.ts from brand config")
    parser.add_argument("--brand", required=True, help="Path to brand-config.json")
    parser.add_argument("--output", required=True, help="Output directory for generated files")
    args = parser.parse_args()

    with open(args.brand) as f:
        config = json.load(f)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    tokens_path = out / "tokens.ts"
    tokens_path.write_text(generate_tokens_ts(config))
    print(f"  Generated {tokens_path}")

    fonts_path = out / "fonts.ts"
    fonts_path.write_text(generate_fonts_ts(config))
    print(f"  Generated {fonts_path}")

    print(f"\nBrand '{config['brand_name']}' tokens ready.")
    if config.get("design_rules"):
        print("\nDesign rules:")
        for rule in config["design_rules"]:
            print(f"  - {rule}")


if __name__ == "__main__":
    main()
