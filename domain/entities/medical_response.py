"""Medical response entity for AI-generated medical advice."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class UrgencyLevel(Enum):
    """Urgency levels for medical responses."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EMERGENCY = "emergency"


class ConfidenceLevel(Enum):
    """Confidence levels for medical AI responses."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class MedicalResponse:
    """
    Medical response entity representing AI-generated medical advice.
    
    This entity encapsulates the medical AI's analysis, recommendations,
    and metadata about the response quality and urgency.
    """
    
    id: str
    text: str
    confidence: float  # 0.0 to 1.0
    urgency: UrgencyLevel
    primary_diagnosis: Optional[str] = None
    differential_diagnoses: List[str] = None
    recommendations: List[str] = None
    red_flags: List[str] = None
    follow_up_required: bool = False
    follow_up_timeframe: Optional[str] = None
    model_used: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.differential_diagnoses is None:
            self.differential_diagnoses = []
        if self.recommendations is None:
            self.recommendations = []
        if self.red_flags is None:
            self.red_flags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    def create_from_text(
        cls,
        text: str,
        confidence: float = 0.5,
        urgency: UrgencyLevel = UrgencyLevel.MODERATE,
        model_used: Optional[str] = None
    ) -> "MedicalResponse":
        """Create a medical response from text with default values."""
        return cls(
            id=f"response_{uuid.uuid4().hex[:8]}",
            text=text,
            confidence=confidence,
            urgency=urgency,
            model_used=model_used,
            created_at=datetime.now()
        )
    
    def get_confidence_level(self) -> ConfidenceLevel:
        """Get confidence level enum based on confidence score."""
        if self.confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif self.confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            return ConfidenceLevel.MODERATE
        elif self.confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def is_emergency(self) -> bool:
        """Check if this response indicates an emergency."""
        return self.urgency == UrgencyLevel.EMERGENCY
    
    def requires_immediate_attention(self) -> bool:
        """Check if response requires immediate medical attention."""
        return self.urgency in [UrgencyLevel.HIGH, UrgencyLevel.EMERGENCY]
    
    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation to the response."""
        if recommendation and recommendation not in self.recommendations:
            self.recommendations.append(recommendation)
    
    def add_red_flag(self, red_flag: str) -> None:
        """Add a red flag warning to the response."""
        if red_flag and red_flag not in self.red_flags:
            self.red_flags.append(red_flag)
    
    def set_follow_up(self, required: bool, timeframe: Optional[str] = None) -> None:
        """Set follow-up requirements."""
        self.follow_up_required = required
        self.follow_up_timeframe = timeframe
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the medical response."""
        return {
            "id": self.id,
            "confidence": self.confidence,
            "confidence_level": self.get_confidence_level().value,
            "urgency": self.urgency.value,
            "is_emergency": self.is_emergency(),
            "requires_immediate_attention": self.requires_immediate_attention(),
            "follow_up_required": self.follow_up_required,
            "follow_up_timeframe": self.follow_up_timeframe,
            "num_recommendations": len(self.recommendations),
            "num_red_flags": len(self.red_flags),
            "model_used": self.model_used,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat()
        }
    
    def to_patient_friendly_text(self) -> str:
        """Convert response to patient-friendly text."""
        parts = [self.text]
        
        if self.recommendations:
            parts.append("\nRecommendations:")
            for rec in self.recommendations:
                parts.append(f"• {rec}")
        
        if self.red_flags:
            parts.append("\n⚠️ Important warnings:")
            for flag in self.red_flags:
                parts.append(f"• {flag}")
        
        if self.follow_up_required:
            follow_up_text = f"\nPlease follow up with a healthcare provider"
            if self.follow_up_timeframe:
                follow_up_text += f" within {self.follow_up_timeframe}"
            parts.append(follow_up_text)
        
        return "\n".join(parts)
    
    def __str__(self) -> str:
        """String representation of medical response."""
        return f"MedicalResponse(id={self.id}, urgency={self.urgency.value}, confidence={self.confidence:.2f})"
