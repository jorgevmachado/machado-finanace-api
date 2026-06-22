import re
import unicodedata
import uuid
from typing import Any

from pydantic import BaseModel


def is_valid_uuid(value: str | None = None) -> bool:
    if not value:
        return False
    try:
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj) == value
    except (ValueError, AttributeError, TypeError):
        return False


def _normalize_entry(entry: Any) -> dict:
    if isinstance(entry, BaseModel):
        return entry.model_dump()
    if isinstance(entry, dict):
        return entry
    return dict(entry)


def text_strip(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def to_snake_case(text: str) -> str:
    text = text_strip(text)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text
