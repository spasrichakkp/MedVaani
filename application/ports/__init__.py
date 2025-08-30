"""Port interfaces for external dependencies."""

from .voice_interface_port import VoiceInterfacePort
from .medical_model_port import MedicalModelPort
from .audio_repository_port import AudioRepositoryPort
from .configuration_port import ConfigurationPort

__all__ = [
    "VoiceInterfacePort",
    "MedicalModelPort", 
    "AudioRepositoryPort",
    "ConfigurationPort"
]
