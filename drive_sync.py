import json
import mimetypes
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse


class DriveAuthRequired(RuntimeError):
    """Raised when an interactive Google login is required."""


class DriveConfigError(RuntimeError):
    """Raised when Drive configuration or dependencies are unavailable."""


class DriveSyncManager:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.config_path = self.base_dir / "drive_config.json"

    def load_config(self):
        if not self.config_path.exists():
            raise DriveConfigError("drive_config.json is missing.")
        try:
            config = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise DriveConfigError("drive_config.json could not be read.") from error

        if not config.get("folder_url"):
            raise DriveConfigError("Google Drive folder_url is missing from drive_config.json.")
        return config

    def resolve_path(self, value):
        path = Path(value)
        return path if path.is_absolute() else self.base_dir / path

    @staticmethod
    def extract_folder_id(url):
        parsed = urlparse(url.strip())
        match = re.search(r"/folders/([a-zA-Z0-9_-]+)", parsed.path)
        if match:
            return match.group(1)
        query = parse_qs(parsed.query)
        if query.get("id"):
            return query["id"][0]
        raise DriveConfigError("Could not extract a Google Drive folder ID from drive_config.json.")

    def _google_modules(self):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
        except ImportError as error:
            raise DriveConfigError(
                "Google Drive packages are missing. Install requirements.txt first."
            ) from error
        return Request, Credentials, InstalledAppFlow, build, MediaFileUpload

    def _save_token(self, token_path, credentials):
        token_path.write_text(credentials.to_json(), encoding="utf-8")

    def authenticate(self, interactive=False):
        Request, Credentials, InstalledAppFlow, build, _ = self._google_modules()
        config = self.load_config()
        credentials_path = self.resolve_path(config.get("credentials_file", "credentials.json"))
        token_path = self.resolve_path(config.get("token_file", "token.json"))
        scopes = config.get("scopes") or ["https://www.googleapis.com/auth/drive"]
        credentials = None

        if token_path.exists():
            try:
                credentials = Credentials.from_authorized_user_file(str(token_path), scopes)
            except (OSError, ValueError):
                credentials = None

        if credentials and credentials.valid:
            return build("drive", "v3", credentials=credentials, cache_discovery=False)

        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                self._save_token(token_path, credentials)
                return build("drive", "v3", credentials=credentials, cache_discovery=False)
            except Exception:
                credentials = None

        if not interactive:
            raise DriveAuthRequired("Google Drive authorization is required.")
        if not credentials_path.exists():
            raise DriveConfigError(f"Google credentials file was not found: {credentials_path.name}")

        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), scopes)
        credentials = flow.run_local_server(
            port=0,
            open_browser=True,
            access_type="offline",
            prompt="consent",
        )
        token_path.parent.mkdir(parents=True, exist_ok=True)
        self._save_token(token_path, credentials)
        return build("drive", "v3", credentials=credentials, cache_discovery=False)

    def get_folder_info(self, service):
        config = self.load_config()
        folder_id = self.extract_folder_id(config["folder_url"])
        result = service.files().get(
            fileId=folder_id,
            supportsAllDrives=True,
            fields="id,name,mimeType,driveId,webViewLink",
        ).execute()
        if result.get("mimeType") != "application/vnd.google-apps.folder":
            raise DriveConfigError("The configured Google Drive ID is not a folder.")
        return result

    def _list_children(self, service, parent_id, name, drive_id=None):
        escaped_name = name.replace("'", "\\'")
        params = {
            "q": (
                f"'{parent_id}' in parents and "
                f"name = '{escaped_name}' and "
                "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            ),
            "spaces": "drive",
            "pageSize": 10,
            "fields": "files(id,name,mimeType,webViewLink,driveId)",
            "supportsAllDrives": True,
            "includeItemsFromAllDrives": True,
        }
        if drive_id:
            params["corpora"] = "drive"
            params["driveId"] = drive_id
        else:
            params["corpora"] = "user"
        return service.files().list(**params).execute().get("files", [])

    def get_or_create_post_folder(self, service, parent_id, title, drive_id=None):
        matches = self._list_children(service, parent_id, title, drive_id)
        if matches:
            return matches[0]
        return service.files().create(
            body={
                "name": title,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            },
            supportsAllDrives=True,
            fields="id,name,mimeType,webViewLink,driveId",
        ).execute()

    def upload_file(self, service, folder_id, local_path, progress_callback=None):
        _, _, _, _, MediaFileUpload = self._google_modules()
        path = Path(local_path)
        if not path.is_file():
            raise FileNotFoundError(f"Local media file is missing: {path.name}")

        mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        media = MediaFileUpload(str(path), mimetype=mime_type, resumable=True)
        upload_request = service.files().create(
            body={"name": path.name, "parents": [folder_id]},
            media_body=media,
            supportsAllDrives=True,
            fields="id,name,mimeType,webViewLink",
        )

        response = None
        while response is None:
            status, response = upload_request.next_chunk()
            if status and progress_callback:
                progress_callback(int(status.progress() * 100))
        if progress_callback:
            progress_callback(100)
        return response

    def update_file(self, service, file_id, local_path, progress_callback=None):
        _, _, _, _, MediaFileUpload = self._google_modules()
        path = Path(local_path)
        if not path.is_file():
            raise FileNotFoundError(f"Local file is missing: {path.name}")

        mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        media = MediaFileUpload(str(path), mimetype=mime_type, resumable=True)
        update_request = service.files().update(
            fileId=file_id,
            media_body=media,
            supportsAllDrives=True,
            fields="id,name,mimeType,webViewLink",
        )

        response = None
        while response is None:
            status, response = update_request.next_chunk()
            if status and progress_callback:
                progress_callback(int(status.progress() * 100))
        if progress_callback:
            progress_callback(100)
        return response

    def file_exists(self, service, file_id):
        try:
            result = service.files().get(
                fileId=file_id,
                supportsAllDrives=True,
                fields="id,trashed",
            ).execute()
        except Exception as error:
            if getattr(getattr(error, "resp", None), "status", None) == 404:
                return False
            raise
        return not result.get("trashed", False)

    def delete_file(self, service, file_id):
        service.files().delete(fileId=file_id, supportsAllDrives=True).execute()

    def status(self):
        try:
            service = self.authenticate(interactive=False)
            folder = self.get_folder_info(service)
            return {
                "status": "connected",
                "message": f"Google Drive ready: {folder['name']}",
                "folder_name": folder["name"],
            }
        except DriveAuthRequired as error:
            return {"status": "auth_required", "message": str(error)}
        except DriveConfigError as error:
            return {"status": "error", "message": str(error)}
        except Exception:
            return {
                "status": "error",
                "message": "Google Drive could not be reached. Check the account and folder access.",
            }
