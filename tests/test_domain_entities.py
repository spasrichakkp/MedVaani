"""Tests for domain entities."""

import pytest
from datetime import datetime

from domain.entities.patient import Patient
from domain.entities.consultation import Consultation, ConsultationType, ConsultationStatus
from domain.entities.medical_response import MedicalResponse, UrgencyLevel, ConfidenceLevel


class TestPatient:
    """Test cases for Patient entity."""
    
    def test_create_anonymous_patient(self):
        """Test creating an anonymous patient."""
        patient = Patient.create_anonymous()
        
        assert patient.id.startswith("anon_")
        assert len(patient.id) == 13  # "anon_" + 8 hex chars
        assert patient.age is None
        assert patient.gender is None
        assert patient.medical_history == []
        assert patient.current_medications == []
        assert patient.allergies == []
        assert isinstance(patient.created_at, datetime)
    
    def test_add_medical_history(self):
        """Test adding medical history items."""
        patient = Patient.create_anonymous()
        
        patient.add_medical_history_item("diabetes")
        patient.add_medical_history_item("hypertension")
        
        assert "diabetes" in patient.medical_history
        assert "hypertension" in patient.medical_history
        assert len(patient.medical_history) == 2
    
    def test_add_duplicate_medical_history(self):
        """Test that duplicate medical history items are not added."""
        patient = Patient.create_anonymous()
        
        patient.add_medical_history_item("diabetes")
        patient.add_medical_history_item("diabetes")  # Duplicate
        
        assert len(patient.medical_history) == 1
        assert patient.medical_history[0] == "diabetes"
    
    def test_add_medication(self):
        """Test adding medications."""
        patient = Patient.create_anonymous()
        
        patient.add_medication("metformin")
        patient.add_medication("lisinopril")
        
        assert "metformin" in patient.current_medications
        assert "lisinopril" in patient.current_medications
        assert len(patient.current_medications) == 2
    
    def test_add_allergy(self):
        """Test adding allergies."""
        patient = Patient.create_anonymous()
        
        patient.add_allergy("penicillin")
        patient.add_allergy("shellfish")
        
        assert "penicillin" in patient.allergies
        assert "shellfish" in patient.allergies
        assert len(patient.allergies) == 2
    
    def test_has_drug_allergy(self):
        """Test checking for drug allergies."""
        patient = Patient.create_anonymous()
        patient.add_allergy("penicillin")
        patient.add_allergy("sulfa drugs")
        
        assert patient.has_drug_allergy("penicillin")
        assert patient.has_drug_allergy("Penicillin")  # Case insensitive
        assert patient.has_drug_allergy("sulfa")  # Partial match
        assert not patient.has_drug_allergy("aspirin")
    
    def test_is_high_risk(self):
        """Test high-risk patient identification."""
        patient = Patient.create_anonymous()
        
        # Not high risk initially
        assert not patient.is_high_risk()
        
        # Add high-risk condition
        patient.add_medical_history_item("diabetes mellitus")
        assert patient.is_high_risk()
        
        # Test other high-risk conditions
        patient2 = Patient.create_anonymous()
        patient2.add_medical_history_item("heart disease")
        assert patient2.is_high_risk()
    
    def test_get_context_for_analysis(self):
        """Test getting patient context for analysis."""
        patient = Patient.create_anonymous()
        patient.age = 65
        patient.gender = "male"
        patient.add_medical_history_item("hypertension")
        patient.add_medication("lisinopril")
        patient.add_allergy("penicillin")
        
        context = patient.get_context_for_analysis()
        
        assert context["age"] == 65
        assert context["gender"] == "male"
        assert context["medical_history"] == ["hypertension"]
        assert context["current_medications"] == ["lisinopril"]
        assert context["allergies"] == ["penicillin"]
        assert context["has_medical_history"] is True
        assert context["has_medications"] is True
        assert context["has_allergies"] is True


