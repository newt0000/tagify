from __future__ import annotations

import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional
import win32gui

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from PIL import Image, ImageDraw, ImageFont

import win32con
import win32print
import win32ui


# ---------- Public API (unchanged signatures) ----------

def make_temp_label_path() -> Path:
    d = Path(tempfile.gettempdir()) / "tagify_labels"
    d.mkdir(parents=True, exist_ok=True)
    return d / "prep_label_1x1.pdf"


def generate_1x1_label_pdf(item_name: str, prepped: date, expires: date, out_path: Path):
    """
    Generates:
      - a 1x1 inch PDF at out_path (for compatibility / debugging)
      - a same-stem PNG next to it (this is what we print directly)
    """
    out_path = Path(out_path)
    png_path = out_path.with_suffix(".png")

    # Render crisp label PNG (used for printing)
    _render_label_png(item_name, prepped, expires, png_path, dpi=300)

    # Also produce a true 1x1 PDF embedding that PNG (optional but useful)
    w = 1.0 * inch
    h = 1.0 * inch
    c = canvas.Canvas(str(out_path), pagesize=(w, h))
    c.drawImage(str(png_path), 0, 0, width=w, height=h, preserveAspectRatio=True, mask='auto')
    c.showPage()
    c.save()


def print_label_pdf(pdf_path: str, printer_name: str | None = None):
    """
    Prints directly via Win32 GDI to the selected printer.
    No ShellExecute. No external viewer.
    """
    pdf = Path(pdf_path)
    if not pdf.exists():
        raise FileNotFoundError(f"Label PDF not found: {pdf}")

    png = pdf.with_suffix(".png")
    if not png.exists():
        raise FileNotFoundError(
            f"Label PNG not found next to PDF: {png}\n"
            "Call generate_1x1_label_pdf(...) before print_label_pdf(...)."
        )

    if os.name != "nt":
        raise RuntimeError("Printing is implemented for Windows only.")

    if not printer_name:
        printer_name = win32print.GetDefaultPrinter()

    # Best-effort: try to force a 1x1 form to reduce long feed
    _try_select_1x1_form(printer_name)

    # Print the PNG via GDI
    _print_png_gdi(printer_name, png)


# ---------- Internal helpers ----------

def _render_label_png(item_name: str, prepped: date, expires: date, out_path: Path, dpi: int = 300) -> None:
    size_px = int(dpi * 1.0)  # 1 inch square
    img = Image.new("RGB", (size_px, size_px), "white")
    draw = ImageDraw.Draw(img)

    pad = int(size_px * 0.08)
    y = pad

    font_bold = _load_font(prefer_bold=True, size=int(size_px * 0.13))
    font_small = _load_font(prefer_bold=False, size=int(size_px * 0.09))

    title = item_name.strip()
    title = _ellipsize_to_width(draw, title, font_bold, size_px - pad * 2)

    draw.text((pad, y), title, fill="black", font=font_bold)
    y += int(size_px * 0.22)

    prepped_s = prepped.strftime("%m/%d/%Y")
    expires_s = expires.strftime("%m/%d/%Y")

    draw.text((pad, y), f"Prepped: {prepped_s}", fill="black", font=font_small)
    y += int(size_px * 0.14)
    draw.text((pad, y), f"Expires: {expires_s}", fill="black", font=font_small)

    img.save(out_path, "PNG", optimize=True)


def _load_font(prefer_bold: bool, size: int) -> ImageFont.ImageFont:
    win = os.environ.get("WINDIR", r"C:\Windows")
    fonts = Path(win) / "Fonts"

    candidates = []
    if prefer_bold:
        candidates += [fonts / "segoeuib.ttf", fonts / "arialbd.ttf", fonts / "calibrib.ttf"]
    else:
        candidates += [fonts / "segoeui.ttf", fonts / "arial.ttf", fonts / "calibri.ttf"]

    for p in candidates:
        try:
            if p.exists():
                return ImageFont.truetype(str(p), size=size)
        except Exception:
            pass

    return ImageFont.load_default()


def _ellipsize_to_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int) -> str:
    if draw.textlength(text, font=font) <= max_w:
        return text
    ell = "…"
    t = text
    while t and draw.textlength(t + ell, font=font) > max_w:
        t = t[:-1]
    return (t + ell) if t else ell


def _try_select_1x1_form(printer_name: str) -> None:
    """
    Best-effort: create/select a 1x1 inch form.
    If the driver honors it, the printer will stop feeding a long tail.
    If the driver ignores forms (common on receipt printers), you'll still get extra feed.
    """
    FORM_NAME = "TAGIFY_1x1"
    mm_thousandths = int(25.4 * 1000)  # 1 inch in thousandths of mm

    hPrinter = None
    try:
        hPrinter = win32print.OpenPrinter(printer_name)

        # Try add form if missing
        try:
            forms = [f["pName"] for f in win32print.EnumForms(hPrinter, 1)]
            if FORM_NAME not in forms:
                form = {
                    "pName": FORM_NAME,
                    "Size": {"cx": mm_thousandths, "cy": mm_thousandths},
                    "ImageableArea": {"left": 0, "top": 0, "right": mm_thousandths, "bottom": mm_thousandths},
                }
                win32print.AddForm(hPrinter, 1, form)
        except Exception:
            pass

        # Set printer devmode to use the form
        try:
            info2 = win32print.GetPrinter(hPrinter, 2)
            devmode = info2["pDevMode"]
            if devmode:
                devmode.FormName = FORM_NAME
                devmode.Fields |= win32con.DM_FORMNAME
                info2["pDevMode"] = devmode
                win32print.SetPrinter(hPrinter, 2, info2, 0)
        except Exception:
            pass

    finally:
        if hPrinter:
            try:
                win32print.ClosePrinter(hPrinter)
            except Exception:
                pass


def _print_png_gdi(printer_name: str, png_path: Path) -> None:
    from PIL import ImageWin

    img = Image.open(png_path).convert("RGB")

    # Create printer device context
    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name)

    hDC.StartDoc("Tagify Label")
    hDC.StartPage()

    printable_w = hDC.GetDeviceCaps(win32con.HORZRES)
    printable_h = hDC.GetDeviceCaps(win32con.VERTRES)

    img_w, img_h = img.size

    scale = min(printable_w / img_w, printable_h / img_h)

    out_w = int(img_w * scale)
    out_h = int(img_h * scale)

    x = int((printable_w - out_w) / 2)
    y = int((printable_h - out_h) / 2)

    # Convert PIL image to Windows bitmap
    dib = ImageWin.Dib(img)

    dib.draw(
        hDC.GetHandleOutput(),
        (x, y, x + out_w, y + out_h)
    )

    hDC.EndPage()
    hDC.EndDoc()
    hDC.DeleteDC()


def _make_bmi_header(w: int, h: int):
    """
    BITMAPINFOHEADER for 24bpp DIB.
    """
    return {
        "bmiHeader": {
            "biSize": 40,
            "biWidth": w,
            "biHeight": h,
            "biPlanes": 1,
            "biBitCount": 24,
            "biCompression": 0,
            "biSizeImage": w * h * 3,
            "biXPelsPerMeter": 0,
            "biYPelsPerMeter": 0,
            "biClrUsed": 0,
            "biClrImportant": 0,
        }
    }