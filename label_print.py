import os
import tempfile
from datetime import date
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def generate_1x1_label_pdf(item_name: str, prepped: date, expires: date, out_path: Path):
    # 1x1 inch page
    c = canvas.Canvas(str(out_path), pagesize=(1*inch, 1*inch))

    # Simple layout: big name + two lines of dates
    # Keep it tight; 1x1 is tiny.
    name = item_name.strip()[:26]  # safety
    prepped_s = prepped.strftime("%m/%d/%Y")
    expires_s = expires.strftime("%m/%d/%Y")

    # Font sizes
    c.setFont("Helvetica-Bold", 10)
    c.drawString(4, 52, name)

    c.setFont("Helvetica", 7)
    c.drawString(4, 34, f"Prepped: {prepped_s}")
    c.drawString(4, 22, f"Expires: {expires_s}")

    c.showPage()
    c.save()

def _try_print_win32(pdf_path: str, printer_name: str | None) -> bool:
    """
    Uses pywin32 if installed. If not installed, return False.
    """
    try:
        import win32api
        import win32print
    except Exception:
        return False

    if printer_name:
        win32print.SetDefaultPrinter(printer_name)

    # "print" uses the default app handler for PDF (e.g., Adobe/Edge),
    # which can be acceptable for many setups. For robust spool control,
    # you'd do a dedicated PDF -> printer pipeline (later).

    win32api.ShellExecute(0, "print", pdf_path, None, ".", 0)
    return True

def print_label_pdf(pdf_path: str, printer_name: str | None = None):
    # Try pywin32 path first, then fallback to os.startfile
    if os.name == "nt":
        if _try_print_win32(pdf_path, printer_name):
            return
        try:
            os.startfile(pdf_path, "print")  # type: ignore[attr-defined]
            return
        except Exception as e:
            raise RuntimeError(f"Printing failed. Install pywin32 for better reliability. Details: {e}")
    else:
        raise RuntimeError("Printing is currently implemented for Windows only.")

def make_temp_label_path() -> Path:
    d = Path(tempfile.gettempdir())
    return d / "prep_label_1x1.pdf"