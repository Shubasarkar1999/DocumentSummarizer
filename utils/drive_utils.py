# drive_utils.py
import io
import os
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request

# Only readonly access
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

class DriveClient:
    def __init__(self, credentials_path: str = "client_secret.json", token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds: Optional[Credentials] = None
        self.service = None

    def authenticate(self):
        """Authenticate user via OAuth2, store token for reuse."""
        if os.path.exists(self.token_path):
            try:
                self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception:
                self.creds = None

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open(self.token_path, "w") as token:
                token.write(self.creds.to_json())

        self.service = build("drive", "v3", credentials=self.creds)

    def list_files_in_folder(self, folder_id: str) -> List[Dict]:
        """List PDF/DOCX/TXT files in the given folder."""
        mime_filters = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        ]
        q = f"'{folder_id}' in parents and ({' or '.join([f'mimeType = \"{m}\"' for m in mime_filters])}) and trashed = false"
        files = []
        page_token = None
        while True:
            res = self.service.files().list(
                q=q,
                fields="nextPageToken, files(id, name, mimeType, webViewLink)",
                pageToken=page_token,
            ).execute()
            files.extend(res.get("files", []))
            page_token = res.get("nextPageToken")
            if not page_token:
                break
        return files

    def download_file(self, file_id: str, dest_path: str) -> str:
        """Download a file by ID into dest_path."""
        request = self.service.files().get_media(fileId=file_id)
        with io.FileIO(dest_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done: 
                _, done = downloader.next_chunk()
        return dest_path
