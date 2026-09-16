from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config.settings import GOOGLE_CREDENTIALS_FILE, TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_drive_service():
    creds: Optional[Credentials] = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not GOOGLE_CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                "Google OAuth credentials not found. Put your OAuth client JSON at credentials/credentials.json."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(GOOGLE_CREDENTIALS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return build("drive", "v3", credentials=creds)


def upload_file(file_path: Path, folder_id: str) -> str:
    service = get_drive_service()
    metadata = {"name": file_path.name, "parents": [folder_id]}
    media = MediaFileUpload(str(file_path), mimetype="image/jpeg", resumable=True)
    result = service.files().create(body=metadata, media_body=media, fields="id,webViewLink").execute()
    return result.get("webViewLink") or result.get("id", "")


def upload_report(file_path: Path, folder_id: str) -> str:
    service = get_drive_service()
    metadata = {"name": file_path.name, "parents": [folder_id]}
    media = MediaFileUpload(
        str(file_path),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        resumable=True,
    )
    result = service.files().create(body=metadata, media_body=media, fields="id,webViewLink").execute()
    return result.get("webViewLink") or result.get("id", "")
