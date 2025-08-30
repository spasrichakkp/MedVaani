"""Integration tests for Phase 2 implementation."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path
import tempfile

from domain.entities.patient import Patient
from domain.value_objects.audio_data import AudioData
from domain.value_objects.medical_symptoms import MedicalSymptoms
from application.use_cases.voice_consultation_use_case import VoiceConsultationUseCase
from application.use_cases.medical_analysis_use_case import MedicalAnalysisUseCase
from infrastructure.adapters.composite_voice_interface import CompositeVoiceInterface
from infrastructure.adapters.filesystem_audio_repository import FileSystemAudioRepository
from infrastructure.config.dependency_injection import ApplicationContainer
from infrastructure.config.app_config import AppConfig


class TestMedicalAnalysisUseCase:
    """Integration tests for medical analysis use case."""
    
    @pytest.fixture
    def mock_medical_model(self):
        """Create mock medical model."""
        mock = AsyncMock()
        mock.is_model_available.return_value = True
        mock.analyze_symptoms.return_value = Mock(
            text="Based on your symptoms, you should see a doctor.",
            confidence=0.8,
            urgency="moderate",
            recommendations=["See a doctor", "Monitor symptoms"],
            red_flags=[]
        )
        mock.assess_urgency.return_value = {"urgency": "moderate"}
        mock.identify_red_flags.return_value = []
        mock.generate_differential_diagnosis.return_value = [
            {"diagnosis": "Tension headache", "probability": 0.7}
        ]
        mock.get_model_info.return_value = {"name": "test_model"}
        return mock
    
    @pytest.fixture
    def medical_analysis_use_case(self, mock_medical_model):
        """Create medical analysis use case with mocked dependencies."""
        return MedicalAnalysisUseCase(mock_medical_model)
    
    @pytest.mark.asyncio
    async def test_analyze_patient_symptoms_success(self, medical_analysis_use_case):
        """Test successful symptom analysis."""
        # Create test data
        patient = Patient.create_anonymous()
        patient.age = 30
        patient.gender = "female"
        
        symptoms = MedicalSymptoms.from_text("I have a headache and feel dizzy")
        
        # Execute analysis
        result = await medical_analysis_use_case.analyze_patient_symptoms(symptoms, patient)
        
        # Verify results
        assert result is not None
        assert result.text is not None
        assert 0.0 <= result.confidence <= 1.0
        assert result.urgency is not None
    
    @pytest.mark.asyncio
    async def test_analyze_emergency_symptoms(self, medical_analysis_use_case, mock_medical_model):
        """Test analysis of emergency symptoms."""
        # Mock emergency response
        mock_medical_model.assess_urgency.return_value = {"urgency": "emergency"}
        mock_medical_model.identify_red_flags.return_value = ["Severe chest pain"]
        
        patient = Patient.create_anonymous()
        symptoms = MedicalSymptoms.from_text("Severe chest pain and shortness of breath")
        
        result = await medical_analysis_use_case.analyze_patient_symptoms(symptoms, patient)
        
        assert result.urgency.value in ["emergency", "high"]
        assert len(result.red_flags) > 0
    
    @pytest.mark.asyncio
    async def test_model_unavailable_fallback(self, mock_medical_model):
        """Test fallback when medical model is unavailable."""
        mock_medical_model.is_model_available.return_value = False
        
        use_case = MedicalAnalysisUseCase(mock_medical_model)
        patient = Patient.create_anonymous()
        symptoms = MedicalSymptoms.from_text("I have a headache")
        
        result = await use_case.analyze_patient_symptoms(symptoms, patient)
        
        # Should return fallback response
        assert result is not None
        assert result.model_used == "fallback"
        assert result.confidence < 0.5


class TestVoiceConsultationUseCase:
    """Integration tests for voice consultation use case."""
    
    @pytest.fixture
    def mock_voice_interface(self):
        """Create mock voice interface."""
        mock = AsyncMock()
        mock.validate_audio_quality.return_value = True
        mock.transcribe_audio.return_value = "I have chest pain"
        mock.synthesize_speech.return_value = AudioData.silence(2.0, 16000)
        mock.record_audio.return_value = AudioData.silence(5.0, 16000)
        return mock
    
    @pytest.fixture
    def mock_medical_analysis(self):
        """Create mock medical analysis use case."""
        mock = AsyncMock()
        mock.analyze_patient_symptoms.return_value = Mock(
            text="You should see a doctor immediately.",
            urgency=Mock(value="high"),
            confidence=0.9,
            is_emergency=Mock(return_value=False),
            to_patient_friendly_text=Mock(return_value="Please see a doctor.")
        )
        return mock
    
    @pytest.fixture
    def mock_audio_repository(self):
        """Create mock audio repository."""
        mock = AsyncMock()
        mock.save_audio.return_value = "audio_123"
        return mock
    
    @pytest.fixture
    def voice_consultation_use_case(self, mock_voice_interface, mock_medical_analysis, mock_audio_repository):
        """Create voice consultation use case with mocked dependencies."""
        return VoiceConsultationUseCase(
            voice_interface=mock_voice_interface,
            medical_analysis_use_case=mock_medical_analysis,
            audio_repository=mock_audio_repository
        )
    
    @pytest.mark.asyncio
    async def test_text_to_voice_consultation_success(self, voice_consultation_use_case):
        """Test successful text-to-voice consultation."""
        patient = Patient.create_anonymous()
        symptoms_text = "I have been feeling dizzy and nauseous"
        
        result = await voice_consultation_use_case.execute_text_to_voice_consultation(
            patient=patient,
            symptoms_text=symptoms_text
        )
        
        assert result is not None
        assert result.is_completed()
        assert result.symptoms_text == symptoms_text
        assert result.medical_response is not None
        assert result.audio_response is not None
    
    @pytest.mark.asyncio
    async def test_voice_consultation_with_recording(self, voice_consultation_use_case):
        """Test voice consultation with audio recording."""
        patient = Patient.create_anonymous()
        
        result = await voice_consultation_use_case.execute_voice_consultation(
            patient=patient,
            recording_duration=5.0
        )
        
        assert result is not None
        assert result.is_completed()
        assert result.audio_input is not None
        assert result.transcription is not None
        assert result.medical_response is not None
        assert result.audio_response is not None
    
    @pytest.mark.asyncio
    async def test_consultation_failure_handling(self, voice_consultation_use_case, mock_voice_interface):
        """Test consultation failure handling."""
        # Mock transcription failure
        mock_voice_interface.transcribe_audio.side_effect = Exception("Transcription failed")
        
        patient = Patient.create_anonymous()
        
        with pytest.raises(Exception):
            await voice_consultation_use_case.execute_voice_consultation(
                patient=patient,
                recording_duration=5.0
            )


class TestCompositeVoiceInterface:
    """Integration tests for composite voice interface."""
    
    @pytest.fixture
    def mock_asr_adapter(self):
        """Create mock ASR adapter."""
        mock = AsyncMock()
        mock.transcribe_audio.return_value = "Hello world"
        mock.validate_audio_quality.return_value = True
        mock.is_available.return_value = True
        mock.get_health_status.return_value = {"status": "healthy"}
        mock.get_supported_languages.return_value = ["en"]
        return mock
    
    @pytest.fixture
    def mock_tts_adapter(self):
        """Create mock TTS adapter."""
        mock = AsyncMock()
        mock.synthesize_speech.return_value = AudioData.silence(2.0, 16000)
        mock.is_available.return_value = True
        mock.get_health_status.return_value = {"status": "healthy"}
        return mock
    
    @pytest.fixture
    def composite_voice_interface(self, mock_asr_adapter, mock_tts_adapter):
        """Create composite voice interface with mocked adapters."""
        return CompositeVoiceInterface(
            asr_adapter=mock_asr_adapter,
            tts_adapter=mock_tts_adapter,
            enable_resilience=False  # Disable for simpler testing
        )
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, composite_voice_interface):
        """Test successful audio transcription."""
        audio = AudioData.silence(2.0, 16000)
        
        result = await composite_voice_interface.transcribe_audio(audio)
        
        assert result == "Hello world"
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_success(self, composite_voice_interface):
        """Test successful speech synthesis."""
        text = "Hello, this is a test."
        
        result = await composite_voice_interface.synthesize_speech(text)
        
        assert result is not None
        assert isinstance(result, AudioData)
        assert result.duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_health_status(self, composite_voice_interface):
        """Test health status reporting."""
        status = await composite_voice_interface.get_health_status()
        
        assert "service" in status
        assert "asr_health" in status
        assert "tts_health" in status
        assert "overall_status" in status


class TestFileSystemAudioRepository:
    """Integration tests for filesystem audio repository."""
    
    @pytest.fixture
    def temp_audio_repo(self):
        """Create temporary audio repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = FileSystemAudioRepository(
                base_path=Path(temp_dir),
                max_storage_gb=1.0,
                auto_cleanup_days=1
            )
            yield repo
    
    @pytest.mark.asyncio
    async def test_save_and_load_audio(self, temp_audio_repo):
        """Test saving and loading audio."""
        # Create test audio
        audio = AudioData.silence(1.0, 16000)
        metadata = {"test": True, "type": "demo"}
        
        # Save audio
        audio_id = await temp_audio_repo.save_audio(audio, "test.wav", metadata)
        assert audio_id is not None
        
        # Load audio back
        loaded_audio = await temp_audio_repo.load_audio(audio_id)
        assert loaded_audio is not None
        assert loaded_audio.duration_seconds == audio.duration_seconds
        assert loaded_audio.sample_rate == audio.sample_rate
    
    @pytest.mark.asyncio
    async def test_metadata_operations(self, temp_audio_repo):
        """Test metadata operations."""
        audio = AudioData.silence(1.0, 16000)
        metadata = {"original": True}
        
        # Save with metadata
        audio_id = await temp_audio_repo.save_audio(audio, metadata=metadata)
        
        # Get metadata
        retrieved_metadata = await temp_audio_repo.get_audio_metadata(audio_id)
        assert retrieved_metadata is not None
        assert retrieved_metadata["custom_metadata"]["original"] is True
        
        # Update metadata
        new_metadata = {"updated": True}
        success = await temp_audio_repo.update_audio_metadata(audio_id, new_metadata)
        assert success
        
        # Verify update
        updated_metadata = await temp_audio_repo.get_audio_metadata(audio_id)
        assert updated_metadata["updated"] is True
    
    @pytest.mark.asyncio
    async def test_list_and_delete_audio(self, temp_audio_repo):
        """Test listing and deleting audio files."""
        # Save multiple audio files
        audio1 = AudioData.silence(1.0, 16000)
        audio2 = AudioData.silence(2.0, 16000)
        
        id1 = await temp_audio_repo.save_audio(audio1, "audio1.wav")
        id2 = await temp_audio_repo.save_audio(audio2, "audio2.wav")
        
        # List files
        files = await temp_audio_repo.list_audio_files()
        assert len(files) == 2
        
        # Delete one file
        success = await temp_audio_repo.delete_audio(id1)
        assert success
        
        # Verify deletion
        files = await temp_audio_repo.list_audio_files()
        assert len(files) == 1
        assert files[0]["id"] == id2
    
    @pytest.mark.asyncio
    async def test_storage_stats(self, temp_audio_repo):
        """Test storage statistics."""
        # Save some audio
        audio = AudioData.silence(1.0, 16000)
        await temp_audio_repo.save_audio(audio, "test.wav")
        
        # Get stats
        stats = await temp_audio_repo.get_storage_stats()
        
        assert "total_files" in stats
        assert "total_size_bytes" in stats
        assert "usage_percentage" in stats
        assert stats["total_files"] >= 1


