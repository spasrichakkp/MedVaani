"""Patient entity for medical consultations."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


@dataclass
class Patient:
    """
    Patient entity representing a person seeking medical consultation.
    
    This is a core domain entity that encapsulates patient information
    and business rules related to patient data.
    """
    
    id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_history: List[str] = None
    current_medications: List[str] = None
    allergies: List[str] = None
    emergency_contact: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.medical_history is None:
            self.medical_history = []
        if self.current_medications is None:
            self.current_medications = []
        if self.allergies is None:
            self.allergies = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    @classmethod
    def create_anonymous(cls) -> "Patient":
        """Create an anonymous patient for consultations without personal data."""
        return cls(
            id=f"anon_{uuid.uuid4().hex[:8]}",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def add_medical_history_item(self, condition: str) -> None:
        """Add a medical history item to the patient."""
        if condition and condition not in self.medical_history:
            self.medical_history.append(condition)
            self.updated_at = datetime.now()
    
    def add_medication(self, medication: str) -> None:
        """Add a current medication to the patient."""
        if medication and medication not in self.current_medications:
            self.current_medications.append(medication)
            self.updated_at = datetime.now()
    
    def add_allergy(self, allergy: str) -> None:
        """Add an allergy to the patient."""
        if allergy and allergy not in self.allergies:
            self.allergies.append(allergy)
            self.updated_at = datetime.now()
    
    def has_drug_allergy(self, drug: str) -> bool:
        """Check if patient has an allergy to a specific drug."""
        return any(drug.lower() in allergy.lower() for allergy in self.allergies)
    
    def get_context_for_analysis(self) -> Dict[str, Any]:
        """Get patient context for medical analysis."""
        return {
            "age": self.age,
            "gender": self.gender,
            "medical_history": self.medical_history,
            "current_medications": self.current_medications,
            "allergies": self.allergies,
            "has_medical_history": len(self.medical_history) > 0,
            "has_medications": len(self.current_medications) > 0,
            "has_allergies": len(self.allergies) > 0
        }
    
    def is_high_risk(self) -> bool:
        """Determine if patient is high-risk based on medical history."""
        high_risk_conditions = [
            "diabetes", "heart disease", "hypertension", "cancer",
            "kidney disease", "liver disease", "copd", "asthma"
        ]
        
        return any(
            any(condition.lower() in history_item.lower() 
                for condition in high_risk_conditions)
            for history_item in self.medical_history
        )
    
    def __str__(self) -> str:
        """String representation of patient."""
        return f"Patient(id={self.id}, age={self.age}, gender={self.gender})"
