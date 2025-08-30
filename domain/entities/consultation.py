"""Consultation entity for medical consultations."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

from .patient import Patient
from .medical_response import MedicalResponse
from ..value_objects.audio_data import AudioData


class ConsultationStatus(Enum):
    """Status of a medical consultation."""
    CREATED = "created"
    AUDIO_CAPTURED = "audio_captured"
    TRANSCRIBED = "transcribed"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    RESPONSE_GENERATED = "response_generated"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ConsultationType(Enum):
    """Type of medical consultation."""
    VOICE_TO_VOICE = "voice_to_voice"
    TEXT_TO_VOICE = "text_to_voice"
    TEXT_TO_TEXT = "text_to_text"
    VOICE_TO_TEXT = "voice_to_text"


@dataclass
class Consultation:
    """
    Consultation entity representing a complete medical consultation session.
    
    This is the main aggregate root that orchestrates the entire consultation
    workflow from patient input to medical response.
    """
    
    id: str
    patient: Patient
    consultation_type: ConsultationType
    status: ConsultationStatus = ConsultationStatus.CREATED
    symptoms_text: Optional[str] = None
    audio_input: Optional[AudioData] = None
    transcription: Optional[str] = None
    medical_response: Optional[MedicalResponse] = None
    audio_response: Optional[AudioData] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    processing_steps: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create_voice_consultation(cls, patient: Patient) -> "Consultation":
        """Create a new voice-to-voice consultation."""
        return cls(
            id=f"consult_{uuid.uuid4().hex[:8]}",
            patient=patient,
            consultation_type=ConsultationType.VOICE_TO_VOICE,
            status=ConsultationStatus.CREATED
        )
    
    @classmethod
    def create_text_consultation(cls, patient: Patient, symptoms: str) -> "Consultation":
        """Create a new text-based consultation."""
        consultation = cls(
            id=f"consult_{uuid.uuid4().hex[:8]}",
            patient=patient,
            consultation_type=ConsultationType.TEXT_TO_VOICE,
            status=ConsultationStatus.TRANSCRIBED,
            symptoms_text=symptoms,
            transcription=symptoms
        )
        consultation._update_status(ConsultationStatus.TRANSCRIBED)
        return consultation
    
    def set_audio_input(self, audio: AudioData) -> None:
        """Set the audio input for the consultation."""
        self.audio_input = audio
        self._update_status(ConsultationStatus.AUDIO_CAPTURED)
        self._add_processing_step("audio_captured", "Audio input captured successfully")
    
    def set_transcription(self, text: str) -> None:
        """Set the transcription of the audio input."""
        self.transcription = text
        self.symptoms_text = text
        self._update_status(ConsultationStatus.TRANSCRIBED)
        self._add_processing_step("transcribed", f"Audio transcribed: '{text[:50]}...'")
    
    def start_analysis(self) -> None:
        """Mark consultation as being analyzed."""
        self._update_status(ConsultationStatus.ANALYZING)
        self._add_processing_step("analysis_started", "Medical analysis started")
    
    def set_medical_response(self, response: MedicalResponse) -> None:
        """Set the medical response for the consultation."""
        self.medical_response = response
        self._update_status(ConsultationStatus.ANALYZED)
        self._add_processing_step("analysis_completed", 
                                f"Medical analysis completed with {response.urgency.value} urgency")
    
    def set_audio_response(self, audio: AudioData) -> None:
        """Set the audio response for the consultation."""
        self.audio_response = audio
        self._update_status(ConsultationStatus.RESPONSE_GENERATED)
        self._add_processing_step("audio_response_generated", "Audio response generated")
    
    def complete(self) -> None:
        """Mark consultation as completed."""
        self._update_status(ConsultationStatus.COMPLETED)
        self.completed_at = datetime.now()
        self._add_processing_step("completed", "Consultation completed successfully")
    
    def fail(self, error_message: str) -> None:
        """Mark consultation as failed with error message."""
        self.error_message = error_message
        self._update_status(ConsultationStatus.FAILED)
        self._add_processing_step("failed", f"Consultation failed: {error_message}")
    
    def cancel(self, reason: str = "User cancelled") -> None:
        """Cancel the consultation."""
        self.error_message = reason
        self._update_status(ConsultationStatus.CANCELLED)
        self._add_processing_step("cancelled", reason)
    
    def _update_status(self, new_status: ConsultationStatus) -> None:
        """Update consultation status and timestamp."""
        self.status = new_status
        self.updated_at = datetime.now()
    
    def _add_processing_step(self, step_name: str, description: str) -> None:
        """Add a processing step to the consultation history."""
        step = {
            "step": step_name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "status": self.status.value
        }
        self.processing_steps.append(step)
    
    def get_duration_seconds(self) -> Optional[float]:
        """Get consultation duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None
    
    def is_completed(self) -> bool:
        """Check if consultation is completed."""
        return self.status == ConsultationStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if consultation failed."""
        return self.status == ConsultationStatus.FAILED
    
    def is_in_progress(self) -> bool:
        """Check if consultation is in progress."""
        return self.status not in [
            ConsultationStatus.COMPLETED,
            ConsultationStatus.FAILED,
            ConsultationStatus.CANCELLED
        ]
    
    def requires_emergency_attention(self) -> bool:
        """Check if consultation indicates emergency."""
        return (self.medical_response and 
                self.medical_response.is_emergency())
    
    def get_summary(self) -> Dict[str, Any]:
        """Get consultation summary."""
        summary = {
            "id": self.id,
            "patient_id": self.patient.id,
            "type": self.consultation_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "duration_seconds": self.get_duration_seconds(),
            "has_audio_input": self.audio_input is not None,
            "has_transcription": bool(self.transcription),
            "has_medical_response": self.medical_response is not None,
            "has_audio_response": self.audio_response is not None,
            "processing_steps_count": len(self.processing_steps),
            "error_message": self.error_message
        }
        
        if self.medical_response:
            summary["medical_response"] = self.medical_response.get_summary()
        
        return summary
    
    def __str__(self) -> str:
        """String representation of consultation."""
        return f"Consultation(id={self.id}, status={self.status.value}, type={self.consultation_type.value})"
