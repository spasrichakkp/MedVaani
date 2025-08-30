"""
Interactive Diagnosis Service.

This service manages interactive medical diagnosis sessions,
allowing for iterative questioning and refinement of diagnosis
based on patient responses.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from domain.entities.patient import Patient
from domain.value_objects.medical_symptoms import MedicalSymptoms
from domain.value_objects.medical_response import MedicalResponse
from infrastructure.adapters.enhanced_medical_adapter import (
    EnhancedMedicalAdapter,
    DiagnosisSession,
    DiagnosisStep
)
from infrastructure.logging.medical_logger import MedicalLogger


class QuestionType(Enum):
    """Types of follow-up questions."""
    YES_NO = "yes_no"
    MULTIPLE_CHOICE = "multiple_choice"
    SCALE = "scale"
    TEXT = "text"


@dataclass
class FollowUpQuestion:
    """Represents a follow-up question in the diagnosis process."""
    id: str
    text: str
    question_type: QuestionType
    options: Optional[List[str]] = None
    required: bool = True
    context: Optional[str] = None


@dataclass
class DiagnosisProgress:
    """Tracks progress of an interactive diagnosis session."""
    session_id: str
    total_questions: int
    answered_questions: int
    current_confidence: float
    estimated_completion: float
    current_step: str
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_questions == 0:
            return 0.0
        return min((self.answered_questions / self.total_questions) * 100, 100.0)


class InteractiveDiagnosisService:
    """
    Service for managing interactive medical diagnosis sessions.
    
    This service provides:
    1. Session management for ongoing diagnoses
    2. Dynamic question generation based on responses
    3. Progress tracking and confidence scoring
    4. Adaptive questioning based on patient responses
    """
    
    def __init__(
        self,
        medical_adapter: EnhancedMedicalAdapter,
        logger: Optional[MedicalLogger] = None
    ):
        """
        Initialize the interactive diagnosis service.
        
        Args:
            medical_adapter: Enhanced medical adapter for AI analysis
            logger: Optional medical logger instance
        """
        self.medical_adapter = medical_adapter
        self.logger = logger or MedicalLogger(__name__)
        
        # Active sessions
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Question templates
        self._question_templates = self._initialize_question_templates()
    
    def _initialize_question_templates(self) -> Dict[str, FollowUpQuestion]:
        """Initialize common question templates."""
        
        return {
            "fever_severity": FollowUpQuestion(
                id="fever_severity",
                text="How would you rate your fever on a scale of 1-10?",
                question_type=QuestionType.SCALE,
                options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                context="fever assessment"
            ),
            "pain_location": FollowUpQuestion(
                id="pain_location",
                text="Where exactly is your pain located?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["Head", "Chest", "Abdomen", "Back", "Arms", "Legs", "Other"],
                context="pain assessment"
            ),
            "symptom_duration": FollowUpQuestion(
                id="symptom_duration",
                text="How long have you been experiencing these symptoms?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["Less than 1 day", "1-3 days", "4-7 days", "1-2 weeks", "More than 2 weeks"],
                context="duration assessment"
            ),
            "medication_taken": FollowUpQuestion(
                id="medication_taken",
                text="Have you taken any medications for these symptoms?",
                question_type=QuestionType.YES_NO,
                context="medication history"
            ),
            "symptom_progression": FollowUpQuestion(
                id="symptom_progression",
                text="Are your symptoms getting better, worse, or staying the same?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["Getting better", "Getting worse", "Staying the same", "Fluctuating"],
                context="progression assessment"
            )
        }
    
    async def start_interactive_session(
        self,
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient] = None
    ) -> Dict[str, Any]:
        """
        Start a new interactive diagnosis session.
        
        Args:
            symptoms: Initial symptoms provided by patient
            patient_context: Optional patient information
            
        Returns:
            Dictionary containing session information and first questions
        """
        try:
            self.logger.info("Starting interactive diagnosis session")
            
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Start session with medical adapter
            adapter_session_id = await self.medical_adapter.start_interactive_diagnosis(
                symptoms, patient_context
            )
            
            # Create session tracking
            session_data = {
                "session_id": session_id,
                "adapter_session_id": adapter_session_id,
                "symptoms": symptoms,
                "patient_context": patient_context,
                "questions_asked": [],
                "answers_given": [],
                "current_step": DiagnosisStep.INITIAL_ASSESSMENT.value,
                "confidence_history": [],
                "start_time": asyncio.get_event_loop().time()
            }
            
            self._active_sessions[session_id] = session_data
            
            # Generate initial follow-up questions
            initial_questions = await self._generate_contextual_questions(symptoms, patient_context)
            
            # Calculate initial progress
            progress = DiagnosisProgress(
                session_id=session_id,
                total_questions=len(initial_questions) + 3,  # Estimate
                answered_questions=0,
                current_confidence=0.3,
                estimated_completion=0.0,
                current_step="Initial Assessment"
            )
            
            session_data["progress"] = progress
            session_data["pending_questions"] = initial_questions
            
            self.logger.info(f"Interactive session {session_id} started with {len(initial_questions)} initial questions")
            
            return {
                "session_id": session_id,
                "questions": initial_questions[:2],  # Start with first 2 questions
                "progress": {
                    "percentage": progress.progress_percentage,
                    "current_step": progress.current_step,
                    "confidence": progress.current_confidence
                },
                "estimated_time_remaining": "2-3 minutes"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start interactive session: {e}")
            raise
    
    async def _generate_contextual_questions(
        self,
        symptoms: MedicalSymptoms,
        patient_context: Optional[Patient]
    ) -> List[FollowUpQuestion]:
        """Generate contextual follow-up questions based on symptoms."""
        
        questions = []
        symptom_text = symptoms.raw_text.lower()
        
        # Always ask about duration
        questions.append(self._question_templates["symptom_duration"])
        
        # Ask about progression
        questions.append(self._question_templates["symptom_progression"])
        
        # Symptom-specific questions
        if any(term in symptom_text for term in ["fever", "temperature", "hot"]):
            questions.append(self._question_templates["fever_severity"])
        
        if any(term in symptom_text for term in ["pain", "ache", "hurt"]):
            questions.append(self._question_templates["pain_location"])
        
        # Always ask about medications
        questions.append(self._question_templates["medication_taken"])
        
        # Add age-specific questions
        if patient_context and patient_context.age:
            if patient_context.age > 65:
                questions.append(FollowUpQuestion(
                    id="elderly_specific",
                    text="Have you experienced any falls or dizziness recently?",
                    question_type=QuestionType.YES_NO,
                    context="elderly assessment"
                ))
            elif patient_context.age < 18:
                questions.append(FollowUpQuestion(
                    id="pediatric_specific",
                    text="Has the child been eating and drinking normally?",
                    question_type=QuestionType.YES_NO,
                    context="pediatric assessment"
                ))
        
        return questions
    
    async def answer_question(
        self,
        session_id: str,
        question_id: str,
        answer: str
    ) -> Dict[str, Any]:
        """
        Process an answer to a follow-up question.
        
        Args:
            session_id: ID of the active session
            question_id: ID of the question being answered
            answer: Patient's answer
            
        Returns:
            Dictionary containing next questions and updated progress
        """
        try:
            if session_id not in self._active_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session_data = self._active_sessions[session_id]
            
            # Record the answer
            session_data["answers_given"].append({
                "question_id": question_id,
                "answer": answer,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # Update progress
            progress = session_data["progress"]
            progress.answered_questions += 1
            
            # Process answer with medical adapter if needed
            if hasattr(self.medical_adapter, 'answer_follow_up_question'):
                adapter_result = await self.medical_adapter.answer_follow_up_question(
                    session_data["adapter_session_id"],
                    len(session_data["answers_given"]) - 1,
                    answer
                )
                
                # Update confidence
                progress.current_confidence = adapter_result.get("confidence", progress.current_confidence)
                
                # Check if diagnosis is complete
                if adapter_result.get("should_stop", False):
                    return await self._complete_session(session_id)
            
            # Generate next questions based on answer
            next_questions = await self._get_next_questions(session_data, question_id, answer)
            
            # Update progress
            progress.estimated_completion = min(progress.progress_percentage + 20, 95)
            
            self.logger.info(f"Question answered in session {session_id}: {question_id} = {answer}")
            
            return {
                "session_id": session_id,
                "questions": next_questions,
                "progress": {
                    "percentage": progress.progress_percentage,
                    "current_step": progress.current_step,
                    "confidence": progress.current_confidence
                },
                "is_complete": len(next_questions) == 0,
                "estimated_time_remaining": self._estimate_time_remaining(progress)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process answer for session {session_id}: {e}")
            raise
    
    async def _get_next_questions(
        self,
        session_data: Dict[str, Any],
        answered_question_id: str,
        answer: str
    ) -> List[FollowUpQuestion]:
        """Get next questions based on the answer given."""
        
        next_questions = []
        pending_questions = session_data.get("pending_questions", [])
        
        # Remove answered question from pending
        pending_questions = [q for q in pending_questions if q.id != answered_question_id]
        
        # Generate follow-up questions based on answer
        if answered_question_id == "pain_location" and answer != "Other":
            # Ask about pain severity for specific location
            next_questions.append(FollowUpQuestion(
                id=f"pain_severity_{answer.lower()}",
                text=f"How severe is your {answer.lower()} pain on a scale of 1-10?",
                question_type=QuestionType.SCALE,
                options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                context=f"{answer.lower()} pain assessment"
            ))
        
        elif answered_question_id == "medication_taken" and answer.lower() in ["yes", "true"]:
            # Ask what medications were taken
            next_questions.append(FollowUpQuestion(
                id="medications_list",
                text="What medications have you taken?",
                question_type=QuestionType.TEXT,
                context="medication details"
            ))
        
        elif answered_question_id == "symptom_progression" and answer == "Getting worse":
            # Ask about rate of worsening
            next_questions.append(FollowUpQuestion(
                id="worsening_rate",
                text="How quickly are your symptoms getting worse?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["Very rapidly (hours)", "Gradually (days)", "Slowly (weeks)"],
                context="progression rate"
            ))
        
        # Add remaining pending questions (limit to 2 more)
        next_questions.extend(pending_questions[:2])
        
        # Update session data
        session_data["pending_questions"] = pending_questions[2:]
        
        return next_questions[:2]  # Limit to 2 questions at a time

    async def _complete_session(self, session_id: str) -> Dict[str, Any]:
        """Complete an interactive diagnosis session."""

        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session_data = self._active_sessions[session_id]

        try:
            # Get final diagnosis from medical adapter
            final_response = await self.medical_adapter.complete_interactive_diagnosis(
                session_data["adapter_session_id"]
            )

            # Update progress to complete
            progress = session_data["progress"]
            progress.answered_questions = progress.total_questions
            progress.current_confidence = final_response.confidence
            progress.current_step = "Diagnosis Complete"
            progress.estimated_completion = 100.0

            # Calculate session duration
            session_duration = asyncio.get_event_loop().time() - session_data["start_time"]

            self.logger.info(f"Interactive session {session_id} completed in {session_duration:.1f} seconds")

            # Clean up session
            del self._active_sessions[session_id]

            return {
                "session_id": session_id,
                "is_complete": True,
                "final_diagnosis": final_response,
                "progress": {
                    "percentage": 100.0,
                    "current_step": "Complete",
                    "confidence": final_response.confidence
                },
                "session_summary": {
                    "duration_seconds": session_duration,
                    "questions_answered": len(session_data["answers_given"]),
                    "final_confidence": final_response.confidence
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to complete session {session_id}: {e}")
            raise

    def _estimate_time_remaining(self, progress: DiagnosisProgress) -> str:
        """Estimate time remaining for diagnosis completion."""

        if progress.progress_percentage >= 90:
            return "Less than 1 minute"
        elif progress.progress_percentage >= 70:
            return "1-2 minutes"
        elif progress.progress_percentage >= 50:
            return "2-3 minutes"
        else:
            return "3-5 minutes"

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a diagnosis session."""

        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session_data = self._active_sessions[session_id]
        progress = session_data["progress"]

        return {
            "session_id": session_id,
            "progress": {
                "percentage": progress.progress_percentage,
                "current_step": progress.current_step,
                "confidence": progress.current_confidence
            },
            "questions_answered": len(session_data["answers_given"]),
            "pending_questions": len(session_data.get("pending_questions", [])),
            "estimated_time_remaining": self._estimate_time_remaining(progress),
            "is_active": True
        }

    async def cancel_session(self, session_id: str) -> bool:
        """Cancel an active diagnosis session."""

        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            self.logger.info(f"Session {session_id} cancelled")
            return True
        return False

    async def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self._active_sessions.keys())

    async def cleanup_expired_sessions(self, max_age_hours: float = 2.0) -> int:
        """Clean up expired sessions."""

        current_time = asyncio.get_event_loop().time()
        max_age_seconds = max_age_hours * 3600

        expired_sessions = []
        for session_id, session_data in self._active_sessions.items():
            if current_time - session_data["start_time"] > max_age_seconds:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self._active_sessions[session_id]

        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        return len(expired_sessions)

    # Progress tracking methods

    async def update_progress_callback(
        self,
        session_id: str,
        step: str,
        progress_percentage: float,
        message: str
    ) -> None:
        """Update progress for a session (for external progress tracking)."""

        if session_id in self._active_sessions:
            session_data = self._active_sessions[session_id]
            progress = session_data["progress"]

            progress.current_step = step
            progress.estimated_completion = progress_percentage

            # Log progress update
            self.logger.info(f"Session {session_id} progress: {step} ({progress_percentage:.1f}%)")

    async def get_diagnosis_insights(self, session_id: str) -> Dict[str, Any]:
        """Get insights about the diagnosis process for a session."""

        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session_data = self._active_sessions[session_id]
        answers = session_data["answers_given"]

        # Analyze answer patterns
        insights = {
            "total_questions": len(answers),
            "response_patterns": {},
            "confidence_trend": session_data.get("confidence_history", []),
            "key_symptoms_identified": [],
            "risk_factors": []
        }

        # Analyze responses
        for answer_data in answers:
            question_id = answer_data["question_id"]
            answer = answer_data["answer"]

            if "pain" in question_id and answer.isdigit():
                pain_level = int(answer)
                if pain_level >= 7:
                    insights["risk_factors"].append("High pain level reported")

            if "fever" in question_id and answer.isdigit():
                fever_level = int(answer)
                if fever_level >= 8:
                    insights["risk_factors"].append("High fever reported")

            if "progression" in question_id and "worse" in answer.lower():
                insights["risk_factors"].append("Symptoms worsening")

        return insights
