# Parses downloaded DockSync export files (xlsx/pdf) and prints contents for verification
import glob, openpyxl, pypdf

for f in sorted(glob.glob("/tmp/exports/*")):
    print("=====", f)
    if f.endswith(".xlsx"):
        ws = openpyxl.load_workbook(f).active
        print("sheet:", ws.title)
        for r in ws.iter_rows(values_only=True):
            print(r)
    else:
        for p in pypdf.PdfReader(f).pages:
            print(p.extract_text())
