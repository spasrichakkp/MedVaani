"""Voice consultation use case for orchestrating voice-to-voice medical consultations."""

import asyncio
import time
from typing import Optional, Dict, Any
from datetime import datetime

from domain.entities.patient import Patient
from domain.entities.consultation import Consultation, ConsultationType
from domain.entities.medical_response import MedicalResponse
from domain.value_objects.audio_data import AudioData
from domain.value_objects.medical_symptoms import MedicalSymptoms
from application.ports.voice_interface_port import VoiceInterfacePort, VoiceProcessingError, AudioQualityError
from application.ports.medical_model_port import MedicalModelPort, MedicalAnalysisError
from application.ports.audio_repository_port import AudioRepositoryPort
from .medical_analysis_use_case import MedicalAnalysisUseCase
from infrastructure.logging.logger_factory import get_module_logger


class VoiceConsultationUseCase:
    """
    Use case for orchestrating voice-to-voice medical consultations.
    
    This use case coordinates the complete workflow from patient voice input
    to AI doctor voice response, managing all the steps in between.
    """
    
    def __init__(
        self,
        voice_interface: VoiceInterfacePort,
        medical_analysis_use_case: MedicalAnalysisUseCase,
        audio_repository: Optional[AudioRepositoryPort] = None
    ):
        """
        Initialize the voice consultation use case.
        
        Args:
            voice_interface: Voice processing interface (TTS/ASR)
            medical_analysis_use_case: Medical analysis use case
            audio_repository: Optional audio storage repository
        """
        self.voice_interface = voice_interface
        self.medical_analysis_use_case = medical_analysis_use_case
        self.audio_repository = audio_repository
        self.logger = get_module_logger(__name__)
    
    async def execute_voice_consultation(
        self,
        patient: Patient,
        recording_duration: float = 10.0,
        voice_config: Optional[Dict[str, Any]] = None
    ) -> Consultation:
        """
        Execute a complete voice-to-voice consultation.
        
        Args:
            patient: Patient entity
            recording_duration: Duration to record audio in seconds
            voice_config: Optional voice configuration for TTS
            
        Returns:
            Completed consultation entity
            
        Raises:
            VoiceProcessingError: If voice processing fails
            MedicalAnalysisError: If medical analysis fails
        """
        consultation = Consultation.create_voice_consultation(patient)
        
        self.logger.log_consultation_start(
            consultation.id,
            patient.id,
            consultation.consultation_type.value
        )
        
        start_time = time.time()
        
        try:
            # Step 1: Record patient audio
            audio_input = await self._record_patient_audio(consultation, recording_duration)
            
            # Step 2: Transcribe audio to text
            transcription = await self._transcribe_audio(consultation, audio_input)
            
            # Step 3: Analyze symptoms with medical AI
            medical_response = await self._analyze_symptoms(consultation, transcription, patient)
            
            # Step 4: Generate voice response
            audio_response = await self._generate_voice_response(consultation, medical_response, voice_config)
            
            # Step 5: Complete consultation
            consultation.complete()
            
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.log_consultation_complete(consultation.id, duration_ms, True)
            
            return consultation
            
        except Exception as e:
            consultation.fail(str(e))
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.log_consultation_complete(consultation.id, duration_ms, False)
            self.logger.error(f"Voice consultation failed: {e}", exc_info=e)
            raise
    
    async def execute_text_to_voice_consultation(
        self,
        patient: Patient,
        symptoms_text: str,
        voice_config: Optional[Dict[str, Any]] = None
    ) -> Consultation:
        """
        Execute a text-to-voice consultation (text input, voice output).
        
        Args:
            patient: Patient entity
            symptoms_text: Patient symptoms as text
            voice_config: Optional voice configuration for TTS
            
        Returns:
            Completed consultation entity
        """
        consultation = Consultation.create_text_consultation(patient, symptoms_text)
        
        self.logger.log_consultation_start(
            consultation.id,
            patient.id,
            consultation.consultation_type.value
        )
        
        start_time = time.time()
        
        try:
            # Step 1: Analyze symptoms with medical AI
            medical_response = await self._analyze_symptoms(consultation, symptoms_text, patient)
            
            # Step 2: Generate voice response
            audio_response = await self._generate_voice_response(consultation, medical_response, voice_config)
            
            # Step 3: Complete consultation
            consultation.complete()
            
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.log_consultation_complete(consultation.id, duration_ms, True)
            
            return consultation
            
        except Exception as e:
            consultation.fail(str(e))
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.log_consultation_complete(consultation.id, duration_ms, False)
            self.logger.error(f"Text-to-voice consultation failed: {e}", exc_info=e)
            raise
    
    async def _record_patient_audio(
        self,
        consultation: Consultation,
        duration: float
    ) -> AudioData:
        """Record audio from patient."""
        self.logger.info(f"Recording patient audio for {duration} seconds")
        
        try:
            audio_data = await self.voice_interface.record_audio(duration)
            
            if audio_data is None:
                raise VoiceProcessingError("Failed to record audio")
            
            # Validate audio quality
            if not await self.voice_interface.validate_audio_quality(audio_data):
                raise AudioQualityError("Audio quality insufficient for processing")
            
            consultation.set_audio_input(audio_data)
            
            # Save audio if repository available
            if self.audio_repository:
                await self.audio_repository.save_audio(
                    audio_data,
                    f"consultation_{consultation.id}_input.wav",
                    {"consultation_id": consultation.id, "type": "input"}
                )
            
            self.logger.log_audio_processing("recording", audio_data.get_duration_ms(), True)
            return audio_data
            
        except Exception as e:
            self.logger.log_audio_processing("recording", 0, False)
            raise VoiceProcessingError(f"Audio recording failed: {e}") from e
    
    async def _transcribe_audio(
        self,
        consultation: Consultation,
        audio_data: AudioData
    ) -> str:
        """Transcribe audio to text."""
        self.logger.info("Transcribing patient audio")
        
        try:
            transcription = await self.voice_interface.transcribe_audio(audio_data)
            
            if not transcription or not transcription.strip():
                raise VoiceProcessingError("No speech detected in audio")
            
            consultation.set_transcription(transcription)
            
            self.logger.log_audio_processing("transcription", audio_data.get_duration_ms(), True)
            self.logger.info(f"Transcription completed: '{transcription[:100]}...'")
            
            return transcription
            
        except Exception as e:
            self.logger.log_audio_processing("transcription", audio_data.get_duration_ms(), False)
            raise VoiceProcessingError(f"Audio transcription failed: {e}") from e
    
    async def _analyze_symptoms(
        self,
        consultation: Consultation,
        symptoms_text: str,
        patient: Patient
    ) -> MedicalResponse:
        """Analyze symptoms using medical AI."""
        self.logger.info("Starting medical analysis")
        consultation.start_analysis()
        
        try:
            # Extract symptoms
            symptoms = MedicalSymptoms.from_text(symptoms_text)
            
            # Perform medical analysis
            medical_response = await self.medical_analysis_use_case.analyze_patient_symptoms(
                symptoms, patient
            )
            
            consultation.set_medical_response(medical_response)
            
            self.logger.info(
                f"Medical analysis completed",
                extra={
                    "urgency": medical_response.urgency.value,
                    "confidence": medical_response.confidence,
                    "is_emergency": medical_response.is_emergency()
                }
            )
            
            return medical_response
            
        except Exception as e:
            raise MedicalAnalysisError(f"Medical analysis failed: {e}") from e
    
    async def _generate_voice_response(
        self,
        consultation: Consultation,
        medical_response: MedicalResponse,
        voice_config: Optional[Dict[str, Any]] = None
    ) -> AudioData:
        """Generate voice response from medical analysis."""
        self.logger.info("Generating voice response")
        
        try:
            # Get patient-friendly text
            response_text = medical_response.to_patient_friendly_text()
            
            # Generate speech
            audio_response = await self.voice_interface.synthesize_speech(
                response_text, voice_config
            )
            
            if audio_response is None:
                raise VoiceProcessingError("Failed to generate speech")
            
            consultation.set_audio_response(audio_response)
            
            # Save audio if repository available
            if self.audio_repository:
                await self.audio_repository.save_audio(
                    audio_response,
                    f"consultation_{consultation.id}_response.wav",
                    {"consultation_id": consultation.id, "type": "response"}
                )
            
            self.logger.log_audio_processing("synthesis", audio_response.get_duration_ms(), True)
            
            return audio_response
            
        except Exception as e:
            self.logger.log_audio_processing("synthesis", 0, False)
            raise VoiceProcessingError(f"Voice synthesis failed: {e}") from e
    
    async def play_consultation_response(self, consultation: Consultation) -> bool:
        """Play the consultation audio response."""
        if not consultation.audio_response:
            self.logger.warning("No audio response to play")
            return False
        
        try:
            success = await self.voice_interface.play_audio(consultation.audio_response)
            
            if success:
                self.logger.info("Audio response played successfully")
            else:
                self.logger.warning("Audio playback failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}", exc_info=e)
            return False
    
    async def get_voice_interface_health(self) -> Dict[str, Any]:
        """Get health status of voice interface."""
        try:
            return await self.voice_interface.get_health_status()
        except Exception as e:
            self.logger.error(f"Failed to get voice interface health: {e}")
            return {"status": "unhealthy", "error": str(e)}
