"""Medical analysis use case for processing patient symptoms and generating medical insights."""

import time
from typing import Optional, List, Dict, Any

from domain.entities.patient import Patient
from domain.entities.medical_response import MedicalResponse, UrgencyLevel
from domain.value_objects.medical_symptoms import MedicalSymptoms, SymptomSeverity
from application.ports.medical_model_port import MedicalModelPort, MedicalAnalysisError
from infrastructure.logging.logger_factory import get_module_logger


class MedicalAnalysisUseCase:
    """
    Use case for medical analysis and symptom processing.
    
    This use case handles the medical reasoning workflow including
    symptom analysis, diagnosis generation, and treatment recommendations.
    """
    
    def __init__(self, medical_model: MedicalModelPort):
        """
        Initialize the medical analysis use case.
        
        Args:
            medical_model: Medical AI model interface
        """
        self.medical_model = medical_model
        self.logger = get_module_logger(__name__)
    
    async def analyze_patient_symptoms(
        self,
        symptoms: MedicalSymptoms,
        patient: Optional[Patient] = None
    ) -> MedicalResponse:
        """
        Analyze patient symptoms and generate medical response.
        
        Args:
            symptoms: Patient symptoms to analyze
            patient: Optional patient context
            
        Returns:
            Medical response with analysis and recommendations
            
        Raises:
            MedicalAnalysisError: If analysis fails
        """
        self.logger.info("Starting comprehensive medical analysis")
        start_time = time.time()
        
        try:
            # Check if medical model is available
            if not await self.medical_model.is_model_available():
                raise MedicalAnalysisError("Medical model not available")
            
            # Perform parallel analysis tasks
            analysis_tasks = await self._perform_parallel_analysis(symptoms, patient)
            
            # Generate comprehensive medical response
            medical_response = await self._generate_medical_response(
                symptoms, patient, analysis_tasks
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            medical_response.processing_time_ms = processing_time_ms
            
            self.logger.log_model_operation(
                "symptom_analysis",
                await self._get_model_name(),
                processing_time_ms,
                True
            )
            
            return medical_response
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            self.logger.log_model_operation(
                "symptom_analysis",
                await self._get_model_name(),
                processing_time_ms,
                False
            )
            self.logger.error(f"Medical analysis failed: {e}", exc_info=e)
            
            # Return fallback response
            return self._generate_fallback_response(symptoms, str(e))
    
    async def _perform_parallel_analysis(
        self,
        symptoms: MedicalSymptoms,
        patient: Optional[Patient]
    ) -> Dict[str, Any]:
        """Perform multiple analysis tasks in parallel."""
        import asyncio
        
        # Create analysis tasks
        tasks = {
            "primary_analysis": self.medical_model.analyze_symptoms(symptoms, patient),
            "urgency_assessment": self.medical_model.assess_urgency(symptoms, patient),
            "red_flags": self.medical_model.identify_red_flags(symptoms, patient),
            "differential_diagnosis": self.medical_model.generate_differential_diagnosis(symptoms, patient)
        }
        
        # Add drug interaction check if patient has medications
        if patient and patient.current_medications:
            tasks["drug_interactions"] = self.medical_model.check_drug_interactions(
                patient.current_medications, patient
            )
        
        # Execute tasks concurrently
        try:
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            
            # Map results back to task names
            analysis_results = {}
            for i, (task_name, _) in enumerate(tasks.items()):
                result = results[i]
                if isinstance(result, Exception):
                    self.logger.warning(f"Analysis task {task_name} failed: {result}")
                    analysis_results[task_name] = None
                else:
                    analysis_results[task_name] = result
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Parallel analysis failed: {e}")
            raise MedicalAnalysisError(f"Analysis execution failed: {e}") from e
    
    async def _generate_medical_response(
        self,
        symptoms: MedicalSymptoms,
        patient: Optional[Patient],
        analysis_results: Dict[str, Any]
    ) -> MedicalResponse:
        """Generate comprehensive medical response from analysis results."""
        
        # Extract primary analysis
        primary_analysis = analysis_results.get("primary_analysis")
        if isinstance(primary_analysis, MedicalResponse):
            medical_response = primary_analysis
        else:
            # Create response from text if primary analysis returned text
            response_text = str(primary_analysis) if primary_analysis else "Unable to analyze symptoms"
            medical_response = MedicalResponse.create_from_text(
                response_text,
                confidence=0.5,
                urgency=UrgencyLevel.MODERATE
            )
        
        # Enhance with urgency assessment
        urgency_result = analysis_results.get("urgency_assessment")
        if urgency_result:
            urgency_level = self._extract_urgency_level(urgency_result)
            medical_response.urgency = urgency_level
        
        # Add red flags
        red_flags = analysis_results.get("red_flags")
        if red_flags and isinstance(red_flags, list):
            for flag in red_flags:
                medical_response.add_red_flag(str(flag))
        
        # Add differential diagnoses
        differential = analysis_results.get("differential_diagnosis")
        if differential and isinstance(differential, list):
            for diagnosis in differential[:3]:  # Top 3 diagnoses
                if isinstance(diagnosis, dict) and "diagnosis" in diagnosis:
                    medical_response.differential_diagnoses.append(diagnosis["diagnosis"])
                else:
                    medical_response.differential_diagnoses.append(str(diagnosis))
        
        # Add drug interaction warnings
        drug_interactions = analysis_results.get("drug_interactions")
        if drug_interactions:
            self._add_drug_interaction_warnings(medical_response, drug_interactions)
        
        # Generate recommendations based on urgency and symptoms
        await self._add_recommendations(medical_response, symptoms, patient)
        
        # Set follow-up requirements
        self._set_follow_up_requirements(medical_response, symptoms)
        
        # Adjust confidence based on analysis quality
        self._adjust_confidence(medical_response, analysis_results)
        
        return medical_response
    
    def _extract_urgency_level(self, urgency_result: Any) -> UrgencyLevel:
        """Extract urgency level from analysis result."""
        if isinstance(urgency_result, dict):
            val = urgency_result.get("urgency", UrgencyLevel.MODERATE)
        else:
            val = urgency_result

        if isinstance(val, UrgencyLevel):
            return val

        urgency_str = str(val).lower()
        
        urgency_mapping = {
            "emergency": UrgencyLevel.EMERGENCY,
            "high": UrgencyLevel.HIGH,
            "moderate": UrgencyLevel.MODERATE,
            "low": UrgencyLevel.LOW
        }
        
        for key, level in urgency_mapping.items():
            if key in urgency_str:
                return level
        
        return UrgencyLevel.MODERATE
    
    def _add_drug_interaction_warnings(
        self,
        medical_response: MedicalResponse,
        drug_interactions: Dict[str, Any]
    ) -> None:
        """Add drug interaction warnings to medical response."""
        if isinstance(drug_interactions, dict):
            interactions = drug_interactions.get("interactions", [])
            for interaction in interactions:
                if isinstance(interaction, dict):
                    warning = f"Drug interaction: {interaction.get('description', 'Unknown interaction')}"
                    medical_response.add_red_flag(warning)
                else:
                    medical_response.add_red_flag(f"Drug interaction: {interaction}")
    
    async def _add_recommendations(
        self,
        medical_response: MedicalResponse,
        symptoms: MedicalSymptoms,
        patient: Optional[Patient]
    ) -> None:
        """Add treatment recommendations based on analysis."""
        
        # Emergency recommendations
        if medical_response.urgency == UrgencyLevel.EMERGENCY:
            medical_response.add_recommendation("Seek immediate emergency medical attention")
            medical_response.add_recommendation("Call 911 or go to the nearest emergency room")
            return
        
        # High urgency recommendations
        if medical_response.urgency == UrgencyLevel.HIGH:
            medical_response.add_recommendation("Schedule urgent appointment with healthcare provider")
            medical_response.add_recommendation("Seek medical attention within 24 hours")
        
        # General recommendations based on symptoms
        if symptoms.has_emergency_symptoms():
            medical_response.add_recommendation("Monitor symptoms closely")
            medical_response.add_recommendation("Seek medical evaluation if symptoms worsen")
        
        # High-risk patient recommendations
        if patient and patient.is_high_risk():
            medical_response.add_recommendation("Given your medical history, consult with your regular healthcare provider")
        
        # Default recommendation
        if not medical_response.recommendations:
            medical_response.add_recommendation("Consult with a healthcare professional for proper evaluation")
    
    def _set_follow_up_requirements(
        self,
        medical_response: MedicalResponse,
        symptoms: MedicalSymptoms
    ) -> None:
        """Set follow-up requirements based on urgency and symptoms."""
        
        if medical_response.urgency == UrgencyLevel.EMERGENCY:
            medical_response.set_follow_up(True, "immediately")
        elif medical_response.urgency == UrgencyLevel.HIGH:
            medical_response.set_follow_up(True, "within 24 hours")
        elif symptoms.has_emergency_symptoms():
            medical_response.set_follow_up(True, "within 48 hours")
        else:
            medical_response.set_follow_up(True, "within 1-2 weeks if symptoms persist")
    
    def _adjust_confidence(
        self,
        medical_response: MedicalResponse,
        analysis_results: Dict[str, Any]
    ) -> None:
        """Adjust confidence based on analysis quality."""
        
        # Count successful analysis tasks
        successful_tasks = sum(1 for result in analysis_results.values() if result is not None)
        total_tasks = len(analysis_results)
        
        if total_tasks > 0:
            success_ratio = successful_tasks / total_tasks
            # Adjust confidence based on analysis completeness
            medical_response.confidence = min(medical_response.confidence * success_ratio, 1.0)
    
    def _generate_fallback_response(
        self,
        symptoms: MedicalSymptoms,
        error_message: str
    ) -> MedicalResponse:
        """Generate fallback response when analysis fails."""
        
        # Determine urgency based on symptoms
        urgency = UrgencyLevel.HIGH if symptoms.has_emergency_symptoms() else UrgencyLevel.MODERATE
        
        fallback_text = (
            "I apologize, but I'm currently unable to provide a complete medical analysis. "
            "Based on your symptoms, I recommend consulting with a healthcare professional "
            "for proper evaluation and treatment."
        )
        
        response = MedicalResponse.create_from_text(
            fallback_text,
            confidence=0.3,
            urgency=urgency,
            model_used="fallback"
        )
        
        # Add emergency recommendation if needed
        if symptoms.has_emergency_symptoms():
            response.add_recommendation("Seek immediate medical attention")
            response.add_red_flag("Unable to complete AI analysis - seek professional help")
        else:
            response.add_recommendation("Schedule appointment with healthcare provider")
        
        response.set_follow_up(True, "as soon as possible")
        response.metadata["error"] = error_message
        
        return response
    
    async def _get_model_name(self) -> str:
        """Get the name of the medical model being used."""
        try:
            model_info = await self.medical_model.get_model_info()
            return model_info.get("name", "unknown_model")
        except Exception:
            return "unknown_model"
    
    async def check_drug_interactions_only(
        self,
        medications: List[str],
        patient: Optional[Patient] = None
    ) -> Dict[str, Any]:
        """
        Check for drug interactions only.
        
        Args:
            medications: List of medication names
            patient: Optional patient context
            
        Returns:
            Drug interaction analysis results
        """
        self.logger.info(f"Checking drug interactions for {len(medications)} medications")
        
        try:
            return await self.medical_model.check_drug_interactions(medications, patient)
        except Exception as e:
            self.logger.error(f"Drug interaction check failed: {e}")
            return {"error": str(e), "interactions": []}
