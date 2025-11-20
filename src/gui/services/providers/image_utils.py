"""
Utility helpers shared by image-capable providers.
"""

import base64
import os
from typing import List, Dict, Any, Callable


def build_image_message(prompt: str | None, image_path: str, default_prompt: Callable[[], str]) -> List[Dict[str, Any]]:
    """Encode an image and build a Chat Completions message payload."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lower()
    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")

    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt or default_prompt()},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
            ],
        }
    ]
