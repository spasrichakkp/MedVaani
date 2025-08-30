"""Mock adapters to enable demos without heavy model downloads/deps."""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from application.ports.voice_interface_port import VoiceInterfacePort
from application.ports.medical_model_port import MedicalModelPort
from application.ports.audio_repository_port import AudioRepositoryPort
from domain.value_objects.audio_data import AudioData
from domain.value_objects.medical_symptoms import MedicalSymptoms
from domain.entities.medical_response import MedicalResponse, UrgencyLevel
from infrastructure.logging.logger_factory import get_module_logger


class MockVoiceAdapter(VoiceInterfacePort):
    def __init__(self):
        self.logger = get_module_logger(__name__)

    async def transcribe_audio(self, audio: AudioData) -> Optional[str]:
        await asyncio.sleep(0.05)
        return "this is a mock transcription"

    async def synthesize_speech(self, text: str, voice_config: Optional[Dict[str, Any]] = None) -> Optional[AudioData]:
        await asyncio.sleep(0.05)
        return AudioData.silence(1.5, 16000)

    async def validate_audio_quality(self, audio: AudioData) -> bool:
        return True

    async def record_audio(self, duration_seconds: float) -> Optional[AudioData]:
        await asyncio.sleep(0.05)
        return AudioData.silence(duration_seconds, 16000)

    async def play_audio(self, audio: AudioData) -> bool:
        await asyncio.sleep(0.01)
        return True

    async def get_supported_languages(self) -> list[str]:
        return ["en"]

    async def detect_language(self, audio: AudioData) -> Optional[str]:
        return "en"

    async def get_transcription_confidence(self, audio: AudioData) -> float:
        return 0.9

    async def enhance_audio_quality(self, audio: AudioData) -> AudioData:
        return audio

    async def is_available(self) -> bool:
        return True

    async def get_health_status(self) -> Dict[str, Any]:
        return {"status": "healthy", "service": "mock_voice"}


class MockMedicalAdapter(MedicalModelPort):
    def __init__(self):
        self.logger = get_module_logger(__name__)

    async def analyze_symptoms(self, symptoms: MedicalSymptoms, patient_context=None) -> MedicalResponse:
        await asyncio.sleep(0.05)
        urgency = UrgencyLevel.EMERGENCY if symptoms.has_emergency_symptoms() else UrgencyLevel.MODERATE
        return MedicalResponse.create_from_text(
            "This is a mock medical assessment. Please consult a doctor if symptoms persist.",
            confidence=0.8,
            urgency=urgency,
            model_used="mock_medical"
        )

    async def check_drug_interactions(self, medications: List[str], patient_context=None) -> Dict[str, Any]:
        await asyncio.sleep(0.02)
        return {"medications": medications, "interactions": [], "warnings": []}

    async def generate_differential_diagnosis(self, symptoms: MedicalSymptoms, patient_context=None) -> List[Dict[str, Any]]:
        await asyncio.sleep(0.02)
        return [{"diagnosis": "Mock Condition", "probability": 0.5}]

    async def assess_urgency(self, symptoms: MedicalSymptoms, patient_context=None) -> Dict[str, Any]:
        await asyncio.sleep(0.02)
        return {"urgency": "moderate"}

    async def generate_treatment_recommendations(self, diagnosis: str, symptoms: MedicalSymptoms, patient_context=None) -> List[str]:
        await asyncio.sleep(0.02)
        return ["Rest", "Hydration"]

    async def identify_red_flags(self, symptoms: MedicalSymptoms, patient_context=None) -> List[str]:
        await asyncio.sleep(0.02)
        return ["Mock red flag"] if symptoms.has_emergency_symptoms() else []

    async def summarize_clinical_note(self, clinical_text: str) -> str:
        await asyncio.sleep(0.02)
        return clinical_text[:100]

    async def extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        return {"symptoms": ["headache" if "headache" in text.lower() else ""]}

    async def get_model_confidence(self, analysis_result: Any) -> float:
        return 0.8

    async def is_model_available(self) -> bool:
        return True

    async def get_model_info(self) -> Dict[str, Any]:
        return {"name": "mock_medical", "is_loaded": True}

    async def warm_up_model(self) -> bool:
        return True

