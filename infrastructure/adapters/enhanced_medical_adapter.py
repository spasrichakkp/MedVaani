"""
Enhanced Medical AI Adapter with multiple AI backends.

This adapter integrates multiple medical AI services:
- Infermedica API for interactive diagnosis
- Clinical Knowledge Graph for drug information
- RxNorm for medication standardization
- Fallback to local medical models
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import aiohttp
import requests
from transformers import pipeline
import yaml

from application.ports.medical_model_port import (
    MedicalModelPort,
    MedicalAnalysisError,
    DrugInteractionError
)
from domain.entities.patient import Patient
from domain.value_objects.medical_symptoms import MedicalSymptoms
from domain.value_objects.medical_response import (
    MedicalResponse,
    UrgencyLevel,
    Recommendation,
    RedFlag
)
from infrastructure.logging.medical_logger import MedicalLogger
from .aloe_medical_adapter import AloemedicalAdapter


class DiagnosisStep(Enum):
    """Steps in the diagnosis process."""
    INITIAL_ASSESSMENT = "initial_assessment"
    SYMPTOM_ANALYSIS = "symptom_analysis"
    FOLLOW_UP_QUESTIONS = "follow_up_questions"
    DIFFERENTIAL_DIAGNOSIS = "differential_diagnosis"
    DRUG_RECOMMENDATIONS = "drug_recommendations"
    FINAL_ASSESSMENT = "final_assessment"


@dataclass
class DiagnosisSession:
    """Represents an ongoing diagnosis session."""
    session_id: str
    patient_demographics: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    current_step: DiagnosisStep
    infermedica_interview_id: Optional[str] = None
    confidence_score: float = 0.0
    should_stop: bool = False
    follow_up_questions: List[str] = None
    
    def __post_init__(self):
        if self.follow_up_questions is None:
            self.follow_up_questions = []


@dataclass
class DrugRecommendation:
    """Represents a drug recommendation."""
    generic_name: str
    brand_names: List[str]
    dosage: str
    frequency: str
    duration: str
    route: str
    contraindications: List[str]
    side_effects: List[str]
    indian_availability: bool = True
    estimated_cost_inr: Optional[str] = None


class EnhancedMedicalAdapter(MedicalModelPort):
    """
    Enhanced medical adapter with multiple AI backends.
    
    Provides comprehensive medical diagnosis using:
    1. Infermedica API for interactive symptom assessment
    2. Clinical Knowledge Graph for drug interactions
    3. RxNorm for standardized medication information
    4. Local medical models as fallback
    """
    
    def __init__(
        self,
        infermedica_app_id: Optional[str] = None,
        infermedica_app_key: Optional[str] = None,
        enable_drug_recommendations: bool = True,
        enable_interactive_diagnosis: bool = True,
        fallback_model_name: str = "google/flan-t5-base",
        logger: Optional[MedicalLogger] = None,
        models_config_path: str = "configs/models.yaml"
    ):
        """
        Initialize the enhanced medical adapter.

        Args:
            infermedica_app_id: Infermedica API application ID
            infermedica_app_key: Infermedica API application key
            enable_drug_recommendations: Whether to enable drug recommendations
            enable_interactive_diagnosis: Whether to enable interactive diagnosis
            fallback_model_name: Name of fallback model to use
            logger: Optional medical logger instance
            models_config_path: Path to models configuration file
        """
        self.infermedica_app_id = infermedica_app_id
        self.infermedica_app_key = infermedica_app_key
        self.enable_drug_recommendations = enable_drug_recommendations
        self.enable_interactive_diagnosis = enable_interactive_diagnosis
        self.fallback_model_name = fallback_model_name
        self.models_config_path = models_config_path

        self.logger = logger or MedicalLogger(__name__)

        # API endpoints
        self.infermedica_base_url = "https://api.infermedica.com/v3"

        # Model state
        self._is_loaded = False
        self._fallback_model = None
        self._session = None
        self._aloe_adapter = None

        # Load models configuration
        self._load_models_config()

        # Active diagnosis sessions
        self._active_sessions: Dict[str, DiagnosisSession] = {}
        
        # Drug database cache
        self._drug_cache: Dict[str, DrugRecommendation] = {}
        
        # Indian drug mapping (simplified for demo)
        self._indian_drug_mapping = {
            "paracetamol": DrugRecommendation(
                generic_name="Paracetamol",
                brand_names=["Crocin", "Dolo", "Calpol"],
                dosage="500mg",
                frequency="Every 6-8 hours",
                duration="As needed",
                route="Oral",
                contraindications=["Severe liver disease"],
                side_effects=["Rare: liver damage with overdose"],
                indian_availability=True,
                estimated_cost_inr="₹2-5 per tablet"
            ),
            "ibuprofen": DrugRecommendation(
                generic_name="Ibuprofen",
                brand_names=["Brufen", "Combiflam", "Advil"],
                dosage="400mg",
                frequency="Every 6-8 hours",
                duration="As needed",
                route="Oral",
                contraindications=["Peptic ulcer", "kidney disease"],
                side_effects=["Stomach upset", "kidney problems"],
                indian_availability=True,
                estimated_cost_inr="₹3-8 per tablet"
            ),
            "amoxicillin": DrugRecommendation(
                generic_name="Amoxicillin",
                brand_names=["Novamox", "Amoxil", "Moxikind"],
                dosage="500mg",
                frequency="Every 8 hours",
                duration="5-7 days",
                route="Oral",
                contraindications=["Penicillin allergy"],
                side_effects=["Diarrhea", "nausea", "rash"],
                indian_availability=True,
                estimated_cost_inr="₹5-12 per capsule"
            )
        }

    def _load_models_config(self):
        """Load models configuration from YAML file"""
        try:
            with open(self.models_config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Initialize Aloe medical adapter if configured
            if 'aloe_medical_7b' in config.get('models', {}):
                aloe_config = config['models']['aloe_medical_7b']
                self._aloe_adapter = AloemedicalAdapter(aloe_config)
                self.logger.info("Aloe medical adapter initialized")
            else:
                self.logger.warning("Aloe medical model not found in configuration")

        except Exception as e:
            self.logger.error(f"Failed to load models configuration: {e}")
            self._aloe_adapter = None

    async def _ensure_model_loaded(self):
        """Ensure the medical model is loaded and ready."""
        if not self._is_loaded:
            await self._load_model()
    
    async def _load_model(self):
        """Load the fallback medical model and initialize services."""
        try:
            self.logger.info("Loading enhanced medical adapter...")

            # Initialize HTTP session for API calls
            self._session = aiohttp.ClientSession()

            # Load Aloe medical model if available
            if self._aloe_adapter:
                self.logger.info("Loading Aloe medical model...")
                await self._aloe_adapter.load_model()

            # Load fallback model
            if self.fallback_model_name:
                loop = asyncio.get_event_loop()
                self._fallback_model = await loop.run_in_executor(
                    None,
                    lambda: pipeline(
                        "text2text-generation",
                        model=self.fallback_model_name,
                        device=-1  # CPU
                    )
                )

            self._is_loaded = True
            self.logger.info("Enhanced medical adapter loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load enhanced medical adapter: {e}")
            raise MedicalAnalysisError(f"Model loading failed: {e}") from e
    
    async def analyze_symptoms(
        self, 
        symptoms: MedicalSymptoms, 
        patient_context: Optional[Patient] = None
    ) -> MedicalResponse:
        """
        Analyze patient symptoms using enhanced multi-backend approach.
        
        Args:
            symptoms: MedicalSymptoms object containing patient symptoms
            patient_context: Optional patient information for context
            
        Returns:
            MedicalResponse containing comprehensive analysis and recommendations
        """
        try:
            await self._ensure_model_loaded()
            
            self.logger.info("Starting enhanced symptom analysis")
            start_time = time.time()
            
            # Create diagnosis session
            session_id = f"session_{int(time.time())}"
            session = await self._create_diagnosis_session(session_id, symptoms, patient_context)
            
            # Perform multi-step analysis
            medical_response = await self._perform_comprehensive_analysis(session, symptoms, patient_context)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            medical_response.processing_time_ms = processing_time_ms
            medical_response.model_used = "enhanced_medical_adapter"
            
            self.logger.info(f"Enhanced analysis completed in {processing_time_ms}ms")
            
            return medical_response
            
        except Exception as e:
            self.logger.error(f"Enhanced symptom analysis failed: {e}")
            # Fallback to basic analysis
            return await self._fallback_analysis(symptoms, patient_context, str(e))
    
    async def _create_diagnosis_session(
        self, 
        session_id: str, 
        symptoms: MedicalSymptoms, 
        patient_context: Optional[Patient]
    ) -> DiagnosisSession:
        """Create a new diagnosis session."""
        
        # Extract patient demographics
        demographics = {}
        if patient_context:
            demographics = {
                "sex": getattr(patient_context, 'gender', 'unknown').lower(),
                "age": {"value": getattr(patient_context, 'age', 30)}
            }
        else:
            # Default demographics
            demographics = {
                "sex": "unknown",
                "age": {"value": 30}
            }
        
        # Convert symptoms to evidence format
        evidence = []
        for symptom in symptoms.extracted_symptoms:
            evidence.append({
                "id": f"s_{hash(symptom) % 10000}",  # Simplified symptom ID
                "choice_id": "present",
                "source": "initial"
            })
        
        session = DiagnosisSession(
            session_id=session_id,
            patient_demographics=demographics,
            evidence=evidence,
            current_step=DiagnosisStep.INITIAL_ASSESSMENT
        )

        # Store original symptoms for Aloe adapter
        session._original_symptoms = symptoms.raw_text

        self._active_sessions[session_id] = session
        return session

    def _extract_symptoms_from_session(self, session: DiagnosisSession) -> str:
        """Extract symptoms text from DiagnosisSession for Aloe adapter"""
        # For now, we'll need to store the original symptoms in the session
        # This is a temporary solution - ideally we'd modify the session structure
        if hasattr(session, '_original_symptoms'):
            return session._original_symptoms

        # Fallback: create a generic symptoms description from evidence
        if session.evidence:
            return f"Patient presents with {len(session.evidence)} reported symptoms requiring medical evaluation"

        return "General medical consultation"

    async def _perform_comprehensive_analysis(
        self,
        session: DiagnosisSession,
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient]
    ) -> MedicalResponse:
        """Perform comprehensive multi-step medical analysis."""

        try:
            # Step 1: Initial Infermedica assessment
            session.current_step = DiagnosisStep.SYMPTOM_ANALYSIS
            infermedica_result = await self._query_infermedica_diagnosis(session)

            # Step 2: Generate follow-up questions if needed
            if not session.should_stop and self.enable_interactive_diagnosis:
                session.current_step = DiagnosisStep.FOLLOW_UP_QUESTIONS
                follow_up_questions = await self._generate_follow_up_questions(session, infermedica_result)
                session.follow_up_questions = follow_up_questions

            # Step 3: Drug recommendations
            if self.enable_drug_recommendations:
                session.current_step = DiagnosisStep.DRUG_RECOMMENDATIONS
                drug_recommendations = await self._generate_drug_recommendations(session, infermedica_result)
            else:
                drug_recommendations = []

            # Step 4: Final assessment
            session.current_step = DiagnosisStep.FINAL_ASSESSMENT
            medical_response = await self._create_final_medical_response(
                session, infermedica_result, drug_recommendations, symptoms, patient_context
            )

            return medical_response

        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed: {e}")
            # Fallback to basic analysis
            return await self._fallback_analysis(symptoms, patient_context, str(e))

    async def _query_infermedica_diagnosis(self, session: DiagnosisSession) -> Dict[str, Any]:
        """Query Infermedica API for diagnosis."""

        if not self.infermedica_app_id or not self.infermedica_app_key:
            self.logger.warning("Infermedica credentials not provided, using Aloe medical model")
            # Extract symptoms from evidence for Aloe model
            symptoms_text = self._extract_symptoms_from_session(session)
            return await self._aloe_medical_response(session, symptoms_text)

        try:
            headers = {
                "App-Id": self.infermedica_app_id,
                "App-Key": self.infermedica_app_key,
                "Content-Type": "application/json"
            }

            payload = {
                "sex": session.patient_demographics.get("sex", "unknown"),
                "age": session.patient_demographics.get("age", {"value": 30}),
                "evidence": session.evidence
            }

            async with self._session.post(
                f"{self.infermedica_base_url}/diagnosis",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # Update session with results
                    session.should_stop = result.get("should_stop", False)
                    session.confidence_score = max([c.get("probability", 0) for c in result.get("conditions", [])], default=0)

                    return result
                else:
                    self.logger.error(f"Infermedica API error: {response.status}")
                    symptoms_text = self._extract_symptoms_from_session(session)
                    return await self._aloe_medical_response(session, symptoms_text)

        except Exception as e:
            self.logger.error(f"Infermedica API call failed: {e}")
            symptoms_text = self._extract_symptoms_from_session(session)
            return await self._aloe_medical_response(session, symptoms_text)

    async def _aloe_medical_response(self, session: DiagnosisSession, symptoms_text: str = None) -> Dict[str, Any]:
        """Generate medical response using Aloe medical model."""

        if not self._aloe_adapter or not self._aloe_adapter.is_model_loaded():
            self.logger.warning("Aloe medical model not available, using basic fallback")
            return await self._basic_fallback_response(session)

        try:
            # Create a session-like object with symptoms for Aloe adapter
            aloe_session = type('AloeSession', (), {
                'symptoms': symptoms_text or "general medical consultation",
                'patient': type('Patient', (), {
                    'age': session.patient_demographics.get('age', {}).get('value'),
                    'gender': session.patient_demographics.get('sex', 'unknown')
                })()
            })()

            # Use Aloe model for diagnosis
            aloe_result = await self._aloe_adapter.diagnose(aloe_session)

            # Convert Aloe response to Infermedica-compatible format
            primary_diagnosis = aloe_result.get('primary_diagnosis', {})
            differential_diagnoses = aloe_result.get('differential_diagnoses', [])

            # Build conditions list
            conditions = []
            if primary_diagnosis:
                conditions.append({
                    "id": f"aloe_{primary_diagnosis.get('condition', 'unknown').lower().replace(' ', '_')}",
                    "name": primary_diagnosis.get('condition', 'Unknown condition'),
                    "common_name": primary_diagnosis.get('condition', 'Unknown'),
                    "probability": primary_diagnosis.get('confidence', 50) / 100.0
                })

            # Add differential diagnoses
            for diff_dx in differential_diagnoses[:3]:  # Limit to top 3
                conditions.append({
                    "id": f"aloe_{diff_dx.get('condition', 'unknown').lower().replace(' ', '_')}",
                    "name": diff_dx.get('condition', 'Unknown condition'),
                    "common_name": diff_dx.get('condition', 'Unknown'),
                    "probability": diff_dx.get('probability', 10) / 100.0
                })

            # Generate follow-up question from Aloe model
            follow_up_questions = aloe_result.get('follow_up_questions', [])
            question_text = follow_up_questions[0] if follow_up_questions else "Do you have any other symptoms?"

            # Update session with Aloe results
            session.confidence_score = primary_diagnosis.get('confidence', 0) / 100.0
            session.urgency_level = aloe_result.get('urgency', 'MEDIUM')
            session.aloe_result = aloe_result  # Store full Aloe result

            return {
                "question": {
                    "type": "single",
                    "text": question_text,
                    "items": [
                        {"id": "follow_up", "name": "Follow-up", "choices": [
                            {"id": "yes", "label": "Yes"},
                            {"id": "no", "label": "No"},
                            {"id": "unsure", "label": "Not sure"}
                        ]}
                    ]
                },
                "conditions": conditions,
                "should_stop": len(session.evidence) >= 2 or session.confidence_score > 0.7,
                "extras": {
                    "aloe_diagnosis": aloe_result,
                    "urgency": aloe_result.get('urgency', 'MEDIUM'),
                    "emergency_detected": aloe_result.get('emergency_detected', False)
                }
            }

        except Exception as e:
            self.logger.error(f"Aloe medical model failed: {e}")
            return await self._basic_fallback_response(session)

    async def _basic_fallback_response(self, session: DiagnosisSession) -> Dict[str, Any]:
        """Basic fallback response when all AI models fail."""

        conditions = [
            {
                "id": "c_general",
                "name": "Medical consultation required",
                "common_name": "Requires professional evaluation",
                "probability": 0.8
            }
        ]

        return {
            "question": {
                "type": "single",
                "text": "Please consult with a healthcare professional for proper diagnosis.",
                "items": [
                    {"id": "s_consult", "name": "Medical consultation", "choices": [
                        {"id": "urgent", "label": "Urgent consultation needed"},
                        {"id": "routine", "label": "Routine consultation"},
                        {"id": "emergency", "label": "Emergency - seek immediate help"}
                    ]}
                ]
            },
            "conditions": conditions,
            "should_stop": True,
            "extras": {"fallback_used": True}
        }

    async def _generate_follow_up_questions(
        self,
        session: DiagnosisSession,
        infermedica_result: Dict[str, Any]
    ) -> List[str]:
        """Generate follow-up questions based on initial assessment."""

        questions = []

        # Extract question from Infermedica result
        question_data = infermedica_result.get("question", {})
        if question_data and not session.should_stop:
            question_text = question_data.get("text", "")
            if question_text:
                questions.append(question_text)

        # Add contextual follow-up questions
        if len(session.evidence) < 5:
            questions.extend([
                "How long have you been experiencing these symptoms?",
                "On a scale of 1-10, how would you rate your pain or discomfort?",
                "Have you taken any medications for these symptoms?"
            ])

        return questions[:3]  # Limit to 3 questions

    async def _generate_drug_recommendations(
        self,
        session: DiagnosisSession,
        infermedica_result: Dict[str, Any]
    ) -> List[DrugRecommendation]:
        """Generate drug recommendations based on diagnosis."""

        recommendations = []
        conditions = infermedica_result.get("conditions", [])

        if not conditions:
            return recommendations

        # Get top condition
        top_condition = conditions[0] if conditions else None
        if not top_condition:
            return recommendations

        condition_name = top_condition.get("common_name", "").lower()

        # Map conditions to drug recommendations
        if "cold" in condition_name or "viral" in condition_name:
            recommendations.extend([
                self._indian_drug_mapping["paracetamol"],
                # Add vitamin C recommendation
                DrugRecommendation(
                    generic_name="Vitamin C",
                    brand_names=["Limcee", "Celin", "Redoxon"],
                    dosage="500mg",
                    frequency="Once daily",
                    duration="5-7 days",
                    route="Oral",
                    contraindications=["Kidney stones (high doses)"],
                    side_effects=["Stomach upset (high doses)"],
                    indian_availability=True,
                    estimated_cost_inr="₹1-3 per tablet"
                )
            ])
        elif "fever" in condition_name:
            recommendations.append(self._indian_drug_mapping["paracetamol"])
        elif "pain" in condition_name:
            recommendations.extend([
                self._indian_drug_mapping["paracetamol"],
                self._indian_drug_mapping["ibuprofen"]
            ])
        elif "infection" in condition_name and "bacterial" in condition_name:
            recommendations.append(self._indian_drug_mapping["amoxicillin"])

        return recommendations[:3]  # Limit to 3 recommendations

    async def _create_final_medical_response(
        self,
        session: DiagnosisSession,
        infermedica_result: Dict[str, Any],
        drug_recommendations: List[DrugRecommendation],
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient]
    ) -> MedicalResponse:
        """Create final comprehensive medical response."""

        conditions = infermedica_result.get("conditions", [])
        top_condition = conditions[0] if conditions else None

        # Determine urgency level
        urgency = self._determine_urgency_level(symptoms, conditions)

        # Create response text
        if top_condition:
            condition_name = top_condition.get("common_name", top_condition.get("name", "Unknown condition"))
            probability = top_condition.get("probability", 0)

            response_text = f"""Based on your symptoms, the most likely condition is {condition_name} with {probability*100:.0f}% confidence.

