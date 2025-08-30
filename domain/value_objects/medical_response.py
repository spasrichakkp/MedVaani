"""Medical response value objects for diagnosis results."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class UrgencyLevel(Enum):
    """Urgency levels for medical responses."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EMERGENCY = "emergency"


@dataclass(frozen=True)
class Recommendation:
    """A medical recommendation."""
    text: str
    category: str = "general"
    priority: int = 1  # 1 = highest priority


@dataclass(frozen=True)
class RedFlag:
    """A red flag warning in medical diagnosis."""
    warning: str
    severity: str = "warning"  # warning, danger, critical


@dataclass
class MedicalResponse:
    """
    Value object representing a medical diagnosis response.
    
    Contains the AI's analysis, recommendations, and metadata
    about the diagnostic process.
    """
    
    response_text: str
    confidence: float
    urgency: UrgencyLevel
    recommendations: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    model_used: str = "unknown"
    processing_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate response data after creation."""
        if not self.response_text.strip():
            raise ValueError("Response text cannot be empty")
        
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
    
    @classmethod
    def create_from_text(
        cls,
        text: str,
        confidence: float = 0.5,
        urgency: UrgencyLevel = UrgencyLevel.MODERATE,
        model_used: str = "unknown"
    ) -> "MedicalResponse":
        """Create a MedicalResponse from basic text."""
        return cls(
            response_text=text.strip(),
            confidence=confidence,
            urgency=urgency,
            model_used=model_used
        )
    
    @property
    def is_emergency(self) -> bool:
        """Check if this is an emergency response."""
        return self.urgency == UrgencyLevel.HIGH or self.urgency == UrgencyLevel.EMERGENCY
    
    @property
    def has_red_flags(self) -> bool:
        """Check if response has red flags."""
        return len(self.red_flags) > 0
    
    def add_recommendation(self, recommendation: str, category: str = "general") -> None:
        """Add a recommendation to the response."""
        if recommendation.strip() and recommendation not in self.recommendations:
            self.recommendations.append(recommendation.strip())
    
    def add_red_flag(self, warning: str, severity: str = "warning") -> None:
        """Add a red flag warning to the response."""
        if warning.strip() and warning not in self.red_flags:
            self.red_flags.append(warning.strip())
    
    def to_patient_friendly_text(self) -> str:
        """Convert to patient-friendly text format."""
        lines = []
        
        # Main response
        lines.append(self.response_text)
        lines.append("")
        
        # Urgency indicator
        if self.urgency == UrgencyLevel.EMERGENCY:
            lines.append("🚨 **EMERGENCY**: Seek immediate medical attention!")
        elif self.urgency == UrgencyLevel.HIGH:
            lines.append("⚠️ **HIGH PRIORITY**: Please consult a healthcare provider soon.")
        elif self.urgency == UrgencyLevel.MODERATE:
            lines.append("📋 **MODERATE**: Consider consulting a healthcare provider.")
        else:
            lines.append("ℹ️ **LOW PRIORITY**: Monitor symptoms and seek care if they worsen.")
        
        lines.append("")
        
        # Recommendations
        if self.recommendations:
            lines.append("**Recommendations:**")
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        
        # Red flags
        if self.red_flags:
            lines.append("**⚠️ Important Warnings:**")
            for flag in self.red_flags:
                lines.append(f"• {flag}")
            lines.append("")
        
        # Confidence and disclaimer
        confidence_pct = int(self.confidence * 100)
        lines.append(f"**Confidence Level**: {confidence_pct}%")
        lines.append("")
        lines.append("**Disclaimer**: This is an AI-generated assessment and should not replace professional medical advice. Always consult with a qualified healthcare provider for proper diagnosis and treatment.")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "response_text": self.response_text,
            "confidence": self.confidence,
            "urgency": self.urgency.value,
            "is_emergency": self.is_emergency,
            "recommendations": self.recommendations,
            "red_flags": self.red_flags,
            "model_used": self.model_used,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "has_red_flags": self.has_red_flags
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the medical response."""
        return {
            "urgency": self.urgency.value,
            "confidence": self.confidence,
            "is_emergency": self.is_emergency,
            "recommendation_count": len(self.recommendations),
            "red_flag_count": len(self.red_flags),
            "model_used": self.model_used,
            "processing_time_ms": self.processing_time_ms
        }
    
    def __str__(self) -> str:
        """String representation of medical response."""
        return f"MedicalResponse(urgency={self.urgency.value}, confidence={self.confidence:.2f}, emergency={self.is_emergency})"


@dataclass
class DiagnosisResult:
    """Extended diagnosis result with additional medical information."""
    
    medical_response: MedicalResponse
    differential_diagnoses: List[str] = field(default_factory=list)
    suggested_tests: List[str] = field(default_factory=list)
    drug_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    
    def add_differential_diagnosis(self, diagnosis: str, probability: float = None) -> None:
        """Add a differential diagnosis."""
        if diagnosis.strip() and diagnosis not in self.differential_diagnoses:
            self.differential_diagnoses.append(diagnosis.strip())
    
    def add_suggested_test(self, test: str) -> None:
        """Add a suggested medical test."""
        if test.strip() and test not in self.suggested_tests:
            self.suggested_tests.append(test.strip())
    
    def add_drug_recommendation(self, drug_info: Dict[str, Any]) -> None:
        """Add a drug recommendation."""
        if drug_info and drug_info not in self.drug_recommendations:
            self.drug_recommendations.append(drug_info)
    
    def add_follow_up_question(self, question: str) -> None:
        """Add a follow-up question."""
        if question.strip() and question not in self.follow_up_questions:
            self.follow_up_questions.append(question.strip())
    
    def to_comprehensive_text(self) -> str:
        """Convert to comprehensive text format."""
        lines = []
        
        # Main medical response
        lines.append(self.medical_response.to_patient_friendly_text())
        lines.append("")
        
        # Differential diagnoses
        if self.differential_diagnoses:
            lines.append("**Possible Conditions:**")
            for i, diagnosis in enumerate(self.differential_diagnoses, 1):
                lines.append(f"{i}. {diagnosis}")
            lines.append("")
        
        # Drug recommendations
        if self.drug_recommendations:
            lines.append("**Medication Suggestions:**")
            for drug in self.drug_recommendations:
                drug_name = drug.get('generic_name', 'Unknown')
                brands = drug.get('brand_names', [])
                cost = drug.get('cost_range', 'Cost not available')
                
                lines.append(f"• **{drug_name}**")
                if brands:
                    lines.append(f"  - Brands: {', '.join(brands[:3])}")
                lines.append(f"  - Cost: {cost}")
                lines.append("")
        
        # Suggested tests
        if self.suggested_tests:
            lines.append("**Suggested Tests:**")
            for test in self.suggested_tests:
                lines.append(f"• {test}")
            lines.append("")
        
        # Follow-up questions
        if self.follow_up_questions:
            lines.append("**Follow-up Questions:**")
            for question in self.follow_up_questions:
                lines.append(f"• {question}")
            lines.append("")
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        """String representation of diagnosis result."""
        return f"DiagnosisResult(urgency={self.medical_response.urgency.value}, diagnoses={len(self.differential_diagnoses)})"
