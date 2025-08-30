"""Medical symptoms value object for symptom analysis."""

from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from enum import Enum
import re


class SymptomSeverity(Enum):
    """Severity levels for medical symptoms."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class SymptomCategory(Enum):
    """Categories of medical symptoms."""
    PAIN = "pain"
    RESPIRATORY = "respiratory"
    CARDIOVASCULAR = "cardiovascular"
    NEUROLOGICAL = "neurological"
    GASTROINTESTINAL = "gastrointestinal"
    DERMATOLOGICAL = "dermatological"
    MUSCULOSKELETAL = "musculoskeletal"
    PSYCHOLOGICAL = "psychological"
    GENERAL = "general"
    OTHER = "other"


@dataclass(frozen=True)
class MedicalSymptoms:
    """
    Immutable value object representing medical symptoms.
    
    This value object encapsulates patient symptoms and provides
    methods for analysis and categorization.
    """
    
    raw_text: str
    extracted_symptoms: List[str]
    severity_indicators: Dict[str, SymptomSeverity]
    duration_indicators: Dict[str, str]
    location_indicators: Dict[str, str]
    
    def __post_init__(self):
        """Validate symptoms data after creation."""
        if not self.raw_text.strip():
            raise ValueError("Raw text cannot be empty")
        
        # Ensure extracted symptoms is not empty
        if not self.extracted_symptoms:
            # Try to extract basic symptoms from raw text
            basic_symptoms = self._extract_basic_symptoms(self.raw_text)
            object.__setattr__(self, 'extracted_symptoms', basic_symptoms)
    
    @classmethod
    def from_text(cls, text: str) -> "MedicalSymptoms":
        """Create MedicalSymptoms from raw text input."""
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Extract symptoms and metadata
        symptoms = cls._extract_basic_symptoms(text)
        severity = cls._extract_severity_indicators(text, symptoms)
        duration = cls._extract_duration_indicators(text, symptoms)
        location = cls._extract_location_indicators(text, symptoms)
        
        return cls(
            raw_text=text.strip(),
            extracted_symptoms=symptoms,
            severity_indicators=severity,
            duration_indicators=duration,
            location_indicators=location
        )
    
    @staticmethod
    def _extract_basic_symptoms(text: str) -> List[str]:
        """Extract basic symptoms from text."""
        # Common symptom keywords
        symptom_patterns = [
            r'\b(?:chest|heart)\s+pain\b',
            r'\bshortness\s+of\s+breath\b',
            r'\bdifficulty\s+breathing\b',
            r'\bheadache\b',
            r'\bnausea\b',
            r'\bvomiting\b',
            r'\bfever\b',
            r'\bchills\b',
            r'\bdizziness\b',
            r'\bfatigue\b',
            r'\bweakness\b',
            r'\bcough\b',
            r'\bsore\s+throat\b',
            r'\babdominal\s+pain\b',
            r'\bstomach\s+pain\b',
            r'\bback\s+pain\b',
            r'\bjoint\s+pain\b',
            r'\bmuscle\s+pain\b',
            r'\brash\b',
            r'\bswelling\b',
            r'\bnumbness\b',
            r'\btingling\b',
            r'\bblurred\s+vision\b',
            r'\bconfusion\b',
            r'\bpalpitations\b'
        ]
        
        symptoms = []
        text_lower = text.lower()
        
        for pattern in symptom_patterns:
            matches = re.findall(pattern, text_lower)
            symptoms.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_symptoms = []
        for symptom in symptoms:
            if symptom not in seen:
                seen.add(symptom)
                unique_symptoms.append(symptom)
        
        return unique_symptoms
    
    @staticmethod
    def _extract_severity_indicators(text: str, symptoms: List[str]) -> Dict[str, SymptomSeverity]:
        """Extract severity indicators for symptoms."""
        severity_map = {}
        text_lower = text.lower()
        
        # Severity keywords
        severe_keywords = ['severe', 'intense', 'excruciating', 'unbearable', 'worst']
        moderate_keywords = ['moderate', 'significant', 'noticeable', 'concerning']
        mild_keywords = ['mild', 'slight', 'minor', 'little']
        critical_keywords = ['critical', 'emergency', 'life-threatening', 'urgent']
        
        for symptom in symptoms:
            # Look for severity indicators near the symptom
            symptom_context = MedicalSymptoms._get_symptom_context(text_lower, symptom)
            
            if any(keyword in symptom_context for keyword in critical_keywords):
                severity_map[symptom] = SymptomSeverity.CRITICAL
            elif any(keyword in symptom_context for keyword in severe_keywords):
                severity_map[symptom] = SymptomSeverity.SEVERE
            elif any(keyword in symptom_context for keyword in moderate_keywords):
                severity_map[symptom] = SymptomSeverity.MODERATE
            elif any(keyword in symptom_context for keyword in mild_keywords):
                severity_map[symptom] = SymptomSeverity.MILD
            else:
                severity_map[symptom] = SymptomSeverity.MODERATE  # Default
        
        return severity_map
    
    @staticmethod
    def _extract_duration_indicators(text: str, symptoms: List[str]) -> Dict[str, str]:
        """Extract duration indicators for symptoms."""
        duration_map = {}
        text_lower = text.lower()
        
        # Duration patterns
        duration_patterns = [
            r'for\s+(\d+)\s+(minutes?|hours?|days?|weeks?|months?)',
            r'since\s+(yesterday|today|this\s+morning|last\s+week)',
            r'(\d+)\s+(minutes?|hours?|days?|weeks?|months?)\s+ago',
            r'(sudden|suddenly|gradual|gradually)',
            r'(chronic|acute|persistent|intermittent)'
        ]
        
        for symptom in symptoms:
            symptom_context = MedicalSymptoms._get_symptom_context(text_lower, symptom)
            
            for pattern in duration_patterns:
                matches = re.findall(pattern, symptom_context)
                if matches:
                    duration_map[symptom] = ' '.join(matches[0]) if isinstance(matches[0], tuple) else matches[0]
                    break
        
        return duration_map
    
    @staticmethod
    def _extract_location_indicators(text: str, symptoms: List[str]) -> Dict[str, str]:
        """Extract location indicators for symptoms."""
        location_map = {}
        text_lower = text.lower()
        
        # Location keywords
        location_keywords = [
            'left', 'right', 'center', 'upper', 'lower', 'front', 'back',
            'chest', 'abdomen', 'head', 'neck', 'arm', 'leg', 'hand', 'foot'
        ]
        
        for symptom in symptoms:
            symptom_context = MedicalSymptoms._get_symptom_context(text_lower, symptom)
            
            found_locations = [loc for loc in location_keywords if loc in symptom_context]
            if found_locations:
                location_map[symptom] = ', '.join(found_locations)
        
        return location_map
    
    @staticmethod
    def _get_symptom_context(text: str, symptom: str, context_words: int = 10) -> str:
        """Get context around a symptom in text."""
        words = text.split()
        symptom_words = symptom.split()
        
        # Find symptom position
        for i in range(len(words) - len(symptom_words) + 1):
            if words[i:i+len(symptom_words)] == symptom_words:
                start = max(0, i - context_words)
                end = min(len(words), i + len(symptom_words) + context_words)
                return ' '.join(words[start:end])
        
        return text  # Return full text if symptom not found
    
    def get_symptom_categories(self) -> Dict[str, SymptomCategory]:
        """Categorize symptoms by medical category."""
        categories = {}
        
        # Symptom category mapping
        category_keywords = {
            SymptomCategory.PAIN: ['pain', 'ache', 'hurt', 'sore'],
            SymptomCategory.RESPIRATORY: ['breath', 'breathing', 'cough', 'wheeze'],
            SymptomCategory.CARDIOVASCULAR: ['chest pain', 'heart', 'palpitations'],
            SymptomCategory.NEUROLOGICAL: ['headache', 'dizziness', 'numbness', 'confusion'],
            SymptomCategory.GASTROINTESTINAL: ['nausea', 'vomiting', 'abdominal', 'stomach'],
            SymptomCategory.MUSCULOSKELETAL: ['joint', 'muscle', 'back pain'],
            SymptomCategory.GENERAL: ['fever', 'fatigue', 'weakness', 'chills']
        }
        
        for symptom in self.extracted_symptoms:
            categorized = False
            for category, keywords in category_keywords.items():
                if any(keyword in symptom.lower() for keyword in keywords):
                    categories[symptom] = category
                    categorized = True
                    break
            
            if not categorized:
                categories[symptom] = SymptomCategory.OTHER
        
        return categories
    
    def get_high_severity_symptoms(self) -> List[str]:
        """Get symptoms with high severity."""
        return [
            symptom for symptom, severity in self.severity_indicators.items()
            if severity in [SymptomSeverity.SEVERE, SymptomSeverity.CRITICAL]
        ]
    
    def has_emergency_symptoms(self) -> bool:
        """Check if any symptoms indicate emergency."""
        emergency_keywords = [
            'chest pain', 'difficulty breathing', 'shortness of breath',
            'severe headache', 'confusion', 'loss of consciousness'
        ]
        
        text_lower = self.raw_text.lower()
        return any(keyword in text_lower for keyword in emergency_keywords)
    
    def get_symptom_summary(self) -> Dict[str, any]:
        """Get a summary of the symptoms."""
        categories = self.get_symptom_categories()
        high_severity = self.get_high_severity_symptoms()
        
        return {
            "total_symptoms": len(self.extracted_symptoms),
            "symptoms": self.extracted_symptoms,
            "categories": {cat.value: [s for s, c in categories.items() if c == cat] 
                          for cat in set(categories.values())},
            "high_severity_symptoms": high_severity,
            "has_emergency_indicators": self.has_emergency_symptoms(),
            "duration_info": self.duration_indicators,
            "location_info": self.location_indicators
        }
    
    def __str__(self) -> str:
        """String representation of medical symptoms."""
        return f"MedicalSymptoms(symptoms={len(self.extracted_symptoms)}, emergency={self.has_emergency_symptoms()})"
