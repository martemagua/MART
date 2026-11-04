"""multipart/form-data (file uploads) on the standard library.

Python 3.13 removed the old `cgi` module, so this uses the e-mail parser,
which reads the same MIME format.
"""

from __future__ import annotations

from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import HTTP


@dataclass
class UploadedFile:
    field: str
    filename: str
    content_type: str
    data: bytes


def parse(body: bytes, content_type: str) -> tuple[dict[str, list[str]], dict[str, list[UploadedFile]]]:
    """(form fields, files) of a multipart/form-data body."""
    header = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("latin-1")
    message = BytesParser(policy=HTTP).parsebytes(header + body)
    fields: dict[str, list[str]] = {}
    files: dict[str, list[UploadedFile]] = {}
    if not message.is_multipart():
        return fields, files
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        payload = part.get_payload(decode=True) or b""
        filename = part.get_filename()
        if filename is not None:
            if filename or payload:
                files.setdefault(name, []).append(
                    UploadedFile(name, filename, part.get_content_type(), payload))
        else:
            charset = part.get_content_charset() or "utf-8"
            fields.setdefault(name, []).append(payload.decode(charset, errors="replace"))
    return fields, files
