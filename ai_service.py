#!/usr/bin/env python3
"""
AI Service for waste analysis.

Public API is preserved:
- class AIService
- global instance ai_service
"""

import os

from groq import Groq

from ai_io_mixin import AIServiceIOMixin
from ai_analysis_mixin import AIServiceAnalysisMixin
from ai_validation_mixin import AIServiceValidationMixin


class AIService(AIServiceIOMixin, AIServiceAnalysisMixin, AIServiceValidationMixin):
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.groq_vision_model = os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview")

        # Cost control flags.
        self.free_only_mode = os.getenv("AI_FREE_ONLY_MODE", "true").lower() == "true"
        self.allow_groq_fallback = os.getenv("ALLOW_GROQ_FALLBACK", "false").lower() == "true"

        use_vision_env = os.getenv("USE_FREE_VISION", "true").lower()
        self.use_free_vision = use_vision_env == "true"
        self.hf_token = (os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN") or "").strip()
        self.hf_router_url = os.getenv("HF_ROUTER_URL", "https://router.huggingface.co/v1/chat/completions")
        self.hf_vision_model = os.getenv("HF_VISION_MODEL", "zai-org/GLM-4.5V:cheapest")
        self.ai_http_timeout = int(os.getenv("AI_HTTP_TIMEOUT", "20"))

        self.max_image_bytes = int(os.getenv("MAX_IMAGE_BYTES", str(8 * 1024 * 1024)))

        if self.groq_api_key:
            self.groq_client = Groq(api_key=self.groq_api_key)
        else:
            self.groq_client = None

        if not self.hf_token and not self.groq_client:
            raise ValueError("No AI provider key found. Set HUGGINGFACE_API_KEY or GROQ_API_KEY.")

        print("ðŸ”§ AI Service configuration:")
        print(f"   AI_FREE_ONLY_MODE: {self.free_only_mode}")
        print(f"   ALLOW_GROQ_FALLBACK: {self.allow_groq_fallback}")
        print(f"   HF vision model: {self.hf_vision_model}")
        print(f"   Groq text model: {self.groq_model}")
        print(f"   Groq vision model: {self.groq_vision_model}")
        print(f"   Groq key present: {bool(self.groq_client)}")
        print(f"   USE_FREE_VISION: {self.use_free_vision}")
        print(f"   HF token present: {bool(self.hf_token and self.hf_token != 'your_hf_token_here')}")
        print(f"   AI HTTP timeout (s): {self.ai_http_timeout}")
        print(f"   MAX_IMAGE_BYTES: {self.max_image_bytes}")

# Global AI service instance
ai_service = AIService()

