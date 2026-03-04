from __future__ import annotations

from dataclasses import dataclass

# Windows-only (pywin32)
import win32print


@dataclass
class PrinterState:
    ok: bool                 # True if we consider it connected/online
    status_text: str         # Human-readable status
    printer_name: str | None


def list_printers() -> list[str]:
    """
    Returns local + network printers visible to Windows.
    """
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    printers = [p[2] for p in win32print.EnumPrinters(flags)]

    # de-dupe, preserve order
    seen = set()
    out: list[str] = []
    for name in printers:
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def get_printer_state(printer_name: str | None) -> PrinterState:
    """
    Attempts to determine if the selected printer is available and not offline/paused/paperout.
    """
    if not printer_name:
        return PrinterState(False, "No printer selected", None)

    # ensure it exists in Windows list
    try:
        if printer_name not in list_printers():
            return PrinterState(False, "Not found", printer_name)
    except Exception:
        # If enumeration fails, still try open
        pass

    try:
        h = win32print.OpenPrinter(printer_name)
        try:
            info2 = win32print.GetPrinter(h, 2)  # PRINTER_INFO_2
            status = int(info2.get("Status", 0) or 0)

            OFFLINE = getattr(win32print, "PRINTER_STATUS_OFFLINE", 0x00000080)
            ERROR = getattr(win32print, "PRINTER_STATUS_ERROR", 0x00000002)
            PAPEROUT = getattr(win32print, "PRINTER_STATUS_PAPER_OUT", 0x00000010)
            PAUSED = getattr(win32print, "PRINTER_STATUS_PAUSED", 0x00000001)

            if status & OFFLINE:
                return PrinterState(False, "Offline", printer_name)
            if status & PAUSED:
                return PrinterState(False, "Paused", printer_name)
            if status & PAPEROUT:
                return PrinterState(False, "Paper out", printer_name)
            if status & ERROR:
                return PrinterState(False, "Error", printer_name)

            # Many drivers report 0 even when OK
            return PrinterState(True, "Connected", printer_name)
        finally:
            win32print.ClosePrinter(h)
    except Exception:
        return PrinterState(False, "Unavailable", printer_name)