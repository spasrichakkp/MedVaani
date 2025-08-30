"""Meerkat adapter for medical AI model functionality."""

import asyncio
import torch
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

from application.ports.medical_model_port import (
    MedicalModelPort, MedicalAnalysisError, ModelUnavailableError
)
from domain.entities.patient import Patient
from domain.entities.medical_response import MedicalResponse, UrgencyLevel
from domain.value_objects.medical_symptoms import MedicalSymptoms
from infrastructure.logging.logger_factory import get_module_logger

try:
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        AutoModelForSeq2SeqLM,
        AutoConfig,
        pipeline
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class MeerkatAdapter(MedicalModelPort):
    """
    Meerkat adapter for medical AI reasoning.
    
    This adapter implements the MedicalModelPort using medical language models
    like Meerkat-8B or FLAN-T5 for medical analysis and reasoning.
    """
    
    def __init__(
        self,
        model_name: str = "google/flan-t5-base",
        device: str = "auto",
        torch_dtype: str = "float16",
        max_new_tokens: int = 256
    ):
        """
        Initialize Meerkat adapter.
        
        Args:
            model_name: Medical model name from Hugging Face
            device: Device to run model on ("auto", "cpu", "cuda")
            torch_dtype: Torch data type for model
            max_new_tokens: Maximum tokens to generate
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers not available. Install transformers library.")
        
        self.model_name = model_name
        self.device = self._resolve_device(device)
        self.torch_dtype = getattr(torch, torch_dtype)
        self.max_new_tokens = max_new_tokens
        
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None
        self.pipeline = None
        
        self._model_lock = asyncio.Lock()
        self._is_loaded = False
        
        self.logger = get_module_logger(__name__)
        
        # Medical prompts and templates
        self.symptom_analysis_template = """Medical consultation for patient with {symptoms}. Patient details: {patient_context}.

Provide medical assessment and recommendations:"""
        
        self.urgency_template = """Assess the medical urgency for these symptoms: {symptoms}

Patient context: {patient_context}

Urgency Classification:
- EMERGENCY: Life-threatening condition requiring immediate medical attention (call 911)
- HIGH: Serious condition requiring medical evaluation within 24 hours
- MODERATE: Should see healthcare provider within 2-3 days
- LOW: Routine care, can schedule regular appointment

Consider factors like:
- Severity and progression of symptoms
- Patient's age and medical history
- Potential for rapid deterioration
- Risk of complications

Provide urgency level with brief justification:"""
    
    def _resolve_device(self, device: str) -> str:
        """Resolve device string to actual device."""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    async def _ensure_model_loaded(self) -> None:
        """Ensure medical model is loaded (thread-safe)."""
        if self._is_loaded:
            return
        
        async with self._model_lock:
            if self._is_loaded:  # Double-check pattern
                return
            
            try:
                self.logger.info(f"Loading medical model: {self.model_name}")
                
                # Load tokenizer and model in thread pool
                loop = asyncio.get_event_loop()
                
                # Inspect config to pick correct model class
                config = await loop.run_in_executor(
                    None,
                    lambda: AutoConfig.from_pretrained(self.model_name)
                )

                self.tokenizer = await loop.run_in_executor(
                    None,
                    lambda: AutoTokenizer.from_pretrained(self.model_name)
                )

                def load_model():
                    if hasattr(config, "is_encoder_decoder") and config.is_encoder_decoder:
                        return AutoModelForSeq2SeqLM.from_pretrained(
                            self.model_name,
                            torch_dtype=self.torch_dtype,
                            low_cpu_mem_usage=True
                        ).to(self.device)
                    else:
                        return AutoModelForCausalLM.from_pretrained(
                            self.model_name,
                            torch_dtype=self.torch_dtype,
                            low_cpu_mem_usage=True
                        ).to(self.device)

                self.model = await loop.run_in_executor(None, load_model)

                # Create generation pipeline; choose task by architecture
                task_name = "text2text-generation" if getattr(config, "is_encoder_decoder", False) else "text-generation"

                # Configure pipeline parameters based on model type
                pipeline_kwargs = {
                    "model": self.model,
                    "tokenizer": self.tokenizer,
                    "max_new_tokens": self.max_new_tokens,
                    "do_sample": False
                }

                # Only add temperature for text-generation (causal models)
                # text2text-generation (seq2seq) models ignore temperature when do_sample=False
                if task_name == "text-generation":
                    pipeline_kwargs["temperature"] = 0.1

                self.pipeline = await loop.run_in_executor(
                    None,
                    lambda: pipeline(task_name, **pipeline_kwargs)
                )
                
                self._is_loaded = True
                self.logger.info(f"Medical model loaded successfully")
                
            except Exception as e:
                self.logger.error(f"Failed to load medical model: {e}")
                raise ModelUnavailableError(f"Model loading failed: {e}") from e
    
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
        """
        try:
            await self._ensure_model_loaded()
            
            # Prepare prompt
            patient_info = self._format_patient_context(patient_context)
            prompt = self.symptom_analysis_template.format(
                patient_context=patient_info,
                symptoms=symptoms.raw_text
            )
            
            # Generate response
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                self._generate_text_sync,
                prompt
            )
            
            # Parse response into MedicalResponse
            medical_response = self._parse_medical_response(response_text, symptoms)
            medical_response.model_used = self.model_name
            
            return medical_response
            
        except Exception as e:
            self.logger.error(f"Symptom analysis failed: {e}")
            raise MedicalAnalysisError(f"Medical analysis failed: {e}") from e
    
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
        """
        try:
            await self._ensure_model_loaded()
            
            # Prepare drug interaction prompt
            patient_info = self._format_patient_context(patient_context)
            medications_str = ", ".join(medications)
            
            prompt = f"""
