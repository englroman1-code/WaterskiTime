"""Analysiere die Excel-Datei: Named Ranges, Sheets, Datenstruktur."""

import openpyxl
from pathlib import Path

EXCEL_PATH = Path("Excel/Test_StopUhr_V1.xlsm")

wb = openpyxl.load_workbook(EXCEL_PATH, keep_vba=True)

# --- Defined Names ---
print("=" * 60)
print("DEFINED NAMES (Bereichsnamen)")
print("=" * 60)
dn = wb.defined_names
for name, defn in dn.items():
    print(f"\n  Name:  {name}")
    print(f"  Value: {defn.value}")
    destinations = list(defn.destinations)
    for sheet_name, coord in destinations:
        print(f"  Sheet: {sheet_name}  Range: {coord}")

# --- Sheets ---
print("\n" + "=" * 60)
print(f"SHEETS: {wb.sheetnames}")
print("=" * 60)

for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    print(f"\n--- Sheet: {sheet_name} ---")
    print(f"  Max Row: {ws.max_row}, Max Col: {ws.max_column}")
    print()

    max_rows = min(ws.max_row, 25)
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=max_rows, values_only=True), 1):
        vals = list(row)
        while vals and vals[-1] is None:
            vals.pop()
        if vals:
            # Kürze lange Werte
            display = []
            for v in vals:
                s = str(v) if v is not None else ""
                if len(s) > 40:
                    s = s[:37] + "..."
                display.append(s)
            print(f"  {i:3d}: {display}")

wb.close()
