# Content Manager

A local-first content library for preparing, tracking, and publishing Instagram posts. Store media, captions, songs, post status, Instagram URLs, and per-post metadata while keeping Google Drive synchronized in the background.

## Features

- Create posts with one or multiple images or videos.
- Generate collision-safe numbered titles such as `1_Ganpati_Photo`.
- Store all post metadata in a per-post `post.json` file.
- Update `post.json` whenever a post is edited or marked as posted.
- Sync media and `post.json` into the same Google Drive post folder.
- Update the existing Drive JSON file during edits instead of creating duplicates.
- Reconcile missing or trashed Drive files automatically.
- Search, sort, and filter the library by title, description, song, date, and posted status.
- Resolve YouTube titles with `yt-dlp` and show compact clickable link capsules.
- Copy images, download videos, mark posts as published, and delete local/Drive content.
- Responsive dark interface built with Flask, Tailwind CSS, and vanilla JavaScript.

## Requirements

- Python 3.10 or newer.
- Node.js and npm only if the Tailwind stylesheet needs to be rebuilt.
- Google Drive credentials only if Drive synchronization is required.

Python packages are listed in `requirements.txt`. Frontend build tooling is listed in `package.json`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Configuration

### Local-only mode

No configuration is needed for local post management. The application creates `database.db` and `uploads/` automatically.

### Google Drive mode

1. Create or select a Google Cloud project.
2. Enable the Google Drive API.
3. Create an OAuth desktop application and download its client JSON.
4. Copy `credentials.example.json` to `credentials.json` only if you need a reference shape, then replace it with the real downloaded credentials file.
5. Copy `drive_config.example.json` to `drive_config.json`.
6. Set `folder_url` to the target Google Drive folder URL.
7. Run the application and select **Authenticate** in the Drive status bar.

The real files `credentials.json`, `drive_config.json`, and `token.json` are intentionally ignored by Git. Never commit OAuth credentials, access tokens, or private Drive folder URLs. The example files contain placeholders only.

## Running

The application uses port `9999` and does not use port `5000`.

For normal development:

```bash
python app.py
```

For a managed local process with health checks and logging:

```bash
./start_app.sh
```

Restart the managed process with:

```bash
./start_app.sh --restart
```

Open `http://127.0.0.1:9999` in a browser.

## Data Storage

SQLite remains the application database for fast queries and Drive sync state. Each post also has a JSON metadata file beside its media:

```text
uploads/
  1_Ganpati_Photo/
    1_Ganpati_Photo.jpg
    second-image.png
    post.json
```

`post.json` contains the post ID, generated title, description, song, media filename/type, posted state, Instagram URL, creation time, and the complete media list. Its timestamps use `Asia/Kolkata` (`GMT+05:30`, IST).

The JSON file is written atomically. Existing posts receive or refresh their JSON file when the application starts. Editing or marking a post as posted rewrites the file with the latest values.

## Google Drive Synchronization

Synchronization is local-first:

1. The uploaded media is saved under `uploads/<post-folder>/`.
2. The post and media records are committed to SQLite.
3. `post.json` is written beside the media.
4. A background worker uploads the media and `post.json` to the same Drive post folder.
5. Drive file IDs and sync status are tracked locally so retries do not create duplicates.

If a Drive media file or JSON file is missing or trashed, reconciliation queues it for upload again. If a post is edited, the existing Drive `post.json` file is updated in place. Drive deletion is queued and retried when authorization or connectivity is temporarily unavailable.

## Using the Application

- **Add Post:** Select one or more supported media files, enter metadata, and save.
- **Library:** Search, sort A-Z/Z-A, filter by date, or show only unposted content.
- **Post Detail:** Review all media, metadata, Drive state, and the Instagram URL.
- **Mark as Posted:** Confirm publication and provide a valid Instagram URL.
- **Edit:** Update title text, description, song, posted state, or Instagram URL. The numeric sequence remains attached to the post and media is not re-uploaded unnecessarily.
- **Links:** URLs remain clickable. YouTube URLs can display a fetched title while preserving the original fallback URL.
- **Copy/Download:** Copy images through the browser Clipboard API or download media files.
- **Delete:** Remove local post data and queue matching Drive files/folders for deletion.

Press `N` in the library to open the Add Post form.

## Supported Media

Images: `jpg`, `jpeg`, `png`, `webp`, `gif`

Videos: `mp4`, `mov`, `webm`, `mkv`

The maximum request size is 512 MB.

## Rebuilding CSS

The compiled stylesheet is committed, so Node.js is not required to run the application. To modify the design:

```bash
npm install
npm run build:css
```

Use `npm run watch:css` during active styling work.

## Project Structure

```text
app.py                       Flask routes, validation, SQLite, JSON, and sync jobs
drive_sync.py                Google Drive authentication and file operations
requirements.txt             Python dependencies
package.json                 Tailwind build scripts
tailwind.config.js           Tailwind content, tokens, and dynamic class safelist
drive_config.example.json    Safe Google Drive configuration template
credentials.example.json     Safe OAuth client JSON shape with placeholders
start_app.sh                 Managed launcher for http://127.0.0.1:9999
database.db                  Local SQLite state, created at runtime
uploads/<post-folder>/       Local media and per-post post.json, created at runtime
templates/                   Jinja templates
static/css/                  Tailwind source and compiled stylesheet
static/js/                   Vanilla JavaScript interactions
```

## Validation

```bash
python -m py_compile app.py drive_sync.py
node --check static/js/app.js
npm run build:css
```

## Security Notes

- Database queries use parameters.
- Filenames are sanitized with `secure_filename`.
- Media paths are confined to the `uploads/` directory.
- OAuth credentials, tokens, local databases, logs, and uploads are excluded from Git.
- Debug mode is enabled by `python app.py` for local development; disable it before exposing the application beyond localhost.
