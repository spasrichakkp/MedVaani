"""Port interface for voice processing operations."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from domain.value_objects.audio_data import AudioData


class VoiceInterfacePort(ABC):
    """
    Port interface for voice processing operations.
    
    This interface defines the contract for voice-related operations
    including speech-to-text, text-to-speech, and audio validation.
    """
    
    @abstractmethod
    async def transcribe_audio(self, audio: AudioData) -> Optional[str]:
        """
        Convert audio to text using speech recognition.
        
        Args:
            audio: AudioData object containing the audio to transcribe
            
        Returns:
            Transcribed text or None if transcription failed
            
        Raises:
            VoiceProcessingError: If transcription fails
        """
        pass
    
    @abstractmethod
    async def synthesize_speech(self, text: str, voice_config: Optional[Dict[str, Any]] = None) -> Optional[AudioData]:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert to speech
            voice_config: Optional voice configuration (speed, pitch, etc.)
            
        Returns:
            AudioData object containing synthesized speech or None if failed
            
        Raises:
            VoiceProcessingError: If speech synthesis fails
        """
        pass
    
    @abstractmethod
    async def validate_audio_quality(self, audio: AudioData) -> bool:
        """
        Validate if audio quality is sufficient for processing.
        
        Args:
            audio: AudioData object to validate
            
        Returns:
            True if audio quality is sufficient, False otherwise
        """
        pass
    
    @abstractmethod
    async def record_audio(self, duration_seconds: float) -> Optional[AudioData]:
        """
        Record audio from the default input device.
        
        Args:
            duration_seconds: Duration to record in seconds
            
        Returns:
            AudioData object containing recorded audio or None if failed
            
        Raises:
            VoiceProcessingError: If recording fails
        """
        pass
    
    @abstractmethod
    async def play_audio(self, audio: AudioData) -> bool:
        """
        Play audio through the default output device.
        
        Args:
            audio: AudioData object to play
            
        Returns:
            True if playback succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_supported_languages(self) -> list[str]:
        """
        Get list of supported languages for speech processing.
        
        Returns:
            List of language codes (e.g., ['en', 'es', 'fr'])
        """
        pass
    
    @abstractmethod
    async def detect_language(self, audio: AudioData) -> Optional[str]:
        """
        Detect the language of spoken audio.
        
        Args:
            audio: AudioData object to analyze
            
        Returns:
            Language code or None if detection failed
        """
        pass
    
    @abstractmethod
    async def get_transcription_confidence(self, audio: AudioData) -> float:
        """
        Get confidence score for transcription quality.
        
        Args:
            audio: AudioData object to analyze
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        pass
    
    @abstractmethod
    async def enhance_audio_quality(self, audio: AudioData) -> AudioData:
        """
        Enhance audio quality for better processing.
        
        Args:
            audio: AudioData object to enhance
            
        Returns:
            Enhanced AudioData object
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if voice interface is available and ready.
        
        Returns:
            True if interface is ready, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of voice processing components.
        
        Returns:
            Dictionary containing health status information
        """
        pass


class VoiceProcessingError(Exception):
    """Base exception for voice processing errors."""
    pass


class AudioQualityError(VoiceProcessingError):
    """Raised when audio quality is insufficient for processing."""
    pass


class TranscriptionError(VoiceProcessingError):
    """Raised when speech-to-text transcription fails."""
    pass


class SynthesisError(VoiceProcessingError):
    """Raised when text-to-speech synthesis fails.""" 
    pass


class RecordingError(VoiceProcessingError):
    """Raised when audio recording fails."""
    pass


class PlaybackError(VoiceProcessingError):
    """Raised when audio playback fails."""
    pass
