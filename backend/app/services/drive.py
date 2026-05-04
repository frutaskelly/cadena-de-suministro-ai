"""Google Drive uploader (port simplificado del v1 drive_uploader.py).

Sube archivos a una carpeta Drive usando OAuth user credentials. Para
cuentas @gmail personales, los service accounts no funcionan; el OAuth
del usuario se persiste en `secrets/google-drive-token.json`.

Setup (una sola vez):
    cd backend && source venv/bin/activate
    python -m app.services.drive setup

Uso desde codigo:
    from app.services.drive import upload_file
    result = upload_file(Path("foo.pdf"), subfolder="2026-05-04")
    # result = {"id": "...", "name": "...", "link": "https://drive.google.com/..."}
"""
from __future__ import annotations

import logging
import mimetypes
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.config import settings

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

_service = None
_init_attempted = False
_folder_cache: dict[tuple[str, str], str] = {}


def _credentials_path() -> Optional[Path]:
    if not settings.GOOGLE_OAUTH_CREDENTIALS:
        return None
    p = Path(settings.GOOGLE_OAUTH_CREDENTIALS)
    if not p.is_absolute():
        p = Path(__file__).resolve().parents[2] / p
    return p


def _token_path() -> Optional[Path]:
    if not settings.GOOGLE_OAUTH_TOKEN:
        return None
    p = Path(settings.GOOGLE_OAUTH_TOKEN)
    if not p.is_absolute():
        p = Path(__file__).resolve().parents[2] / p
    return p


