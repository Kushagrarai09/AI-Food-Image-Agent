from pathlib import Path
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment


def save_report(rows: list[dict], output_path: Path, assumptions: list[tuple[str, str]] | None = None):
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["Food Item", "Image Found", "AI Score", "Image Processed", "Uploaded", "Source", "Status"])

    assumptions = assumptions or [
        ("Initial image source", "Wikimedia Commons API is used as the free automated source for the MVP."),
        ("AI threshold", "Images at or above the configured score threshold are accepted."),
        ("Output size", "Every final image is center-cropped/resized to exactly 1800 x 1200 pixels."),
        ("File size", "Final JPG files are compressed below 10 MB when possible."),
        ("Retry behavior", "Rejected candidates are skipped and the next candidate is evaluated automatically."),
        ("Image provenance", "Source URL, license and author are recorded when supplied by Wikimedia."),
        ("Drive authorization", "Google Drive uses OAuth; credentials are not stored in source code."),
    ]
    assumptions_df = pd.DataFrame(assumptions, columns=["Assumption", "Details"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Processing Report", index=False)
        assumptions_df.to_excel(writer, sheet_name="Assumptions", index=False)
        for ws in writer.book.worksheets:
            ws.freeze_panes = "A2"
            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")
            for col in ws.columns:
                max_len = max(len(str(c.value or "")) for c in col)
                ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 2, 12), 50)
    return output_path
