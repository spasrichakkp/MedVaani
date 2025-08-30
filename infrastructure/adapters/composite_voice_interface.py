"""Composite voice interface that combines ASR and TTS adapters with resilience patterns."""

import asyncio
from typing import Optional, Dict, Any, List

from application.ports.voice_interface_port import (
    VoiceInterfacePort, VoiceProcessingError, AudioQualityError
)
from domain.value_objects.audio_data import AudioData
from infrastructure.logging.logger_factory import get_module_logger
from infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from infrastructure.resilience.retry_policy import RetryPolicy, RetryConfig, ExponentialBackoff
from .whisper_adapter import WhisperAdapter
from .speecht5_adapter import SpeechT5Adapter

try:
    import pyaudio
    import wave
    import tempfile
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


class CompositeVoiceInterface(VoiceInterfacePort):
    """
    Composite voice interface that combines ASR and TTS adapters.
    
    This interface provides a complete voice processing solution by combining
    separate ASR and TTS adapters with resilience patterns for production use.
    """
    
    def __init__(
        self,
        asr_adapter: WhisperAdapter,
        tts_adapter: SpeechT5Adapter,
        enable_resilience: bool = True
    ):
        """
        Initialize composite voice interface.
        
        Args:
            asr_adapter: ASR adapter (e.g., WhisperAdapter)
            tts_adapter: TTS adapter (e.g., SpeechT5Adapter)
            enable_resilience: Whether to enable circuit breakers and retry
        """
        self.asr_adapter = asr_adapter
        self.tts_adapter = tts_adapter
        self.enable_resilience = enable_resilience
        
        self.logger = get_module_logger(__name__)
        
        # Audio configuration
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        self.audio_format = pyaudio.paInt16 if AUDIO_AVAILABLE else None
        
        # Initialize resilience patterns
        if enable_resilience:
            self._setup_resilience_patterns()
        else:
            self.asr_circuit_breaker = None
            self.tts_circuit_breaker = None
            self.asr_retry_policy = None
            self.tts_retry_policy = None
    
    def _setup_resilience_patterns(self) -> None:
        """Setup circuit breakers and retry policies."""
        # ASR circuit breaker
        asr_cb_config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout_duration=30,
            half_open_max_calls=2
        )
        self.asr_circuit_breaker = CircuitBreaker(asr_cb_config, "asr_composite")
        
        # TTS circuit breaker
        tts_cb_config = CircuitBreakerConfig(
            failure_threshold=3,
            timeout_duration=30,
            half_open_max_calls=2
        )
        self.tts_circuit_breaker = CircuitBreaker(tts_cb_config, "tts_composite")
        
        # ASR retry policy
        asr_retry_config = RetryConfig(
            max_attempts=3,
            backoff_strategy=ExponentialBackoff(base_delay=1.0, max_delay=10.0),
            retryable_exceptions=[VoiceProcessingError],
            timeout_per_attempt=30.0
        )
        self.asr_retry_policy = RetryPolicy(asr_retry_config, "asr_composite")
        
        # TTS retry policy
        tts_retry_config = RetryConfig(
            max_attempts=3,
            backoff_strategy=ExponentialBackoff(base_delay=1.0, max_delay=10.0),
            retryable_exceptions=[VoiceProcessingError],
            timeout_per_attempt=30.0
        )
        self.tts_retry_policy = RetryPolicy(tts_retry_config, "tts_composite")
    
    async def transcribe_audio(self, audio: AudioData) -> Optional[str]:
        """
        Transcribe audio to text with resilience patterns.
        
        Args:
            audio: AudioData object containing audio to transcribe
            
        Returns:
            Transcribed text or None if transcription failed
        """
        try:
            if self.enable_resilience and self.asr_circuit_breaker and self.asr_retry_policy:
                # Use circuit breaker and retry
                return await self.asr_circuit_breaker.call(
                    self.asr_retry_policy.execute,
                    self.asr_adapter.transcribe_audio,
                    audio
                )
            else:
                # Direct call without resilience
                return await self.asr_adapter.transcribe_audio(audio)
                
        except Exception as e:
            self.logger.error(f"Transcription failed in composite interface: {e}")
            return None
    
    async def synthesize_speech(self, text: str, voice_config: Optional[Dict[str, Any]] = None) -> Optional[AudioData]:
        """
        Convert text to speech with resilience patterns.
        
        Args:
            text: Text to convert to speech
            voice_config: Optional voice configuration
            
        Returns:
            AudioData object containing synthesized speech or None if failed
        """
        try:
            if self.enable_resilience and self.tts_circuit_breaker and self.tts_retry_policy:
                # Use circuit breaker and retry
                return await self.tts_circuit_breaker.call(
                    self.tts_retry_policy.execute,
                    self.tts_adapter.synthesize_speech,
                    text,
                    voice_config
                )
            else:
                # Direct call without resilience
                return await self.tts_adapter.synthesize_speech(text, voice_config)
                
        except Exception as e:
            self.logger.error(f"Speech synthesis failed in composite interface: {e}")
            return None
    
    async def validate_audio_quality(self, audio: AudioData) -> bool:
        """
        Validate if audio quality is sufficient for processing.
        
        Args:
            audio: AudioData object to validate
            
        Returns:
            True if audio quality is sufficient
        """
        try:
            # Use ASR adapter for validation
            return await self.asr_adapter.validate_audio_quality(audio)
        except Exception as e:
            self.logger.error(f"Audio quality validation failed: {e}")
            return False
    
    async def record_audio(self, duration_seconds: float) -> Optional[AudioData]:
        """
        Record audio from the default input device.
        
        Args:
            duration_seconds: Duration to record in seconds
            
        Returns:
            AudioData object containing recorded audio or None if failed
        """
        if not AUDIO_AVAILABLE:
            self.logger.error("PyAudio not available for recording")
            return None
        
        try:
            self.logger.info(f"Starting audio recording for {duration_seconds} seconds")
            
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            # Open stream
            stream = p.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            # Record audio
            frames = []
            num_chunks = int(self.sample_rate / self.chunk_size * duration_seconds)
            
            for _ in range(num_chunks):
                data = stream.read(self.chunk_size)
                frames.append(data)
            
            # Stop and close stream
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Convert to AudioData
            audio_data = self._frames_to_audio_data(frames)
            
            self.logger.info("Audio recording completed successfully")
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Audio recording failed: {e}")
            return None
    
    def _frames_to_audio_data(self, frames: List[bytes]) -> AudioData:
        """Convert audio frames to AudioData object."""
        import numpy as np
        
        # Combine all frames
        audio_bytes = b''.join(frames)
        
        # Convert to numpy array
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        
        # Convert to float32 and normalize
        audio_array = audio_array.astype(np.float32) / 32768.0
        
        return AudioData.from_numpy(
            audio_array,
            sample_rate=self.sample_rate,
            channels=self.channels
        )
    
    async def play_audio(self, audio: AudioData) -> bool:
        """
        Play audio through the default output device.
        
        Args:
            audio: AudioData object to play
            
        Returns:
            True if playback succeeded, False otherwise
        """
        if not AUDIO_AVAILABLE:
            self.logger.error("PyAudio not available for playback")
            return False
        
        try:
            self.logger.info("Starting audio playback")
            
            # Convert AudioData to playable format
            audio_array = audio.get_samples_as_numpy()
            
            # Convert to int16 for playback
            audio_int16 = (audio_array * 32767).astype(np.int16)
            
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            # Open stream
            stream = p.open(
                format=self.audio_format,
                channels=audio.channels,
                rate=audio.sample_rate,
                output=True
            )
            
            # Play audio
            stream.write(audio_int16.tobytes())
            
            # Stop and close stream
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            self.logger.info("Audio playback completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Audio playback failed: {e}")
            return False
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        try:
            # Get languages from ASR adapter (TTS typically supports fewer)
            return await self.asr_adapter.get_supported_languages()
        except Exception as e:
            self.logger.error(f"Failed to get supported languages: {e}")
            return ["en"]  # Default to English
    
    async def detect_language(self, audio: AudioData) -> Optional[str]:
        """
        Detect the language of spoken audio.
        
        Args:
            audio: AudioData object to analyze
            
        Returns:
            Language code or None if detection failed
        """
        try:
            return await self.asr_adapter.detect_language(audio)
        except Exception as e:
            self.logger.error(f"Language detection failed: {e}")
            return None
    
    async def get_transcription_confidence(self, audio: AudioData) -> float:
        """
        Get confidence score for transcription quality.
        
        Args:
            audio: AudioData object to analyze
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            return await self.asr_adapter.get_transcription_confidence(audio)
        except Exception as e:
            self.logger.error(f"Confidence calculation failed: {e}")
            return 0.0
    
    async def enhance_audio_quality(self, audio: AudioData) -> AudioData:
        """
        Enhance audio quality for better processing.
        
        Args:
            audio: AudioData object to enhance
            
        Returns:
            Enhanced AudioData object
        """
        try:
            return await self.asr_adapter.enhance_audio_quality(audio)
        except Exception as e:
            self.logger.error(f"Audio enhancement failed: {e}")
            return audio
    
    async def is_available(self) -> bool:
        """Check if voice interface is available and ready."""
        try:
            asr_available = await self.asr_adapter.is_available()
            tts_available = await self.tts_adapter.is_available()
            
            return asr_available and tts_available and AUDIO_AVAILABLE
            
        except Exception as e:
            self.logger.error(f"Availability check failed: {e}")
            return False
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of voice processing components."""
        try:
            asr_health = await self.asr_adapter.get_health_status()
            tts_health = await self.tts_adapter.get_health_status()
            
            # Get resilience stats if enabled
            resilience_stats = {}
            if self.enable_resilience:
                if self.asr_circuit_breaker:
                    resilience_stats["asr_circuit_breaker"] = await self.asr_circuit_breaker.get_stats()
                if self.tts_circuit_breaker:
                    resilience_stats["tts_circuit_breaker"] = await self.tts_circuit_breaker.get_stats()
                if self.asr_retry_policy:
                    resilience_stats["asr_retry_policy"] = self.asr_retry_policy.get_stats()
                if self.tts_retry_policy:
                    resilience_stats["tts_retry_policy"] = self.tts_retry_policy.get_stats()
            
            return {
                "service": "composite_voice_interface",
                "audio_available": AUDIO_AVAILABLE,
                "resilience_enabled": self.enable_resilience,
                "asr_health": asr_health,
                "tts_health": tts_health,
                "resilience_stats": resilience_stats,
                "overall_status": "healthy" if (
                    asr_health.get("status") == "healthy" and 
                    tts_health.get("status") == "healthy" and 
                    AUDIO_AVAILABLE
                ) else "degraded"
            }
            
        except Exception as e:
            self.logger.error(f"Health status check failed: {e}")
            return {
                "service": "composite_voice_interface",
                "status": "unhealthy",
                "error": str(e)
            }
