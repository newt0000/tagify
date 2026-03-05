# label_print.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from PySide6.QtCore import Qt, QSizeF, QRectF
from PySide6.QtGui import QFont, QPainter
from PySide6.QtPrintSupport import QPrinter, QPrinterInfo


MM_PER_INCH = 25.4


@dataclass
class DirectPrintResult:
    ok: bool
    message: str


def list_printers_qt() -> list[str]:
    """Qt-side printer enumeration (works without pywin32)."""
    names = []
    for info in QPrinterInfo.availablePrinters():
        names.append(info.printerName())
    return names


def is_pdf_printer(printer_name: str | None) -> bool:
    if not printer_name:
        return False
    n = printer_name.lower()
    return ("print to pdf" in n) or ("pdf" == n.strip()) or ("pdf" in n and "printer" in n)


def print_label_direct(
    printer_name: str,
    item_name: str,
    prepped: date,
    expires: date,
    copies: int = 1,
) -> DirectPrintResult:
    """
    Prints a 1x1 inch label directly to the printer using Qt (no PDF temp file, no ShellExecute).
    Note: If printer_name is 'Microsoft Print to PDF', Windows will still prompt to save.
    """
    if not printer_name:
        return DirectPrintResult(False, "No printer selected.")

    # Print-to-PDF will always prompt user for a save path; that's driver behavior.
    if is_pdf_printer(printer_name):
        return DirectPrintResult(
            False,
            "Selected printer is a PDF printer (Print to PDF). "
            "Windows will always prompt for a save location. Select a real printer to print silently."
        )

    # Locate printer
    info = None
    for p in QPrinterInfo.availablePrinters():
        if p.printerName() == printer_name:
            info = p
            break
    if info is None:
        return DirectPrintResult(False, f"Printer not found: {printer_name}")

    # Setup printer job
    printer = QPrinter(info)
    printer.setPrinterName(printer_name)
    printer.setCopyCount(max(1, int(copies)))
    printer.setFullPage(True)

    # Force 1x1 inch page size (25.4mm x 25.4mm)
    printer.setPageSizeMM(QSizeF(MM_PER_INCH, MM_PER_INCH))

    # Higher DPI helps small label clarity (driver may override, but it's a good hint)
    printer.setResolution(300)

    painter = QPainter()
    if not painter.begin(printer):
        return DirectPrintResult(False, "Could not start print job (painter.begin failed).")

    try:
        # Work in printer pixels
        page_rect = printer.pageRect(QPrinter.DevicePixel)

        # Padding inside label
        pad = int(page_rect.width() * 0.07)
        x0 = page_rect.left() + pad
        y0 = page_rect.top() + pad
        w = page_rect.width() - 2 * pad
        h = page_rect.height() - 2 * pad

        # Text
        name = (item_name or "").strip()
        prepped_s = prepped.strftime("%m/%d/%Y")
        expires_s = expires.strftime("%m/%d/%Y")

        # Fonts (tune for 1x1)
        name_font = QFont("Segoe UI", 12)
        name_font.setBold(True)

        meta_font = QFont("Segoe UI", 8)

        painter.setRenderHint(QPainter.TextAntialiasing, True)

        # Draw name at top
        painter.setFont(name_font)
        name_box = QRectF(x0, y0, w, h * 0.50)
        painter.drawText(name_box, Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, name)

        # Draw meta
        painter.setFont(meta_font)
        meta_y = y0 + int(h * 0.55)
        line_h = int(h * 0.18)

        painter.drawText(QRectF(x0, meta_y, w, line_h), Qt.AlignLeft | Qt.AlignVCenter, f"Prepped: {prepped_s}")
        painter.drawText(QRectF(x0, meta_y + line_h, w, line_h), Qt.AlignLeft | Qt.AlignVCenter, f"Expires:  {expires_s}")

    finally:
        painter.end()

    return DirectPrintResult(True, f"Sent {copies} label(s) to printer: {printer_name}")