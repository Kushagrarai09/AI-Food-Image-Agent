# AI Food Image Agent

A small AI-powered employee for restaurant menu image preparation.

## Assignment mapping

Excel food list → image search → candidate selection → AI quality evaluation → blur/resolution checks → retry → 1800×1200 JPG → exact food-name filename → Google Drive → Excel report.

## Architecture

```text
                         ┌───────────────────────┐
                         │     Restaurant Excel  │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │   Agent Controller    │
                         └───────────┬───────────┘
                                     │
                         ┌───────────▼───────────┐
                         │ Wikimedia Image Search│
                         └───────────┬───────────┘
                                     │ candidates
                                     ▼
                         ┌───────────────────────┐
                         │ Basic Quality Checks  │
                         │ blur / resolution     │
                         └───────────┬───────────┘
                                     ▼
                         ┌───────────────────────┐
                         │ Gemini Vision         │
                         │ match / clarity /     │
                         │ centering / framing   │
                         └───────────┬───────────┘
                                     │ accept/reject
                                     ▼
                         ┌───────────────────────┐
                         │ Pillow Processor      │
                         │ 1800×1200 / <10 MB    │
                         └───────────┬───────────┘
                                     ▼
                         ┌───────────────────────┐
                         │ Google Drive          │
                         └───────────┬───────────┘
                                     ▼
                         ┌───────────────────────┐
                         │ Processing Report     │
                         └───────────────────────┘
```

## 1. Install

Windows PowerShell:

```powershell
cd AI-Food-Image-Agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, run the project with the venv Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Configure Gemini

Copy `.env.example` to `.env` and add your Gemini API key:

```text
GEMINI_API_KEY=YOUR_KEY
GEMINI_MODEL=gemini-2.5-flash
```

The agent can still run without a key using a deterministic fallback evaluator, but Gemini is the intended AI evaluation mode for the assignment.

## 3. Prepare the supplied dataset

The employer supplied a 17-page PDF containing menu columns including `menu_category`, `menu_sub_category`, `item_name`, `Description`, and `Google drive link`.

Run:

```powershell
python convert_menu_pdf.py "..\Assignment - Ai agent  - Sheet1.pdf" data\sample_input.xlsx
```

Or use any Excel file with an `item_name` or `Food Item` column.

## 4. Google Drive setup

1. Create/select a Google Cloud project.
2. Enable Google Drive API.
3. Configure an OAuth Desktop application.
4. Download the OAuth client JSON.
5. Rename it to `credentials.json` and put it in `credentials/credentials.json`.
6. Create a Google Drive folder and copy its folder ID from the folder URL.
7. Paste the ID into the Streamlit sidebar.

On the first upload, a browser window opens for OAuth authorization. The token is stored locally in `credentials/token.json` and is ignored by Git.

## 5. Run the application

```powershell
streamlit run app.py
```

Then:

1. Upload `data/sample_input.xlsx`.
2. Set candidates per item (5 is a good demo setting).
3. Set AI threshold (75 is a good demo threshold).
4. Enter the Google Drive folder ID.
5. Click **START AGENT**.

## 6. Output

Local output:

```text
output/images/
  Chicken_Tandoori.jpg
  Dal_Tadka.jpg
  Veg_Dum_Biryani.jpg
  ...
```

Report:

```text
data/processing_report.xlsx
```

The report contains Processing Report and Assumptions sheets. It records food item, image found, AI score, processing status, Drive status, source URL, license, author, output dimensions and errors.

## 7. Important image-source note

This free MVP uses Wikimedia Commons as the automated search provider. It is not a claim that Google Images, Zomato or restaurant websites are freely scrapeable. The provider is isolated in `agent/search.py`, so a compliant commercial search provider can be added later without changing the rest of the agent.

For real menu publishing, review the source license/permissions. The report keeps provenance fields when the source provides them.

## 8. Error handling

Each food item is processed independently. If a search, download, quality check, AI evaluation, processing step or Drive upload fails, the agent records the error and continues with the next food item.

## 9. Quick CLI test

You can run the agent without Streamlit:

```powershell
python -c "from agent.controller import run_agent; print(run_agent('data/sample_input.xlsx')[1])"
```

## 10. Demo flow for employer

Upload the Excel → click Start Agent → show candidate evaluation/retry → show processed 1800×1200 files in Drive → open `processing_report.xlsx` → explain that the agent removed repetitive manual search/resize/upload work.
