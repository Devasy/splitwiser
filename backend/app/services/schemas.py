from typing import Dict, Optional

from pydantic import BaseModel


class ImageUploadResponse(BaseModel):
    success: bool
    urls: Dict[str, str]  # {"thumbnail": "url", "medium": "url", "full": "url"}
    message: str
    processing_id: Optional[str] = None
