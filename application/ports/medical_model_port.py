"""Port interface for medical AI model operations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from domain.value_objects.medical_response import MedicalResponse
from domain.entities.patient import Patient
from domain.value_objects.medical_symptoms import MedicalSymptoms


class MedicalAnalysisError(Exception):
    """Exception raised when medical analysis fails."""
    pass


class DrugInteractionError(Exception):
    """Exception raised when drug interaction analysis fails."""
    pass


class MedicalModelPort(ABC):
    """
    Port interface for medical AI model operations.
    
    This interface defines the contract for medical AI operations
    including symptom analysis, diagnosis, and treatment recommendations.
    """
    
    @abstractmethod
    async def analyze_symptoms(
        self, 
        symptoms: MedicalSymptoms, 
        patient_context: Optional[Patient] = None
    ) -> MedicalResponse:
        """
        Analyze patient symptoms and provide medical insights.
        
        Args:
            symptoms: MedicalSymptoms object containing patient symptoms
            patient_context: Optional patient information for context
            
        Returns:
            MedicalResponse containing analysis and recommendations
            
        Raises:
            MedicalAnalysisError: If analysis fails
        """
        pass
    
    @abstractmethod
    async def check_drug_interactions(
        self, 
        medications: List[str], 
        patient_context: Optional[Patient] = None
    ) -> Dict[str, Any]:
        """
        Check for drug interactions and contraindications.
        
        Args:
            medications: List of medication names
            patient_context: Optional patient information for context
            
        Returns:
            Dictionary containing interaction analysis
            
        Raises:
            DrugInteractionError: If analysis fails
        """
        pass
    
    @abstractmethod
    async def generate_differential_diagnosis(
        self, 
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate differential diagnosis list.
        
        Args:
            symptoms: MedicalSymptoms object
            patient_context: Optional patient information
            
        Returns:
            List of possible diagnoses with probabilities
        """
        pass
    
    @abstractmethod
    async def assess_urgency(
        self, 
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None
    ) -> Dict[str, Any]:
        """
        Assess urgency level of patient condition.
        
        Args:
            symptoms: MedicalSymptoms object
            patient_context: Optional patient information
            
        Returns:
            Dictionary containing urgency assessment
        """
        pass
    
    @abstractmethod
    async def generate_treatment_recommendations(
        self, 
        diagnosis: str,
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None
    ) -> List[str]:
        """
        Generate treatment recommendations for a diagnosis.
        
        Args:
            diagnosis: Primary diagnosis
            symptoms: Patient symptoms
            patient_context: Optional patient information
            
        Returns:
            List of treatment recommendations
        """
        pass
    
    @abstractmethod
    async def identify_red_flags(
        self, 
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None
    ) -> List[str]:
        """
        Identify red flag symptoms requiring immediate attention.
        
        Args:
            symptoms: MedicalSymptoms object
            patient_context: Optional patient information
            
        Returns:
            List of identified red flags
        """
        pass
    
    @abstractmethod
    async def summarize_clinical_note(self, clinical_text: str) -> str:
        """
        Summarize a clinical note or medical text.
        
        Args:
            clinical_text: Clinical text to summarize
            
        Returns:
            Summarized text
        """
        pass
    
    @abstractmethod
    async def extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract medical entities from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary mapping entity types to lists of entities
        """
        pass
    
    @abstractmethod
    async def get_model_confidence(self, analysis_result: Any) -> float:
        """
        Get confidence score for a model analysis result.
        
        Args:
            analysis_result: Result from model analysis
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        pass
    
    @abstractmethod
    async def is_model_available(self) -> bool:
        """
        Check if medical model is loaded and available.
        
        Returns:
            True if model is ready, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded medical model.
        
        Returns:
            Dictionary containing model information
        """
        pass
    
    @abstractmethod
    async def warm_up_model(self) -> bool:
        """
        Warm up the model for faster inference.
        
        Returns:
            True if warm-up succeeded, False otherwise
        """
        pass


class MedicalAnalysisError(Exception):
    """Base exception for medical analysis errors."""
    pass


class DrugInteractionError(MedicalAnalysisError):
    """Raised when drug interaction analysis fails."""
    pass


class DiagnosisError(MedicalAnalysisError):
    """Raised when diagnosis generation fails."""
    pass


class ModelUnavailableError(MedicalAnalysisError):
    """Raised when medical model is not available."""
    pass


class InvalidInputError(MedicalAnalysisError):
    """Raised when input data is invalid for analysis."""
    pass
