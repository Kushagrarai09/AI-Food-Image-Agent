from pathlib import Path
import pandas as pd

from config.settings import OUTPUT_DIR, DATA_DIR, CANDIDATES, AI_THRESHOLD, BLUR_THRESHOLD
from agent.search import search_wikimedia, download_image
from agent.evaluator import evaluate_image
from agent.processor import process_image
from agent.validator import passes_basic_quality
from agent.reporter import save_report


def load_food_items(excel_path: Path) -> list[str]:
    df = pd.read_excel(excel_path)
    # Assignment requires a food item list; support the supplied item_name column and simpler Food Item variants.
    candidates = ["item_name", "Food Item", "food_item", "FoodItem"]
    column = next((c for c in candidates if c in df.columns), None)
    if column is None:
        raise ValueError("Excel must contain an 'item_name' or 'Food Item' column.")
    return [str(x).strip() for x in df[column].dropna().tolist() if str(x).strip()]


def run_agent(excel_path: Path, candidates_per_item: int = CANDIDATES,
              threshold: int = AI_THRESHOLD, blur_threshold: float = BLUR_THRESHOLD,
              drive_folder_id: str = "", progress_callback=None):
    food_items = load_food_items(excel_path)
    rows = []
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    for index, food_name in enumerate(food_items, start=1):
        def progress(message):
            if progress_callback:
                progress_callback(index, len(food_items), food_name, message)

        row = {
            "Food Item": food_name,
            "Image Found": "No",
            "AI Score": "",
            "Image Processed": "No",
            "Uploaded": "No",
            "Source": "",
            "Source URL": "",
            "License": "",
            "Author": "",
            "Status": "Failed",
            "Error": "",
        }
        try:
            progress("Searching candidate images...")
            candidates = search_wikimedia(food_name, limit=candidates_per_item)
            if not candidates:
                raise RuntimeError("No image candidates found.")
            row["Image Found"] = "Yes"

            selected = None
            selected_bytes = None
            selected_eval = None
            for n, candidate in enumerate(candidates, start=1):
                progress(f"Evaluating candidate {n}/{len(candidates)}...")
                raw = download_image(candidate)
                basic_ok, stats = passes_basic_quality(raw, blur_threshold)
                if not basic_ok:
                    continue
                evaluation = evaluate_image(food_name, raw, threshold)
                if selected_eval is None or evaluation.get("overall_score", 0) > selected_eval.get("overall_score", 0):
                    selected, selected_bytes, selected_eval = candidate, raw, evaluation
                if evaluation.get("decision") == "ACCEPT":
                    break

            if selected is None or selected_eval is None:
                raise RuntimeError("All candidate images failed basic quality checks.")
            if selected_eval.get("decision") != "ACCEPT":
                raise RuntimeError(f"No candidate met AI threshold {threshold}; best score {selected_eval.get('overall_score', 0)}.")

            row["AI Score"] = selected_eval.get("overall_score", 0)
            row["Source"] = selected.source
            row["Source URL"] = selected.page_url
            row["License"] = selected.license
            row["Author"] = selected.author
            progress(f"Accepted image with AI score {row['AI Score']}; processing...")
            path, metadata = process_image(selected_bytes, food_name, output_dir)
            row["Image Processed"] = "Yes"
            row["Output File"] = str(path)
            row["Output Size Bytes"] = metadata["size_bytes"]
            row["Dimensions"] = f"{metadata['width']}x{metadata['height']}"

            if drive_folder_id:
                from agent.drive import upload_file
                progress("Uploading to Google Drive...")
                row["Drive Link"] = upload_file(path, drive_folder_id)
                row["Uploaded"] = "Yes"
            row["Status"] = "Success" if row["Uploaded"] == "Yes" else "Processed - Drive not configured"
            progress(row["Status"])
        except Exception as exc:
            row["Error"] = str(exc)
            progress(f"Error: {exc}")
        rows.append(row)

    report_path = DATA_DIR / "processing_report.xlsx"
    save_report(rows, report_path)
    if drive_folder_id:
        try:
            from agent.drive import upload_report
            upload_report(report_path, drive_folder_id)
        except Exception as exc:
            # Report remains available locally even if its Drive upload fails.
            pass
    return rows, report_path
