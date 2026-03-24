"""Vision and analysis mixin for AI service."""

from typing import Any, Dict, List, Optional

import requests


class AIServiceAnalysisMixin:

    def _analyze_image_with_hf_router_vlm(self, image_input: str) -> Optional[Dict[str, Any]]:
        """
        Analyze image using Hugging Face Inference Providers chat-completions router
        with an image-text-to-text model.
        """
        if not self.hf_token:
            return None

        try:
            image_bytes, mime_type = self._decode_image_input(image_input)
            image_bytes, mime_type = self._preprocess_image(image_bytes, mime_type)
            data_url = self._to_data_url(image_bytes, mime_type)

            payload = {
                "model": self.hf_vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self._vision_analysis_prompt()},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
                "max_tokens": 1400,
            }

            response = requests.post(
                self.hf_router_url,
                headers={
                    "Authorization": f"Bearer {self.hf_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )

            if response.status_code != 200:
                print(f"âš ï¸ HF router VLM failed: {response.status_code} {response.text[:240]}")
                return None

            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                return None

            content = choices[0].get("message", {}).get("content", "")
            try:
                parsed = self._extract_json_block(content)
                return self._validate_analysis_response(parsed)
            except Exception:
                # Some providers return plain text despite JSON instructions.
                print("âš ï¸ HF router returned non-JSON content, falling back to text inference")
                print(f"ðŸ“ HF content preview: {str(content)[:240]}")
                return self._infer_from_caption(str(content))
        except Exception as exc:
            print(f"âŒ HF router vision analysis failed: {exc}")
            return None

    def _vision_analysis_prompt(self) -> str:
        return (
            "Analyze this waste scene image with high precision.\n"
            "Rules:\n"
            "- Only report what is visually supported by the image.\n"
            "- Do not assume plastic unless clearly visible.\n"
            "- If scene is mostly dust/soil/sand/fine debris, classify it accordingly.\n"
            "- If confidence is low, explicitly reduce confidence and use Unknown/Other in composition.\n\n"
            "Return ONLY valid JSON with this exact shape:\n"
            "{\n"
            '  "description": "2-3 sentence visual summary",\n'
            '  "severity": "LOW|MEDIUM|HIGH|CRITICAL",\n'
            '  "estimatedVolume": "human-readable estimate",\n'
            '  "environmentalImpact": "LOW|MODERATE|HIGH|SEVERE",\n'
            '  "healthHazard": true,\n'
            '  "hazardDetails": "details or empty string",\n'
            '  "recommendedAction": "specific action plan",\n'
            '  "estimatedCleanupTime": "time + crew estimate",\n'
            '  "confidence": 0,\n'
            '  "wasteComposition": [{"type":"...","percentage":0,"recyclable":false}],\n'
            '  "specialEquipmentNeeded": ["..."]\n'
            "}"
        )

    def _analyze_image_with_groq_vision(self, image_input: str) -> Optional[Dict[str, Any]]:
        if not self.groq_client:
            return None

        try:
            image_bytes, mime_type = self._decode_image_input(image_input)
            image_bytes, mime_type = self._preprocess_image(image_bytes, mime_type)
            data_url = self._to_data_url(image_bytes, mime_type)

            response = self.groq_client.chat.completions.create(
                model=self.groq_vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self._vision_analysis_prompt()},
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url},
                            },
                        ],
                    }
                ],
                temperature=0.1,
                max_tokens=1400,
            )

            content = response.choices[0].message.content
            if not content:
                return None

            parsed = self._extract_json_block(content)
            return self._validate_analysis_response(parsed)
        except Exception as exc:
            print(f"âŒ Groq vision analysis failed: {exc}")
            return None

    def _analyze_image_with_free_vision(self, image_input: str) -> Optional[Dict[str, Any]]:
        """
        Analyze image via HF router caption prompt, then infer structured waste report.
        This avoids deprecated serverless model endpoints that may return HTTP 410.
        """
        if not self.hf_token:
            return None

        try:
            image_bytes, mime_type = self._decode_image_input(image_input)
            image_bytes, mime_type = self._preprocess_image(image_bytes, mime_type)
            data_url = self._to_data_url(image_bytes, mime_type)

            payload = {
                "model": self.hf_vision_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe only visible materials in this image in one short sentence. Do not guess.",
                            },
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
                "temperature": 0.0,
                "max_tokens": 180,
            }

            response = requests.post(
                self.hf_router_url,
                headers={
                    "Authorization": f"Bearer {self.hf_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )

            if response.status_code != 200:
                print(f"âš ï¸ HF caption fallback failed: {response.status_code} {response.text[:240]}")
                return None

            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                return None

            caption = str(choices[0].get("message", {}).get("content", "")).strip()
            if not caption:
                return None

            return self._infer_from_caption(caption)
        except Exception as exc:
            print(f"âŒ Free vision caption fallback error: {exc}")
            return None

    def _infer_from_caption(self, caption: str) -> Dict[str, Any]:
        prompt = f"""
You are a strict waste-scene analyst.
Given this model-generated caption, build a cautious structured report.

Caption: {caption}

Requirements:
- If caption does not clearly mention plastic objects, do NOT classify primary waste as plastic.
- If caption mentions dust, dirt, soil, sand, powder, particles, ash, or debris, include dust/fine debris composition.
- Keep confidence lower when caption is vague.
- Return JSON only.
"""

        try:
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Return valid JSON only. Be conservative and evidence-based.",
                    },
                    {"role": "user", "content": f"{prompt}\n\n{self._vision_analysis_prompt()}"},
                ],
                temperature=0.2,
                max_tokens=900,
            )

            content = response.choices[0].message.content
            parsed = self._extract_json_block(content)
            return self._validate_analysis_response(parsed)
        except Exception:
            # Deterministic conservative heuristic fallback from caption.
            text = caption.lower()
            has_dust = any(w in text for w in ["dust", "dirt", "soil", "sand", "powder", "particle", "ash"])
            has_plastic = any(
                w in text
                for w in [
                    "plastic bottle",
                    "plastic bag",
                    "bottle",
                    "wrapper",
                    "packaging",
                    "container",
                ]
            )

            if has_dust and not has_plastic:
                data = {
                    "description": f"Fine particulate/dust-like material is visible. Caption: {caption}",
                    "severity": "LOW",
                    "estimatedVolume": "Small to moderate dust/debris accumulation",
                    "environmentalImpact": "LOW",
                    "healthHazard": True,
                    "hazardDetails": "Airborne particles can irritate eyes and respiratory system.",
                    "recommendedAction": "Use dust suppression, masks, and careful collection of fine debris.",
                    "estimatedCleanupTime": "1-2 hours with 2 workers",
                    "confidence": 72,
                    "wasteComposition": [
                        {"type": "Dust/Fine Debris", "percentage": 85, "recyclable": False},
                        {"type": "Unknown/Other", "percentage": 15, "recyclable": False},
                    ],
                    "specialEquipmentNeeded": ["N95 masks", "Brooms", "Vacuum", "Water sprayer"],
                }
            else:
                data = {
                    "description": f"Caption-based analysis only: {caption}",
                    "severity": "MEDIUM",
                    "estimatedVolume": "Moderate visible waste",
                    "environmentalImpact": "MODERATE",
                    "healthHazard": True,
                    "hazardDetails": "Possible mixed-material contamination.",
                    "recommendedAction": "Perform manual verification and sort waste by material type.",
                    "estimatedCleanupTime": "2-3 hours with 2-4 workers",
                    "confidence": 60,
                    "wasteComposition": [
                        {"type": "Unknown/Other", "percentage": 60, "recyclable": False},
                        {"type": "Mixed Waste", "percentage": 40, "recyclable": False},
                    ],
                    "specialEquipmentNeeded": ["Gloves", "Collection bags", "Sorting bins"],
                }

            return self._validate_analysis_response(data)

    def analyze_waste_image(self, image_url: str) -> Dict[str, Any]:
        """
        Analyze waste image using a vision-first pipeline.
        """
        print("ðŸ” AI Analysis request received")

        # Free-tier-first path.
        hf_router_result = self._analyze_image_with_hf_router_vlm(image_url)
        if hf_router_result:
            print("âœ… HF router vision analysis succeeded")
            return hf_router_result

        # Free caption fallback.
        if self.use_free_vision:
            print("âš ï¸ HF router VLM failed, attempting HF caption fallback")
            hf_caption_result = self._analyze_image_with_free_vision(image_url)
            if hf_caption_result:
                print("âœ… HF caption fallback succeeded")
                return hf_caption_result

        # Optional Groq fallback, disabled by default in free-only mode.
        if self.groq_client and (not self.free_only_mode or self.allow_groq_fallback):
            print("âš ï¸ Attempting optional Groq vision fallback")
            groq_result = self._analyze_image_with_groq_vision(image_url)
            if groq_result:
                print("âœ… Groq fallback succeeded")
                return groq_result

        # Final conservative fallback.
        print("âš ï¸ Falling back to conservative low-confidence analysis")
        return self._get_contextual_fallback_analysis(image_url)

    def compare_cleanup_images(
        self, before_image_url: str, after_image_url: str, report_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare before and after images with vision model.
        Falls back to contextual comparison if needed.
        """
        try:
            before_bytes, before_mime = self._decode_image_input(before_image_url)
            after_bytes, after_mime = self._decode_image_input(after_image_url)

            before_bytes, before_mime = self._preprocess_image(before_bytes, before_mime)
            after_bytes, after_mime = self._preprocess_image(after_bytes, after_mime)

            before_data_url = self._to_data_url(before_bytes, before_mime)
            after_data_url = self._to_data_url(after_bytes, after_mime)

            prompt = """
You are evaluating waste cleanup effectiveness from BEFORE and AFTER photos.
Be strict and evidence-based. Return JSON only with this shape:
{
  "completionPercentage": 0,
  "beforeSummary": "...",
  "afterSummary": "...",
  "qualityRating": "POOR|FAIR|GOOD|EXCELLENT",
  "environmentalBenefit": "...",
  "verificationStatus": "VERIFIED|NEEDS_REVIEW|INCOMPLETE",
  "feedback": "...",
  "confidence": 0,
  "wasteRemoved": [{"type": "...", "percentage": 0, "recyclable": false}],
  "remainingIssues": ["..."]
}
"""

            # 1) Free-tier-first comparison via HF router.
            if self.hf_token:
                hf_payload = {
                    "model": self.hf_vision_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "text", "text": "BEFORE IMAGE"},
                                {"type": "image_url", "image_url": {"url": before_data_url}},
                                {"type": "text", "text": "AFTER IMAGE"},
                                {"type": "image_url", "image_url": {"url": after_data_url}},
                            ],
                        }
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1200,
                }

                hf_response = requests.post(
                    self.hf_router_url,
                    headers={
                        "Authorization": f"Bearer {self.hf_token}",
                        "Content-Type": "application/json",
                    },
                    json=hf_payload,
                    timeout=60,
                )

                if hf_response.status_code == 200:
                    hf_data = hf_response.json()
                    choices = hf_data.get("choices") or []
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        parsed = self._extract_json_block(content)
                        return self._validate_comparison_response(parsed)
                else:
                    print(f"âš ï¸ HF router compare failed: {hf_response.status_code} {hf_response.text[:240]}")

            # 2) Optional Groq fallback (disabled by default in free-only mode).
            if self.groq_client and (not self.free_only_mode or self.allow_groq_fallback):
                response = self.groq_client.chat.completions.create(
                    model=self.groq_vision_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "text", "text": "BEFORE IMAGE"},
                                {"type": "image_url", "image_url": {"url": before_data_url}},
                                {"type": "text", "text": "AFTER IMAGE"},
                                {"type": "image_url", "image_url": {"url": after_data_url}},
                            ],
                        }
                    ],
                    temperature=0.2,
                    max_tokens=1200,
                )

                content = response.choices[0].message.content
                parsed = self._extract_json_block(content)
                return self._validate_comparison_response(parsed)

            raise ValueError("No free vision provider path succeeded")
        except Exception as exc:
            print(f"âŒ Vision cleanup comparison failed: {exc}")
            return self._get_contextual_fallback_comparison(before_image_url, after_image_url)


