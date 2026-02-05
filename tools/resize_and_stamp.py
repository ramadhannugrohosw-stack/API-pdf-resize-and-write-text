#!/usr/bin/env python3
# tools/resize_and_stamp.py
#
# Resize PDF page canvas (MediaBox/CropBox) without scaling content,
# then stamp custom text at desired coordinates.
#
# Called by server.js:
#   python tools/resize_and_stamp.py --input in.pdf --output out.pdf --options '{"..."}'
#
# Dependencies:
#   pikepdf, reportlab

import argparse
import io
import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import pikepdf
from pikepdf import Name

from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.colors import black
from reportlab.pdfbase.pdfmetrics import stringWidth

PT_PER_INCH = 72.0
CM_PER_INCH = 2.54
PT_PER_CM = PT_PER_INCH / CM_PER_INCH  # 28.3464566929...


def cm_to_pt(cm: float) -> float:
    return float(cm) * PT_PER_CM


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def normalize_side(side: str) -> str:
    side = (side or "right").strip().lower()
    if side not in ("right", "left", "both"):
        return "right"
    return side


def normalize_apply_to(apply_to: str) -> str:
    a = (apply_to or "both").strip().lower()
    if a not in ("mediabox", "cropbox", "both"):
        return "both"
    return a


def parse_page_selector(page_value: Any, page_count: int) -> List[int]:
    """
    Returns list of 0-based page indices to apply.
    page_value can be:
      - "all"
      - int (1-based)
      - list of ints (1-based)
    """
    if page_value is None or (
        isinstance(page_value, str) and page_value.strip().lower() == "all"
    ):
        return list(range(page_count))

    if isinstance(page_value, (int, float)) and not isinstance(page_value, bool):
        idx = int(page_value) - 1
        if 0 <= idx < page_count:
            return [idx]
        return []

    if isinstance(page_value, str):
        try:
            idx = int(page_value.strip()) - 1
            if 0 <= idx < page_count:
                return [idx]
        except Exception:
            return []

    if isinstance(page_value, list):
        out: List[int] = []
        for it in page_value:
            try:
                idx = int(it) - 1
                if 0 <= idx < page_count and idx not in out:
                    out.append(idx)
            except Exception:
                continue
        return out

    return []


def get_box(
    page: pikepdf.Page, box_name: str
) -> Optional[Tuple[float, float, float, float]]:
    """
    box_name: "MediaBox" / "CropBox"
    Returns (x0, y0, x1, y1) in pts, or None if absent.
    """
    key = Name(f"/{box_name}")
    if key not in page.obj:
        return None
    arr = page.obj[key]
    if arr is None or len(arr) != 4:
        return None
    return (float(arr[0]), float(arr[1]), float(arr[2]), float(arr[3]))


def set_box(page: pikepdf.Page, box_name: str, box: Tuple[float, float, float, float]) -> None:
    key = Name(f"/{box_name}")
    page.obj[key] = pikepdf.Array([box[0], box[1], box[2], box[3]])


def resize_box(
    box: Tuple[float, float, float, float],
    add_width_pt: float,
    side: str,
) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = box
    if add_width_pt <= 0:
        return (x0, y0, x1, y1)

    if side == "right":
        return (x0, y0, x1 + add_width_pt, y1)
    if side == "left":
        return (x0 - add_width_pt, y0, x1, y1)

    half = add_width_pt / 2.0
    return (x0 - half, y0, x1 + half, y1)


def ensure_cropbox_consistent(page: pikepdf.Page, new_media: Tuple[float, float, float, float]) -> None:
    """
    If CropBox missing, set to MediaBox so viewers show expanded canvas.
    """
    if get_box(page, "CropBox") is None:
        set_box(page, "CropBox", new_media)


def clamp_font_size(v: Any, default: float = 8.5) -> float:
    fs = safe_float(v, default)
    if fs <= 0:
        return default
    if fs > 500:
        return 500.0
    return fs


def normalize_font_name(v: Any) -> str:
    s = str(v) if v is not None else "Helvetica"
    s = s.strip()
    return s or "Helvetica"


