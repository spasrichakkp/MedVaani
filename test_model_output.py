#!/usr/bin/env python3
"""
Test script to debug model output quality
"""
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from infrastructure.adapters.meerkat_adapter import MeerkatAdapter
from domain.value_objects.medical_symptoms import MedicalSymptoms
from domain.entities.patient import Patient
from infrastructure.logging.logger_factory import LoggerFactory

async def test_model_output():
    """Test the raw model output to debug quality issues."""

    # Initialize logging
    LoggerFactory.initialize()

    # Initialize the adapter with a better model
    adapter = MeerkatAdapter(
        model_name="google/flan-t5-base",
        device="auto"
    )
    
    # Create test patient and symptoms
    patient = Patient.create_anonymous()
    patient.age = 55
    patient.gender = "male"
    patient.add_medical_history_item("hypertension")
    patient.add_medical_history_item("diabetes")
    
    symptoms = MedicalSymptoms.from_text(
        "I have severe chest pain radiating to my left arm, shortness of breath, and I'm sweating profusely"
    )
    
    print("🔬 Testing Medical AI Model Output")
    print("=" * 50)
    print(f"Patient: {patient.age}-year-old {patient.gender}")
    print(f"Medical History: {', '.join(patient.medical_history)}")
    print(f"Symptoms: {symptoms.raw_text}")
    print("=" * 50)
    
    try:
        # Test the analysis
        print("\n📋 Running Medical Analysis...")
        response = await adapter.analyze_symptoms(symptoms, patient)
        
        print(f"\n✅ Analysis Complete!")
        print(f"Urgency: {response.urgency.value}")
        print(f"Confidence: {response.confidence}")
        print(f"Model Used: {response.model_used}")
        
        print(f"\n📝 Response Text:")
        print("-" * 30)
        print(response.text)
        print("-" * 30)
        
        print(f"\n💡 Recommendations ({len(response.recommendations)}):")
        for i, rec in enumerate(response.recommendations, 1):
            print(f"  {i}. {rec}")
        
        print(f"\n⚠️ Red Flags ({len(response.red_flags)}):")
        for i, flag in enumerate(response.red_flags, 1):
            print(f"  {i}. {flag}")
        
        print(f"\n👤 Patient-Friendly Response:")
        print("-" * 30)
        if hasattr(response, 'patient_friendly_response'):
            print(response.patient_friendly_response)
        else:
            print("Not available - using main text response")
        print("-" * 30)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_model_output())
