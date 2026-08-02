"""Build frozen paper tables and publication-ready static figures.

This script only reads completed JSON reports. It never re-runs inference or
statistical resampling, so the confirmatory results remain frozen.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
TABLES = PAPER / "tables"
FIGURES = PAPER / "figures"
SONNET_REPORT = ROOT / "results/api/sob_sonnet5_confirmatory_report.json"
GPT_REPORT = ROOT / "results/api/sob_gpt55_cross_model_report.json"
EXPLORATORY_REPORT = ROOT / "results/analysis/sob_cross_model_exploratory.json"
DECOMP_SONNET_REPORT = ROOT / "results/api/sob_decomposed_sonnet5_report.json"
DECOMP_GPT_REPORT = ROOT / "results/api/sob_decomposed_gpt55_report.json"
DECOMP_DEEPSEEK_REPORT = (
    ROOT / "results/api/sob_official_deepseek_v4_flash_report.json"
)
DECOMP_QWEN_REPORT = (
    ROOT / "results/api/sob_official_qwen_plus_resource_full160_report.json"
)
QWEN_JSON_REPORT = (
    ROOT / "results/api/sob_official_qwen_plus_json_mode_100_report.json"
)
QWEN_INTERACTION_REPORT = (
    ROOT / "results/api/sob_official_qwen_plus_mode_interaction_100_report.json"
)
ROBUSTNESS_REPORT = ROOT / "results/api/sob_decomposed_robustness_audit.json"
DECOMP_CROSS_REPORT = ROOT / "results/analysis/sob_decomposed_cross_model.json"

VARIANTS = (
    "properties_reversed",
    "required_reversed",
    "keywords_reversed",
    "descriptions_first",
)
DISPLAY = {
    "original": "Original",
    "properties_reversed": "Properties reversed",
    "required_reversed": "Required reversed",
    "keywords_reversed": "Keywords reversed",
    "descriptions_first": "Descriptions first",
}
MODELS = (
    ("Sonnet gateway alias", "sonnet", SONNET_REPORT),
    ("GPT gateway alias", "gpt", GPT_REPORT),
)
DECOMP_CONTRASTS = (
    "property_order",
    "additional_keyword_order_given_reversed_properties",
)
DECOMP_DISPLAY = {
    "property_order": "Property order",
    "additional_keyword_order_given_reversed_properties": "Additional member order",
}

INK = "#172033"
MUTED = "#667085"
GRID = "#D0D5DD"
BLUE = "#2563A6"
BLUE_LIGHT = "#DCEAF7"
ORANGE = "#C66A1B"
ORANGE_LIGHT = "#FBE8D5"
GREEN = "#23856D"
PURPLE = "#7656A8"
TEAL = "#007C83"
GOLD = "#A07914"
PANEL = "#F8FAFC"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    )
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], value: str, size: int,
         *, fill: str = INK, bold: bool = False, anchor: str | None = None) -> None:
    draw.text(xy, value, font=font(size, bold), fill=fill, anchor=anchor)


def rounded_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int],
                *, fill: str, outline: str = GRID, radius: int = 18, width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int],
          *, fill: str = MUTED, width: int = 4) -> None:
    draw.line((start, end), fill=fill, width=width)
    x, y = end
    draw.polygon([(x, y), (x - 13, y - 8), (x - 13, y + 8)], fill=fill)


def build_method_figure() -> None:
    image = Image.new("RGB", (1800, 560), "white")
    draw = ImageDraw.Draw(image)
    text(draw, (80, 44), "Schema-serialization metamorphic testing workflow", 38, bold=True)
    text(
        draw,
        (80, 92),
        "Only the JSON Schema serialization changes; task content and prompt template remain fixed.",
        23,
        fill=MUTED,
    )

    boxes = [
        (70, 185, 330, 420),
        (405, 160, 735, 445),
        (810, 185, 1075, 420),
        (1150, 165, 1460, 440),
        (1535, 185, 1740, 420),
    ]
    fills = [PANEL, BLUE_LIGHT, PANEL, ORANGE_LIGHT, PANEL]
    for box, fill in zip(boxes, fills):
        rounded_box(draw, box, fill=fill)
    for left, right in zip(boxes, boxes[1:]):
        arrow(draw, (left[2] + 16, 302), (right[0] - 16, 302))

    text(draw, (200, 220), "Frozen task", 26, bold=True, anchor="ma")
    text(draw, (200, 270), "Context", 23, anchor="ma")
    text(draw, (200, 305), "Question", 23, anchor="ma")
    text(draw, (200, 340), "JSON Schema", 23, anchor="ma")
    text(draw, (200, 382), "Frozen record panels", 20, fill=MUTED, anchor="ma")

    text(draw, (570, 190), "Validation-equivalent", 25, bold=True, anchor="ma")
    text(draw, (570, 225), "serializations", 25, bold=True, anchor="ma")
    variants = ["Original", "Properties reversed", "Required reversed", "Member order reversed", "Descriptions first"]
    for idx, label in enumerate(variants):
        text(draw, (570, 275 + idx * 31), label, 20, anchor="ma")

    text(draw, (942, 220), "Black-box calls", 26, bold=True, anchor="ma")
    text(draw, (942, 275), "5 repeats", 23, anchor="ma")
    text(draw, (942, 310), "per representation", 23, anchor="ma")
    text(draw, (942, 355), "gateway + official APIs", 20, fill=MUTED, anchor="ma")
    text(draw, (942, 385), "text and JSON Mode", 20, fill=MUTED, anchor="ma")

    text(draw, (1305, 198), "Independent oracles", 25, bold=True, anchor="ma")
    text(draw, (1305, 260), "JSON parsing", 21, anchor="ma")
    text(draw, (1305, 298), "Schema validation", 21, anchor="ma")
    text(draw, (1305, 336), "Gold leaf accuracy", 21, anchor="ma")
    text(draw, (1305, 374), "Output normalization", 21, anchor="ma")
    text(draw, (1305, 412), "Deterministic; no LLM judge", 19, fill=MUTED, anchor="ma")

    text(draw, (1638, 218), "Noise-adjusted", 23, bold=True, anchor="ma")
    text(draw, (1638, 250), "comparison", 23, bold=True, anchor="ma")
    text(draw, (1638, 310), "cross", 22, anchor="ma")
    text(draw, (1638, 345), "minus", 19, fill=MUTED, anchor="ma")
    text(draw, (1638, 380), "within-prompt", 22, anchor="ma")

    text(
        draw,
        (900, 515),
        "Excess disagreement = cross(original, variant) - 0.5 x [within(original) + within(variant)]",
        22,
        fill=INK,
        anchor="mm",
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    image.crop((0, 135, image.width, image.height)).save(
        FIGURES / "figure1_method.png", dpi=(180, 180)
    )


def xmap(value: float, domain: tuple[float, float], left: int, right: int) -> float:
    low, high = domain
    return left + (value - low) / (high - low) * (right - left)


def marker(draw: ImageDraw.ImageDraw, x: float, y: float, model: str) -> None:
    if model == "sonnet":
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=BLUE, outline=INK, width=1)
    elif model == "gpt":
        draw.rectangle((x - 8, y - 8, x + 8, y + 8), fill="white", outline=ORANGE, width=4)
    elif model == "deepseek":
        draw.polygon(
            ((x, y - 10), (x - 10, y + 8), (x + 10, y + 8)),
            fill=GREEN,
            outline=INK,
        )
    elif model == "qwen":
        draw.polygon(
            ((x, y - 10), (x - 10, y), (x, y + 10), (x + 10, y)),
            fill=PURPLE,
            outline=INK,
        )
    else:
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=TEAL, outline=INK, width=1)


def panel(
    draw: ImageDraw.ImageDraw,
    reports: dict[str, dict[str, Any]],
    *,
    left: int,
    right: int,
    top: int,
    bottom: int,
    title_value: str,
    subtitle: str,
    field: str,
    ci_field: str,
    domain: tuple[float, float],
    ticks: list[float],
    threshold: float | None = None,
    show_labels: bool = False,
) -> None:
    draw.rounded_rectangle((left, top, right, bottom), radius=16, fill=PANEL, outline=GRID, width=2)
    text(draw, (left + 28, top + 28), title_value, 27, bold=True)
    text(draw, (left + 28, top + 66), subtitle, 18, fill=MUTED)
    plot_left = left + (230 if show_labels else 55)
    plot_right = right - 35
    axis_top = top + 125
    axis_bottom = bottom - 60
    for tick in ticks:
        x = xmap(tick, domain, plot_left, plot_right)
        draw.line((x, axis_top, x, axis_bottom), fill=GRID, width=2)
        text(draw, (x, axis_bottom + 18), f"{tick:+.2f}", 17, fill=MUTED, anchor="ma")
    zero = xmap(0.0, domain, plot_left, plot_right)
    draw.line((zero, axis_top, zero, axis_bottom), fill=INK, width=3)
    if threshold is not None:
        tx = xmap(threshold, domain, plot_left, plot_right)
        for y in range(axis_top, axis_bottom, 12):
            draw.line((tx, y, tx, min(y + 6, axis_bottom)), fill=GOLD, width=3)
        text(draw, (tx + 5, axis_top - 8), "practical threshold", 15, fill=GOLD, anchor="ls")

    row_gap = (axis_bottom - axis_top - 20) / len(VARIANTS)
    for row_idx, variant in enumerate(VARIANTS):
        base_y = axis_top + 28 + row_idx * row_gap
        if show_labels:
            text(draw, (left + 28, base_y + 4), DISPLAY[variant], 19, anchor="lm")
        for model_idx, (_, key, _) in enumerate(MODELS):
            y = base_y + (-10 if model_idx == 0 else 10)
            result = reports[key]["comparisons_vs_original"][variant]
            value = float(result[field])
            ci_low, ci_high = (float(v) for v in result[ci_field])
            lo = xmap(ci_low, domain, plot_left, plot_right)
            hi = xmap(ci_high, domain, plot_left, plot_right)
            x = xmap(value, domain, plot_left, plot_right)
            color = BLUE if key == "sonnet" else ORANGE
            draw.line((lo, y, hi, y), fill=color, width=4)
            draw.line((lo, y - 6, lo, y + 6), fill=color, width=3)
            draw.line((hi, y - 6, hi, y + 6), fill=color, width=3)
            marker(draw, x, y, key)


def build_forest_figure(reports: dict[str, dict[str, Any]]) -> None:
    image = Image.new("RGB", (1900, 1080), "white")
    draw = ImageDraw.Draw(image)
    text(draw, (85, 50), "Effects of validation-equivalent schema reorderings", 39, bold=True)
    text(
        draw,
        (85, 102),
        "100 SOB text records; five calls per representation; 95% record-cluster bootstrap confidence intervals",
        22,
        fill=MUTED,
    )
    panel(
        draw,
        reports,
        left=70,
        right=980,
        top=160,
        bottom=930,
        title_value="A. Noise-adjusted output-distribution shift",
        subtitle="Token-normalized excess disagreement; positive values indicate representation sensitivity",
        field="normalized_excess_disagreement",
        ci_field="normalized_excess_disagreement_ci95",
        domain=(-0.02, 0.15),
        ticks=[-0.02, 0.00, 0.05, 0.10, 0.15],
        threshold=0.05,
        show_labels=True,
    )
    panel(
        draw,
        reports,
        left=1015,
        right=1830,
        top=160,
        bottom=930,
        title_value="B. Leaf-value accuracy difference",
        subtitle="Variant minus original; intervals crossing zero do not support an average change",
        field="leaf_value_accuracy_difference",
        ci_field="leaf_value_accuracy_difference_ci95",
        domain=(-0.06, 0.06),
        ticks=[-0.06, -0.03, 0.00, 0.03, 0.06],
        show_labels=False,
    )

    # Legend and interpretation key.
    marker(draw, 105, 995, "sonnet")
    text(draw, (125, 995), "Sonnet gateway alias", 20, anchor="lm")
    marker(draw, 385, 995, "gpt")
    text(draw, (405, 995), "GPT gateway alias", 20, anchor="lm")
    text(
        draw,
        (1815, 995),
        "Gateway aliases are reported verbatim; upstream identity was not independently verified.",
        17,
        fill=MUTED,
        anchor="rm",
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    image.crop((0, 135, image.width, image.height)).save(
        FIGURES / "figure2_forest.png", dpi=(180, 180)
    )


def decomposed_panel(
    draw: ImageDraw.ImageDraw,
    reports: dict[str, dict[str, Any]],
    *,
    left: int,
    right: int,
    top: int,
    bottom: int,
    title_value: str,
    subtitle: str,
    field: str,
    ci_field: str,
    domain: tuple[float, float],
    ticks: list[float],
    threshold: float | None = None,
    show_labels: bool = False,
) -> None:
    draw.rounded_rectangle((left, top, right, bottom), radius=16, fill=PANEL, outline=GRID, width=2)
    text(draw, (left + 28, top + 28), title_value, 27, bold=True)
    text(draw, (left + 28, top + 66), subtitle, 18, fill=MUTED)
    plot_left = left + (285 if show_labels else 55)
    plot_right = right - 35
    axis_top = top + 125
    axis_bottom = bottom - 65
    for tick in ticks:
        x = xmap(tick, domain, plot_left, plot_right)
        draw.line((x, axis_top, x, axis_bottom), fill=GRID, width=2)
        text(draw, (x, axis_bottom + 18), f"{tick:+.2f}", 17, fill=MUTED, anchor="ma")
    zero = xmap(0.0, domain, plot_left, plot_right)
    draw.line((zero, axis_top, zero, axis_bottom), fill=INK, width=3)
    if threshold is not None:
        tx = xmap(threshold, domain, plot_left, plot_right)
        for y in range(axis_top, axis_bottom, 12):
            draw.line((tx, y, tx, min(y + 6, axis_bottom)), fill=GOLD, width=3)
        text(draw, (tx + 5, axis_top - 8), "0.05 threshold", 15, fill=GOLD, anchor="ls")

    row_gap = (axis_bottom - axis_top - 20) / len(DECOMP_CONTRASTS)
    for row_idx, contrast in enumerate(DECOMP_CONTRASTS):
        base_y = axis_top + 45 + row_idx * row_gap
        if show_labels:
            text(draw, (left + 28, base_y + 4), DECOMP_DISPLAY[contrast], 19, anchor="lm")
        for model_idx, key in enumerate(("sonnet", "gpt", "deepseek", "qwen")):
            y = base_y + (-27, -9, 9, 27)[model_idx]
            result = reports[key]["contrasts"][contrast]
            value = float(result[field])
            ci_low, ci_high = (float(v) for v in result[ci_field])
            lo = xmap(ci_low, domain, plot_left, plot_right)
            hi = xmap(ci_high, domain, plot_left, plot_right)
            x = xmap(value, domain, plot_left, plot_right)
            color = (
                BLUE
                if key == "sonnet"
                else ORANGE
                if key == "gpt"
                else GREEN
                if key == "deepseek"
                else PURPLE
            )
            draw.line((lo, y, hi, y), fill=color, width=4)
            draw.line((lo, y - 6, lo, y + 6), fill=color, width=3)
            draw.line((hi, y - 6, hi, y + 6), fill=color, width=3)
            marker(draw, x, y, key)


def build_decomposed_figure(reports: dict[str, dict[str, Any]]) -> None:
    image = Image.new("RGB", (1900, 900), "white")
    draw = ImageDraw.Draw(image)
    text(draw, (85, 50), "Decomposed schema-order confirmation effects", 39, bold=True)
    text(
        draw,
        (85, 102),
        "Disjoint SOB records (n=200; Qwen n=160); five calls per representation; 95% record-cluster bootstrap intervals",
        22,
        fill=MUTED,
    )
    decomposed_panel(
        draw,
        reports,
        left=70,
        right=980,
        top=160,
        bottom=750,
        title_value="A. Noise-adjusted distribution contrast",
        subtitle="Only model-specific effects at or above 0.05 meet the preregistered practical rule",
        field="normalized_excess_disagreement",
        ci_field="normalized_excess_ci95",
        domain=(-0.01, 0.19),
        ticks=[0.00, 0.05, 0.10, 0.15],
        threshold=0.05,
        show_labels=True,
    )
    decomposed_panel(
        draw,
        reports,
        left=1015,
        right=1830,
        top=160,
        bottom=750,
        title_value="B. Leaf-value accuracy contrast",
        subtitle="Treatment minus baseline; negative values indicate lower average accuracy",
        field="leaf_value_accuracy_difference",
        ci_field="leaf_accuracy_ci95",
        domain=(-0.06, 0.06),
        ticks=[-0.06, -0.03, 0.00, 0.03, 0.06],
        show_labels=False,
    )
    marker(draw, 105, 820, "sonnet")
    text(draw, (125, 820), "Sonnet gateway alias", 20, anchor="lm")
    marker(draw, 385, 820, "gpt")
    text(draw, (405, 820), "GPT gateway alias", 20, anchor="lm")
    marker(draw, 640, 820, "deepseek")
    text(draw, (660, 820), "DeepSeek official endpoint", 20, anchor="lm")
    marker(draw, 980, 820, "qwen")
    text(draw, (1000, 820), "Qwen-Plus official endpoint", 20, anchor="lm")
    text(
        draw,
        (1815, 870),
        "Each deployment is judged against the same frozen 0.05 practical threshold.",
        16,
        fill=MUTED,
        anchor="rm",
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    image.crop((0, 135, image.width, image.height)).save(
        FIGURES / "figure3_decomposed_confirmation.png", dpi=(180, 180)
    )


def build_mode_figure(interaction: dict[str, Any]) -> None:
    """Visualize the matched Qwen text-versus-JSON-Mode boundary."""
    image = Image.new("RGB", (1900, 820), "white")
    draw = ImageDraw.Draw(image)
    text(draw, (85, 50), "Matched Qwen-Plus text versus JSON Mode", 39, bold=True)
    text(
        draw,
        (85, 102),
        "Same 100 frozen records; JSON Mode uses response_format={type: json_object}, not strict schema decoding",
        22,
        fill=MUTED,
    )

    left, right, top, bottom = 70, 930, 160, 690
    draw.rounded_rectangle((left, top, right, bottom), radius=16, fill=PANEL, outline=GRID, width=2)
    text(draw, (left + 28, top + 28), "A. Within-interface order effects", 27, bold=True)
    text(draw, (left + 28, top + 66), "Descriptive matched effects; both JSON-Mode effects met the 0.05 rule", 18, fill=MUTED)
    plot_left, plot_right = left + 270, right - 45
    axis_top, axis_bottom = top + 135, bottom - 70
    for tick in (0.00, 0.05, 0.10, 0.15, 0.20):
        x = xmap(tick, (0.0, 0.20), plot_left, plot_right)
        draw.line((x, axis_top, x, axis_bottom), fill=GRID, width=2)
        text(draw, (x, axis_bottom + 18), f"{tick:.2f}", 17, fill=MUTED, anchor="ma")
    threshold_x = xmap(0.05, (0.0, 0.20), plot_left, plot_right)
    for y in range(axis_top, axis_bottom, 12):
        draw.line((threshold_x, y, threshold_x, min(y + 6, axis_bottom)), fill=GOLD, width=3)

    for row_idx, contrast in enumerate(DECOMP_CONTRASTS):
        item = interaction["contrasts"][contrast]
        y = axis_top + 80 + row_idx * 145
        text(draw, (left + 28, y), DECOMP_DISPLAY[contrast], 19, anchor="lm")
        tx = xmap(float(item["text_mode_excess"]), (0.0, 0.20), plot_left, plot_right)
        jx = xmap(float(item["json_mode_excess"]), (0.0, 0.20), plot_left, plot_right)
        draw.line((tx, y - 15, jx, y + 15), fill=MUTED, width=3)
        marker(draw, tx, y - 15, "qwen")
        marker(draw, jx, y + 15, "json")

    marker(draw, left + 45, bottom - 30, "qwen")
    text(draw, (left + 65, bottom - 30), "Text mode", 18, anchor="lm")
    marker(draw, left + 210, bottom - 30, "json")
    text(draw, (left + 230, bottom - 30), "JSON Mode", 18, anchor="lm")

    left, right = 970, 1830
    draw.rounded_rectangle((left, top, right, bottom), radius=16, fill=PANEL, outline=GRID, width=2)
    text(draw, (left + 28, top + 28), "B. JSON-minus-text mode interaction", 27, bold=True)
    text(draw, (left + 28, top + 66), "95% record-cluster intervals; frozen material-change boundary is +/-0.03", 18, fill=MUTED)
    plot_left, plot_right = left + 270, right - 45
    axis_top, axis_bottom = top + 135, bottom - 70
    for tick in (-0.08, -0.04, 0.00, 0.04, 0.08):
        x = xmap(tick, (-0.08, 0.08), plot_left, plot_right)
        draw.line((x, axis_top, x, axis_bottom), fill=GRID, width=2)
        text(draw, (x, axis_bottom + 18), f"{tick:+.2f}", 17, fill=MUTED, anchor="ma")
    for boundary in (-0.03, 0.03):
        bx = xmap(boundary, (-0.08, 0.08), plot_left, plot_right)
        for y in range(axis_top, axis_bottom, 12):
            draw.line((bx, y, bx, min(y + 6, axis_bottom)), fill=GOLD, width=3)
    zx = xmap(0.0, (-0.08, 0.08), plot_left, plot_right)
    draw.line((zx, axis_top, zx, axis_bottom), fill=INK, width=3)
    for row_idx, contrast in enumerate(DECOMP_CONTRASTS):
        item = interaction["contrasts"][contrast]
        y = axis_top + 80 + row_idx * 145
        text(draw, (left + 28, y), DECOMP_DISPLAY[contrast], 19, anchor="lm")
        lo, hi = (float(v) for v in item["mode_change_ci95"])
        value = float(item["mode_change"])
        lx = xmap(lo, (-0.08, 0.08), plot_left, plot_right)
        hx = xmap(hi, (-0.08, 0.08), plot_left, plot_right)
        vx = xmap(value, (-0.08, 0.08), plot_left, plot_right)
        draw.line((lx, y, hx, y), fill=TEAL, width=5)
        draw.line((lx, y - 7, lx, y + 7), fill=TEAL, width=3)
        draw.line((hx, y - 7, hx, y + 7), fill=TEAL, width=3)
        marker(draw, vx, y, "json")
    text(
        draw,
        (1815, 760),
        "No material attenuation was confirmed; this is not an equivalence claim.",
        18,
        fill=MUTED,
        anchor="rm",
    )
    FIGURES.mkdir(parents=True, exist_ok=True)
    image.crop((0, 135, image.width, image.height)).save(
        FIGURES / "figure4_qwen_mode_interaction.png", dpi=(180, 180)
    )


def build_tables(reports: dict[str, dict[str, Any]], exploratory: dict[str, Any]) -> None:
    design_rows = [
        {
            "system": model_name,
            "requested_alias": "claude-sonnet-5" if key == "sonnet" else "gpt-5.5",
            "returned_alias": next(iter(reports[key]["returned_model_counts"])),
            "records": reports[key]["record_count"],
            "representations": len(reports[key]["variants"]),
            "repeats_per_representation": reports[key]["repeats_per_variant"],
            "successful_responses": reports[key]["prediction_count"],
            "schema_pass_rate": f"{reports[key]['overall_schema_pass_rate']:.4f}",
            "formal_decision": reports[key]["decision"],
        }
        for model_name, key, report_path in MODELS
    ]
    write_csv(
        TABLES / "table1_experimental_design.csv",
        list(design_rows[0]),
        design_rows,
    )

    effects: list[dict[str, Any]] = []
    for model_name, key, _ in MODELS:
        for variant in VARIANTS:
            result = reports[key]["comparisons_vs_original"][variant]
            low, high = result["normalized_excess_disagreement_ci95"]
            effects.append(
                {
                    "system": model_name,
                    "variant": DISPLAY[variant],
                    "hypothesis_role": (
                        "primary" if variant in reports[key].get("primary_variants", []) else "exploratory"
                    ),
                    "normalized_excess": f"{result['normalized_excess_disagreement']:.4f}",
                    "ci95_low": f"{low:.4f}",
                    "ci95_high": f"{high:.4f}",
                    "holm_p": f"{result['normalized_energy_holm_p']:.6f}",
                    "meets_0_05_practical_threshold": (
                        "yes"
                        if result["normalized_excess_disagreement"] >= 0.05
                        and low > 0
                        and result["normalized_energy_holm_p"] < 0.05
                        else "no"
                    ),
                }
            )
    write_csv(TABLES / "table2_distribution_effects.csv", list(effects[0]), effects)

    quality: list[dict[str, Any]] = []
    for model_name, key, _ in MODELS:
        for variant in ("original",) + VARIANTS:
            result = reports[key]["variant_summary"][variant]
            quality.append(
                {
                    "system": model_name,
                    "representation": DISPLAY[variant],
                    "responses": result["response_count"],
                    "applicable_records": result["applicable_record_count"],
                    "schema_pass_rate": f"{result['schema_pass_rate']:.4f}",
                    "leaf_value_accuracy": f"{result['leaf_value_accuracy']:.4f}",
                    "token_f1": f"{result['value_token_f1']:.4f}",
                    "perfect_response_rate": f"{result['perfect_response_rate']:.4f}",
                    "within_normalized_disagreement": f"{result['mean_within_normalized_disagreement']:.4f}",
                }
            )
    write_csv(TABLES / "table3_quality_metrics.csv", list(quality[0]), quality)

    paired = exploratory["paired_model_comparisons"]
    paired_rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        row = paired[variant]
        low, high = row["difference_ci95"]
        paired_rows.append(
            {
                "variant": DISPLAY[variant],
                "sonnet_minus_gpt": f"{row['sonnet_minus_gpt_mean_difference']:.4f}",
                "ci95_low": f"{low:.4f}",
                "ci95_high": f"{high:.4f}",
                "holm_p": f"{row['difference_holm_p']:.6f}",
                "analysis_status": "post-hoc exploratory",
            }
        )
    write_csv(TABLES / "table4_paired_model_differences.csv", list(paired_rows[0]), paired_rows)


def build_decomposed_tables(
    reports: dict[str, dict[str, Any]], cross_model: dict[str, Any]
) -> None:
    rows: list[dict[str, Any]] = []
    for model_label, key in (
        ("Sonnet gateway alias", "sonnet"),
        ("GPT gateway alias", "gpt"),
        ("DeepSeek official endpoint", "deepseek"),
        ("Qwen-Plus official endpoint", "qwen"),
    ):
        for contrast in DECOMP_CONTRASTS:
            item = reports[key]["contrasts"][contrast]
            nlow, nhigh = item["normalized_excess_ci95"]
            alow, ahigh = item["leaf_accuracy_ci95"]
            rows.append(
                {
                    "system": model_label,
                    "contrast": DECOMP_DISPLAY[contrast],
                    "normalized_excess": f"{item['normalized_excess_disagreement']:.4f}",
                    "normalized_ci95_low": f"{nlow:.4f}",
                    "normalized_ci95_high": f"{nhigh:.4f}",
                    "normalized_holm_p": f"{item['normalized_energy_holm_p']:.6f}",
                    "meets_preregistered_rule": "yes" if item["confirmed"] else "no",
                    "leaf_accuracy_difference": f"{item['leaf_value_accuracy_difference']:.4f}",
                    "leaf_accuracy_ci95_low": f"{alow:.4f}",
                    "leaf_accuracy_ci95_high": f"{ahigh:.4f}",
                    "leaf_accuracy_holm_p": f"{item['leaf_accuracy_holm_p']:.6f}",
                }
            )
    write_csv(TABLES / "table5_decomposed_confirmation.csv", list(rows[0]), rows)

    cross_rows: list[dict[str, Any]] = []
    for contrast in DECOMP_CONTRASTS:
        item = cross_model["contrasts"][contrast]
        dlow, dhigh = item["distribution_difference_ci95"]
        alow, ahigh = item["accuracy_difference_of_differences_ci95"]
        cross_rows.append(
            {
                "contrast": DECOMP_DISPLAY[contrast],
                "sonnet_minus_gpt_distribution": f"{item['distribution_difference']:.4f}",
                "distribution_ci95_low": f"{dlow:.4f}",
                "distribution_ci95_high": f"{dhigh:.4f}",
                "distribution_holm_p": f"{item['distribution_difference_holm_p']:.6f}",
                "sonnet_minus_gpt_accuracy_contrast": f"{item['accuracy_difference_of_differences']:.4f}",
                "accuracy_ci95_low": f"{alow:.4f}",
                "accuracy_ci95_high": f"{ahigh:.4f}",
                "accuracy_holm_p": f"{item['accuracy_difference_holm_p']:.6f}",
                "analysis_status": "post-hoc exploratory",
            }
        )
    write_csv(TABLES / "table6_decomposed_cross_model.csv", list(cross_rows[0]), cross_rows)


def build_qwen_mode_tables(
    json_mode: dict[str, Any], interaction: dict[str, Any], robustness: dict[str, Any]
) -> None:
    mode_rows: list[dict[str, Any]] = []
    for contrast in DECOMP_CONTRASTS:
        within = json_mode["contrasts"][contrast]
        item = interaction["contrasts"][contrast]
        low, high = item["mode_change_ci95"]
        mode_rows.append(
            {
                "contrast": DECOMP_DISPLAY[contrast],
                "text_mode_excess_matched_100": f"{item['text_mode_excess']:.4f}",
                "json_mode_excess": f"{within['normalized_excess_disagreement']:.4f}",
                "json_mode_ci95_low": f"{within['normalized_excess_ci95'][0]:.4f}",
                "json_mode_ci95_high": f"{within['normalized_excess_ci95'][1]:.4f}",
                "json_minus_text": f"{item['mode_change']:.4f}",
                "mode_change_ci95_low": f"{low:.4f}",
                "mode_change_ci95_high": f"{high:.4f}",
                "mode_change_holm_p": f"{item['mode_change_holm_p']:.6f}",
                "material_mode_change_confirmed": "no",
            }
        )
    write_csv(TABLES / "table7_qwen_mode_interaction.csv", list(mode_rows[0]), mode_rows)

    robust_rows: list[dict[str, Any]] = []
    for system, run in robustness["runs"].items():
        for contrast in DECOMP_CONTRASTS:
            item = run["contrasts"][contrast]
            robust_rows.append(
                {
                    "system": system,
                    "contrast": DECOMP_DISPLAY[contrast],
                    "records": run["record_count"],
                    "mean": f"{item['mean']:.4f}",
                    "median": f"{item['median']:.4f}",
                    "symmetric_10pct_trimmed_mean": f"{item['symmetric_10pct_trimmed_mean']:.4f}",
                    "mean_after_removing_largest_10pct": f"{item['mean_after_removing_largest_10pct']:.4f}",
                    "top_decile_positive_mass_share": f"{item['largest_10pct_positive_mass_share']:.4f}",
                    "medium_mean": f"{item['by_schema_complexity']['medium']:.4f}",
                    "hard_mean": f"{item['by_schema_complexity']['hard']:.4f}",
                    "analysis_status": "post-hoc descriptive",
                }
            )
    write_csv(TABLES / "table8_effect_concentration.csv", list(robust_rows[0]), robust_rows)

    concordance_rows = []
    for item in robustness["cross_system_concordance"]:
        low, high = item["rho_ci95"]
        concordance_rows.append(
            {
                "left": item["left"],
                "right": item["right"],
                "contrast": DECOMP_DISPLAY[item["contrast"]],
                "shared_records": item["shared_record_count"],
                "spearman_rho": f"{item['spearman_rho']:.4f}",
                "ci95_low": f"{low:.4f}",
                "ci95_high": f"{high:.4f}",
                "global_holm_p": f"{item['holm_p']:.6f}",
                "analysis_status": "post-hoc exploratory",
            }
        )
    write_csv(TABLES / "table9_record_concordance.csv", list(concordance_rows[0]), concordance_rows)


def main() -> int:
    reports = {
        "sonnet": load_json(SONNET_REPORT),
        "gpt": load_json(GPT_REPORT),
    }
    exploratory = load_json(EXPLORATORY_REPORT)
    decomposed_reports = {
        "sonnet": load_json(DECOMP_SONNET_REPORT),
        "gpt": load_json(DECOMP_GPT_REPORT),
        "deepseek": load_json(DECOMP_DEEPSEEK_REPORT),
        "qwen": load_json(DECOMP_QWEN_REPORT),
    }
    decomposed_cross = load_json(DECOMP_CROSS_REPORT)
    qwen_json = load_json(QWEN_JSON_REPORT)
    qwen_interaction = load_json(QWEN_INTERACTION_REPORT)
    robustness = load_json(ROBUSTNESS_REPORT)
    build_tables(reports, exploratory)
    build_decomposed_tables(decomposed_reports, decomposed_cross)
    build_qwen_mode_tables(qwen_json, qwen_interaction, robustness)
    build_method_figure()
    build_forest_figure(reports)
    build_decomposed_figure(decomposed_reports)
    build_mode_figure(qwen_interaction)
    outputs = sorted(TABLES.glob("*.csv")) + sorted(FIGURES.glob("*.png"))
    manifest = {
        "generated_by": "src/build_paper_artifacts.py",
        "source_reports": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for path in (
                SONNET_REPORT,
                GPT_REPORT,
                EXPLORATORY_REPORT,
                DECOMP_SONNET_REPORT,
                DECOMP_GPT_REPORT,
                DECOMP_DEEPSEEK_REPORT,
                DECOMP_QWEN_REPORT,
                QWEN_JSON_REPORT,
                QWEN_INTERACTION_REPORT,
                ROBUSTNESS_REPORT,
                DECOMP_CROSS_REPORT,
            )
        ],
        "frozen_results_recomputed": False,
        "outputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "bytes": path.stat().st_size}
            for path in outputs
        ],
    }
    (PAPER / "artifact_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
