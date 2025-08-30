#!/usr/bin/env python3
"""
Phase 2 Core Refactoring Demo

This script demonstrates the Phase 2 implementation including:
- Use cases (VoiceConsultationUseCase, MedicalAnalysisUseCase)
- Infrastructure adapters (Whisper, SpeechT5, Meerkat, FileSystem)
- Async processing pipeline
- Circuit breaker and resilience patterns
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

from domain.entities.patient import Patient
from domain.value_objects.audio_data import AudioData
from domain.value_objects.medical_symptoms import MedicalSymptoms
from infrastructure.config.dependency_injection import create_container, get_logger
from infrastructure.config.app_config import AppConfig


async def demo_medical_analysis_use_case():
    """Demonstrate medical analysis use case."""
    logger = get_logger("demo")
    logger.info("Starting medical analysis use case demo")
    
    # Get container and use case
    container = create_container()
    medical_analysis = container.get_medical_analysis_use_case()
    
    # Create test patient
    patient = Patient.create_anonymous()
    patient.age = 45
    patient.gender = "female"
    patient.add_medical_history_item("hypertension")
    patient.add_medication("lisinopril")
    
    # Create symptoms
    symptoms_text = "I have severe chest pain and shortness of breath that started suddenly"
    symptoms = MedicalSymptoms.from_text(symptoms_text)
    
    print(f"\n=== Medical Analysis Demo ===")
    print(f"Patient: {patient.age} year old {patient.gender}")
    print(f"Medical History: {patient.medical_history}")
    print(f"Symptoms: {symptoms_text}")
    print(f"Emergency Indicators: {symptoms.has_emergency_symptoms()}")
    
    try:
        # Perform medical analysis
        logger.info("Performing medical analysis")
        medical_response = await medical_analysis.analyze_patient_symptoms(symptoms, patient)
        
        print(f"\n=== Medical Analysis Results ===")
        print(f"Urgency: {medical_response.urgency.value}")
        print(f"Confidence: {medical_response.confidence:.2f}")
        print(f"Is Emergency: {medical_response.is_emergency()}")
        print(f"Model Used: {medical_response.model_used}")
        
        if medical_response.recommendations:
            print(f"\nRecommendations:")
            for rec in medical_response.recommendations:
                print(f"• {rec}")
        
        if medical_response.red_flags:
            print(f"\nRed Flags:")
            for flag in medical_response.red_flags:
                print(f"⚠️ {flag}")
        
        print(f"\nPatient-Friendly Response:")
        print(medical_response.to_patient_friendly_text())
        
        return medical_response
        
    except Exception as e:
        logger.error(f"Medical analysis failed: {e}")
        print(f"❌ Medical analysis failed: {e}")
        return None


async def demo_voice_interface():
    """Demonstrate voice interface capabilities."""
    logger = get_logger("demo")
    logger.info("Starting voice interface demo")
    
    # Get container and voice interface
    container = create_container()
    voice_interface = container.get_voice_interface()
    
    print(f"\n=== Voice Interface Demo ===")
    
    # Check availability
    is_available = await voice_interface.is_available()
    print(f"Voice Interface Available: {is_available}")
    
    # Get health status
    health_status = await voice_interface.get_health_status()
    print(f"Health Status: {health_status.get('overall_status', 'unknown')}")
    
    # Get supported languages
    languages = await voice_interface.get_supported_languages()
    print(f"Supported Languages: {languages}")
    
    # Demo with synthetic audio (since we may not have microphone access)
    print(f"\n=== Synthetic Audio Demo ===")
    
    # Create test audio (silence for demo)
    test_audio = AudioData.silence(duration_seconds=2.0, sample_rate=16000)
    print(f"Created test audio: {test_audio}")
    
    # Validate audio quality
    is_valid = await voice_interface.validate_audio_quality(test_audio)
    print(f"Audio Quality Valid: {is_valid}")
    
    # Get transcription confidence
    confidence = await voice_interface.get_transcription_confidence(test_audio)
    print(f"Transcription Confidence: {confidence:.2f}")
    
    # Demo TTS
    test_text = "Hello, this is a test of the text-to-speech system."
    print(f"\nSynthesizing speech: '{test_text}'")
    
    try:
        audio_response = await voice_interface.synthesize_speech(test_text)
        if audio_response:
            print(f"✅ TTS successful: {audio_response.duration_seconds:.2f}s audio generated")
        else:
            print("❌ TTS failed")
    except Exception as e:
        logger.error(f"TTS demo failed: {e}")
        print(f"❌ TTS demo failed: {e}")
    
    return voice_interface


async def demo_text_to_voice_consultation():
    """Demonstrate text-to-voice consultation workflow."""
    logger = get_logger("demo")
    logger.info("Starting text-to-voice consultation demo")
    
    # Get container and use case
    container = create_container()
    consultation_use_case = container.get_voice_consultation_use_case()
    
    # Create test patient
    patient = Patient.create_anonymous()
    patient.age = 35
    patient.gender = "male"
    
    # Test symptoms
    symptoms_text = "I have been experiencing persistent headaches and dizziness for the past week"
    
    print(f"\n=== Text-to-Voice Consultation Demo ===")
    print(f"Patient: {patient.age} year old {patient.gender}")
    print(f"Symptoms: {symptoms_text}")
    
    try:
        # Execute consultation
        logger.info("Starting text-to-voice consultation")
        consultation = await consultation_use_case.execute_text_to_voice_consultation(
            patient=patient,
            symptoms_text=symptoms_text
        )
        
        print(f"\n=== Consultation Results ===")
        print(f"Consultation ID: {consultation.id}")
        print(f"Status: {consultation.status.value}")
        print(f"Type: {consultation.consultation_type.value}")
        
        if consultation.medical_response:
            print(f"Medical Response Urgency: {consultation.medical_response.urgency.value}")
            print(f"Confidence: {consultation.medical_response.confidence:.2f}")
            print(f"Emergency: {consultation.medical_response.is_emergency()}")
        
        if consultation.audio_response:
            print(f"Audio Response Generated: {consultation.audio_response.duration_seconds:.2f}s")
        
        # Get consultation summary
        summary = consultation.get_summary()
        print(f"\nConsultation Summary:")
        for key, value in summary.items():
            if key not in ['medical_response']:  # Skip nested objects
                print(f"  {key}: {value}")
        
        return consultation
        
    except Exception as e:
        logger.error(f"Consultation failed: {e}")
        print(f"❌ Consultation failed: {e}")
        return None


async def demo_audio_repository():
    """Demonstrate audio repository functionality."""
    logger = get_logger("demo")
    logger.info("Starting audio repository demo")
    
    # Get container and repository
    container = create_container()
    audio_repo = container.get_audio_repository()
    
    print(f"\n=== Audio Repository Demo ===")
    
    # Get storage stats
    stats = await audio_repo.get_storage_stats()
    print(f"Storage Stats:")
    print(f"  Total Files: {stats.get('total_files', 0)}")
    print(f"  Total Size: {stats.get('total_size_mb', 0):.2f} MB")
    print(f"  Usage: {stats.get('usage_percentage', 0):.1f}%")
    
    # Create test audio
    test_audio = AudioData.silence(duration_seconds=1.0, sample_rate=16000)
    
    try:
        # Save audio
        audio_id = await audio_repo.save_audio(
            test_audio,
            "demo_audio.wav",
            {"demo": True, "type": "test"}
        )
        print(f"✅ Audio saved with ID: {audio_id}")
        
        # Load audio back
        loaded_audio = await audio_repo.load_audio(audio_id)
        if loaded_audio:
            print(f"✅ Audio loaded: {loaded_audio.duration_seconds:.2f}s")
        
        # Get metadata
        metadata = await audio_repo.get_audio_metadata(audio_id)
        if metadata:
            print(f"✅ Metadata retrieved: {metadata.get('filename')}")
        
        # List files
        files = await audio_repo.list_audio_files(limit=5)
        print(f"✅ Found {len(files)} audio files")
        
        # Clean up
        deleted = await audio_repo.delete_audio(audio_id)
        print(f"✅ Audio deleted: {deleted}")
        
    except Exception as e:
        logger.error(f"Audio repository demo failed: {e}")
        print(f"❌ Audio repository demo failed: {e}")


async def demo_resilience_patterns():
    """Demonstrate resilience patterns."""
    logger = get_logger("demo")
    logger.info("Starting resilience patterns demo")
    
    # Get container and voice interface (which has resilience patterns)
    container = create_container()
    voice_interface = container.get_voice_interface()
    
    print(f"\n=== Resilience Patterns Demo ===")
    
    # Get health status to see resilience stats
    health_status = await voice_interface.get_health_status()
    
    if health_status.get("resilience_enabled"):
        print("✅ Resilience patterns enabled")
        
        resilience_stats = health_status.get("resilience_stats", {})
        
        # Show circuit breaker stats
        if "asr_circuit_breaker" in resilience_stats:
            asr_cb = resilience_stats["asr_circuit_breaker"]
            print(f"ASR Circuit Breaker:")
            print(f"  State: {asr_cb.get('state')}")
            print(f"  Total Calls: {asr_cb.get('total_calls')}")
            print(f"  Success Rate: {asr_cb.get('success_rate', 0):.1f}%")
        
        if "tts_circuit_breaker" in resilience_stats:
            tts_cb = resilience_stats["tts_circuit_breaker"]
            print(f"TTS Circuit Breaker:")
            print(f"  State: {tts_cb.get('state')}")
            print(f"  Total Calls: {tts_cb.get('total_calls')}")
            print(f"  Success Rate: {tts_cb.get('success_rate', 0):.1f}%")
        
        # Show retry policy stats
        if "asr_retry_policy" in resilience_stats:
            asr_retry = resilience_stats["asr_retry_policy"]
            print(f"ASR Retry Policy:")
            print(f"  Total Calls: {asr_retry.get('total_calls')}")
            print(f"  Average Attempts: {asr_retry.get('average_attempts', 0):.1f}")
    else:
        print("❌ Resilience patterns not enabled")


async def main():
    """Main demo function."""
    print("🏥 Medical Research - Phase 2 Core Refactoring Demo")
    print("=" * 60)
    
    # Initialize the application container
    config = AppConfig.from_env()
    container = create_container(config)
    
    logger = get_logger("main")
    logger.info("Phase 2 demo started")
    
    try:
        # Demo 1: Medical Analysis Use Case
        print("\n1. Medical Analysis Use Case Demo")
        medical_response = await demo_medical_analysis_use_case()
        
        # Demo 2: Voice Interface
        print("\n2. Voice Interface Demo")
        voice_interface = await demo_voice_interface()
        
        # Demo 3: Text-to-Voice Consultation
        print("\n3. Text-to-Voice Consultation Demo")
        consultation = await demo_text_to_voice_consultation()
        
        # Demo 4: Audio Repository
        print("\n4. Audio Repository Demo")
        await demo_audio_repository()
        
        # Demo 5: Resilience Patterns
        print("\n5. Resilience Patterns Demo")
        await demo_resilience_patterns()
        
        print("\n" + "=" * 60)
        print("✅ Phase 2 Core Refactoring Demo Complete!")
        print("\nKey Features Demonstrated:")
        print("• Use cases with async orchestration")
        print("• Infrastructure adapters (Whisper, SpeechT5, Meerkat)")
        print("• Composite voice interface with resilience")
        print("• Circuit breakers and retry policies")
        print("• Filesystem audio repository")
        print("• Complete voice consultation workflow")
        print("• Dependency injection and configuration")
        
        logger.info("Phase 2 demo completed successfully")
        
    except Exception as e:
        logger.error("Demo failed", exc_info=e)
        print(f"\n❌ Demo failed: {e}")
        raise
    
    finally:
        # Cleanup
        container.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