class TestMedicalResponse:
    """Test cases for MedicalResponse entity."""
    
    def test_create_from_text(self):
        """Test creating medical response from text."""
        response = MedicalResponse.create_from_text(
            "You should see a doctor",
            confidence=0.8,
            urgency=UrgencyLevel.MODERATE,
            model_used="test_model"
        )
        
        assert response.text == "You should see a doctor"
        assert response.confidence == 0.8
        assert response.urgency == UrgencyLevel.MODERATE
        assert response.model_used == "test_model"
        assert response.id.startswith("response_")
        assert isinstance(response.created_at, datetime)
    
    def test_get_confidence_level(self):
        """Test confidence level mapping."""
        response = MedicalResponse.create_from_text("test", confidence=0.95)
        assert response.get_confidence_level() == ConfidenceLevel.VERY_HIGH
        
        response = MedicalResponse.create_from_text("test", confidence=0.75)
        assert response.get_confidence_level() == ConfidenceLevel.HIGH
        
        response = MedicalResponse.create_from_text("test", confidence=0.55)
        assert response.get_confidence_level() == ConfidenceLevel.MODERATE
        
        response = MedicalResponse.create_from_text("test", confidence=0.35)
        assert response.get_confidence_level() == ConfidenceLevel.LOW
        
        response = MedicalResponse.create_from_text("test", confidence=0.15)
        assert response.get_confidence_level() == ConfidenceLevel.VERY_LOW
    
    def test_is_emergency(self):
        """Test emergency detection."""
        response = MedicalResponse.create_from_text(
            "Emergency", urgency=UrgencyLevel.EMERGENCY
        )
        assert response.is_emergency()
        
        response = MedicalResponse.create_from_text(
            "Not emergency", urgency=UrgencyLevel.LOW
        )
        assert not response.is_emergency()
    
    def test_requires_immediate_attention(self):
        """Test immediate attention requirement."""
        response = MedicalResponse.create_from_text(
            "High urgency", urgency=UrgencyLevel.HIGH
        )
        assert response.requires_immediate_attention()
        
        response = MedicalResponse.create_from_text(
            "Emergency", urgency=UrgencyLevel.EMERGENCY
        )
        assert response.requires_immediate_attention()
        
        response = MedicalResponse.create_from_text(
            "Low urgency", urgency=UrgencyLevel.LOW
        )
        assert not response.requires_immediate_attention()
    
    def test_add_recommendation(self):
        """Test adding recommendations."""
        response = MedicalResponse.create_from_text("test")
        
        response.add_recommendation("Take medication")
        response.add_recommendation("Rest")
        
        assert "Take medication" in response.recommendations
        assert "Rest" in response.recommendations
        assert len(response.recommendations) == 2
    
    def test_add_red_flag(self):
        """Test adding red flags."""
        response = MedicalResponse.create_from_text("test")
        
        response.add_red_flag("Severe pain")
        response.add_red_flag("Difficulty breathing")
        
        assert "Severe pain" in response.red_flags
        assert "Difficulty breathing" in response.red_flags
        assert len(response.red_flags) == 2
    
    def test_set_follow_up(self):
        """Test setting follow-up requirements."""
        response = MedicalResponse.create_from_text("test")
        
        response.set_follow_up(True, "within 24 hours")
        
        assert response.follow_up_required is True
        assert response.follow_up_timeframe == "within 24 hours"
    
    def test_to_patient_friendly_text(self):
        """Test converting to patient-friendly text."""
        response = MedicalResponse.create_from_text("You have a cold")
        response.add_recommendation("Rest and drink fluids")
        response.add_recommendation("Take over-the-counter medication")
        response.add_red_flag("Fever over 102°F")
        response.set_follow_up(True, "if symptoms worsen")
        
        friendly_text = response.to_patient_friendly_text()
        
        assert "You have a cold" in friendly_text
        assert "Rest and drink fluids" in friendly_text
        assert "Take over-the-counter medication" in friendly_text
        assert "Fever over 102°F" in friendly_text
        assert "follow up with a healthcare provider" in friendly_text
        assert "if symptoms worsen" in friendly_text


