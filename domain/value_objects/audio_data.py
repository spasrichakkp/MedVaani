"""Audio data value object for voice processing."""

from dataclasses import dataclass
from typing import List, Optional, Union
import numpy as np
from pathlib import Path


@dataclass(frozen=True)
class AudioData:
    """
    Immutable value object representing audio data.
    
    This value object encapsulates audio samples and metadata,
    providing a consistent interface for audio processing operations.
    """
    
    samples: Union[List[float], np.ndarray]
    sample_rate: int
    channels: int = 1
    duration_seconds: Optional[float] = None
    file_path: Optional[str] = None
    format: str = "wav"
    bit_depth: int = 16
    
    def __post_init__(self):
        """Validate audio data after creation."""
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be positive")
        
        if self.channels <= 0:
            raise ValueError("Number of channels must be positive")
        
        if isinstance(self.samples, list):
            # Convert list to numpy array for consistency
            object.__setattr__(self, 'samples', np.array(self.samples, dtype=np.float32))
        
        # Calculate duration if not provided
        if self.duration_seconds is None:
            duration = len(self.samples) / self.sample_rate
            object.__setattr__(self, 'duration_seconds', duration)
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "AudioData":
        """Create AudioData from an audio file."""
        try:
            import soundfile as sf
        except ImportError:
            raise ImportError("soundfile is required to load audio files")
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        samples, sample_rate = sf.read(str(file_path))
        
        # Handle stereo to mono conversion
        if len(samples.shape) > 1:
            samples = np.mean(samples, axis=1)
            channels = 1
        else:
            channels = 1
        
        return cls(
            samples=samples,
            sample_rate=sample_rate,
            channels=channels,
            file_path=str(file_path),
            format=file_path.suffix.lower().lstrip('.')
        )
    
    @classmethod
    def from_numpy(
        cls, 
        samples: np.ndarray, 
        sample_rate: int,
        channels: int = 1
    ) -> "AudioData":
        """Create AudioData from numpy array."""
        return cls(
            samples=samples,
            sample_rate=sample_rate,
            channels=channels
        )
    
    @classmethod
    def silence(cls, duration_seconds: float, sample_rate: int = 16000) -> "AudioData":
        """Create silent audio data."""
        num_samples = int(duration_seconds * sample_rate)
        samples = np.zeros(num_samples, dtype=np.float32)
        
        return cls(
            samples=samples,
            sample_rate=sample_rate,
            duration_seconds=duration_seconds
        )
    
    def get_samples_as_numpy(self) -> np.ndarray:
        """Get audio samples as numpy array."""
        if isinstance(self.samples, np.ndarray):
            return self.samples
        return np.array(self.samples, dtype=np.float32)
    
    def get_samples_as_list(self) -> List[float]:
        """Get audio samples as list."""
        if isinstance(self.samples, list):
            return self.samples
        return self.samples.tolist()
    
    def get_rms_amplitude(self) -> float:
        """Calculate RMS amplitude of the audio."""
        samples_array = self.get_samples_as_numpy()
        return float(np.sqrt(np.mean(samples_array ** 2)))
    
    def get_peak_amplitude(self) -> float:
        """Get peak amplitude of the audio."""
        samples_array = self.get_samples_as_numpy()
        return float(np.max(np.abs(samples_array)))
    
    def is_silent(self, threshold: float = 0.01) -> bool:
        """Check if audio is effectively silent."""
        return self.get_rms_amplitude() < threshold
    
    def has_sufficient_volume(self, min_rms: float = 0.02) -> bool:
        """Check if audio has sufficient volume for processing."""
        return self.get_rms_amplitude() >= min_rms
    
    def get_duration_ms(self) -> int:
        """Get duration in milliseconds."""
        return int(self.duration_seconds * 1000)
    
    def is_valid_for_processing(self) -> bool:
        """Check if audio data is valid for processing."""
        return (
            len(self.samples) > 0 and
            self.sample_rate > 0 and
            self.duration_seconds > 0.1 and  # At least 100ms
            self.has_sufficient_volume()
        )
    
    def resample(self, target_sample_rate: int) -> "AudioData":
        """Resample audio to target sample rate."""
        if self.sample_rate == target_sample_rate:
            return self
        
        try:
            import librosa
        except ImportError:
            raise ImportError("librosa is required for resampling")
        
        samples_array = self.get_samples_as_numpy()
        resampled = librosa.resample(
            samples_array, 
            orig_sr=self.sample_rate, 
            target_sr=target_sample_rate
        )
        
        return AudioData(
            samples=resampled,
            sample_rate=target_sample_rate,
            channels=self.channels,
            format=self.format,
            bit_depth=self.bit_depth
        )
    
    def trim_silence(self, threshold: float = 0.01) -> "AudioData":
        """Trim silence from beginning and end of audio."""
        samples_array = self.get_samples_as_numpy()
        
        # Find first and last non-silent samples
        non_silent = np.abs(samples_array) > threshold
        if not np.any(non_silent):
            # All silent, return minimal audio
            return AudioData.silence(0.1, self.sample_rate)
        
        first_sound = np.argmax(non_silent)
        last_sound = len(samples_array) - np.argmax(non_silent[::-1]) - 1
        
        trimmed_samples = samples_array[first_sound:last_sound + 1]
        
        return AudioData(
            samples=trimmed_samples,
            sample_rate=self.sample_rate,
            channels=self.channels,
            format=self.format,
            bit_depth=self.bit_depth
        )
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save audio data to file.

        Uses soundfile when available; falls back to standard library 'wave' for WAV files.
        """
        file_path = Path(file_path)
        samples_array = self.get_samples_as_numpy()

        # Prefer soundfile if available
        try:
            import soundfile as sf
            sf.write(str(file_path), samples_array, self.sample_rate)
            return
        except Exception:
            # Fall back to wave for WAV files
            if file_path.suffix.lower() == ".wav":
                import wave
                import struct
                # Convert float32 [-1.0,1.0] to int16
                clipped = np.clip(samples_array, -1.0, 1.0)
                int16_samples = (clipped * 32767.0).astype(np.int16)

                with wave.open(str(file_path), 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)  # 16-bit PCM
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(int16_samples.tobytes())
                return
            else:
                raise ImportError("soundfile is required to save non-WAV audio files")
    
    def __len__(self) -> int:
        """Get number of samples."""
        return len(self.samples)
    
    def __str__(self) -> str:
        """String representation of audio data."""
        return (f"AudioData(duration={self.duration_seconds:.2f}s, "
                f"sample_rate={self.sample_rate}Hz, "
                f"channels={self.channels}, "
                f"samples={len(self.samples)})")
    
    def __eq__(self, other) -> bool:
        """Check equality with another AudioData object."""
        if not isinstance(other, AudioData):
            return False
        
        return (
            np.array_equal(self.get_samples_as_numpy(), other.get_samples_as_numpy()) and
            self.sample_rate == other.sample_rate and
            self.channels == other.channels
        )