def normalize_align(v: Any) -> str:
    """
    left | center | right
    """
    s = str(v) if v is not None else "right"
    s = s.strip().lower()
    if s in ("right", "r"):
        return "right"
    if s in ("center", "centre", "c", "middle"):
        return "center"
    return "left"


def get_char_space(item: Dict[str, Any]) -> float:
    # Backward/compat: accept both keys.
    if "charSpace" in item:
        return safe_float(item.get("charSpace"), 0.52)
    if "char_space" in item:
        return safe_float(item.get("char_space"), 0.52)
    return 0.52


def build_overlay_pdf_for_page(
    page_width_pt: float,
    page_height_pt: float,
    text_items: List[Dict[str, Any]],
    # current MediaBox absolute:
    mb_x0: float,
    mb_y0: float,
    mb_x1: float,
    mb_y1: float,
    # old/original MediaBox absolute (for "right edge of original page"):
    old_mb_x0: float,
    old_mb_y0: float,
    old_mb_x1: float,
    old_mb_y1: float,
) -> bytes:
    """
    Create a single-page overlay PDF (same size as resized page)
    containing all text items for that page.

    Key fix for "any paper size":
    - Compute target coordinates in absolute PDF user space using MediaBox.
    - Convert to overlay-local coords by subtracting mb_x0/mb_y0.
    - Default anchor remains "right_top" with marginTop 5cm from top.
    """

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        overlay_path = tf.name

    try:
        c = rl_canvas.Canvas(overlay_path, pagesize=(page_width_pt, page_height_pt))
        c.setFillColor(black)

        for item in text_items:
            value = str(item.get("value", ""))
            if not value:
                continue

            font_name = normalize_font_name(item.get("font", "Helvetica"))
            font_size = clamp_font_size(item.get("fontSize", 8))
            align = normalize_align(item.get("align", "right"))
            char_space = get_char_space(item)

            position = str(item.get("position", "")).strip().lower()

            dx_cm = safe_float(item.get("dxCm"), 0.0)
            dy_cm = safe_float(item.get("dyCm"), 0.0)

            margin_top_cm = safe_float(item.get("marginTopCm"), 5.0)   # default 5 cm from top
            margin_right_cm = safe_float(item.get("marginRightCm"), 1.0)

            # ---- Absolute target coordinate in PDF user space ----
            # Explicit coords (keep compatibility):
            if item.get("xPt") is not None or item.get("yPt") is not None:
                x_abs = mb_x0 + safe_float(item.get("xPt"), 0.0)
                y_abs = mb_y0 + safe_float(item.get("yPt"), 0.0)
            elif item.get("xCm") is not None or item.get("yCm") is not None:
                x_abs = mb_x0 + cm_to_pt(safe_float(item.get("xCm"), 0.0))
                y_abs = mb_y0 + cm_to_pt(safe_float(item.get("yCm"), 0.0))
            else:
                # Default anchor:
                # y = top(current MediaBox) - marginTop + dy
                y_abs = mb_y1 - cm_to_pt(margin_top_cm) + cm_to_pt(dy_cm)

                # Default is right-top:
                # x is near right edge of ORIGINAL page (old MediaBox), not including added blank area
                # So numeric column anchor doesn't shift when resizing canvas.
                if position in ("left_top", "top_left"):
                    x_abs = mb_x0 + cm_to_pt(dx_cm)
                else:
                    # treat empty/unknown position as right_top
                    x_abs = old_mb_x1 - cm_to_pt(margin_right_cm) + cm_to_pt(dx_cm)

            # Convert absolute -> overlay-local (0,0 at mb_x0/mb_y0)
            x = x_abs - mb_x0
            y = y_abs - mb_y0

            # Multi-line
            lines = value.split("\n")
            leading = safe_float(item.get("leading"), font_size * 1.0)

            cur_y = y
            for line in lines:
                base_w = stringWidth(line, font_name, font_size)
                extra_w = max(len(line) - 1, 0) * char_space
                total_w = base_w + extra_w

                t = c.beginText()
                t.setFont(font_name, font_size)
                t.setCharSpace(char_space)

                if align == "right":
                    # x is right boundary
                    t.setTextOrigin(x - total_w, cur_y)
                elif align == "center":
                    t.setTextOrigin(x - (total_w / 2.0), cur_y)
                else:
                    t.setTextOrigin(x, cur_y)

                t.textLine(line)
                c.drawText(t)

                cur_y -= leading

        c.showPage()
        c.save()

        with open(overlay_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(overlay_path)
        except Exception:
            pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Input PDF path")
    ap.add_argument("--output", required=True, help="Output PDF path")
    ap.add_argument("--options", required=True, help="Options JSON string")
    args = ap.parse_args()

    in_path = args.input
    out_path = args.output

    try:
        options = json.loads(args.options)
        if not isinstance(options, dict):
            raise ValueError("Options must be a JSON object")
    except Exception as e:
        print(f"[resize_and_stamp] Invalid options JSON: {e}", file=sys.stderr)
        return 2

    add_width_cm = safe_float(options.get("addWidthCm"), 5.0)
    add_width_pt = cm_to_pt(add_width_cm)

    side = normalize_side(options.get("side", "right"))
    apply_to = normalize_apply_to(options.get("applyTo", "both"))

    texts = options.get("texts", [])
    if not isinstance(texts, list):
        texts = []

    try:
        with pikepdf.open(in_path) as pdf:
            page_count = len(pdf.pages)

            # Capture old MediaBox per page (absolute coords)
            old_media_boxes: List[Tuple[float, float, float, float]] = []
            for p in pdf.pages:
                mb = get_box(p, "MediaBox")
                if mb is None:
                    mb = (0.0, 0.0, 612.0, 792.0)  # fallback letter
                    set_box(p, "MediaBox", mb)
                old_media_boxes.append(mb)

            # 1) Resize page boxes
            for i, page in enumerate(pdf.pages):
                old_mb = old_media_boxes[i]
                new_mb = resize_box(old_mb, add_width_pt, side)

                if apply_to in ("mediabox", "both"):
                    set_box(page, "MediaBox", new_mb)

                if apply_to in ("cropbox", "both"):
                    cb = get_box(page, "CropBox")
                    if cb is None:
                        cb = old_mb
                    new_cb = resize_box(cb, add_width_pt, side)
                    set_box(page, "CropBox", new_cb)

                cur_mb = get_box(page, "MediaBox") or new_mb
                ensure_cropbox_consistent(page, cur_mb)

            # 2) Stamp overlays
            if texts:
                items_by_page: Dict[int, List[Dict[str, Any]]] = {
                    i: [] for i in range(page_count)
                }

                for item in texts:
                    if not isinstance(item, dict):
                        continue
                    target_pages = parse_page_selector(item.get("page", "all"), page_count)
                    if not target_pages:
                        continue
                    for pi in target_pages:
                        items_by_page[pi].append(item)

                for i, page in enumerate(pdf.pages):
                    page_items = items_by_page.get(i, [])
                    if not page_items:
                        continue

                    mb = get_box(page, "MediaBox")
                    if mb is None:
                        continue
                    mb_x0, mb_y0, mb_x1, mb_y1 = mb
                    page_w = mb_x1 - mb_x0
                    page_h = mb_y1 - mb_y0

                    old_mb = old_media_boxes[i]
                    old_x0, old_y0, old_x1, old_y1 = old_mb

                    overlay_bytes = build_overlay_pdf_for_page(
                        page_width_pt=page_w,
                        page_height_pt=page_h,
                        text_items=page_items,
                        mb_x0=mb_x0,
                        mb_y0=mb_y0,
                        mb_x1=mb_x1,
                        mb_y1=mb_y1,
                        old_mb_x0=old_x0,
                        old_mb_y0=old_y0,
                        old_mb_x1=old_x1,
                        old_mb_y1=old_y1,
                    )

                    overlay_pdf = pikepdf.Pdf.open(io.BytesIO(overlay_bytes))
                    overlay_page = overlay_pdf.pages[0]

                    # Keep compatibility with pikepdf version:
                    page.add_overlay(overlay_page)

            pdf.save(out_path)
        return 0

    except Exception as e:
        print(f"[resize_and_stamp] Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
