"""SpeechT5 adapter for text-to-speech functionality."""

import asyncio
import torch
import numpy as np
from typing import Optional, Dict, Any, List
from pathlib import Path

from application.ports.voice_interface_port import (
    VoiceInterfacePort, VoiceProcessingError, SynthesisError
)
from domain.value_objects.audio_data import AudioData
from infrastructure.logging.logger_factory import get_module_logger

try:
    from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
    from datasets import load_dataset
    SPEECHT5_AVAILABLE = True
except ImportError:
    SPEECHT5_AVAILABLE = False


class SpeechT5Adapter(VoiceInterfacePort):
    """
    SpeechT5 adapter for text-to-speech functionality.
    
    This adapter implements the VoiceInterfacePort for TTS functionality
    using Microsoft's SpeechT5 models via Hugging Face transformers.
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/speecht5_tts",
        vocoder_name: str = "microsoft/speecht5_hifigan",
        device: str = "auto",
        torch_dtype: str = "float16"
    ):
        """
        Initialize SpeechT5 adapter.
        
        Args:
            model_name: SpeechT5 model name from Hugging Face
            vocoder_name: HiFiGAN vocoder name
            device: Device to run model on ("auto", "cpu", "cuda")
            torch_dtype: Torch data type for model
        """
        if not SPEECHT5_AVAILABLE:
            raise ImportError("SpeechT5 dependencies not available. Install transformers and datasets.")
        
        self.model_name = model_name
        self.vocoder_name = vocoder_name
        self.device = self._resolve_device(device)
        self.torch_dtype = getattr(torch, torch_dtype)
        
        self.processor: Optional[SpeechT5Processor] = None
        self.model: Optional[SpeechT5ForTextToSpeech] = None
        self.vocoder: Optional[SpeechT5HifiGan] = None
        self.speaker_embeddings: Optional[torch.Tensor] = None
        
        self._model_lock = asyncio.Lock()
        self._is_loaded = False
        
        self.logger = get_module_logger(__name__)
        
        # Configuration
        self.sample_rate = 16000
        self.max_text_length = 600  # Maximum characters for TTS
        self.default_voice_speed = 1.0
        self.default_voice_pitch = 1.0
    
    def _resolve_device(self, device: str) -> str:
        """Resolve device string to actual device."""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    async def _ensure_model_loaded(self) -> None:
        """Ensure SpeechT5 model is loaded (thread-safe)."""
        if self._is_loaded:
            return
        
        async with self._model_lock:
            if self._is_loaded:  # Double-check pattern
                return
            
            try:
                self.logger.info(f"Loading SpeechT5 model: {self.model_name}")
                
                # Load components in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                
                # Load processor
                self.processor = await loop.run_in_executor(
                    None,
                    lambda: SpeechT5Processor.from_pretrained(self.model_name)
                )
                
                # Load TTS model
                self.model = await loop.run_in_executor(
                    None,
                    lambda: SpeechT5ForTextToSpeech.from_pretrained(
                        self.model_name,
                        torch_dtype=self.torch_dtype,
                        low_cpu_mem_usage=True
                    ).to(self.device)
                )
                
                # Load vocoder
                self.vocoder = await loop.run_in_executor(
                    None,
                    lambda: SpeechT5HifiGan.from_pretrained(
                        self.vocoder_name,
                        torch_dtype=self.torch_dtype
                    ).to(self.device)
                )
                
                # Load speaker embeddings
                await self._load_speaker_embeddings()
                
                self._is_loaded = True
                self.logger.info(f"SpeechT5 model loaded successfully on {self.device}")
                
            except Exception as e:
                self.logger.error(f"Failed to load SpeechT5 model: {e}")
                raise VoiceProcessingError(f"Model loading failed: {e}") from e
    
    async def _load_speaker_embeddings(self) -> None:
        """Load default speaker embeddings."""
        try:
            # Load speaker embeddings from CMU ARCTIC dataset
            loop = asyncio.get_event_loop()
            
            embeddings_dataset = await loop.run_in_executor(
                None,
                lambda: load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
            )
            
            # Use first speaker embedding as default
            self.speaker_embeddings = torch.tensor(
                embeddings_dataset[7306]["xvector"]  # Female speaker
            ).unsqueeze(0).to(self.device)
            
            self.logger.debug("Speaker embeddings loaded successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to load speaker embeddings: {e}")
            # Create dummy embeddings as fallback
            self.speaker_embeddings = torch.randn(1, 512).to(self.device)
    
    async def synthesize_speech(self, text: str, voice_config: Optional[Dict[str, Any]] = None) -> Optional[AudioData]:
        """
        Convert text to speech using SpeechT5.
        
        Args:
            text: Text to convert to speech
            voice_config: Optional voice configuration (speed, pitch, etc.)
            
        Returns:
            AudioData object containing synthesized speech or None if failed
        """
        try:
            await self._ensure_model_loaded()
            
            # Validate and prepare text
            processed_text = self._prepare_text_for_synthesis(text)
            if not processed_text:
                raise SynthesisError("Text preparation failed")
            
            # Apply voice configuration
            config = self._parse_voice_config(voice_config)
            
            # Run synthesis in thread pool
            loop = asyncio.get_event_loop()
            audio_array = await loop.run_in_executor(
                None,
                self._synthesize_sync,
                processed_text,
                config
            )
            
            if audio_array is not None and len(audio_array) > 0:
                # Create AudioData object
                audio_data = AudioData.from_numpy(
                    audio_array,
                    sample_rate=self.sample_rate
                )
                
                self.logger.debug(f"Speech synthesis successful: {audio_data.duration_seconds:.2f}s")
                return audio_data
            else:
                self.logger.warning("Empty synthesis result")
                return None
                
        except Exception as e:
            self.logger.error(f"Speech synthesis failed: {e}")
            raise SynthesisError(f"SpeechT5 synthesis failed: {e}") from e
    
    def _prepare_text_for_synthesis(self, text: str) -> str:
        """Prepare text for speech synthesis."""
        if not text or not text.strip():
            return ""
        
        # Clean and normalize text
        processed_text = text.strip()
        
        # Truncate if too long
        if len(processed_text) > self.max_text_length:
            self.logger.warning(f"Text truncated from {len(processed_text)} to {self.max_text_length} characters")
            processed_text = processed_text[:self.max_text_length]
            
            # Try to end at a sentence boundary
            last_period = processed_text.rfind('.')
            last_exclamation = processed_text.rfind('!')
            last_question = processed_text.rfind('?')
            
            last_sentence_end = max(last_period, last_exclamation, last_question)
            if last_sentence_end > self.max_text_length * 0.8:  # If we can save 20% of text
                processed_text = processed_text[:last_sentence_end + 1]
        
        return processed_text
    
    def _parse_voice_config(self, voice_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse voice configuration parameters."""
        config = {
            "speed": self.default_voice_speed,
            "pitch": self.default_voice_pitch,
            "speaker_id": 0
        }
        
        if voice_config:
            config.update({
                "speed": voice_config.get("speed", config["speed"]),
                "pitch": voice_config.get("pitch", config["pitch"]),
                "speaker_id": voice_config.get("speaker_id", config["speaker_id"])
            })
        
        return config
    
    def _synthesize_sync(self, text: str, config: Dict[str, Any]) -> Optional[np.ndarray]:
        """Synchronous speech synthesis for thread pool execution."""
        try:
            # Tokenize text
            inputs = self.processor(text=text, return_tensors="pt")
            input_ids = inputs["input_ids"].to(self.device)
            
            # Generate speech
            with torch.no_grad():
                speech = self.model.generate_speech(
                    input_ids,
                    self.speaker_embeddings,
                    vocoder=self.vocoder
                )
            
            # Convert to numpy and apply voice modifications
            audio_array = speech.cpu().numpy()
            
            # Apply speed modification (simple time stretching)
            speed = config.get("speed", 1.0)
            if speed != 1.0:
                audio_array = self._apply_speed_change(audio_array, speed)
            
            # Apply pitch modification (simple pitch shifting)
            pitch = config.get("pitch", 1.0)
            if pitch != 1.0:
                audio_array = self._apply_pitch_change(audio_array, pitch)
            
            return audio_array
            
        except Exception as e:
            raise SynthesisError(f"Synchronous synthesis failed: {e}") from e
    
    def _apply_speed_change(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """Apply speed change to audio (simple resampling)."""
        try:
            if speed == 1.0:
                return audio
            
            # Simple speed change by resampling
            new_length = int(len(audio) / speed)
            indices = np.linspace(0, len(audio) - 1, new_length)
            return np.interp(indices, np.arange(len(audio)), audio)
            
        except Exception as e:
            self.logger.warning(f"Speed change failed: {e}")
            return audio
    
    def _apply_pitch_change(self, audio: np.ndarray, pitch: float) -> np.ndarray:
        """Apply pitch change to audio (simplified)."""
        try:
            if pitch == 1.0:
                return audio
            
            # This is a very simplified pitch shift
            # In practice, you'd use more sophisticated algorithms
            return audio * pitch
            
        except Exception as e:
            self.logger.warning(f"Pitch change failed: {e}")
            return audio
    
    async def transcribe_audio(self, audio: AudioData) -> Optional[str]:
        """Not implemented in SpeechT5 adapter (TTS only)."""
        raise NotImplementedError("SpeechT5 adapter only supports TTS, not ASR")
    
    async def validate_audio_quality(self, audio: AudioData) -> bool:
        """Not implemented in SpeechT5 adapter (TTS only)."""
        raise NotImplementedError("SpeechT5 adapter does not validate input audio")
    
    async def record_audio(self, duration_seconds: float) -> Optional[AudioData]:
        """Not implemented in SpeechT5 adapter (use system recording)."""
        raise NotImplementedError("SpeechT5 adapter does not support audio recording")
    
    async def play_audio(self, audio: AudioData) -> bool:
        """Not implemented in SpeechT5 adapter (use system playback)."""
        raise NotImplementedError("SpeechT5 adapter does not support audio playback")
    
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages for SpeechT5."""
        # SpeechT5 primarily supports English
        return ["en"]
    
    async def detect_language(self, audio: AudioData) -> Optional[str]:
        """Not implemented in SpeechT5 adapter (TTS only)."""
        raise NotImplementedError("SpeechT5 adapter does not support language detection")
    
    async def get_transcription_confidence(self, audio: AudioData) -> float:
        """Not implemented in SpeechT5 adapter (TTS only)."""
        raise NotImplementedError("SpeechT5 adapter does not support transcription")
    
    async def enhance_audio_quality(self, audio: AudioData) -> AudioData:
        """Not implemented in SpeechT5 adapter (TTS only)."""
        raise NotImplementedError("SpeechT5 adapter does not enhance input audio")
    
    async def is_available(self) -> bool:
        """Check if SpeechT5 interface is available and ready."""
        try:
            await self._ensure_model_loaded()
            return self._is_loaded
        except Exception:
            return False
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of SpeechT5 processing components."""
        status = {
            "service": "speecht5_tts",
            "model": self.model_name,
            "vocoder": self.vocoder_name,
            "device": self.device,
            "is_loaded": self._is_loaded,
            "available": SPEECHT5_AVAILABLE
        }
        
        if self._is_loaded and self.model and self.vocoder:
            try:
                # Test with dummy text
                test_text = "Hello"
                inputs = self.processor(text=test_text, return_tensors="pt")
                input_ids = inputs["input_ids"].to(self.device)
                
                with torch.no_grad():
                    _ = self.model.generate_speech(
                        input_ids,
                        self.speaker_embeddings,
                        vocoder=self.vocoder
                    )
                
                status["status"] = "healthy"
                status["last_check"] = "success"
                
            except Exception as e:
                status["status"] = "unhealthy"
                status["error"] = str(e)
        else:
            status["status"] = "not_loaded"
        
        return status
