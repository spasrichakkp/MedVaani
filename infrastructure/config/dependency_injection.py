"""Dependency injection container for the medical research application."""

from typing import Optional
from pathlib import Path
import os


# Note: dependency-injector will be installed as part of requirements
# For now, we'll create a simple manual DI container
from .app_config import AppConfig
from ..logging.logger_factory import LoggerFactory, initialize_logging
from ..logging.log_config import LogConfig
from ..adapters.whisper_adapter import WhisperAdapter
from ..adapters.speecht5_adapter import SpeechT5Adapter
from ..adapters.meerkat_adapter import MeerkatAdapter
from ..adapters.filesystem_audio_repository import FileSystemAudioRepository
from ..adapters.composite_voice_interface import CompositeVoiceInterface
from ..adapters.mock_adapters import MockVoiceAdapter, MockMedicalAdapter
from application.use_cases.voice_consultation_use_case import VoiceConsultationUseCase
from application.use_cases.medical_analysis_use_case import MedicalAnalysisUseCase


class ApplicationContainer:
    """
    Dependency injection container for the medical research application.

    This container manages the creation and lifecycle of application dependencies,
    ensuring proper initialization order and configuration.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize the application container.

        Args:
            config: Application configuration, auto-detected if None
        """
        self._config = config or AppConfig.from_env()
        self._logger_factory: Optional[LoggerFactory] = None
        self._initialized = False

        # Infrastructure adapters
        self._whisper_adapter: Optional[WhisperAdapter] = None
        self._speecht5_adapter: Optional[SpeechT5Adapter] = None
        self._meerkat_adapter: Optional[MeerkatAdapter] = None
        self._audio_repository: Optional[FileSystemAudioRepository] = None
        self._voice_interface: Optional[CompositeVoiceInterface] = None

        # Use cases
        self._medical_analysis_use_case: Optional[MedicalAnalysisUseCase] = None
        self._voice_consultation_use_case: Optional[VoiceConsultationUseCase] = None

    def initialize(self) -> None:
        """Initialize all container dependencies."""
        if self._initialized:
            return

        # Validate configuration
        errors = self._config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {errors}")

        # Initialize logging
        self._setup_logging()

        # Create directories
        self._create_directories()

        self._initialized = True

    def _setup_logging(self) -> None:
        """Setup logging system."""
        log_config = self._create_log_config()
        self._logger_factory = initialize_logging(log_config)

    def _create_log_config(self) -> LogConfig:
        """Create logging configuration from app config."""
        if self._config.is_production():
            log_config = LogConfig.production()
            log_config.log_file = self._config.logs_dir / "medical_research.log"
        elif self._config.is_testing():
            log_config = LogConfig.testing()
        else:
            log_config = LogConfig.development()

        return log_config

    def _create_directories(self) -> None:
        """Create necessary directories."""
        self._config.data_dir.mkdir(parents=True, exist_ok=True)
        self._config.logs_dir.mkdir(parents=True, exist_ok=True)

        # Create voice output directory
        voice_output_dir = Path(self._config.voice.audio_output_dir)
        voice_output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def config(self) -> AppConfig:
        """Get application configuration."""
        return self._config

    @property
    def logger_factory(self) -> LoggerFactory:
        """Get logger factory."""
        if not self._initialized:
            self.initialize()

        if self._logger_factory is None:
            raise RuntimeError("Logger factory not initialized")

        return self._logger_factory

    def get_logger(self, name: str):
        """Get a logger instance."""
        return self.logger_factory.get_logger(name)

    def get_whisper_adapter(self) -> WhisperAdapter:
        """Get Whisper ASR adapter."""
        if not self._initialized:
            self.initialize()

        if self._whisper_adapter is None:
            if str(self._config.environment).lower() == "testing" or str(os.getenv("USE_MOCK_ADAPTERS", "false")).lower() == "true":
                self._whisper_adapter = MockVoiceAdapter()
            else:
                dtype_arg = os.getenv("FORCE_TORCH_DTYPE", self._config.medical.torch_dtype)
                self._whisper_adapter = WhisperAdapter(
                    model_name=os.getenv("ASR_MODEL", self._config.voice.asr_model),
                    device=os.getenv("VOICE_DEVICE", self._config.voice.device),
                    torch_dtype=dtype_arg
                )

        return self._whisper_adapter

    def get_speecht5_adapter(self) -> SpeechT5Adapter:
        """Get SpeechT5 TTS adapter."""
        if not self._initialized:
            self.initialize()

        if self._speecht5_adapter is None:
            if str(self._config.environment).lower() == "testing" or str(os.getenv("USE_MOCK_ADAPTERS", "false")).lower() == "true":
                # Reuse the mock voice adapter for TTS too
                self._speecht5_adapter = MockVoiceAdapter()
            else:
                dtype_arg = os.getenv("FORCE_TORCH_DTYPE", self._config.medical.torch_dtype)
                self._speecht5_adapter = SpeechT5Adapter(
                    model_name=os.getenv("TTS_MODEL", self._config.voice.tts_model),
                    vocoder_name=os.getenv("TTS_VOCODER", self._config.voice.tts_vocoder),
                    device=os.getenv("VOICE_DEVICE", self._config.voice.device),
                    torch_dtype=dtype_arg
                )

        return self._speecht5_adapter

    def get_meerkat_adapter(self) -> MeerkatAdapter:
        """Get Meerkat medical AI adapter."""
        if not self._initialized:
            self.initialize()

        if self._meerkat_adapter is None:
            if str(self._config.environment).lower() == "testing" and str(os.getenv("USE_MOCK_ADAPTERS", "false")).lower() == "true":
                self._meerkat_adapter = MockMedicalAdapter()
            else:
                dtype_arg = os.getenv("FORCE_TORCH_DTYPE", self._config.medical.torch_dtype)
                self._meerkat_adapter = MeerkatAdapter(
                    model_name=os.getenv("MEDICAL_MODEL", self._config.medical.reasoning_model),
                    device=os.getenv("MEDICAL_DEVICE", "cpu"),
                    torch_dtype=dtype_arg,
                    max_new_tokens=int(os.getenv("MAX_NEW_TOKENS", str(self._config.medical.max_new_tokens)))
                )

        return self._meerkat_adapter

    def get_audio_repository(self) -> FileSystemAudioRepository:
        """Get filesystem audio repository."""
        if not self._initialized:
            self.initialize()

        if self._audio_repository is None:
            audio_dir = self._config.data_dir / "audio"
            self._audio_repository = FileSystemAudioRepository(
                base_path=audio_dir,
                max_storage_gb=5.0,  # 5GB limit
                auto_cleanup_days=30
            )

        return self._audio_repository

    def get_voice_interface(self) -> CompositeVoiceInterface:
        """Get composite voice interface."""
        if not self._initialized:
            self.initialize()

        if self._voice_interface is None:
            asr_adapter = self.get_whisper_adapter()
            tts_adapter = self.get_speecht5_adapter()

            self._voice_interface = CompositeVoiceInterface(
                asr_adapter=asr_adapter,
                tts_adapter=tts_adapter,
                enable_resilience=True
            )

        return self._voice_interface

    def get_medical_analysis_use_case(self) -> MedicalAnalysisUseCase:
        """Get medical analysis use case."""
        if not self._initialized:
            self.initialize()

        if self._medical_analysis_use_case is None:
            medical_adapter = self.get_meerkat_adapter()
            self._medical_analysis_use_case = MedicalAnalysisUseCase(medical_adapter)

        return self._medical_analysis_use_case

    def get_voice_consultation_use_case(self) -> VoiceConsultationUseCase:
        """Get voice consultation use case."""
        if not self._initialized:
            self.initialize()

        if self._voice_consultation_use_case is None:
            voice_interface = self.get_voice_interface()
            medical_analysis = self.get_medical_analysis_use_case()
            audio_repository = self.get_audio_repository()

            self._voice_consultation_use_case = VoiceConsultationUseCase(
                voice_interface=voice_interface,
                medical_analysis_use_case=medical_analysis,
                audio_repository=audio_repository
            )

        return self._voice_consultation_use_case

    def shutdown(self) -> None:
        """Shutdown the container and clean up resources."""
        if self._logger_factory:
            self._logger_factory.shutdown()

        # Clear all cached instances
        self._whisper_adapter = None
        self._speecht5_adapter = None
        self._meerkat_adapter = None
        self._audio_repository = None
        self._voice_interface = None
        self._medical_analysis_use_case = None
        self._voice_consultation_use_case = None

        self._initialized = False


# Global container instance
_container: Optional[ApplicationContainer] = None


def create_container(config: Optional[AppConfig] = None) -> ApplicationContainer:
    """
    Create and initialize the application container.

    Args:
        config: Application configuration

    Returns:
        Initialized ApplicationContainer
    """
    global _container

    if _container is None:
        _container = ApplicationContainer(config)
        _container.initialize()

    return _container


def get_container() -> ApplicationContainer:
    """
    Get the global application container.

    Returns:
        ApplicationContainer instance

    Raises:
        RuntimeError: If container not initialized
    """
    global _container

    if _container is None:
        raise RuntimeError("Container not initialized. Call create_container() first.")

    return _container


def reset_container() -> None:
    """Reset the global container (useful for testing)."""
    global _container

    if _container:
        _container.shutdown()
        _container = None


# Convenience functions for dependency access
def get_config() -> AppConfig:
    """Get application configuration."""
    return get_container().config


def get_logger(name: str):
    """Get a logger instance."""
    return get_container().get_logger(name)


def get_module_logger(module_name: str):
    """Get a logger for a module."""
    return get_container().logger_factory.get_logger_for_module(module_name)
