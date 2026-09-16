"""Convert the employer's 17-page menu PDF into a usable Excel input file.
The production agent itself expects Excel; this helper is only for preparing the provided sample dataset.
"""
import sys
from pathlib import Path
import pdfplumber
import pandas as pd


def convert(pdf_path: str, output_path: str = "data/sample_input.xlsx"):
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(x_tolerance=1, y_tolerance=2)
            groups = {}
            for w in words:
                key = round(w["top"], 1)
                groups.setdefault(key, []).append(w)
            for _, ws in sorted(groups.items()):
                cols = {"menu_category": [], "menu_sub_category": [], "item_name": [], "Description": [], "Google drive link": []}
                for w in sorted(ws, key=lambda x: x["x0"]):
                    x = w["x0"]
                    if x < 240:
                        cols["menu_category"].append(w["text"])
                    elif x < 345:
                        cols["menu_sub_category"].append(w["text"])
                    elif x < 495:
                        cols["item_name"].append(w["text"])
                    elif x < 570:
                        cols["Description"].append(w["text"])
                    else:
                        cols["Google drive link"].append(w["text"])
                item = " ".join(cols["item_name"]).strip()
                if item and item.lower() != "item_name":
                    rows.append({k: " ".join(v).strip() for k, v in cols.items()})
    df = pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)
    print(f"Wrote {len(df)} rows to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_menu_pdf.py <menu.pdf> [output.xlsx]")
        raise SystemExit(1)
    convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data/sample_input.xlsx")
