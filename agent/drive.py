from pathlib import Path

import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from config.settings import (
    GOOGLE_CREDENTIALS_FILE,
    TOKEN_FILE,
)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def get_drive_service():

    # =========================================================
    # STREAMLIT CLOUD - SERVICE ACCOUNT
    # =========================================================

    if "gcp_service_account" in st.secrets:

        try:
            service_account_info = dict(
                st.secrets["gcp_service_account"]
            )

            required_fields = [
                "type",
                "project_id",
                "private_key",
                "client_email",
            ]

            missing = [
                field
                for field in required_fields
                if not service_account_info.get(field)
            ]

            if missing:
                raise RuntimeError(
                    "Missing Service Account fields in "
                    f"Streamlit Secrets: {', '.join(missing)}"
                )

            creds = (
                service_account.Credentials
                .from_service_account_info(
                    service_account_info,
                    scopes=SCOPES,
                )
            )

            return build(
                "drive",
                "v3",
                credentials=creds,
                cache_discovery=False,
            )

        except Exception as exc:
            raise RuntimeError(
                f"Streamlit Service Account authentication failed: {exc}"
            ) from exc

    # =========================================================
    # LOCAL DEVELOPMENT - OAUTH
    # =========================================================

    creds = None

    if TOKEN_FILE.exists():

        creds = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES,
        )

    if creds and creds.expired and creds.refresh_token:

        creds.refresh(Request())

    if not creds or not creds.valid:

        if not GOOGLE_CREDENTIALS_FILE.exists():

            raise FileNotFoundError(
                "Google Drive authentication is not configured. "
                "Add [gcp_service_account] to Streamlit Secrets "
                "for the deployed app, or put credentials.json "
                "inside credentials/ for local development."
            )

        flow = (
            InstalledAppFlow
            .from_client_secrets_file(
                str(GOOGLE_CREDENTIALS_FILE),
                SCOPES,
            )
        )

        creds = flow.run_local_server(
            port=0
        )

        TOKEN_FILE.write_text(
            creds.to_json(),
            encoding="utf-8",
        )

    return build(
        "drive",
        "v3",
        credentials=creds,
        cache_discovery=False,
    )


def upload_file(
    file_path: Path,
    folder_id: str,
) -> str:

    service = get_drive_service()

    metadata = {
        "name": file_path.name,
        "parents": [folder_id],
    }

    media = MediaFileUpload(
        str(file_path),
        mimetype="image/jpeg",
        resumable=True,
    )

    result = (
        service.files()
        .create(
            body=metadata,
            media_body=media,
            fields="id,webViewLink",
        )
        .execute()
    )

    return (
        result.get("webViewLink")
        or result.get("id", "")
    )


def upload_report(
    file_path: Path,
    folder_id: str,
) -> str:

    service = get_drive_service()

    metadata = {
        "name": file_path.name,
        "parents": [folder_id],
    }

    media = MediaFileUpload(
        str(file_path),
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        resumable=True,
    )

    result = (
        service.files()
        .create(
            body=metadata,
            media_body=media,
            fields="id,webViewLink",
        )
        .execute()
    )

    return (
        result.get("webViewLink")
        or result.get("id", "")
    )