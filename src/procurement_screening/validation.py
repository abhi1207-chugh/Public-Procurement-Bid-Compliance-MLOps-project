"""Upload validation: type, size, content signature, and filename/path safety.

Uploaded files are untrusted input. Nothing here trusts the client-supplied filename,
content type, or extension alone.
"""
import io
import re
import zipfile
from pathlib import Path

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf": "pdf", ".docx": "docx"}

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


class UploadError(ValueError):
    """Raised when an upload fails validation."""


def sanitize_filename(filename: str) -> str:
    """Return a safe basename: no directories, no odd characters, no leading dots."""
    if not filename or "\x00" in filename:
        raise UploadError("invalid filename")
    name = filename.replace("\\", "/").split("/")[-1]
    name = _SAFE_NAME.sub("_", name).lstrip(".")
    stem, dot, ext = name.rpartition(".")
    if not dot or not stem:
        raise UploadError("filename must have a name and an extension")
    return f"{stem[:100]}.{ext.lower()}"


def detect_kind(filename: str, data: bytes) -> str:
    """Validate and return the document kind ('pdf' or 'docx').

    Checks extension allowlist, size, and that magic bytes match the extension.
    """
    ext = Path(sanitize_filename(filename)).suffix.lower()
    kind = ALLOWED_EXTENSIONS.get(ext)
    if kind is None:
        raise UploadError(f"unsupported file type {ext!r}; allowed: pdf, docx")
    if not data:
        raise UploadError("empty file")
    if len(data) > MAX_UPLOAD_BYTES:
        raise UploadError(f"file too large (limit {MAX_UPLOAD_BYTES} bytes)")
    if kind == "pdf":
        if not data.startswith(b"%PDF-"):
            raise UploadError("content is not a PDF")
    else:
        _check_docx(data)
    return kind


def _check_docx(data: bytes) -> None:
    if not data.startswith(b"PK\x03\x04"):
        raise UploadError("content is not a DOCX")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
            if "word/document.xml" not in names:
                raise UploadError("content is not a DOCX")
            if sum(i.file_size for i in zf.infolist()) > MAX_DOCX_UNCOMPRESSED_BYTES:
                raise UploadError("DOCX expands too large (possible zip bomb)")
    except zipfile.BadZipFile as e:
        raise UploadError("corrupt DOCX") from e


def safe_upload_path(upload_dir: Path, filename: str) -> Path:
    """Resolve a destination inside upload_dir; refuse anything that escapes it."""
    base = upload_dir.resolve()
    dest = (base / sanitize_filename(filename)).resolve()
    if dest.parent != base:
        raise UploadError("path escapes upload directory")
    return dest
