"""
Voice prompting module using Grok Voice Agent API.
Allows users to provide prompts via voice input.
"""
import logging
import base64
from typing import Optional, Dict, Any
import httpx
from config import settings

logger = logging.getLogger(__name__)


class VoicePrompting:
    """Handles voice prompting using Grok Voice Agent API."""

    def __init__(self):
        self.api_key = settings.xai_api_key
        self.base_url = settings.xai_api_base.rstrip('/')

    def transcribe_audio(
        self,
        audio_data: bytes,
        audio_format: str = "wav"
    ) -> Optional[str]:
        """
        Transcribe audio to text using Grok Voice Agent API.
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (wav, mp3, etc.)
            
        Returns:
            Transcribed text or None if error
        """
        try:
            # Encode audio to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            # Prepare request
            url = f"{self.base_url}/audio/transcriptions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "file": f"data:audio/{audio_format};base64,{audio_base64}",
                "model": "whisper-1"  # Using Whisper model for transcription
            }

            # Make request
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()

                return result.get("text", "")
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return None

    def process_voice_prompt(
        self,
        audio_data: bytes,
        audio_format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Process a voice prompt: transcribe and return the text.
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format
            
        Returns:
            Dictionary with transcribed text and metadata
        """
        try:
            transcribed_text = self.transcribe_audio(audio_data, audio_format)

            if not transcribed_text:
                return {
                    "success": False,
                    "error": "Failed to transcribe audio",
                    "text": None
                }

            return {
                "success": True,
                "text": transcribed_text,
                "audio_format": audio_format
            }
        except Exception as e:
            logger.error(f"Error processing voice prompt: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": None
            }

    def validate_audio_format(self, audio_format: str) -> bool:
        """
        Validate if audio format is supported.
        
        Args:
            audio_format: Audio format string
            
        Returns:
            True if supported
        """
        supported_formats = ["wav", "mp3", "m4a", "ogg", "flac"]
        return audio_format.lower() in supported_formats
