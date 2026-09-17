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

from agent.search import (
    search_wikimedia,
    download_image,
)

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
        (
            c
            for c in candidates
            if c in df.columns
        ),
        None,
    )

    if column is None:
        raise ValueError(
            "Excel must contain an "
            "'item_name' or 'Food Item' column."
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

    total_items = len(food_items)

    for index, food_name in enumerate(
        food_items,
        start=1,
    ):

        def progress(message):

            if progress_callback:
                progress_callback(
                    index,
                    total_items,
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

            progress(
                "Searching candidate images..."
            )

            candidates = search_wikimedia(
                food_name,
                limit=candidates_per_item,
            )

            if not candidates:

                raise RuntimeError(
                    "No image candidates found after "
                    "retrying Wikimedia searches."
                )

            row["Image Found"] = "Yes"

            # ==================================================
            # CANDIDATE EVALUATION
            # ==================================================

            selected = None
            selected_bytes = None
            selected_eval = None

            best_score = -1

            for n, candidate in enumerate(
                candidates,
                start=1,
            ):

                progress(
                    f"Evaluating candidate "
                    f"{n}/{len(candidates)}..."
                )

                # ----------------------------------------------
                # DOWNLOAD
                # ----------------------------------------------

                try:

                    raw = download_image(
                        candidate
                    )

                except Exception as download_error:

                    progress(
                        f"Candidate {n} download failed; "
                        f"trying next candidate..."
                    )

                    continue

                # ----------------------------------------------
                # BASIC QUALITY
                # ----------------------------------------------

                try:

                    basic_ok, stats = (
                        passes_basic_quality(
                            raw,
                            blur_threshold,
                        )
                    )

                except Exception:

                    basic_ok = False

                if not basic_ok:

                    progress(
                        f"Candidate {n} failed basic "
                        f"quality check."
                    )

                    continue

                # ----------------------------------------------
                # AI EVALUATION
                # ----------------------------------------------

                try:

                    evaluation = evaluate_image(
                        food_name,
                        raw,
                        threshold,
                    )

                except Exception as evaluation_error:

                    progress(
                        f"Candidate {n} AI evaluation "
                        f"failed; trying next candidate..."
                    )

                    continue

                score = float(
                    evaluation.get(
                        "overall_score",
                        0,
                    )
                    or 0
                )

                # Save the best candidate even if it
                # doesn't immediately meet the threshold.
                if score > best_score:

                    best_score = score

                    selected = candidate
                    selected_bytes = raw
                    selected_eval = evaluation

                # Stop immediately when we have a valid
                # accepted candidate.
                if (
                    evaluation.get("decision")
                    == "ACCEPT"
                ):

                    break

            # ==================================================
            # FINAL CANDIDATE DECISION
            # ==================================================

            if (
                selected is None
                or selected_eval is None
            ):

                raise RuntimeError(
                    "All candidate images failed "
                    "download or quality checks."
                )

            final_score = float(
                selected_eval.get(
                    "overall_score",
                    0,
                )
                or 0
            )

            if (
                selected_eval.get("decision")
                != "ACCEPT"
            ):

                raise RuntimeError(
                    f"No candidate met AI threshold "
                    f"{threshold}; best score "
                    f"{final_score}."
                )

            row["AI Score"] = final_score

            row["Source"] = (
                selected.source
            )

            row["Source URL"] = (
                selected.page_url
            )

            row["License"] = (
                selected.license
            )

            row["Author"] = (
                selected.author
            )

            # ==================================================
            # IMAGE PROCESSING
            # ==================================================

            progress(
                f"Accepted image with AI score "
                f"{final_score}; processing..."
            )

            path, metadata = process_image(
                selected_bytes,
                food_name,
                output_dir,
            )

            row["Image Processed"] = "Yes"

            row["Output File"] = str(path)

            row["Output Size Bytes"] = (
                metadata["size_bytes"]
            )

            row["Dimensions"] = (
                f"{metadata['width']}x"
                f"{metadata['height']}"
            )

            # ==================================================
            # GOOGLE DRIVE
            # ==================================================

            if drive_folder_id:

                from agent.drive import upload_file

                progress(
                    "Uploading to Google Drive..."
                )

                upload_error = None

                # Retry Drive upload up to 3 times.
                for upload_attempt in range(3):

                    try:

                        drive_link = upload_file(
                            path,
                            drive_folder_id,
                        )

                        row["Drive Link"] = (
                            drive_link
                        )

                        row["Uploaded"] = "Yes"

                        upload_error = None

                        break

                    except Exception as exc:

                        upload_error = exc

                        if upload_attempt < 2:

                            progress(
                                "Drive upload failed; "
                                "retrying..."
                            )

                            time.sleep(
                                2 * (
                                    upload_attempt + 1
                                )
                            )

                if upload_error is not None:

                    raise RuntimeError(
                        "Google Drive upload failed "
                        f"after 3 attempts: "
                        f"{upload_error}"
                    )

            # ==================================================
            # SUCCESS
            # ==================================================

            if row["Uploaded"] == "Yes":

                row["Status"] = "Success"

            else:

                row["Status"] = (
                    "Processed - Drive not configured"
                )

            progress(
                row["Status"]
            )

        except Exception as exc:

            row["Error"] = str(exc)

            row["Status"] = "Failed"

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
    from agent.drive import upload_file

    progress("Uploading to Google Drive...")

    try:
        row["Drive Link"] = upload_file(path, drive_folder_id)
        row["Uploaded"] = "Yes"

    except Exception as exc:
        row["Uploaded"] = "No"
        row["Error"] = f"DRIVE UPLOAD ERROR: {type(exc).__name__}: {exc}"
        progress(f"Drive upload failed: {exc}")
        raise