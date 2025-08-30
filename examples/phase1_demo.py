#!/usr/bin/env python3
"""
Phase 1 Foundation Demo

This script demonstrates the Phase 1 foundation layer implementation
including domain entities, value objects, logging, and dependency injection.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

from domain.entities.patient import Patient
from domain.entities.consultation import Consultation, ConsultationType
from domain.entities.medical_response import MedicalResponse, UrgencyLevel
from domain.value_objects.audio_data import AudioData
from domain.value_objects.medical_symptoms import MedicalSymptoms
from infrastructure.config.dependency_injection import create_container, get_logger
from infrastructure.config.app_config import AppConfig


async def demo_domain_entities():
    """Demonstrate domain entities functionality."""
    logger = get_logger("demo")
    logger.info("Starting domain entities demo")
    
    # Create a patient
    patient = Patient.create_anonymous()
    patient.age = 45
    patient.gender = "female"
    patient.add_medical_history_item("hypertension")
    patient.add_medication("lisinopril")
    patient.add_allergy("penicillin")
    
    logger.info("Created patient", extra={
        "patient_id": patient.id,
        "age": patient.age,
        "is_high_risk": patient.is_high_risk()
    })
    
    # Create medical symptoms
    symptoms_text = "I have severe chest pain and shortness of breath that started suddenly"
    symptoms = MedicalSymptoms.from_text(symptoms_text)
    
    logger.info("Extracted symptoms", extra={
        "symptoms_count": len(symptoms.extracted_symptoms),
        "symptoms": symptoms.extracted_symptoms,
        "has_emergency": symptoms.has_emergency_symptoms()
    })
    
    # Create a consultation
    consultation = Consultation.create_text_consultation(patient, symptoms_text)
    consultation.start_analysis()
    
    # Create medical response
    medical_response = MedicalResponse.create_from_text(
        "Based on your symptoms of severe chest pain and shortness of breath, "
        "this could indicate a serious cardiac condition. Please seek immediate "
        "medical attention at the nearest emergency room.",
        confidence=0.85,
        urgency=UrgencyLevel.EMERGENCY,
        model_used="demo_model"
    )
    
    medical_response.add_recommendation("Go to emergency room immediately")
    medical_response.add_recommendation("Call 911 if symptoms worsen")
    medical_response.add_red_flag("Severe chest pain")
    medical_response.add_red_flag("Sudden onset shortness of breath")
    medical_response.set_follow_up(True, "within 24 hours if symptoms persist")
    
    consultation.set_medical_response(medical_response)
    consultation.complete()
    
    logger.info("Consultation completed", extra={
        "consultation_id": consultation.id,
        "status": consultation.status.value,
        "urgency": medical_response.urgency.value,
        "requires_emergency": consultation.requires_emergency_attention()
    })
    
    # Print consultation summary
    summary = consultation.get_summary()
    print("\n=== Consultation Summary ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    return consultation


async def demo_audio_value_object():
    """Demonstrate audio value object functionality."""
    logger = get_logger("demo")
    logger.info("Starting audio value object demo")
    
    # Create silent audio for demo
    audio = AudioData.silence(duration_seconds=2.0, sample_rate=16000)
    
    logger.info("Created audio data", extra={
        "duration_seconds": audio.duration_seconds,
        "sample_rate": audio.sample_rate,
        "samples_count": len(audio.samples),
        "is_valid": audio.is_valid_for_processing()
    })
    
    # Test audio properties
    print(f"\n=== Audio Properties ===")
    print(f"Duration: {audio.duration_seconds:.2f} seconds")
    print(f"Sample Rate: {audio.sample_rate} Hz")
    print(f"Samples: {len(audio.samples)}")
    print(f"RMS Amplitude: {audio.get_rms_amplitude():.4f}")
    print(f"Peak Amplitude: {audio.get_peak_amplitude():.4f}")
    print(f"Is Silent: {audio.is_silent()}")
    print(f"Valid for Processing: {audio.is_valid_for_processing()}")
    
    return audio


async def demo_logging_system():
    """Demonstrate structured logging system."""
    logger = get_logger("demo")
    
    # Test different log levels
    logger.debug("This is a debug message", extra={"debug_info": "test_value"})
    logger.info("This is an info message", extra={"operation": "demo", "step": 1})
    logger.warning("This is a warning message", extra={"warning_type": "demo"})
    logger.error("This is an error message", extra={"error_code": "DEMO_001"})
    
    # Test consultation logging
    logger.log_consultation_start("consult_123", "patient_456", "voice_to_voice")
    logger.log_consultation_complete("consult_123", 5000, True)
    
    # Test model operation logging
    logger.log_model_operation("transcription", "whisper-small", 1500, True)
    logger.log_audio_processing("recording", 3000, True)
    
    print("\n=== Logging Demo Complete ===")
    print("Check the console output above for structured log messages")


async def demo_configuration():
    """Demonstrate configuration management."""
    logger = get_logger("demo")
    
    # Get configuration from container
    from infrastructure.config.dependency_injection import get_config
    config = get_config()
    
    logger.info("Configuration loaded", extra={
        "environment": config.environment,
        "debug": config.debug,
        "voice_model": config.voice.tts_model,
        "medical_model": config.medical.reasoning_model
    })
    
    print(f"\n=== Configuration Demo ===")
    print(f"Environment: {config.environment}")
    print(f"Debug Mode: {config.debug}")
    print(f"TTS Model: {config.voice.tts_model}")
    print(f"ASR Model: {config.voice.asr_model}")
    print(f"Medical Model: {config.medical.reasoning_model}")
    print(f"Audio Output Dir: {config.voice.audio_output_dir}")
    print(f"Data Directory: {config.data_dir}")
    print(f"Logs Directory: {config.logs_dir}")
    
    # Test configuration validation
    errors = config.validate()
    if errors:
        logger.warning("Configuration validation errors", extra={"errors": errors})
        print(f"Configuration Errors: {errors}")
    else:
        logger.info("Configuration is valid")
        print("Configuration: ✅ Valid")


async def main():
    """Main demo function."""
    print("🏥 Medical Research - Phase 1 Foundation Demo")
    print("=" * 50)
    
    # Initialize the application container
    config = AppConfig.from_env()
    container = create_container(config)
    
    logger = get_logger("main")
    logger.info("Phase 1 demo started")
    
    try:
        # Demo 1: Configuration
        print("\n1. Configuration Management Demo")
        await demo_configuration()
        
        # Demo 2: Logging
        print("\n2. Structured Logging Demo")
        await demo_logging_system()
        
        # Demo 3: Domain Entities
        print("\n3. Domain Entities Demo")
        consultation = await demo_domain_entities()
        
        # Demo 4: Value Objects
        print("\n4. Value Objects Demo")
        audio = await demo_audio_value_object()
        
        print("\n" + "=" * 50)
        print("✅ Phase 1 Foundation Demo Complete!")
        print("\nKey Features Demonstrated:")
        print("• Domain entities (Patient, Consultation, MedicalResponse)")
        print("• Value objects (AudioData, MedicalSymptoms)")
        print("• Structured logging with correlation IDs")
        print("• Configuration management")
        print("• Dependency injection container")
        print("\nNext: Phase 2 will add use cases and port interfaces")
        
        logger.info("Phase 1 demo completed successfully")
        
    except Exception as e:
        logger.error("Demo failed", exc_info=e)
        print(f"\n❌ Demo failed: {e}")
        raise
    
    finally:
        # Cleanup
        container.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