class TestApplicationContainer:
    """Integration tests for application container."""
    
    @pytest.fixture
    def test_config(self):
        """Create test configuration."""
        config = AppConfig()
        config.voice.asr_model = "openai/whisper-tiny"  # Use tiny model for testing
        config.voice.tts_model = "microsoft/speecht5_tts"
        config.medical.reasoning_model_large = "google/flan-t5-small"  # Use small model
        return config
    
    @pytest.fixture
    def container(self, test_config):
        """Create application container with test config."""
        container = ApplicationContainer(test_config)
        yield container
        container.shutdown()
    
    def test_container_initialization(self, container):
        """Test container initialization."""
        container.initialize()
        assert container._initialized
        assert container.config is not None
        assert container.logger_factory is not None
    
    def test_dependency_creation(self, container):
        """Test dependency creation."""
        # This test may fail if models aren't available, so we'll mock
        with patch('infrastructure.adapters.whisper_adapter.WHISPER_AVAILABLE', False):
            with patch('infrastructure.adapters.speecht5_adapter.SPEECHT5_AVAILABLE', False):
                with patch('infrastructure.adapters.meerkat_adapter.TRANSFORMERS_AVAILABLE', False):
                    # Test that container can create instances even with missing dependencies
                    container.initialize()
                    assert container._initialized
    
    def test_singleton_behavior(self, container):
        """Test that dependencies are singletons."""
        container.initialize()
        
        # Get same dependency twice
        logger1 = container.get_logger("test")
        logger2 = container.get_logger("test")
        
        # Should be same instance
        assert logger1 is logger2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
