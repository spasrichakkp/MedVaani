"""Whisper adapter for speech-to-text functionality."""

import asyncio
import torch
import numpy as np
from typing import Optional, Dict, Any, List
from pathlib import Path

from application.ports.voice_interface_port import (
    VoiceInterfacePort, VoiceProcessingError, TranscriptionError, AudioQualityError
)
from domain.value_objects.audio_data import AudioData
from infrastructure.logging.logger_factory import get_module_logger

try:
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class WhisperAdapter(VoiceInterfacePort):
    """
    Whisper adapter for automatic speech recognition.
    
    This adapter implements the VoiceInterfacePort for ASR functionality
    using OpenAI's Whisper models via Hugging Face transformers.
    """
    
    def __init__(
        self,
        model_name: str = "openai/whisper-small",
        device: str = "auto",
        torch_dtype: str = "float16"
    ):
        """
        Initialize Whisper adapter.
        
        Args:
            model_name: Whisper model name from Hugging Face
            device: Device to run model on ("auto", "cpu", "cuda")
            torch_dtype: Torch data type for model
        """
        if not WHISPER_AVAILABLE:
            raise ImportError("Whisper dependencies not available. Install transformers.")
        
        self.model_name = model_name
        self.device = self._resolve_device(device)
        self.torch_dtype = getattr(torch, torch_dtype)
        
        self.processor: Optional[WhisperProcessor] = None
        self.model: Optional[WhisperForConditionalGeneration] = None
        self._model_lock = asyncio.Lock()
        self._is_loaded = False
        
        self.logger = get_module_logger(__name__)
        
        # Configuration
        self.sample_rate = 16000
        self.min_audio_length = 0.1  # 100ms minimum
        self.max_audio_length = 30.0  # 30 seconds maximum
        self.quality_threshold = 0.01  # RMS amplitude threshold
    
    def _resolve_device(self, device: str) -> str:
        """Resolve device string to actual device."""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    async def _ensure_model_loaded(self) -> None:
        """Ensure Whisper model is loaded (thread-safe)."""
        if self._is_loaded:
            return
        
        async with self._model_lock:
            if self._is_loaded:  # Double-check pattern
                return
            
            try:
                self.logger.info(f"Loading Whisper model: {self.model_name}")
                
                # Load processor and model in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                
                self.processor = await loop.run_in_executor(
                    None,
                    lambda: WhisperProcessor.from_pretrained(self.model_name)
                )
                
                self.model = await loop.run_in_executor(
                    None,
                    lambda: WhisperForConditionalGeneration.from_pretrained(
                        self.model_name,
                        torch_dtype=self.torch_dtype,
                        low_cpu_mem_usage=True
                    ).to(self.device)
                )
                
                self._is_loaded = True
                self.logger.info(f"Whisper model loaded successfully on {self.device}")
                
            except Exception as e:
                self.logger.error(f"Failed to load Whisper model: {e}")
                raise VoiceProcessingError(f"Model loading failed: {e}") from e
    
    async def transcribe_audio(self, audio: AudioData) -> Optional[str]:
        """
        Transcribe audio to text using Whisper.
        
        Args:
            audio: AudioData object containing audio to transcribe
            
        Returns:
            Transcribed text or None if transcription failed
        """
        try:
            await self._ensure_model_loaded()
            
            # Validate audio
            if not self._validate_audio_for_transcription(audio):
                raise AudioQualityError("Audio validation failed")
            
            # Prepare audio for Whisper
            audio_array = self._prepare_audio_for_whisper(audio)
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            transcription = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                audio_array
            )
            
            if transcription and transcription.strip():
                self.logger.debug(f"Transcription successful: '{transcription[:50]}...'")
                return transcription.strip()
            else:
                self.logger.warning("Empty transcription result")
                return None
                
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise TranscriptionError(f"Whisper transcription failed: {e}") from e
    
    def _validate_audio_for_transcription(self, audio: AudioData) -> bool:
        """Validate audio is suitable for transcription."""
        # Check duration
        if audio.duration_seconds < self.min_audio_length:
            self.logger.warning(f"Audio too short: {audio.duration_seconds}s")
            return False
        
        if audio.duration_seconds > self.max_audio_length:
            self.logger.warning(f"Audio too long: {audio.duration_seconds}s")
            return False
        
        # Check audio quality
        if not audio.has_sufficient_volume(self.quality_threshold):
            self.logger.warning(f"Audio volume too low: {audio.get_rms_amplitude()}")
            return False
        
        return True
    
    def _prepare_audio_for_whisper(self, audio: AudioData) -> np.ndarray:
        """Prepare audio data for Whisper processing."""
        audio_array = audio.get_samples_as_numpy()
        
        # Ensure correct sample rate
        if audio.sample_rate != self.sample_rate:
            # Resample if needed (requires librosa)
            try:
                audio = audio.resample(self.sample_rate)
                audio_array = audio.get_samples_as_numpy()
            except ImportError:
                self.logger.warning(f"Cannot resample audio from {audio.sample_rate} to {self.sample_rate}")
        
        # Ensure float32 and normalize
        audio_array = audio_array.astype(np.float32)
        
        # Normalize to [-1, 1] range
        max_val = np.max(np.abs(audio_array))
        if max_val > 0:
            audio_array = audio_array / max_val
        
        return audio_array
    
    def _transcribe_sync(self, audio_array: np.ndarray) -> str:
        """Synchronous transcription for thread pool execution."""
        try:
            # Process audio
            inputs = self.processor(
                audio_array,
                sampling_rate=self.sample_rate,
                return_tensors="pt"
            )
            
            # Move inputs to device
            input_features = inputs["input_features"].to(self.device)
            
            # Generate transcription
            with torch.no_grad():
                predicted_ids = self.model.generate(
                    input_features,
                    max_new_tokens=448,  # Whisper's max length
                    do_sample=False,
                    num_beams=1,
                    return_dict_in_generate=True,
                    output_scores=True
                )
            
            # Decode transcription
            transcription = self.processor.batch_decode(
                predicted_ids.sequences,
                skip_special_tokens=True
            )[0]
            
            return transcription
            
        except Exception as e:
            raise TranscriptionError(f"Synchronous transcription failed: {e}") from e
    
    async def synthesize_speech(self, text: str, voice_config: Optional[Dict[str, Any]] = None) -> Optional[AudioData]:
        """Not implemented in Whisper adapter (ASR only)."""
        raise NotImplementedError("Whisper adapter only supports ASR, not TTS")
    
    async def validate_audio_quality(self, audio: AudioData) -> bool:
        """
        Validate if audio quality is sufficient for processing.
        
        Args:
            audio: AudioData object to validate
            
        Returns:
            True if audio quality is sufficient
        """
        return self._validate_audio_for_transcription(audio)
    
    async def record_audio(self, duration_seconds: float) -> Optional[AudioData]:
        """Not implemented in Whisper adapter (use system recording)."""
        raise NotImplementedError("Whisper adapter does not support audio recording")
    
    async def play_audio(self, audio: AudioData) -> bool:
        """Not implemented in Whisper adapter (use system playback)."""
        raise NotImplementedError("Whisper adapter does not support audio playback")
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages for Whisper."""
        # Whisper supports many languages
        return [
            "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "tr", "pl", "nl", "sv", "da", "no", "fi"
        ]
    
    async def detect_language(self, audio: AudioData) -> Optional[str]:
        """
        Detect language of spoken audio.
        
        Args:
            audio: AudioData object to analyze
            
        Returns:
            Language code or None if detection failed
        """
        try:
            await self._ensure_model_loaded()
            
            # Prepare audio
            audio_array = self._prepare_audio_for_whisper(audio)
            
            # Run language detection in thread pool
            loop = asyncio.get_event_loop()
            language = await loop.run_in_executor(
                None,
                self._detect_language_sync,
                audio_array
            )
            
            return language
            
        except Exception as e:
            self.logger.error(f"Language detection failed: {e}")
            return None
    
    def _detect_language_sync(self, audio_array: np.ndarray) -> Optional[str]:
        """Synchronous language detection."""
        try:
            # Process audio
            inputs = self.processor(
                audio_array,
                sampling_rate=self.sample_rate,
                return_tensors="pt"
            )
            
            input_features = inputs["input_features"].to(self.device)
            
            # Generate with language detection
            with torch.no_grad():
                predicted_ids = self.model.generate(
                    input_features,
                    max_new_tokens=1,
                    return_dict_in_generate=True,
                    output_scores=True
                )
            
            # Extract language token (this is a simplified approach)
            # In practice, you'd need to decode the language token properly
            return "en"  # Default to English for now
            
        except Exception as e:
            self.logger.error(f"Language detection sync failed: {e}")
            return None
    
    async def get_transcription_confidence(self, audio: AudioData) -> float:
        """
        Get confidence score for transcription quality.
        
        Args:
            audio: AudioData object to analyze
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Simple confidence based on audio quality
        if not self._validate_audio_for_transcription(audio):
            return 0.0
        
        # Base confidence on audio properties
        rms = audio.get_rms_amplitude()
        duration = audio.duration_seconds
        
        # Simple heuristic for confidence
        quality_score = min(rms / self.quality_threshold, 1.0)
        duration_score = min(duration / 2.0, 1.0)  # Prefer 2+ second audio
        
        return (quality_score + duration_score) / 2.0
    
    async def enhance_audio_quality(self, audio: AudioData) -> AudioData:
        """
        Enhance audio quality for better processing.
        
        Args:
            audio: AudioData object to enhance
            
        Returns:
            Enhanced AudioData object
        """
        # Simple enhancement: trim silence and normalize
        try:
            enhanced = audio.trim_silence(threshold=self.quality_threshold / 2)
            
            # Ensure minimum duration
            if enhanced.duration_seconds < self.min_audio_length:
                return audio  # Return original if too short after trimming
            
            return enhanced
            
        except Exception as e:
            self.logger.warning(f"Audio enhancement failed: {e}")
            return audio
    
    async def is_available(self) -> bool:
        """Check if Whisper interface is available and ready."""
        try:
            await self._ensure_model_loaded()
            return self._is_loaded
        except Exception:
            return False
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of Whisper processing components."""
        status = {
            "service": "whisper_asr",
            "model": self.model_name,
            "device": self.device,
            "is_loaded": self._is_loaded,
            "available": WHISPER_AVAILABLE
        }
        
        if self._is_loaded and self.model:
            try:
                # Test with dummy data
                dummy_audio = np.zeros(1600, dtype=np.float32)  # 0.1 second of silence
                inputs = self.processor(dummy_audio, sampling_rate=self.sample_rate, return_tensors="pt")
                
                with torch.no_grad():
                    _ = self.model.generate(inputs["input_features"].to(self.device), max_new_tokens=1)
                
                status["status"] = "healthy"
                status["last_check"] = "success"
                
            except Exception as e:
                status["status"] = "unhealthy"
                status["error"] = str(e)
        else:
            status["status"] = "not_loaded"
        
        return status