**Symptoms Analysis:**
{self._format_symptoms_analysis(symptoms, infermedica_result)}

**Recommendations:**
{self._format_general_recommendations(urgency, condition_name)}

**Medication Suggestions:**
{self._format_drug_recommendations(drug_recommendations)}

**Important Notes:**
- This is an AI-generated assessment and should not replace professional medical advice
- If symptoms worsen or persist, please consult a healthcare provider
- For emergency symptoms, seek immediate medical attention"""
        else:
            response_text = """I was unable to determine a specific condition based on your symptoms. Please consider consulting with a healthcare professional for proper evaluation.

**General Recommendations:**
- Monitor your symptoms closely
- Stay hydrated and get adequate rest
- Seek medical attention if symptoms worsen
- Consider over-the-counter medications for symptom relief if appropriate"""

        # Create medical response
        medical_response = MedicalResponse.create_from_text(
            response_text,
            confidence=session.confidence_score,
            urgency=urgency,
            model_used="enhanced_medical_adapter"
        )

        # Add follow-up questions if available
        if session.follow_up_questions:
            medical_response.metadata["follow_up_questions"] = session.follow_up_questions

        # Add drug recommendations
        if drug_recommendations:
            medical_response.metadata["drug_recommendations"] = [
                {
                    "generic_name": drug.generic_name,
                    "brand_names": drug.brand_names,
                    "dosage": drug.dosage,
                    "frequency": drug.frequency,
                    "estimated_cost": drug.estimated_cost_inr
                }
                for drug in drug_recommendations
            ]

        # Add recommendations
        if top_condition:
            medical_response.add_recommendation(f"Primary diagnosis: {top_condition.get('common_name', 'Unknown')}")

        for drug in drug_recommendations:
            medical_response.add_recommendation(
                f"Consider {drug.generic_name} ({drug.dosage}) {drug.frequency}"
            )

        # Add red flags if urgent
        if urgency == UrgencyLevel.HIGH:
            medical_response.add_red_flag("High urgency symptoms detected")

        if symptoms.has_emergency_symptoms():
            medical_response.add_red_flag("Emergency symptoms present - seek immediate care")

        return medical_response

    def _determine_urgency_level(self, symptoms: MedicalSymptoms, conditions: List[Dict]) -> UrgencyLevel:
        """Determine urgency level based on symptoms and conditions."""

        if symptoms.has_emergency_symptoms():
            return UrgencyLevel.HIGH

        # Check for high-probability serious conditions
        for condition in conditions:
            probability = condition.get("probability", 0)
            condition_name = condition.get("name", "").lower()

            if probability > 0.8 and any(serious in condition_name for serious in
                                       ["heart", "stroke", "pneumonia", "appendicitis"]):
                return UrgencyLevel.HIGH

        # Check symptom severity
        high_severity_symptoms = symptoms.get_high_severity_symptoms()
        if len(high_severity_symptoms) >= 2:
            return UrgencyLevel.MODERATE

        return UrgencyLevel.LOW

    def _format_symptoms_analysis(self, symptoms: MedicalSymptoms, infermedica_result: Dict) -> str:
        """Format symptoms analysis for response."""

        analysis_parts = []

        # List main symptoms
        if symptoms.extracted_symptoms:
            analysis_parts.append(f"Main symptoms: {', '.join(symptoms.extracted_symptoms[:5])}")

        # Add severity information
        high_severity = symptoms.get_high_severity_symptoms()
        if high_severity:
            analysis_parts.append(f"High severity symptoms: {', '.join(high_severity)}")

        # Add emergency indicators
        if symptoms.has_emergency_symptoms():
            analysis_parts.append("⚠️ Emergency symptoms detected")

        return "\n".join(analysis_parts) if analysis_parts else "No specific symptoms identified"

    def _format_general_recommendations(self, urgency: UrgencyLevel, condition_name: str) -> str:
        """Format general recommendations based on urgency and condition."""

        recommendations = []

        if urgency == UrgencyLevel.HIGH:
            recommendations.append("🚨 Seek immediate medical attention")
            recommendations.append("Consider visiting emergency department")
        elif urgency == UrgencyLevel.MODERATE:
            recommendations.append("Schedule appointment with healthcare provider within 24-48 hours")
            recommendations.append("Monitor symptoms closely")
        else:
            recommendations.append("Rest and monitor symptoms")
            recommendations.append("Consider home remedies and over-the-counter medications")

        # Add condition-specific recommendations
        if "cold" in condition_name.lower():
            recommendations.extend([
                "Stay hydrated with warm fluids",
                "Get adequate rest",
                "Use humidifier or steam inhalation"
            ])
        elif "fever" in condition_name.lower():
            recommendations.extend([
                "Stay hydrated",
                "Rest in cool environment",
                "Monitor temperature regularly"
            ])

        return "\n".join(f"• {rec}" for rec in recommendations)

    def _format_drug_recommendations(self, drug_recommendations: List[DrugRecommendation]) -> str:
        """Format drug recommendations for response."""

        if not drug_recommendations:
            return "No specific medications recommended at this time."

        formatted_drugs = []
        for drug in drug_recommendations:
            drug_info = f"""**{drug.generic_name}** ({', '.join(drug.brand_names[:2])})
   • Dosage: {drug.dosage}
   • Frequency: {drug.frequency}
   • Duration: {drug.duration}
   • Estimated cost: {drug.estimated_cost_inr}
   • Contraindications: {', '.join(drug.contraindications[:2])}"""
            formatted_drugs.append(drug_info)

        disclaimer = "\n\n⚠️ **Important:** Consult a pharmacist or doctor before taking any medications. Check for allergies and drug interactions."

        return "\n\n".join(formatted_drugs) + disclaimer

    async def _fallback_analysis(
        self,
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient],
        error_message: str
    ) -> MedicalResponse:
        """Perform fallback analysis using local model."""

        try:
            if self._fallback_model:
                # Use fallback model for basic analysis
                prompt = f"""Analyze these medical symptoms and provide recommendations:
