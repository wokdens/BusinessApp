import os
import sys
import ctypes
from ctypes import wintypes
from datetime import datetime

class DOC_INFO_1(ctypes.Structure):
    _fields_ = [
        ('pDocName', wintypes.LPCWSTR),
        ('pOutputFile', wintypes.LPCWSTR),
        ('pDatatype', wintypes.LPCWSTR),
    ]

class PRINTER_INFO_1(ctypes.Structure):
    _fields_ = [
        ('flags', wintypes.DWORD),
        ('pDescription', wintypes.LPCWSTR),
        ('pName', wintypes.LPCWSTR),
        ('pComment', wintypes.LPCWSTR),
    ]

def get_available_printers():
    """Return list of all installed printer names on Windows (instant winspool)."""
    printers = []
    if sys.platform != 'win32':
        return printers
    try:
        winspool = ctypes.WinDLL('winspool.drv')
        flags = 2 | 4  # PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS
        cbNeeded = wintypes.DWORD(0)
        cReturned = wintypes.DWORD(0)
        winspool.EnumPrintersW(flags, None, 1, None, 0, ctypes.byref(cbNeeded), ctypes.byref(cReturned))
        if cbNeeded.value > 0:
            buf = (ctypes.c_byte * cbNeeded.value)()
            if winspool.EnumPrintersW(flags, None, 1, buf, cbNeeded.value, ctypes.byref(cbNeeded), ctypes.byref(cReturned)):
                p_info = ctypes.cast(buf, ctypes.POINTER(PRINTER_INFO_1))
                for i in range(cReturned.value):
                    if p_info[i].pName:
                        printers.append(p_info[i].pName)
    except Exception:
        pass
    return printers

def find_thermal_printer():
    printers = get_available_printers()
    keywords = ['POS80', 'POS-80', 'H80I', 'H80', 'HOIN', 'HELETT', 'XP-80', '80MM', 'RECEIPT', 'THERMAL', 'POS']
    for kw in keywords:
        for p in printers:
            if kw.lower() in p.lower():
                return p
    return None

