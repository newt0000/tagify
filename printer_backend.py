from __future__ import annotations
from dataclasses import dataclass

@dataclass
class PrinterState:
    ok: bool                 # True if we consider it "connected/online"
    status_text: str         # Human-readable status
    printer_name: str | None

def list_printers() -> list[str]:
    """
    Returns local + network printers if pywin32 is installed.
    """
    try:
        import win32print
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        printers = [p[2] for p in win32print.EnumPrinters(flags)]
        # de-dupe while preserving order
        seen = set()
        out = []
        for name in printers:
            if name not in seen:
                seen.add(name)
                out.append(name)
        return out
    except Exception:
        return []

def get_printer_state(printer_name: str | None) -> PrinterState:
    """
    Checks whether the printer exists and if Windows reports it as offline.
    """
    if not printer_name:
        return PrinterState(False, "No printer selected", None)

    try:
        import win32print

        # Ensure printer exists
        all_printers = list_printers()
        if printer_name not in all_printers:
            return PrinterState(False, "Not found", printer_name)

        h = win32print.OpenPrinter(printer_name)
        try:
            info2 = win32print.GetPrinter(h, 2)  # PRINTER_INFO_2
            status = info2.get("Status", 0)

            # Common flags (not exhaustive)
            # Some drivers don't set these consistently; treat offline as hard-fail.
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
                # Many devices set "ERROR" even when fine; still mark not-ok.
                return PrinterState(False, "Error", printer_name)

            # If not offline/paused/paperout/error, assume OK.
            return PrinterState(True, "Connected", printer_name)
        finally:
            win32print.ClosePrinter(h)

    except Exception:
        # If pywin32 isn't available or driver behaves weirdly
        return PrinterState(False, "Unknown", printer_name)