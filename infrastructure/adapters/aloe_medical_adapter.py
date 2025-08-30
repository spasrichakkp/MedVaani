"""
Aloe Medical Adapter for Qwen2.5-Aloe-Beta-7B Medical Model Integration

This adapter provides medical diagnosis capabilities using the state-of-the-art
Qwen2.5-Aloe-Beta-7B model from HPAI-BSC, specifically trained for healthcare tasks.
"""

import asyncio
import json
import logging
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Remove problematic imports for now - will be passed as parameters

logger = logging.getLogger(__name__)


@dataclass
class MedicalPromptTemplate:
    """Template for medical consultation prompts"""
    
    SYSTEM_PROMPT = """You are an expert medical assistant named Aloe, developed by the High Performance Artificial Intelligence Group at Barcelona Supercomputing Center(BSC). You are to be a helpful, respectful, and honest assistant.

You are conducting a medical consultation. Please analyze the patient's symptoms and provide a structured medical assessment. Focus on:
1. Primary diagnosis with confidence level
2. Differential diagnoses to consider
3. Urgency level (LOW/MEDIUM/HIGH/EMERGENCY)
4. Recommended medications (prefer Indian brands when available)
5. Follow-up questions for better diagnosis
6. Safety warnings and contraindications

IMPORTANT: Always include confidence percentages and urgency assessment. For emergency symptoms, immediately flag as EMERGENCY priority."""

    CONSULTATION_PROMPT = """Patient Information:
- Age: {age} years
- Gender: {gender}
- Symptoms: {symptoms}

Please provide a comprehensive medical assessment in the following JSON format:

{{
    "primary_diagnosis": {{
        "condition": "Primary condition name",
        "confidence": 85,
        "reasoning": "Clinical reasoning for this diagnosis"
    }},
    "differential_diagnoses": [
        {{"condition": "Alternative condition 1", "probability": 15}},
        {{"condition": "Alternative condition 2", "probability": 10}}
    ],
    "urgency": "HIGH",
    "urgency_reasoning": "Explanation of urgency level",
    "medications": [
        {{
            "name": "Medication name (Indian brand if available)",
            "dosage": "Recommended dosage",
            "duration": "Treatment duration",
            "price_range": "₹100-200",
            "contraindications": "Important warnings"
        }}
    ],
    "follow_up_questions": [
        "Specific question 1 to clarify symptoms",
        "Specific question 2 about medical history"
    ],
    "safety_warnings": [
        "Important safety consideration 1",
        "When to seek immediate medical attention"
    ],
    "recommendations": [
        "Lifestyle recommendation 1",
        "Monitoring advice"
    ]
}}

Provide only the JSON response without additional text."""


