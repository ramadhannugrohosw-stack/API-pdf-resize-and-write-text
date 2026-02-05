#!/usr/bin/env python3
# tools/resize_and_stamp.py
#
# Resize PDF page canvas (MediaBox/CropBox) without scaling content,
# then stamp custom text at desired coordinates.
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
    if page_value is None or (
        isinstance(page_value, str) and page_value.strip().lower() == "all"
    ):
        return list(range(page_count))

    if isinstance(page_value, (int, float)) and not isinstance(page_value, bool):
        idx = int(page_value) - 1
        return [idx] if 0 <= idx < page_count else []

    if isinstance(page_value, str):
        try:
            idx = int(page_value.strip()) - 1
            return [idx] if 0 <= idx < page_count else []
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


def get_box(page: pikepdf.Page, box_name: str) -> Optional[Tuple[float, float, float, float]]:
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
    if get_box(page, "CropBox") is None:
        set_box(page, "CropBox", new_media)


def clamp_font_size(v: Any, default: float = 8) -> float:
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
    s = str(v) if v is not None else "right"
    s = s.strip().lower()
    if s in ("right", "r"):
        return "right"
    if s in ("center", "centre", "c", "middle"):
        return "center"
    return "left"


def get_char_space(item: Dict[str, Any]) -> float:
    if "charSpace" in item:
        return safe_float(item.get("charSpace"), 0.52)
    if "char_space" in item:
        return safe_float(item.get("char_space"), 0.52)
    return 0.52


def add_overlay_no_scale(
    target_page: pikepdf.Page,
    overlay_page: pikepdf.Page,
    media_x0: float,
    media_y0: float,
    media_x1: float,
    media_y1: float,
) -> None:
    """
    Best-effort to avoid any scaling:
    - Prefer add_overlay(..., rect=Rectangle(...)) when supported.
    - Fallback to add_overlay(overlay_page) if old pikepdf.
    """
    rect = pikepdf.Rectangle(media_x0, media_y0, media_x1, media_y1)
    try:
        # Newer pikepdf supports rect=
        target_page.add_overlay(overlay_page, rect=rect)
    except TypeError:
        # Older pikepdf: no rect param → fallback (might scale on some PDFs)
        target_page.add_overlay(overlay_page)


def build_overlay_pdf_for_page(
    # overlay size in pts, must be (media_w, media_h)
    media_w: float,
    media_h: float,
    text_items: List[Dict[str, Any]],
    # current MediaBox absolute:
    media_x0: float,
    media_y0: float,
    media_x1: float,
    media_y1: float,
    # original reference top for Y (paper original):
    old_ref_y1: float,
) -> bytes:
    """
    Overlay dibuat dalam koordinat LOCAL (0..media_w, 0..media_h).
    Jadi semua koordinat harus kita convert:
      x_local = x_abs - media_x0
      y_local = y_abs - media_y0
    """

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        overlay_path = tf.name

    try:
        c = rl_canvas.Canvas(overlay_path, pagesize=(media_w, media_h))
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

            margin_top_cm = safe_float(item.get("marginTopCm"), 5.0)
            margin_right_cm = safe_float(item.get("marginRightCm"), 1.0)

            # absolute coordinate in PDF user space
            if item.get("xPt") is not None or item.get("yPt") is not None:
                x_abs = media_x0 + safe_float(item.get("xPt"), 0.0)
                y_abs = media_y0 + safe_float(item.get("yPt"), 0.0)
            elif item.get("xCm") is not None or item.get("yCm") is not None:
                x_abs = media_x0 + cm_to_pt(safe_float(item.get("xCm"), 0.0))
                y_abs = media_y0 + cm_to_pt(safe_float(item.get("yCm"), 0.0))
            else:
                # FORCE Y from original paper top:
                y_abs = old_ref_y1 - cm_to_pt(margin_top_cm) + cm_to_pt(dy_cm)

                # X sticks to CURRENT right edge (after resize):
                if position in ("left_top", "top_left"):
                    x_abs = media_x0 + cm_to_pt(dx_cm)
                else:
                    x_abs = media_x1 - cm_to_pt(margin_right_cm) + cm_to_pt(dx_cm)

            # convert to overlay local (origin 0,0)
            x = x_abs - media_x0
            y = y_abs - media_y0

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

            # old MediaBox and old reference top (prefer old CropBox)
            old_media_boxes: List[Tuple[float, float, float, float]] = []
            old_ref_tops: List[float] = []

            for p in pdf.pages:
                mb = get_box(p, "MediaBox")
                if mb is None:
                    mb = (0.0, 0.0, 612.0, 792.0)
                    set_box(p, "MediaBox", mb)
                old_media_boxes.append(mb)

                cb = get_box(p, "CropBox")
                ref = cb if cb is not None else mb
                old_ref_tops.append(ref[3])  # old top y1

            # 1) resize boxes
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

            # 2) stamp
            if texts:
                items_by_page: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(page_count)}
                for item in texts:
                    if not isinstance(item, dict):
                        continue
                    target_pages = parse_page_selector(item.get("page", "all"), page_count)
                    for pi in target_pages:
                        items_by_page[pi].append(item)

                for i, page in enumerate(pdf.pages):
                    page_items = items_by_page.get(i, [])
                    if not page_items:
                        continue

                    media = get_box(page, "MediaBox")
                    if media is None:
                        continue
                    media_x0, media_y0, media_x1, media_y1 = media
                    media_w = media_x1 - media_x0
                    media_h = media_y1 - media_y0

                    overlay_bytes = build_overlay_pdf_for_page(
                        media_w=media_w,
                        media_h=media_h,
                        text_items=page_items,
                        media_x0=media_x0,
                        media_y0=media_y0,
                        media_x1=media_x1,
                        media_y1=media_y1,
                        old_ref_y1=old_ref_tops[i],
                    )

                    overlay_pdf = pikepdf.Pdf.open(io.BytesIO(overlay_bytes))
                    overlay_page = overlay_pdf.pages[0]

                    # IMPORTANT: overlay must be 0-based (0..w,h), not absolute coords
                    set_box(overlay_page, "MediaBox", (0.0, 0.0, media_w, media_h))
                    set_box(overlay_page, "CropBox", (0.0, 0.0, media_w, media_h))

                    # Copy rotation (safe if 0)
                    rot = int(page.obj.get(Name("/Rotate"), 0) or 0)
                    overlay_page.obj[Name("/Rotate")] = rot

                    # Add overlay without scaling (rect if supported)
                    add_overlay_no_scale(page, overlay_page, media_x0, media_y0, media_x1, media_y1)

            pdf.save(out_path)
        return 0

    except Exception as e:
        print(f"[resize_and_stamp] Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