def _load_credentials():
    """Carga credenciales OAuth del token guardado; refresca si expiro."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    tp = _token_path()
    if not tp or not tp.exists():
        log.warning(
            f"Drive: token OAuth no existe en {tp}. "
            f"Corre `python -m app.services.drive setup` para autorizar."
        )
        return None

    creds = Credentials.from_authorized_user_file(str(tp), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            log.info("Drive: token refrescado")
            try:
                tp.write_text(creds.to_json(), encoding="utf-8")
            except OSError:
                pass
        except Exception as e:
            log.exception(f"Drive: error refrescando token: {e}")
            return None
    return creds if creds and creds.valid else None


def _get_service(force_new: bool = False):
    """Lazy init del cliente Drive. Devuelve None si Drive no configurado."""
    global _service, _init_attempted
    if _service is not None and not force_new:
        return _service
    if _init_attempted and not force_new:
        return None
    _init_attempted = True

    if not settings.GOOGLE_DRIVE_FOLDER_ID:
        log.info("Drive: GOOGLE_DRIVE_FOLDER_ID no configurado")
        return None

    creds = _load_credentials()
    if not creds:
        return None

    try:
        from googleapiclient.discovery import build
        _service = build("drive", "v3", credentials=creds, cache_discovery=False)
        log.info("Drive: cliente inicializado")
        return _service
    except Exception as e:
        log.exception(f"Drive: error inicializando: {e}")
        return None


def _get_or_create_folder(name: str, parent_id: str, service) -> str:
    """Busca/crea subcarpeta. Cachea resultado."""
    cache_key = (parent_id, name)
    if cache_key in _folder_cache:
        return _folder_cache[cache_key]

    safe = name.replace("'", "\\'")
    query = (
        f"name = '{safe}' "
        f"and mimeType = 'application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed = false"
    )
    try:
        results = (
            service.files()
            .list(q=query, fields="files(id,name)", pageSize=5)
            .execute()
        )
        files = results.get("files", [])
        if files:
            folder_id = files[0]["id"]
            _folder_cache[cache_key] = folder_id
            return folder_id

        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        f = service.files().create(body=metadata, fields="id,name").execute()
        _folder_cache[cache_key] = f["id"]
        log.info(f"Drive: subcarpeta creada '{name}' (id={f['id']})")
        return f["id"]
    except Exception as e:
        log.exception(f"Drive: error con subcarpeta '{name}': {e}")
        return parent_id


def _build_drive_name(original_name: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    p = Path(original_name)
    return f"{ts}_{p.stem}{p.suffix}"


_TRANSIENT_ERRS = {
    "SSLEOFError", "SSLError", "ConnectionError", "ConnectionResetError",
    "ReadTimeoutError", "ConnectTimeoutError", "ServerDisconnectedError",
    "TimeoutError", "ChunkedEncodingError",
}


def _is_transient(e: Exception) -> bool:
    if type(e).__name__ in _TRANSIENT_ERRS:
        return True
    m = str(e).lower()
    return any(
        t in m
        for t in [
            "ssl", "connection reset", "connection aborted", "timed out",
            "eof occurred", "remote end closed", "broken pipe",
        ]
    )


def upload_file(
    local_path: Path,
    original_name: Optional[str] = None,
    subfolder: Optional[str] = None,
    max_retries: int = 4,
) -> Optional[dict]:
    """Sube archivo a Drive (con subcarpeta opcional por dia).

    Returns: {"id", "name", "link"} or None si Drive no configurado / falla.
    """
    service = _get_service()
    if not service:
        return None

    base_name = original_name or local_path.name
    drive_name = _build_drive_name(base_name)
    size_bytes = local_path.stat().st_size if local_path.exists() else 0
    use_resumable = size_bytes >= 5 * 1024 * 1024

    parent_id = settings.GOOGLE_DRIVE_FOLDER_ID
    if subfolder:
        parent_id = _get_or_create_folder(subfolder, parent_id, service)

    log.info(
        f"Drive: subiendo {drive_name} ({size_bytes//1024} KB) -> "
        f"{subfolder or 'root'}"
    )

    last_error = None
    for attempt in range(max_retries):
        try:
            from googleapiclient.http import MediaFileUpload
            mime_type, _ = mimetypes.guess_type(str(local_path))
            media = MediaFileUpload(
                str(local_path),
                mimetype=mime_type or "application/octet-stream",
                resumable=use_resumable,
            )
            metadata = {"name": drive_name, "parents": [parent_id]}
            f = (
                service.files()
                .create(
                    body=metadata,
                    media_body=media,
                    fields="id,name,webViewLink",
                )
                .execute()
            )
            log.info(f"Drive OK: {f['name']} -> {f.get('webViewLink')}")
            return {
                "id": f["id"],
                "name": f["name"],
                "link": f.get("webViewLink"),
            }
        except Exception as e:
            last_error = e
            msg = str(e)
            # 404 subcarpeta borrada: invalida cache y reintenta
            if subfolder and ("File not found" in msg or "404" in msg):
                _folder_cache.pop(
                    (settings.GOOGLE_DRIVE_FOLDER_ID, subfolder), None
                )
                parent_id = _get_or_create_folder(
                    subfolder, settings.GOOGLE_DRIVE_FOLDER_ID, service
                )
                continue
            if _is_transient(e):
                wait = 2 ** attempt
                log.warning(f"Drive: error transitorio, retry en {wait}s: {e}")
                time.sleep(wait)
                continue
            log.exception(f"Drive: upload fallido: {e}")
            break

    log.error(f"Drive: todos los retries fallaron: {last_error}")
    return None


# ─── CLI: setup interactivo ────────────────────────────────────────────────
def _setup_oauth():
    """Abre el browser para autorizar; guarda token a disco."""
    cp = _credentials_path()
    tp = _token_path()
    if not cp or not cp.exists():
        print(f"ERROR: credenciales OAuth no encontradas en {cp}")
        print(
            "Descarga el JSON de Google Cloud Console (Desktop app) y "
            "ponlo en backend/secrets/google-oauth-credentials.json"
        )
        sys.exit(1)

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(cp), SCOPES)
    creds = flow.run_local_server(port=0)
    tp.parent.mkdir(parents=True, exist_ok=True)
    tp.write_text(creds.to_json(), encoding="utf-8")
    print(f"OK: token guardado en {tp}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        _setup_oauth()
    else:
        print("Uso: python -m app.services.drive setup")
