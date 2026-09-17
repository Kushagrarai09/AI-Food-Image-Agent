from pathlib import Path
import time

import pandas as pd

from config.settings import (
    OUTPUT_DIR,
    DATA_DIR,
    CANDIDATES,
    AI_THRESHOLD,
    BLUR_THRESHOLD,
)

from agent.search import search_wikimedia, download_image
from agent.evaluator import evaluate_image
from agent.processor import process_image
from agent.validator import passes_basic_quality
from agent.reporter import save_report


def load_food_items(excel_path: Path) -> list[str]:
    df = pd.read_excel(excel_path)

    candidates = [
        "item_name",
        "Food Item",
        "food_item",
        "FoodItem",
    ]

    column = next(
        (c for c in candidates if c in df.columns),
        None,
    )

    if column is None:
        raise ValueError(
            "Excel must contain an 'item_name' or 'Food Item' column."
        )

    return [
        str(x).strip()
        for x in df[column].dropna().tolist()
        if str(x).strip()
    ]


def run_agent(
    excel_path: Path,
    candidates_per_item: int = CANDIDATES,
    threshold: int = AI_THRESHOLD,
    blur_threshold: float = BLUR_THRESHOLD,
    drive_folder_id: str = "",
    progress_callback=None,
):
    food_items = load_food_items(excel_path)

    rows = []

    output_dir = OUTPUT_DIR
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    total = len(food_items)

    for index, food_name in enumerate(food_items, start=1):

        def progress(message):
            if progress_callback:
                progress_callback(
                    index,
                    total,
                    food_name,
                    message,
                )

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
            # ==================================================
            # SEARCH
            # ==================================================

            progress("Searching candidate images...")

            candidates = search_wikimedia(
                food_name,
                limit=candidates_per_item,
            )

            if not candidates:
                raise RuntimeError(
                    "No image candidates found."
                )

            row["Image Found"] = "Yes"

            # ==================================================
            # EVALUATION
            # ==================================================

            selected = None
            selected_bytes = None
            selected_eval = None

            for n, candidate in enumerate(
                candidates,
                start=1,
            ):

                progress(
                    f"Evaluating candidate "
                    f"{n}/{len(candidates)}..."
                )

                # ------------------------------------------
                # Download
                # ------------------------------------------

                try:
                    raw = download_image(candidate)

                except Exception as exc:
                    progress(
                        f"Candidate {n} download failed: "
                        f"{exc}"
                    )
                    continue

                # ------------------------------------------
                # Basic quality check
                # ------------------------------------------

                try:
                    basic_ok, stats = passes_basic_quality(
                        raw,
                        blur_threshold,
                    )

                except Exception as exc:
                    progress(
                        f"Candidate {n} quality check failed: "
                        f"{exc}"
                    )
                    continue

                if not basic_ok:
                    progress(
                        f"Candidate {n} failed basic quality check."
                    )
                    continue

                # ------------------------------------------
                # AI evaluation
                # ------------------------------------------

                try:
                    evaluation = evaluate_image(
                        food_name,
                        raw,
                        threshold,
                    )

                except Exception as exc:
                    progress(
                        f"Candidate {n} AI evaluation failed: "
                        f"{exc}"
                    )
                    continue

                score = evaluation.get(
                    "overall_score",
                    0,
                )

                # ------------------------------------------
                # Keep best candidate
                # ------------------------------------------

                if (
                    selected_eval is None
                    or score
                    > selected_eval.get(
                        "overall_score",
                        0,
                    )
                ):
                    selected = candidate
                    selected_bytes = raw
                    selected_eval = evaluation

                # ------------------------------------------
                # Accept immediately if threshold reached
                # ------------------------------------------

                if evaluation.get("decision") == "ACCEPT":
                    break

            # ==================================================
            # NO VALID CANDIDATE
            # ==================================================

            if selected is None or selected_eval is None:
                raise RuntimeError(
                    "All candidate images failed quality/evaluation."
                )

            best_score = selected_eval.get(
                "overall_score",
                0,
            )

            if selected_eval.get("decision") != "ACCEPT":
                raise RuntimeError(
                    f"No candidate met AI threshold "
                    f"{threshold}; best score {best_score}."
                )

            # ==================================================
            # SAVE EVALUATION INFORMATION
            # ==================================================

            row["AI Score"] = best_score
            row["Source"] = selected.source
            row["Source URL"] = selected.page_url
            row["License"] = selected.license
            row["Author"] = selected.author

            progress(
                f"Accepted image with AI score "
                f"{best_score}; processing..."
            )

            # ==================================================
            # IMAGE PROCESSING
            # ==================================================

            path, metadata = process_image(
                selected_bytes,
                food_name,
                output_dir,
            )

            row["Image Processed"] = "Yes"
            row["Output File"] = str(path)
            row["Output Size Bytes"] = metadata[
                "size_bytes"
            ]
            row["Dimensions"] = (
                f"{metadata['width']}x"
                f"{metadata['height']}"
            )

            # ==================================================
            # GOOGLE DRIVE UPLOAD
            # ==================================================

            if drive_folder_id:

                from agent.drive import upload_file

                progress(
                    "Uploading to Google Drive..."
                )

                upload_success = False
                last_error = None

                for attempt in range(1, 4):

                    try:
                        row["Drive Link"] = upload_file(
                            path,
                            drive_folder_id,
                        )

                        row["Uploaded"] = "Yes"
                        upload_success = True

                        progress(
                            "Google Drive upload successful."
                        )

                        break

                    except Exception as exc:

                        last_error = exc

                        progress(
                            f"Drive upload failed "
                            f"(attempt {attempt}/3): "
                            f"{exc}"
                        )

                        if attempt < 3:
                            time.sleep(
                                2 * attempt
                            )

                if not upload_success:
                    raise RuntimeError(
                        "Google Drive upload failed "
                        f"after 3 attempts: "
                        f"{last_error}"
                    )

            # ==================================================
            # FINAL STATUS
            # ==================================================

            if row["Uploaded"] == "Yes":
                row["Status"] = "Success"
            else:
                row["Status"] = (
                    "Processed - Drive not configured"
                )

            progress(row["Status"])

        except Exception as exc:

            row["Error"] = str(exc)

            progress(
                f"Error: {exc}"
            )

        rows.append(row)

    # ==========================================================
    # SAVE REPORT
    # ==========================================================

    report_path = (
        DATA_DIR /
        "processing_report.xlsx"
    )

    save_report(
        rows,
        report_path,
    )

    # ==========================================================
    # UPLOAD REPORT
    # ==========================================================

    if drive_folder_id:

        try:

            from agent.drive import upload_report

            upload_report(
                report_path,
                drive_folder_id,
            )

        except Exception as exc:

            # Keep local report even if Drive report upload fails.
            pass

    return rows, report_path