Symptoms: {symptoms.raw_text}
Patient age: {getattr(patient_context, 'age', 'unknown') if patient_context else 'unknown'}
Patient gender: {getattr(patient_context, 'gender', 'unknown') if patient_context else 'unknown'}

Provide a brief medical assessment and recommendations."""

                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self._fallback_model(prompt, max_length=200, do_sample=True)[0]['generated_text']
                )

                response_text = result.replace(prompt, "").strip()
            else:
                response_text = "Unable to analyze symptoms due to technical issues. Please consult a healthcare professional."

            # Determine urgency
            urgency = UrgencyLevel.HIGH if symptoms.has_emergency_symptoms() else UrgencyLevel.MODERATE

            medical_response = MedicalResponse.create_from_text(
                response_text,
                confidence=0.3,
                urgency=urgency,
                model_used="fallback_model"
            )

            medical_response.add_recommendation("Consult healthcare professional for proper diagnosis")
            medical_response.metadata["fallback_reason"] = error_message

            return medical_response

        except Exception as e:
            self.logger.error(f"Fallback analysis failed: {e}")

            # Final fallback
            return MedicalResponse.create_from_text(
                "I apologize, but I'm unable to analyze your symptoms at this time. "
                "Please consult with a healthcare professional for proper medical evaluation.",
                confidence=0.1,
                urgency=UrgencyLevel.MODERATE,
                model_used="emergency_fallback"
            )

    # Implement remaining MedicalModelPort interface methods

    async def assess_urgency(
        self,
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None
    ) -> Dict[str, Any]:
        """Assess urgency of symptoms."""

        urgency_level = self._determine_urgency_level(symptoms, [])

        return {
            "urgency": urgency_level.value,
            "reasoning": f"Based on symptom analysis: {urgency_level.value} priority",
            "emergency_indicators": symptoms.has_emergency_symptoms(),
            "high_severity_symptoms": symptoms.get_high_severity_symptoms()
        }

    async def generate_differential_diagnosis(
        self,
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None
    ) -> List[str]:
        """Generate differential diagnosis list."""

        # This would typically use the Infermedica API or medical knowledge base
        # For now, provide basic differential based on symptoms

        symptom_text = symptoms.raw_text.lower()
        differentials = []

        if any(term in symptom_text for term in ["fever", "cough", "cold"]):
            differentials.extend(["Viral upper respiratory infection", "Common cold", "Influenza"])

        if any(term in symptom_text for term in ["headache", "pain"]):
            differentials.extend(["Tension headache", "Migraine", "Sinusitis"])

        if any(term in symptom_text for term in ["stomach", "abdominal", "nausea"]):
            differentials.extend(["Gastroenteritis", "Food poisoning", "Indigestion"])

        return differentials[:5]  # Limit to top 5

    async def check_drug_interactions(
        self,
        medications: List[str],
        patient_context: Optional[Patient] = None
    ) -> Dict[str, Any]:
        """Check for drug interactions."""

        # Simplified drug interaction checking
        interactions = []
        warnings = []

        # Check for common interaction patterns
        if "warfarin" in [med.lower() for med in medications]:
            if any("aspirin" in med.lower() or "ibuprofen" in med.lower() for med in medications):
                interactions.append("Warfarin + NSAIDs: Increased bleeding risk")

        if len([med for med in medications if "acetaminophen" in med.lower() or "paracetamol" in med.lower()]) > 1:
            warnings.append("Multiple acetaminophen-containing medications detected")

        return {
            "interactions": interactions,
            "warnings": warnings,
            "total_medications": len(medications),
            "risk_level": "high" if interactions else "low"
        }

    async def generate_treatment_recommendations(
        self,
        diagnosis: str,
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None
    ) -> List[str]:
        """Generate treatment recommendations."""

        recommendations = []
        diagnosis_lower = diagnosis.lower()

        # Basic treatment recommendations based on diagnosis
        if "cold" in diagnosis_lower or "viral" in diagnosis_lower:
            recommendations.extend([
                "Rest and adequate sleep",
                "Increase fluid intake",
                "Use humidifier or steam inhalation",
                "Consider paracetamol for fever/pain",
                "Throat lozenges for sore throat"
            ])
        elif "fever" in diagnosis_lower:
            recommendations.extend([
                "Paracetamol or ibuprofen for fever reduction",
                "Stay hydrated with fluids",
                "Rest in cool environment",
                "Monitor temperature regularly",
                "Seek medical attention if fever persists >3 days"
            ])
        elif "headache" in diagnosis_lower:
            recommendations.extend([
                "Rest in quiet, dark room",
                "Apply cold or warm compress",
                "Stay hydrated",
                "Consider paracetamol or ibuprofen",
                "Avoid triggers (stress, certain foods)"
            ])
        else:
            recommendations.extend([
                "Follow up with healthcare provider",
                "Monitor symptoms closely",
                "Take medications as prescribed",
                "Maintain healthy lifestyle",
                "Seek medical attention if symptoms worsen"
            ])

        return recommendations

    async def identify_red_flags(
        self,
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None
    ) -> List[str]:
        """Identify red flag symptoms."""

        red_flags = []
        symptom_text = symptoms.raw_text.lower()

        # Check for emergency symptoms
        emergency_keywords = [
            "chest pain", "difficulty breathing", "severe headache",
            "loss of consciousness", "severe abdominal pain",
            "high fever", "confusion", "seizure"
        ]

        for keyword in emergency_keywords:
            if keyword in symptom_text:
                red_flags.append(f"Emergency symptom detected: {keyword}")

        # Check for concerning patterns
        if symptoms.has_emergency_symptoms():
            red_flags.append("Multiple emergency indicators present")

        high_severity = symptoms.get_high_severity_symptoms()
        if len(high_severity) >= 3:
            red_flags.append("Multiple high-severity symptoms")

        return red_flags

    async def summarize_clinical_note(self, clinical_text: str) -> str:
        """Summarize clinical note."""

        if self._fallback_model:
            try:
                prompt = f"Summarize this clinical note: {clinical_text}"
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self._fallback_model(prompt, max_length=100)[0]['generated_text']
                )
                return result.replace(prompt, "").strip()
            except Exception as e:
                self.logger.error(f"Clinical note summarization failed: {e}")

        # Simple fallback summarization
        sentences = clinical_text.split('.')[:3]
        return '. '.join(sentences) + '.' if sentences else clinical_text[:200]

    async def extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract medical entities from text."""

        # Simple entity extraction using keyword matching
        entities = {
            "symptoms": [],
            "medications": [],
            "conditions": [],
            "body_parts": []
        }

        text_lower = text.lower()

        # Common symptoms
        symptom_keywords = [
            "fever", "headache", "cough", "pain", "nausea", "vomiting",
            "diarrhea", "fatigue", "dizziness", "shortness of breath"
        ]

        # Common medications
        medication_keywords = [
            "paracetamol", "ibuprofen", "aspirin", "amoxicillin",
            "crocin", "dolo", "brufen", "combiflam"
        ]

        # Common conditions
        condition_keywords = [
            "cold", "flu", "infection", "pneumonia", "diabetes",
            "hypertension", "asthma", "migraine"
        ]

        # Body parts
        body_part_keywords = [
            "head", "chest", "stomach", "abdomen", "back", "leg",
            "arm", "throat", "eye", "ear"
        ]

        # Extract entities
        for keyword in symptom_keywords:
            if keyword in text_lower:
                entities["symptoms"].append(keyword)

        for keyword in medication_keywords:
            if keyword in text_lower:
                entities["medications"].append(keyword)

        for keyword in condition_keywords:
            if keyword in text_lower:
                entities["conditions"].append(keyword)

        for keyword in body_part_keywords:
            if keyword in text_lower:
                entities["body_parts"].append(keyword)

        return entities

    async def get_model_confidence(self, analysis_result: Any) -> float:
        """Get confidence score for analysis result."""

        if isinstance(analysis_result, MedicalResponse):
            return analysis_result.confidence
        elif isinstance(analysis_result, dict) and "confidence" in analysis_result:
            return analysis_result["confidence"]
        else:
            return 0.5  # Default confidence

    async def is_model_available(self) -> bool:
        """Check if model is available."""
        return self._is_loaded

    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "name": "enhanced_medical_adapter",
            "version": "1.0.0",
            "backends": {
                "infermedica": bool(self.infermedica_app_id and self.infermedica_app_key),
                "fallback_model": self.fallback_model_name,
                "drug_recommendations": self.enable_drug_recommendations,
                "interactive_diagnosis": self.enable_interactive_diagnosis
            },
            "loaded": self._is_loaded,
            "active_sessions": len(self._active_sessions)
        }

    async def warm_up_model(self) -> bool:
        """Warm up the model."""
        try:
            await self._ensure_model_loaded()

            # Test basic functionality
            test_symptoms = MedicalSymptoms.from_text("test headache")
            await self.assess_urgency(test_symptoms)

            self.logger.info("Model warm-up completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Model warm-up failed: {e}")
            return False

    async def close(self):
        """Clean up resources."""
        if self._session:
            await self._session.close()

        # Clear active sessions
        self._active_sessions.clear()

        self.logger.info("Enhanced medical adapter closed")

    def __del__(self):
        """Destructor to ensure cleanup."""
        if hasattr(self, '_session') and self._session and not self._session.closed:
            # Note: This is not ideal for async cleanup, but serves as a safety net
            import warnings
            warnings.warn("EnhancedMedicalAdapter was not properly closed. Call close() method.")

    # Interactive diagnosis methods

    async def start_interactive_diagnosis(
        self,
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None
    ) -> str:
        """Start an interactive diagnosis session."""

        session_id = f"interactive_{int(time.time())}"
        session = await self._create_diagnosis_session(session_id, symptoms, patient_context)

        # Get initial assessment
        infermedica_result = await self._query_infermedica_diagnosis(session)

        # Generate first question
        questions = await self._generate_follow_up_questions(session, infermedica_result)

        if questions:
            session.follow_up_questions = questions
            return session_id
        else:
            # No questions needed, complete diagnosis
            session.should_stop = True
            return session_id

    async def answer_follow_up_question(
        self,
        session_id: str,
        question_index: int,
        answer: str
    ) -> Dict[str, Any]:
        """Answer a follow-up question in an interactive session."""

        if session_id not in self._active_sessions:
            raise MedicalAnalysisError(f"Session {session_id} not found")

        session = self._active_sessions[session_id]

        # Add answer to evidence
        if question_index < len(session.follow_up_questions):
            question = session.follow_up_questions[question_index]

            # Convert answer to evidence format
            evidence_item = {
                "id": f"q_{question_index}",
                "choice_id": "present" if answer.lower() in ["yes", "true", "1"] else "absent",
                "source": "follow_up"
            }
            session.evidence.append(evidence_item)

        # Get updated assessment
        infermedica_result = await self._query_infermedica_diagnosis(session)

        # Check if more questions needed
        if not session.should_stop:
            new_questions = await self._generate_follow_up_questions(session, infermedica_result)
            session.follow_up_questions.extend(new_questions)

        return {
            "session_id": session_id,
            "should_stop": session.should_stop,
            "confidence": session.confidence_score,
            "next_questions": session.follow_up_questions[question_index + 1:],
            "conditions": infermedica_result.get("conditions", [])
        }

    async def complete_interactive_diagnosis(self, session_id: str) -> MedicalResponse:
        """Complete an interactive diagnosis session."""

        if session_id not in self._active_sessions:
            raise MedicalAnalysisError(f"Session {session_id} not found")

        session = self._active_sessions[session_id]

        # Get final assessment
        infermedica_result = await self._query_infermedica_diagnosis(session)

        # Generate drug recommendations
        drug_recommendations = await self._generate_drug_recommendations(session, infermedica_result)

        # Create final response
        # Create dummy symptoms object for compatibility
        symptoms = MedicalSymptoms.from_text("interactive diagnosis session")

        medical_response = await self._create_final_medical_response(
            session, infermedica_result, drug_recommendations, symptoms, None
        )

        # Clean up session
        del self._active_sessions[session_id]

        return medical_response