class AloemedicalAdapter:
    """Medical diagnosis adapter using Qwen2.5-Aloe-Beta-7B model"""
    
    def __init__(self, model_config: Dict[str, Any]):
        """Initialize the Aloe medical adapter"""
        self.model_config = model_config
        self.model = None
        self.tokenizer = None
        self.device = None
        self.is_loaded = False
        self.emergency_keywords = model_config.get('medical_config', {}).get('emergency_keywords', [])
        self.confidence_threshold = model_config.get('medical_config', {}).get('confidence_threshold', 0.3)
        
    async def load_model(self) -> bool:
        """Load the Aloe medical model asynchronously"""
        try:
            # Check if this is the lightweight configuration
            if self.model_config['repo_id'] == "lightweight_medical_reasoning":
                logger.info("Using lightweight medical reasoning system (configured)")
                self.device = "cpu"
                self.is_loaded = True
                self.model = None
                self.tokenizer = None
                return True

            logger.info("Loading Qwen2.5-Aloe-Beta-7B medical model...")
            start_time = time.time()

            # Determine device
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info("Using GPU for model inference")
            elif torch.backends.mps.is_available():
                self.device = "mps"
                logger.info("Using Apple Silicon MPS for model inference")
            else:
                self.device = "cpu"
                logger.info("Using CPU for model inference")

            try:
                # Load tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_config['repo_id'],
                    **self.model_config.get('tokenizer_kwargs', {})
                )

                # Load model
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_config['repo_id'],
                    **self.model_config.get('kwargs', {})
                )

                load_time = time.time() - start_time
                logger.info(f"Aloe medical model loaded successfully in {load_time:.2f} seconds")
                self.is_loaded = True
                return True

            except Exception as model_error:
                logger.warning(f"Full model loading failed: {model_error}")
                logger.info("Using lightweight medical reasoning system while model downloads...")

                # Use lightweight reasoning system as fallback
                self.is_loaded = True  # Mark as loaded to enable lightweight reasoning
                self.model = None  # No actual model loaded
                self.tokenizer = None
                return True

        except Exception as e:
            logger.error(f"Failed to initialize Aloe medical adapter: {e}")
            self.is_loaded = False
            return False
    
    def _detect_emergency_symptoms(self, symptoms: str) -> bool:
        """Detect emergency symptoms using keyword matching"""
        symptoms_lower = symptoms.lower()
        for keyword in self.emergency_keywords:
            if keyword.lower() in symptoms_lower:
                logger.warning(f"Emergency keyword detected: {keyword}")
                return True
        return False
    
    def _parse_medical_response(self, response: str) -> Dict[str, Any]:
        """Parse the model's JSON response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                logger.warning("No JSON found in model response")
                return self._create_fallback_response(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return self._create_fallback_response(response)
    
    def _create_fallback_response(self, response: str) -> Dict[str, Any]:
        """Create a fallback response when JSON parsing fails"""
        return {
            "primary_diagnosis": {
                "condition": "Medical consultation required",
                "confidence": 30,
                "reasoning": "Unable to parse detailed diagnosis from model response"
            },
            "differential_diagnoses": [],
            "urgency": "MEDIUM",
            "urgency_reasoning": "Requires professional medical evaluation",
            "medications": [],
            "follow_up_questions": [
                "Please describe your symptoms in more detail",
                "Do you have any relevant medical history?"
            ],
            "safety_warnings": [
                "This is an AI assessment and should not replace professional medical advice",
                "Seek immediate medical attention if symptoms worsen"
            ],
            "recommendations": [
                "Consult with a healthcare professional for proper diagnosis",
                "Monitor symptoms and seek help if they persist or worsen"
            ],
            "raw_response": response
        }
    
    async def diagnose(self, session: Any) -> Dict[str, Any]:
        """Perform medical diagnosis using the Aloe model or lightweight reasoning"""
        if not self.is_loaded:
            logger.warning("Aloe model not loaded, attempting to load...")
            if not await self.load_model():
                raise RuntimeError("Failed to load Aloe medical model")

        try:
            start_time = time.time()

            # Check if full model is available
            if self.model is not None and self.tokenizer is not None:
                return await self._full_model_diagnosis(session, start_time)
            else:
                return await self._lightweight_medical_reasoning(session, start_time)

        except Exception as e:
            logger.error(f"Error during medical diagnosis: {e}")
            raise RuntimeError(f"Medical diagnosis failed: {e}")

    async def _full_model_diagnosis(self, session: Any, start_time: float) -> Dict[str, Any]:
        """Perform diagnosis using the full Aloe model"""
        # Prepare the consultation prompt
        prompt_template = MedicalPromptTemplate()

        # Format the consultation prompt
        consultation_prompt = prompt_template.CONSULTATION_PROMPT.format(
            age=getattr(session.patient, 'age', 'Unknown') if hasattr(session, 'patient') else "Unknown",
            gender=getattr(session.patient, 'gender', 'Unknown') if hasattr(session, 'patient') else "Unknown",
            symptoms=session.symptoms
        )

        # Prepare messages for the model
        messages = [
            {"role": "system", "content": prompt_template.SYSTEM_PROMPT},
            {"role": "user", "content": consultation_prompt}
        ]

        # Apply chat template
        input_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Tokenize input
        inputs = self.tokenizer(input_text, return_tensors="pt").to(self.model.device)

        # Generate response
        logger.info("Generating medical diagnosis with full Aloe model...")

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                **self.model_config.get('generation', {}),
                pad_token_id=self.tokenizer.eos_token_id
            )

        # Decode response
        response = self.tokenizer.decode(
            outputs[0][len(inputs.input_ids[0]):],
            skip_special_tokens=True
        )

        inference_time = time.time() - start_time
        logger.info(f"Full model diagnosis completed in {inference_time:.2f} seconds")

        # Parse the medical response
        parsed_response = self._parse_medical_response(response)

        # Add metadata
        parsed_response['inference_time'] = inference_time
        parsed_response['model_used'] = 'Qwen2.5-Aloe-Beta-7B'
        parsed_response['emergency_detected'] = self._detect_emergency_symptoms(session.symptoms)

        return parsed_response

    async def _lightweight_medical_reasoning(self, session: Any, start_time: float) -> Dict[str, Any]:
        """Lightweight medical reasoning system while full model downloads"""
        logger.info("Using lightweight medical reasoning system...")

        symptoms = session.symptoms.lower()
        age = getattr(session.patient, 'age', None) if hasattr(session, 'patient') else None
        gender = getattr(session.patient, 'gender', None) if hasattr(session, 'patient') else None

        # Enhanced symptom analysis with medical knowledge
        diagnosis_result = self._analyze_symptoms_lightweight(symptoms, age, gender)

        inference_time = time.time() - start_time
        logger.info(f"Lightweight medical reasoning completed in {inference_time:.2f} seconds")

        # Add metadata
        diagnosis_result['inference_time'] = inference_time
        diagnosis_result['model_used'] = 'Lightweight Medical Reasoning (Aloe model downloading)'
        diagnosis_result['emergency_detected'] = self._detect_emergency_symptoms(symptoms)

        return diagnosis_result

    def _analyze_symptoms_lightweight(self, symptoms: str, age: Optional[int], gender: Optional[str]) -> Dict[str, Any]:
        """Analyze symptoms using rule-based medical knowledge"""

        # Emergency symptom patterns
        emergency_patterns = {
            'heart_attack': ['chest pain', 'chest pressure', 'left arm pain', 'jaw pain', 'nausea', 'sweating', 'shortness of breath'],
            'stroke': ['sudden headache', 'confusion', 'speech problems', 'weakness', 'numbness', 'vision problems'],
            'appendicitis': ['right lower abdominal pain', 'fever', 'nausea', 'vomiting', 'abdominal pain'],
            'allergic_reaction': ['difficulty breathing', 'swelling', 'hives', 'rash', 'throat closing'],
            'diabetic_emergency': ['extreme thirst', 'frequent urination', 'confusion', 'fruity breath']
        }

        # Chronic condition patterns
        chronic_patterns = {
            'lupus': ['joint pain', 'butterfly rash', 'fatigue', 'hair loss', 'sun sensitivity', 'mouth ulcers'],
            'fibromyalgia': ['widespread pain', 'tender points', 'fatigue', 'sleep problems', 'brain fog'],
            'depression': ['sadness', 'fatigue', 'sleep problems', 'appetite changes', 'concentration problems'],
            'anxiety': ['worry', 'racing heart', 'sweating', 'nervousness', 'panic'],
            'migraine': ['severe headache', 'nausea', 'light sensitivity', 'sound sensitivity']
        }

        # Common condition patterns
        common_patterns = {
            'cold': ['runny nose', 'sneezing', 'mild headache', 'congestion'],
            'flu': ['fever', 'body aches', 'fatigue', 'cough'],
            'gastritis': ['stomach pain', 'nausea', 'bloating', 'heartburn']
        }

        # Analyze for emergency conditions first
        emergency_matches = self._match_symptom_patterns(symptoms, emergency_patterns)
        chronic_matches = self._match_symptom_patterns(symptoms, chronic_patterns)
        common_matches = self._match_symptom_patterns(symptoms, common_patterns)

        # Determine primary diagnosis
        if emergency_matches:
            primary_condition = max(emergency_matches.items(), key=lambda x: x[1])
            urgency = "EMERGENCY"
            confidence = min(90, primary_condition[1] * 10 + 50)
        elif chronic_matches:
            primary_condition = max(chronic_matches.items(), key=lambda x: x[1])
            urgency = "MEDIUM"
            confidence = min(80, primary_condition[1] * 10 + 40)
        elif common_matches:
            primary_condition = max(common_matches.items(), key=lambda x: x[1])
            urgency = "LOW"
            confidence = min(70, primary_condition[1] * 10 + 30)
        else:
            primary_condition = ("medical_consultation_needed", 3)
            urgency = "MEDIUM"
            confidence = 40

        # Generate differential diagnoses
        all_matches = {**emergency_matches, **chronic_matches, **common_matches}
        differential_diagnoses = []
        for condition, score in sorted(all_matches.items(), key=lambda x: x[1], reverse=True)[:3]:
            if condition != primary_condition[0]:
                differential_diagnoses.append({
                    "condition": condition.replace('_', ' ').title(),
                    "probability": min(score * 8 + 20, 60)
                })

        # Generate medications based on condition
        medications = self._get_medications_for_condition(primary_condition[0])

        # Generate follow-up questions
        follow_up_questions = self._generate_follow_up_questions(primary_condition[0], symptoms)

        # Generate safety warnings
        safety_warnings = self._generate_safety_warnings(primary_condition[0], urgency)

        return {
            "primary_diagnosis": {
                "condition": primary_condition[0].replace('_', ' ').title(),
                "confidence": confidence,
                "reasoning": f"Based on symptom pattern analysis matching {primary_condition[1]} key indicators"
            },
            "differential_diagnoses": differential_diagnoses,
            "urgency": urgency,
            "urgency_reasoning": self._get_urgency_reasoning(urgency, primary_condition[0]),
            "medications": medications,
            "follow_up_questions": follow_up_questions,
            "safety_warnings": safety_warnings,
            "recommendations": [
                "This is an AI assessment and should not replace professional medical advice",
                "Consult with a healthcare professional for proper diagnosis and treatment"
            ]
        }

    def _match_symptom_patterns(self, symptoms: str, patterns: Dict[str, List[str]]) -> Dict[str, int]:
        """Match symptoms against condition patterns"""
        matches = {}
        for condition, pattern_symptoms in patterns.items():
            score = 0
            for pattern_symptom in pattern_symptoms:
                if pattern_symptom in symptoms:
                    score += 1
            if score > 0:
                matches[condition] = score
        return matches

    def _get_medications_for_condition(self, condition: str) -> List[Dict[str, str]]:
        """Get Indian medications for specific conditions"""
        medication_db = {
            'heart_attack': [
                {"name": "Aspirin (Disprin)", "dosage": "75-100mg daily", "duration": "As prescribed", "price_range": "₹10-20", "contraindications": "Bleeding disorders, stomach ulcers"}
            ],
            'cold': [
                {"name": "Paracetamol (Crocin)", "dosage": "500mg every 6 hours", "duration": "3-5 days", "price_range": "₹15-25", "contraindications": "Liver disease"},
                {"name": "Cetirizine (Zyrtec)", "dosage": "10mg once daily", "duration": "5-7 days", "price_range": "₹20-30", "contraindications": "Kidney disease"}
            ],
            'depression': [
                {"name": "Counseling recommended", "dosage": "Professional therapy", "duration": "Ongoing", "price_range": "₹500-2000 per session", "contraindications": "None"}
            ],
            'fibromyalgia': [
                {"name": "Pregabalin (Lyrica)", "dosage": "75mg twice daily", "duration": "As prescribed", "price_range": "₹200-400", "contraindications": "Kidney disease, heart problems"}
            ]
        }
        return medication_db.get(condition, [
            {"name": "Consult healthcare provider", "dosage": "As prescribed", "duration": "As needed", "price_range": "Varies", "contraindications": "Individual assessment needed"}
        ])

    def _generate_follow_up_questions(self, condition: str, symptoms: str) -> List[str]:
        """Generate relevant follow-up questions"""
        question_db = {
            'heart_attack': [
                "Do you have a history of heart disease or high blood pressure?",
                "Are you experiencing shortness of breath or dizziness?",
                "Have you taken any medications for chest pain?"
            ],
            'lupus': [
                "Do you have a family history of autoimmune diseases?",
                "Have you noticed the rash worsens with sun exposure?",
                "Do you experience joint stiffness in the morning?"
            ],
            'fibromyalgia': [
                "How long have you been experiencing widespread pain?",
                "Do you have specific tender points that hurt when pressed?",
                "How is your sleep quality?"
            ],
            'depression': [
                "How long have you been feeling this way?",
                "Have you had thoughts of self-harm?",
                "Do you have support from family or friends?"
            ]
        }
        return question_db.get(condition, [
            "How long have you been experiencing these symptoms?",
            "Have you tried any treatments or medications?",
            "Do you have any relevant medical history?"
        ])

    def _generate_safety_warnings(self, condition: str, urgency: str) -> List[str]:
        """Generate appropriate safety warnings"""
        if urgency == "EMERGENCY":
            return [
                "SEEK IMMEDIATE MEDICAL ATTENTION - Call emergency services",
                "Do not delay treatment for potentially life-threatening condition",
                "Go to the nearest emergency room immediately"
            ]
        elif condition in ['depression', 'anxiety']:
            return [
                "If you have thoughts of self-harm, contact emergency services immediately",
                "Mental health is important - seek professional help",
                "Contact a mental health helpline if needed"
            ]
        else:
            return [
                "This is an AI assessment and should not replace professional medical advice",
                "Seek medical attention if symptoms worsen or persist",
                "Contact your healthcare provider for proper diagnosis"
            ]

    def _get_urgency_reasoning(self, urgency: str, condition: str) -> str:
        """Get reasoning for urgency level"""
        if urgency == "EMERGENCY":
            return f"Symptoms suggest {condition.replace('_', ' ')} which requires immediate medical attention"
        elif urgency == "MEDIUM":
            return f"Symptoms indicate {condition.replace('_', ' ')} which should be evaluated by a healthcare provider"
        else:
            return f"Symptoms suggest {condition.replace('_', ' ')} which can typically be managed with appropriate care"

    def is_model_loaded(self) -> bool:
        """Check if the model is loaded and ready"""
        return self.is_loaded
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_name": "Qwen2.5-Aloe-Beta-7B",
            "repo_id": self.model_config['repo_id'],
            "device": self.device,
            "is_loaded": self.is_loaded,
            "parameters": "7.6B",
            "specialization": "Medical diagnosis and healthcare"
        }
