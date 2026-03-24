"""I/O and parsing mixin for AI service."""

import base64
import json
import re
from io import BytesIO
from typing import Any, Dict, Tuple

import requests

from ai_image_stack import PILLOW_AVAILABLE, Image, ImageOps


class AIServiceIOMixin:

    def _is_data_url(self, value: str) -> bool:
        return isinstance(value, str) and value.startswith("data:image/")

    def _decode_data_url(self, data_url: str) -> Tuple[bytes, str]:
        match = re.match(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.*)$", data_url, re.DOTALL)
        if not match:
            raise ValueError("Invalid data URL format. Expected data:image/<type>;base64,<data>")

        mime_type = match.group(1).lower()
        encoded = match.group(2).strip()

        # Some clients may remove padding; add it back safely.
        padding = len(encoded) % 4
        if padding:
            encoded += "=" * (4 - padding)

        try:
            image_bytes = base64.b64decode(encoded, validate=True)
        except Exception as exc:
            raise ValueError(f"Invalid base64 image payload: {exc}") from exc

        return image_bytes, mime_type

    def _download_image(self, image_url: str) -> Tuple[bytes, str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "image/*,*/*;q=0.8",
        }
        response = requests.get(image_url, timeout=20, stream=True, headers=headers)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type and not content_type.startswith("image/"):
            raise ValueError(f"URL does not point to an image. content-type={content_type}")

        image_bytes = response.content
        if not image_bytes:
            raise ValueError("Downloaded image is empty")

        if not content_type:
            content_type = "image/jpeg"

        return image_bytes, content_type

    def _decode_image_input(self, image_input: str) -> Tuple[bytes, str]:
        if not image_input or not isinstance(image_input, str):
            raise ValueError("image input must be a non-empty string")

        image_input = image_input.strip()

        if self._is_data_url(image_input):
            image_bytes, mime_type = self._decode_data_url(image_input)
        elif image_input.startswith("http://") or image_input.startswith("https://"):
            image_bytes, mime_type = self._download_image(image_input)
        else:
            # Raw base64 fallback.
            try:
                encoded = image_input
                padding = len(encoded) % 4
                if padding:
                    encoded += "=" * (4 - padding)
                image_bytes = base64.b64decode(encoded, validate=True)
                mime_type = "image/jpeg"
            except Exception as exc:
                raise ValueError(
                    "Unsupported image input format. Provide an image URL or data URL."
                ) from exc

        if len(image_bytes) > self.max_image_bytes:
            raise ValueError(
                f"Image too large ({len(image_bytes)} bytes). Max allowed is {self.max_image_bytes} bytes."
            )

        return image_bytes, mime_type

    def _preprocess_image(self, image_bytes: bytes, mime_type: str) -> Tuple[bytes, str]:
        if not PILLOW_AVAILABLE:
            return image_bytes, mime_type

        try:
            image = Image.open(BytesIO(image_bytes))
            image = ImageOps.exif_transpose(image)

            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            elif image.mode == "L":
                image = image.convert("RGB")

            max_dim = 1280
            width, height = image.size
            if max(width, height) > max_dim:
                scale = max_dim / float(max(width, height))
                new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            output = BytesIO()
            image.save(output, format="JPEG", quality=88, optimize=True)
            return output.getvalue(), "image/jpeg"
        except Exception as exc:
            print(f"⚠️ Image preprocessing skipped due to error: {exc}")
            return image_bytes, mime_type

    def _to_data_url(self, image_bytes: bytes, mime_type: str) -> str:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    def _extract_json_block(self, text: str) -> Dict[str, Any]:
        if not text:
            raise ValueError("Empty model response")

        cleaned = text.strip().replace("```json", "").replace("```", "").strip()

        # Direct JSON object string.
        if cleaned.startswith("{") and cleaned.endswith("}"):
            return json.loads(cleaned)

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in model response")

        json_text = cleaned[start : end + 1]
        return json.loads(json_text)



