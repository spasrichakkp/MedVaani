"""Domain entities for the medical research application."""

from .patient import Patient
from .consultation import Consultation
from .medical_response import MedicalResponse

__all__ = ["Patient", "Consultation", "MedicalResponse"]
