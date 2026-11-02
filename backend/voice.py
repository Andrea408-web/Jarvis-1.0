"""Optional ElevenLabs text-to-speech; local fallback lives in the browser."""

import os
import re

from .providers import ProviderError, provider_status, request_bytes, reserve


class VoiceClient:
    def __init__(self, store, transport=None):
        self.store = store
        self.transport = transport or request_bytes

    def synthesize(self, text):
        if not isinstance(text, str) or not text.strip() or len(text) > 2_000:
            raise ProviderError("Sprachausgabe benötigt 1 bis 2.000 Zeichen.")
        settings = self.store.settings()
        if not settings.get("elevenlabs_enabled", False):
            raise ProviderError("ElevenLabs ist deaktiviert. Die lokale Browserstimme bleibt verfügbar.", 409)
        key = os.environ.get("ELEVENLABS_API_KEY", "")
        if not key:
            raise ProviderError("ElevenLabs-Schlüssel fehlt. Öffnen Sie Einstellungen → ElevenLabs → Schlüssel hinterlegen, oder verwenden Sie die lokale Stimme.", 409)
        voice = settings.get("elevenlabs_voice_id", "")
        if not isinstance(voice, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", voice):
            raise ProviderError("Bitte konfigurieren Sie eine gültige ElevenLabs Voice ID.", 409)
        text = text.strip()
        reserve(self.store, "elevenlabs_characters", len(text), settings.get("elevenlabs_daily_char_limit", 1500))
        result = self.transport(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
            {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
            {"xi-api-key": key, "Accept": "audio/mpeg"},
            expected_type="audio/mpeg",
            max_bytes=12_000_000,
        )
        if not result:
            raise ProviderError("ElevenLabs hat keine Audiodaten geliefert.", 502)
        return result
