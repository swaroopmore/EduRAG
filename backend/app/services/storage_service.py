"""Upload validation and file storage.

* extension allow-list (``ALLOWED_FILE_TYPES``)
* declared MIME type must be plausible for the extension
* size limit enforced while streaming (never buffers more than the limit)
* magic-byte / structure checks (a renamed .exe is rejected)
* files are stored under generated names - the client filename is only kept as
  display metadata, so path traversal through the name is impossible
"""

from __future__ import annotations

import os
import re
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import FileTooLargeError, UnsupportedFileError
from app.core.logging import get_logger
from app.models.document import Document

logger = get_logger("storage")

_GENERIC_MIME = {"", "application/octet-stream", "binary/octet-stream"}
_ALLOWED_MIME: dict[str, set[str]] = {
    "pdf": {"application/pdf", "application/x-pdf", "application/acrobat", "text/pdf"},
    "txt": {"text/plain", "text/markdown", "text/x-markdown"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/x-zip-compressed",
    },
    "pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
        "application/x-zip-compressed",
    },
}
_ZIP_REQUIRED_MEMBER = {"docx": "word/document.xml", "pptx": "ppt/presentation.xml"}
_MAX_UNCOMPRESSED_BYTES = 300 * 1024 * 1024
_CHUNK = 1024 * 1024


@dataclass
class StoredFile:
    filename: str           # generated, unique
    path: str               # absolute path on disk
    size: int
    file_type: str          # normalised extension without dot
    original_filename: str  # sanitised display name


def sanitize_filename(name: str | None, fallback_ext: str = "") -> str:
    """Return a safe display name (no directories, control chars or overlong names)."""
    name = (name or "").replace("\\", "/").split("/")[-1]
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip().strip(".")
    if not name:
        name = f"document.{fallback_ext}" if fallback_ext else "document"
    if len(name) > 200:
        stem, ext = os.path.splitext(name)
        name = stem[: 200 - len(ext)] + ext
    return name


class StorageService:
    def __init__(self, upload_dir: str | None = None):
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIR)

    # ------------------------------------------------------------------ save
    async def save_upload(self, file: UploadFile) -> StoredFile:
        original = sanitize_filename(file.filename)
        extension = os.path.splitext(original)[1].lower().lstrip(".")

        if extension not in settings.allowed_file_types:
            allowed = ", ".join(sorted(t.upper() for t in settings.allowed_file_types))
            raise UnsupportedFileError(f"Unsupported file type. Please upload one of: {allowed}.")

        declared = (file.content_type or "").split(";")[0].strip().lower()
        if declared not in _GENERIC_MIME and declared not in _ALLOWED_MIME.get(extension, set()):
            raise UnsupportedFileError("The file's content type doesn't match its extension.")

        self.upload_dir.mkdir(parents=True, exist_ok=True)
        generated = f"{uuid.uuid4().hex}.{extension}"
        final_path = self._safe_path(generated)
        temp_path = final_path.with_suffix(final_path.suffix + ".part")

        size = 0
        try:
            async with aiofiles.open(temp_path, "wb") as out:
                while True:
                    chunk = await file.read(_CHUNK)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > settings.max_upload_bytes:
                        raise FileTooLargeError(
                            f"That file is larger than the {settings.MAX_UPLOAD_MB} MB limit."
                        )
                    await out.write(chunk)

            if size == 0:
                raise UnsupportedFileError("That file is empty.")
            self._validate_content(temp_path, extension)
            os.replace(temp_path, final_path)
        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise

        return StoredFile(
            filename=generated,
            path=str(final_path),
            size=size,
            file_type=extension,
            original_filename=original,
        )

    # --------------------------------------------------------------- lookups
    def _safe_path(self, filename: str) -> Path:
        base = self.upload_dir.resolve()
        candidate = (base / os.path.basename(filename)).resolve()
        if base != candidate.parent:
            raise UnsupportedFileError("Invalid file name.")
        return candidate

    def resolve(self, document: Document) -> Path | None:
        """Locate a stored file (robust to UPLOAD_DIR changes between deploys)."""
        try:
            candidate = self._safe_path(document.filename)
            if candidate.is_file():
                return candidate
        except UnsupportedFileError:
            pass
        legacy = Path(document.file_path)  # older rows stored a CWD-relative path
        if legacy.is_file() and legacy.name == os.path.basename(document.filename):
            return legacy.resolve()
        return None

    def delete(self, document: Document) -> None:
        path = self.resolve(document)
        if path:
            try:
                path.unlink()
            except OSError as exc:
                logger.warning("could not delete file for document %s: %s", str(document.id)[:8], exc)

    # ------------------------------------------------------------ validation
    @staticmethod
    def _validate_content(path: Path, extension: str) -> None:
        with open(path, "rb") as handle:
            head = handle.read(8192)

        if extension == "pdf":
            if b"%PDF-" not in head[:1024]:
                raise UnsupportedFileError("This file doesn't look like a valid PDF.")
        elif extension == "txt":
            if b"\x00" in head and not head.startswith((b"\xff\xfe", b"\xfe\xff")):
                raise UnsupportedFileError("This file doesn't look like a plain-text file.")
        elif extension in _ZIP_REQUIRED_MEMBER:
            if not zipfile.is_zipfile(path):
                raise UnsupportedFileError(f"This file doesn't look like a valid {extension.upper()} document.")
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
                if _ZIP_REQUIRED_MEMBER[extension] not in names:
                    raise UnsupportedFileError(f"This file doesn't look like a valid {extension.upper()} document.")
                if sum(i.file_size for i in archive.infolist()) > _MAX_UNCOMPRESSED_BYTES:
                    raise UnsupportedFileError("This document is too large once unpacked.")