Check for drug interactions between these medications: {medications_str}

Patient context: {patient_info}

Please identify:
1. Any dangerous interactions
2. Contraindications
3. Warnings
4. Recommendations

Drug interaction analysis:"""
            
            # Generate response
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                self._generate_text_sync,
                prompt
            )
            
            return {
                "medications": medications,
                "analysis": response_text,
                "interactions": self._extract_interactions(response_text),
                "warnings": self._extract_warnings(response_text)
            }
            
        except Exception as e:
            self.logger.error(f"Drug interaction check failed: {e}")
            return {"error": str(e), "interactions": [], "warnings": []}
    
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
        try:
            await self._ensure_model_loaded()
            
            patient_info = self._format_patient_context(patient_context)
            prompt = f"""
Generate a differential diagnosis for these symptoms: {symptoms.raw_text}

Patient context: {patient_info}

List the top 5 most likely diagnoses with brief explanations:

Differential diagnosis:"""
            
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                self._generate_text_sync,
                prompt
            )
            
            return self._parse_differential_diagnosis(response_text)
            
        except Exception as e:
            self.logger.error(f"Differential diagnosis failed: {e}")
            return []
    
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
        try:
            await self._ensure_model_loaded()
            
            patient_info = self._format_patient_context(patient_context)
            prompt = self.urgency_template.format(
                symptoms=symptoms.raw_text,
                patient_context=patient_info
            )
            
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                self._generate_text_sync,
                prompt
            )
            
            urgency_level = self._extract_urgency_level(response_text)
            
            return {
                "urgency": urgency_level,
                "reasoning": response_text,
                "emergency_indicators": symptoms.has_emergency_symptoms()
            }
            
        except Exception as e:
            self.logger.error(f"Urgency assessment failed: {e}")
            return {"urgency": "moderate", "error": str(e)}
    
    def _format_patient_context(self, patient: Optional[Patient]) -> str:
        """Format patient context for prompts."""
        if not patient:
            return "No patient context provided"
        
        context_parts = []
        
        if patient.age:
            context_parts.append(f"Age: {patient.age}")
        
        if patient.gender:
            context_parts.append(f"Gender: {patient.gender}")
        
        if patient.medical_history:
            context_parts.append(f"Medical history: {', '.join(patient.medical_history)}")
        
        if patient.current_medications:
            context_parts.append(f"Current medications: {', '.join(patient.current_medications)}")
        
        if patient.allergies:
            context_parts.append(f"Allergies: {', '.join(patient.allergies)}")
        
        return "; ".join(context_parts) if context_parts else "No patient context provided"
    
    def _generate_text_sync(self, prompt: str) -> str:
        """Synchronous text generation for thread pool execution."""
        try:
            if self.pipeline:
                result = self.pipeline(prompt)
                if result and len(result) > 0:
                    return result[0]["generated_text"]
            
            # Fallback to direct model inference
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    do_sample=False,
                    temperature=0.1,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the original prompt from response
            if prompt in response:
                response = response.replace(prompt, "").strip()
            
            return response
            
        except Exception as e:
            raise MedicalAnalysisError(f"Text generation failed: {e}") from e
    
    def _parse_medical_response(self, response_text: str, symptoms: MedicalSymptoms) -> MedicalResponse:
        """Parse AI response into MedicalResponse object."""
        # Extract urgency level
        urgency = self._extract_urgency_level(response_text)

        # Create medical response
        medical_response = MedicalResponse.create_from_text(
            response_text,
            confidence=0.7,  # Default confidence
            urgency=urgency
        )

        # Extract recommendations
        recommendations = self._extract_recommendations(response_text)
        for rec in recommendations:
            medical_response.add_recommendation(rec)

        # Extract red flags
        red_flags = self._extract_red_flags(response_text)
        for flag in red_flags:
            medical_response.add_red_flag(flag)

        return medical_response
    
    def _extract_urgency_level(self, text_or_level: Any) -> UrgencyLevel:
        """Extract urgency level from response or pass through if already an enum."""
        # Pass-through if already an UrgencyLevel
        if isinstance(text_or_level, UrgencyLevel):
            return text_or_level

        # Fall back to string parsing
        try:
            text_lower = str(text_or_level).lower()
        except Exception:
            return UrgencyLevel.MODERATE

        if any(word in text_lower for word in ["emergency", "immediate", "urgent", "911"]):
            return UrgencyLevel.EMERGENCY
        elif any(word in text_lower for word in ["high", "soon", "24 hours"]):
            return UrgencyLevel.HIGH
        elif any(word in text_lower for word in ["low", "routine", "not urgent"]):
            return UrgencyLevel.LOW
        else:
            return UrgencyLevel.MODERATE
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from response text."""
        recommendations = []
        lines = text.split('\n')

        # Look for recommendations section
        in_recommendations_section = False
        for line in lines:
            line = line.strip()

            # Check if we're entering recommendations section
            if any(header in line.lower() for header in ["recommendation", "immediate action", "care", "treatment"]):
                in_recommendations_section = True
                continue

            # Check if we're leaving recommendations section
            if in_recommendations_section and any(header in line.lower() for header in ["red flag", "warning", "diagnosis", "assessment"]):
                in_recommendations_section = False
                continue

            # Extract recommendations
            if in_recommendations_section or any(keyword in line.lower() for keyword in ["recommend", "should", "advise", "suggest", "seek", "contact", "call"]):
                if line and not line.startswith('#') and len(line) > 10:
                    # Clean up bullet points and numbering
                    cleaned_line = line.lstrip('•-*123456789. ')
                    if cleaned_line:
                        recommendations.append(cleaned_line)

        return recommendations[:6]  # Limit to 6 recommendations
    
    def _extract_red_flags(self, text: str) -> List[str]:
        """Extract red flags from response text."""
        red_flags = []
        lines = text.split('\n')

        # Look for red flags section
        in_red_flags_section = False
        for line in lines:
            line = line.strip()

            # Check if we're entering red flags section
            if any(header in line.lower() for header in ["red flag", "warning", "emergency", "immediate attention"]):
                in_red_flags_section = True
                continue

            # Check if we're leaving red flags section
            if in_red_flags_section and any(header in line.lower() for header in ["recommendation", "diagnosis", "assessment", "remember"]):
                in_red_flags_section = False
                continue

            # Extract red flags from section or by keywords
            if in_red_flags_section and line and len(line) > 5:
                cleaned_line = line.lstrip('•-*123456789. ')
                if cleaned_line:
                    red_flags.append(cleaned_line)

        # Also check for critical symptoms throughout text
        text_lower = text.lower()
        critical_symptoms = [
            "chest pain", "difficulty breathing", "severe pain", "loss of consciousness",
            "severe bleeding", "stroke symptoms", "heart attack", "call 911"
        ]

        for keyword in critical_symptoms:
            if keyword in text_lower and not any(keyword in flag.lower() for flag in red_flags):
                red_flags.append(f"Warning: {keyword}")

        return red_flags[:5]  # Limit to 5 red flags
    
    def _extract_interactions(self, text: str) -> List[str]:
        """Extract drug interactions from text."""
        interactions = []
        lines = text.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ["interaction", "contraindication", "avoid"]):
                interactions.append(line.strip())
        
        return interactions
    
    def _extract_warnings(self, text: str) -> List[str]:
        """Extract warnings from text."""
        warnings = []
        lines = text.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ["warning", "caution", "risk", "danger"]):
                warnings.append(line.strip())
        
        return warnings
    
    def _parse_differential_diagnosis(self, text: str) -> List[Dict[str, Any]]:
        """Parse differential diagnosis from text."""
        diagnoses = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith('#'):
                # Simple parsing - in practice you'd use more sophisticated NLP
                diagnoses.append({
                    "diagnosis": line,
                    "probability": max(0.1, 1.0 - (i * 0.15)),  # Decreasing probability
                    "reasoning": "Based on symptom analysis"
                })
        
        return diagnoses[:5]  # Top 5 diagnoses
    
    async def generate_treatment_recommendations(
        self, 
        diagnosis: str,
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None
    ) -> List[str]:
        """Generate treatment recommendations for a diagnosis."""
        try:
            await self._ensure_model_loaded()
            
            patient_info = self._format_patient_context(patient_context)
            prompt = f"""
Generate treatment recommendations for:
Diagnosis: {diagnosis}
Symptoms: {symptoms.raw_text}
Patient context: {patient_info}

Treatment recommendations:"""
            
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                self._generate_text_sync,
                prompt
            )
            
            return self._extract_recommendations(response_text)
            
        except Exception as e:
            self.logger.error(f"Treatment recommendations failed: {e}")
            return ["Consult with healthcare provider for treatment options"]
    
    async def identify_red_flags(
        self, 
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None
    ) -> List[str]:
        """Identify red flag symptoms requiring immediate attention."""
        try:
            await self._ensure_model_loaded()
            
            patient_info = self._format_patient_context(patient_context)
            prompt = f"""
Identify red flag symptoms that require immediate medical attention:
Symptoms: {symptoms.raw_text}
Patient context: {patient_info}

Red flags:"""
            
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                self._generate_text_sync,
                prompt
            )
            
            return self._extract_red_flags(response_text)
            
        except Exception as e:
            self.logger.error(f"Red flag identification failed: {e}")
            return []
    
    async def summarize_clinical_note(self, clinical_text: str) -> str:
        """Summarize a clinical note or medical text."""
        try:
            await self._ensure_model_loaded()
            
            prompt = f"""
Summarize this clinical note:
{clinical_text}

Summary:"""
            
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None,
                self._generate_text_sync,
                prompt
            )
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Clinical note summarization failed: {e}")
            return "Unable to summarize clinical note"
    
    async def extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract medical entities from text."""
        # This would typically use a specialized NER model
        # For now, return a simple implementation
        entities = {
            "symptoms": [],
            "medications": [],
            "conditions": [],
            "procedures": []
        }
        
        # Simple keyword-based extraction
        text_lower = text.lower()
        
        symptom_keywords = ["pain", "fever", "nausea", "headache", "cough"]
        for keyword in symptom_keywords:
            if keyword in text_lower:
                entities["symptoms"].append(keyword)
        
        return entities
    
    async def get_model_confidence(self, analysis_result: Any) -> float:
        """Get confidence score for a model analysis result."""
        # Simple confidence calculation
        if isinstance(analysis_result, str):
            # Base confidence on response length and content
            if len(analysis_result) > 100:
                return 0.8
            elif len(analysis_result) > 50:
                return 0.6
            else:
                return 0.4
        
        return 0.5
    
    async def is_model_available(self) -> bool:
        """Check if medical model is loaded and available."""
        try:
            await self._ensure_model_loaded()
            return self._is_loaded
        except Exception:
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded medical model."""
        return {
            "name": self.model_name,
            "type": "medical_language_model",
            "device": self.device,
            "torch_dtype": str(self.torch_dtype),
            "max_new_tokens": self.max_new_tokens,
            "is_loaded": self._is_loaded,
            "available": TRANSFORMERS_AVAILABLE
        }
    
    async def warm_up_model(self) -> bool:
        """Warm up the model for faster inference."""
        try:
            await self._ensure_model_loaded()
            
            # Run a simple inference to warm up
            test_prompt = "Test prompt for model warm-up"
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._generate_text_sync,
                test_prompt
            )
            
            self.logger.info("Model warm-up completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Model warm-up failed: {e}")
            return False