class TestConsultation:
    """Test cases for Consultation entity."""
    
    def test_create_voice_consultation(self):
        """Test creating a voice consultation."""
        patient = Patient.create_anonymous()
        consultation = Consultation.create_voice_consultation(patient)
        
        assert consultation.patient == patient
        assert consultation.consultation_type == ConsultationType.VOICE_TO_VOICE
        assert consultation.status == ConsultationStatus.CREATED
        assert consultation.id.startswith("consult_")
        assert isinstance(consultation.created_at, datetime)
    
    def test_create_text_consultation(self):
        """Test creating a text consultation."""
        patient = Patient.create_anonymous()
        symptoms = "I have a headache"
        consultation = Consultation.create_text_consultation(patient, symptoms)
        
        assert consultation.patient == patient
        assert consultation.consultation_type == ConsultationType.TEXT_TO_VOICE
        assert consultation.status == ConsultationStatus.TRANSCRIBED
        assert consultation.symptoms_text == symptoms
        assert consultation.transcription == symptoms
    
    def test_consultation_workflow(self):
        """Test complete consultation workflow."""
        patient = Patient.create_anonymous()
        consultation = Consultation.create_voice_consultation(patient)
        
        # Start with created status
        assert consultation.status == ConsultationStatus.CREATED
        
        # Set transcription
        consultation.set_transcription("I have chest pain")
        assert consultation.status == ConsultationStatus.TRANSCRIBED
        assert consultation.transcription == "I have chest pain"
        assert consultation.symptoms_text == "I have chest pain"
        
        # Start analysis
        consultation.start_analysis()
        assert consultation.status == ConsultationStatus.ANALYZING
        
        # Set medical response
        response = MedicalResponse.create_from_text("See a doctor")
        consultation.set_medical_response(response)
        assert consultation.status == ConsultationStatus.ANALYZED
        assert consultation.medical_response == response
        
        # Complete consultation
        consultation.complete()
        assert consultation.status == ConsultationStatus.COMPLETED
        assert consultation.completed_at is not None
        assert consultation.is_completed()
        assert not consultation.is_failed()
        assert not consultation.is_in_progress()
    
    def test_consultation_failure(self):
        """Test consultation failure handling."""
        patient = Patient.create_anonymous()
        consultation = Consultation.create_voice_consultation(patient)
        
        consultation.fail("Model not available")
        
        assert consultation.status == ConsultationStatus.FAILED
        assert consultation.error_message == "Model not available"
        assert consultation.is_failed()
        assert not consultation.is_completed()
        assert not consultation.is_in_progress()
    
    def test_consultation_cancellation(self):
        """Test consultation cancellation."""
        patient = Patient.create_anonymous()
        consultation = Consultation.create_voice_consultation(patient)
        
        consultation.cancel("User cancelled")
        
        assert consultation.status == ConsultationStatus.CANCELLED
        assert consultation.error_message == "User cancelled"
    
    def test_requires_emergency_attention(self):
        """Test emergency attention detection."""
        patient = Patient.create_anonymous()
        consultation = Consultation.create_voice_consultation(patient)
        
        # No medical response yet
        assert not consultation.requires_emergency_attention()
        
        # Add emergency response
        emergency_response = MedicalResponse.create_from_text(
            "Emergency", urgency=UrgencyLevel.EMERGENCY
        )
        consultation.set_medical_response(emergency_response)
        
        assert consultation.requires_emergency_attention()
    
    def test_get_summary(self):
        """Test getting consultation summary."""
        patient = Patient.create_anonymous()
        consultation = Consultation.create_text_consultation(patient, "headache")
        consultation.complete()
        
        summary = consultation.get_summary()
        
        assert summary["id"] == consultation.id
        assert summary["patient_id"] == patient.id
        assert summary["type"] == ConsultationType.TEXT_TO_VOICE.value
        assert summary["status"] == ConsultationStatus.COMPLETED.value
        assert summary["has_transcription"] is True
        assert summary["duration_seconds"] is not None