def format_esc_pos_receipt(invoice_number, customer_name, items, grand_total, paid_amount=0, note='', date_str=None):
    clean_num = str(invoice_number).replace('INV-', '').strip()
    d_str = date_str or datetime.now().strftime('%d-%m-%Y  %I:%M %p')
    ESC = b'\x1b'
    GS = b'\x1d'
    INIT = ESC + b'@'
    FONT_A = ESC + b'M\x00'
    ALIGN_LEFT = ESC + b'a\x00'
    ALIGN_CENTER = ESC + b'a\x01'
    ALIGN_RIGHT = ESC + b'a\x02'
    BOLD_ON = ESC + b'E\x01'
    BOLD_OFF = ESC + b'E\x00'
    FEED_CUT = b'\n\n' + GS + b'V\x42\x00'

    out = bytearray()
    out.extend(INIT)
    out.extend(FONT_A)
    out.extend(ALIGN_CENTER + BOLD_ON + b'ESTIMATE ONLY\n' + BOLD_OFF)
    out.extend(f'Date: {d_str}\n'.encode('ascii', 'replace'))
    out.extend(ALIGN_LEFT)
    out.extend(f'Est No   : INV-{clean_num}\n'.encode('ascii', 'replace'))
    out.extend(BOLD_ON + f'Customer : {customer_name.upper()}\n'.encode('ascii', 'replace') + BOLD_OFF)
    out.extend(b'=' * 48 + b'\n')

    # Header: 48 Chars Font A
    out.extend(BOLD_ON + f"{'Item Description & Pricing Details':<38}{'Amount':>10}\n".encode('ascii', 'replace') + BOLD_OFF)
    out.extend(b'-' * 48 + b'\n')

    serial = 1
    total_qty = 0
    for it in items:
        qty = it.get('quantity', 0)
        total_qty += qty
        name = str(it.get('name', ''))[:44]
        mrp = float(it.get('mrp', 0) or 0)
        price = float(it.get('price', 0) or 0)
        unit = str(it.get('unit', 'Pcs') or 'Pcs').strip()
        disc = float(it.get('discount', 0) or 0)
        tot = float(it.get('total', 0) or 0)
        tot_str = f"{tot:,.2f}"

        # Line 1: Item Name in Bold
        out.extend(BOLD_ON + f"{serial}. {name}\n".encode('ascii', 'replace') + BOLD_OFF)

        # Line 2: Details & Tags
        unit_str = f" {unit}" if unit else " pcs"
        left_sub = f"   {qty}{unit_str} x Rs.{price:,.2f}"

        extra_tags = []
        if mrp > 0:
            extra_tags.append(f"MRP: {mrp:,.0f}")
        if disc > 0:
            disc_tag = f"{int(disc) if disc.is_integer() else disc}%"
            extra_tags.append(f"Disc: {disc_tag}")

        if extra_tags:
            left_sub += f" ({' | '.join(extra_tags)})"

        if len(left_sub) > 36:
            left_sub = left_sub[:36]

        out.extend(f"{left_sub:<36}{tot_str:>12}\n".encode('ascii', 'replace'))
        serial += 1

    out.extend(b'=' * 48 + b'\n')
    out.extend(f"Total Items: {len(items)}   |   Total Qty: {total_qty}\n".encode('ascii', 'replace'))
    out.extend(ALIGN_RIGHT + BOLD_ON + f"GRAND TOTAL: Rs. {grand_total:,.2f}\n".encode('ascii', 'replace') + BOLD_OFF)
    if note and note.strip():
        out.extend(ALIGN_LEFT + f"Note: {note.strip()}\n".encode('ascii', 'replace'))
    out.extend(ALIGN_CENTER + b'------------------------------------------------\n')
    out.extend(b'GST as per applicable. Order against PO.\n')
    out.extend(BOLD_ON + b'Powered by wokdens.com\n' + BOLD_OFF)
    out.extend(FEED_CUT)
    return bytes(out)

def send_raw_to_printer(printer_name, data: bytes, doc_name='Receipt'):
    if sys.platform != 'win32':
        return False, 'Direct printing is only supported on Windows.'
    try:
        winspool = ctypes.WinDLL("winspool.drv")
        hPrinter = wintypes.HANDLE()
        if not winspool.OpenPrinterW(printer_name, ctypes.byref(hPrinter), None):
            return False, f'Could not open printer {printer_name} (Error: {ctypes.GetLastError()})'
        doc_info = DOC_INFO_1()
        doc_info.pDocName = doc_name
        doc_info.pOutputFile = None
        doc_info.pDatatype = 'RAW'
        job_id = winspool.StartDocPrinterW(hPrinter, 1, ctypes.byref(doc_info))
        if job_id == 0:
            winspool.ClosePrinter(hPrinter)
            return False, f'StartDocPrinter failed (Error: {ctypes.GetLastError()})'
        winspool.StartPagePrinter(hPrinter)
        written = wintypes.DWORD()
        winspool.WritePrinter(hPrinter, data, len(data), ctypes.byref(written))
        winspool.EndPagePrinter(hPrinter)
        winspool.EndDocPrinter(hPrinter)
        winspool.ClosePrinter(hPrinter)
        return True, f'Successfully printed on {printer_name}'
    except Exception as e:
        return False, str(e)

def print_receipt_direct(invoice_number, customer_name, items, grand_total, paid_amount=0, note='', date_str=None, printer_name=None):
    target_printer = printer_name or find_thermal_printer()
    if not target_printer:
        return False, 'No thermal POS printer detected.'
    raw_data = format_esc_pos_receipt(
        invoice_number=invoice_number,
        customer_name=customer_name,
        items=items,
        grand_total=grand_total,
        paid_amount=paid_amount,
        note=note,
        date_str=date_str
    )
    return send_raw_to_printer(target_printer, raw_data, doc_name=f'INV-{invoice_number}')
