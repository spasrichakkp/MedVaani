"""
Progress Tracking Service for Medical Diagnosis.

This service provides real-time progress indicators and user feedback
during medical diagnosis processing, ensuring users stay informed
during longer processing times.
"""

import asyncio
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from infrastructure.logging.medical_logger import MedicalLogger


class ProgressStage(Enum):
    """Stages of medical diagnosis progress."""
    INITIALIZING = "initializing"
    ANALYZING_SYMPTOMS = "analyzing_symptoms"
    CHECKING_MEDICAL_DATABASE = "checking_medical_database"
    GENERATING_QUESTIONS = "generating_questions"
    PROCESSING_RESPONSES = "processing_responses"
    FINDING_MEDICATIONS = "finding_medications"
    GENERATING_RECOMMENDATIONS = "generating_recommendations"
    FINALIZING_ASSESSMENT = "finalizing_assessment"
    COMPLETE = "complete"


@dataclass
class ProgressStep:
    """Represents a single step in the progress tracking."""
    stage: ProgressStage
    message: str
    estimated_duration_ms: int
    actual_duration_ms: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    substeps: List[str] = field(default_factory=list)
    
    @property
    def is_complete(self) -> bool:
        """Check if step is complete."""
        return self.end_time is not None
    
    @property
    def duration_ms(self) -> int:
        """Get actual or estimated duration."""
        if self.actual_duration_ms is not None:
            return self.actual_duration_ms
        return self.estimated_duration_ms


@dataclass
class ProgressUpdate:
    """Represents a progress update to send to clients."""
    session_id: str
    current_stage: ProgressStage
    message: str
    progress_percentage: float
    estimated_time_remaining_ms: int
    substep: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ProgressTrackingService:
    """
    Service for tracking and reporting progress of medical diagnosis operations.
    
    Provides:
    1. Real-time progress updates
    2. Estimated time remaining calculations
    3. User-friendly progress messages
    4. WebSocket support for live updates
    """
    
    def __init__(self, logger: Optional[MedicalLogger] = None):
        """
        Initialize the progress tracking service.
        
        Args:
            logger: Optional medical logger instance
        """
        self.logger = logger or MedicalLogger(__name__)
        
        # Active progress sessions
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Progress callbacks for real-time updates
        self._progress_callbacks: Dict[str, List[Callable]] = {}
        
        # Default progress steps with estimated durations
        self._default_steps = self._initialize_default_steps()
    
    def _initialize_default_steps(self) -> List[ProgressStep]:
        """Initialize default progress steps with estimated durations."""
        
        return [
            ProgressStep(
                stage=ProgressStage.INITIALIZING,
                message="Initializing medical analysis...",
                estimated_duration_ms=500,
                substeps=["Loading medical models", "Preparing analysis pipeline"]
            ),
            ProgressStep(
                stage=ProgressStage.ANALYZING_SYMPTOMS,
                message="Analyzing your symptoms...",
                estimated_duration_ms=2000,
                substeps=[
                    "Processing symptom description",
                    "Identifying key symptoms",
                    "Assessing symptom severity"
                ]
            ),
            ProgressStep(
                stage=ProgressStage.CHECKING_MEDICAL_DATABASE,
                message="Checking medical database...",
                estimated_duration_ms=1500,
                substeps=[
                    "Querying symptom database",
                    "Matching symptom patterns",
                    "Retrieving medical knowledge"
                ]
            ),
            ProgressStep(
                stage=ProgressStage.GENERATING_QUESTIONS,
                message="Generating follow-up questions...",
                estimated_duration_ms=1000,
                substeps=[
                    "Identifying information gaps",
                    "Formulating targeted questions",
                    "Prioritizing question importance"
                ]
            ),
            ProgressStep(
                stage=ProgressStage.FINDING_MEDICATIONS,
                message="Finding medication recommendations...",
                estimated_duration_ms=1200,
                substeps=[
                    "Searching drug database",
                    "Checking Indian availability",
                    "Calculating dosage recommendations"
                ]
            ),
            ProgressStep(
                stage=ProgressStage.GENERATING_RECOMMENDATIONS,
                message="Generating medical recommendations...",
                estimated_duration_ms=800,
                substeps=[
                    "Compiling diagnosis results",
                    "Formulating recommendations",
                    "Checking safety guidelines"
                ]
            ),
            ProgressStep(
                stage=ProgressStage.FINALIZING_ASSESSMENT,
                message="Finalizing assessment...",
                estimated_duration_ms=300,
                substeps=["Preparing final response", "Quality checks"]
            )
        ]
    
    async def start_progress_tracking(
        self,
        session_id: str,
        operation_type: str = "medical_diagnosis",
        custom_steps: Optional[List[ProgressStep]] = None
    ) -> None:
        """
        Start progress tracking for a session.
        
        Args:
            session_id: Unique identifier for the session
            operation_type: Type of operation being tracked
            custom_steps: Optional custom progress steps
        """
        steps = custom_steps or self._default_steps.copy()
        
        session_data = {
            "session_id": session_id,
            "operation_type": operation_type,
            "steps": steps,
            "current_step_index": 0,
            "start_time": time.time(),
            "total_estimated_duration_ms": sum(step.estimated_duration_ms for step in steps),
            "completed_duration_ms": 0
        }
        
        self._active_sessions[session_id] = session_data
        
        self.logger.info(f"Started progress tracking for session {session_id}")
        
        # Send initial progress update
        await self._send_progress_update(session_id, 0.0, "Starting medical analysis...")
    
    async def update_progress(
        self,
        session_id: str,
        stage: ProgressStage,
        substep: Optional[str] = None,
        custom_message: Optional[str] = None
    ) -> None:
        """
        Update progress for a specific stage.
        
        Args:
            session_id: Session identifier
            stage: Current progress stage
            substep: Optional substep description
            custom_message: Optional custom progress message
        """
        if session_id not in self._active_sessions:
            self.logger.warning(f"Session {session_id} not found for progress update")
            return
        
        session_data = self._active_sessions[session_id]
        steps = session_data["steps"]
        
        # Find the step for this stage
        step_index = next(
            (i for i, step in enumerate(steps) if step.stage == stage),
            None
        )
        
        if step_index is None:
            self.logger.warning(f"Stage {stage} not found in progress steps")
            return
        
        current_step = steps[step_index]
        current_time = time.time()
        
        # Start timing if not already started
        if current_step.start_time is None:
            current_step.start_time = current_time
            
            # Complete previous steps
            for i in range(step_index):
                if not steps[i].is_complete:
                    steps[i].end_time = current_time
                    steps[i].actual_duration_ms = int(
                        (current_time - (steps[i].start_time or current_time)) * 1000
                    )
        
        # Update session data
        session_data["current_step_index"] = step_index
        
        # Calculate progress percentage
        completed_duration = sum(
            step.duration_ms for step in steps[:step_index] if step.is_complete
        )
        
        # Add partial progress for current step
        if current_step.start_time:
            elapsed_current = (current_time - current_step.start_time) * 1000
            partial_progress = min(elapsed_current, current_step.estimated_duration_ms)
            completed_duration += partial_progress
        
        progress_percentage = min(
            (completed_duration / session_data["total_estimated_duration_ms"]) * 100,
            95.0  # Cap at 95% until complete
        )
        
        # Calculate estimated time remaining
        remaining_duration = session_data["total_estimated_duration_ms"] - completed_duration
        estimated_time_remaining_ms = max(int(remaining_duration), 0)
        
        # Prepare message
        message = custom_message or current_step.message
        if substep:
            message = f"{message} - {substep}"
        
        # Send progress update
        await self._send_progress_update(
            session_id,
            progress_percentage,
            message,
            estimated_time_remaining_ms,
            substep
        )
        
        self.logger.debug(f"Progress update for {session_id}: {stage.value} ({progress_percentage:.1f}%)")
    
    async def complete_progress(self, session_id: str, final_message: str = "Analysis complete") -> None:
        """
        Mark progress as complete for a session.
        
        Args:
            session_id: Session identifier
            final_message: Final completion message
        """
        if session_id not in self._active_sessions:
            return
        
        session_data = self._active_sessions[session_id]
        current_time = time.time()
        
        # Complete all remaining steps
        for step in session_data["steps"]:
            if not step.is_complete:
                step.end_time = current_time
                if step.start_time:
                    step.actual_duration_ms = int((current_time - step.start_time) * 1000)
        
        # Send final progress update
        await self._send_progress_update(session_id, 100.0, final_message, 0)
        
        # Calculate total duration
        total_duration = current_time - session_data["start_time"]
        
        self.logger.info(f"Progress tracking completed for session {session_id} in {total_duration:.2f}s")
        
        # Clean up session after a delay
        asyncio.create_task(self._cleanup_session_delayed(session_id, delay_seconds=30))
    
    async def _send_progress_update(
        self,
        session_id: str,
        progress_percentage: float,
        message: str,
        estimated_time_remaining_ms: int = 0,
        substep: Optional[str] = None
    ) -> None:
        """Send progress update to registered callbacks."""
        
        if session_id not in self._active_sessions:
            return
        
        session_data = self._active_sessions[session_id]
        current_step_index = session_data.get("current_step_index", 0)
        steps = session_data["steps"]
        
        current_stage = (
            steps[current_step_index].stage 
            if current_step_index < len(steps) 
            else ProgressStage.COMPLETE
        )
        
        update = ProgressUpdate(
            session_id=session_id,
            current_stage=current_stage,
            message=message,
            progress_percentage=progress_percentage,
            estimated_time_remaining_ms=estimated_time_remaining_ms,
            substep=substep
        )
        
        # Call registered callbacks
        callbacks = self._progress_callbacks.get(session_id, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update)
                else:
                    callback(update)
            except Exception as e:
                self.logger.error(f"Progress callback failed: {e}")
    
    def register_progress_callback(
        self,
        session_id: str,
        callback: Callable[[ProgressUpdate], None]
    ) -> None:
        """Register a callback for progress updates."""
        
        if session_id not in self._progress_callbacks:
            self._progress_callbacks[session_id] = []
        
        self._progress_callbacks[session_id].append(callback)
        
        self.logger.debug(f"Registered progress callback for session {session_id}")
    
    def unregister_progress_callback(
        self,
        session_id: str,
        callback: Callable[[ProgressUpdate], None]
    ) -> None:
        """Unregister a progress callback."""
        
        if session_id in self._progress_callbacks:
            try:
                self._progress_callbacks[session_id].remove(callback)
                if not self._progress_callbacks[session_id]:
                    del self._progress_callbacks[session_id]
            except ValueError:
                pass
    
    async def get_progress_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress status for a session."""
        
        if session_id not in self._active_sessions:
            return None
        
        session_data = self._active_sessions[session_id]
        current_step_index = session_data.get("current_step_index", 0)
        steps = session_data["steps"]
        
        if current_step_index < len(steps):
            current_step = steps[current_step_index]
            completed_steps = [step for step in steps if step.is_complete]
            
            return {
                "session_id": session_id,
                "current_stage": current_step.stage.value,
                "current_message": current_step.message,
                "progress_percentage": (len(completed_steps) / len(steps)) * 100,
                "completed_steps": len(completed_steps),
                "total_steps": len(steps),
                "estimated_time_remaining_ms": sum(
                    step.estimated_duration_ms for step in steps[current_step_index:]
                )
            }
        
        return {
            "session_id": session_id,
            "current_stage": "complete",
            "progress_percentage": 100.0,
            "completed_steps": len(steps),
            "total_steps": len(steps)
        }
    
    async def _cleanup_session_delayed(self, session_id: str, delay_seconds: int = 30) -> None:
        """Clean up session after a delay."""
        await asyncio.sleep(delay_seconds)
        
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
        
        if session_id in self._progress_callbacks:
            del self._progress_callbacks[session_id]
        
        self.logger.debug(f"Cleaned up progress tracking for session {session_id}")
    
    async def cleanup_expired_sessions(self, max_age_hours: float = 1.0) -> int:
        """Clean up expired progress tracking sessions."""
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        expired_sessions = []
        for session_id, session_data in self._active_sessions.items():
            if current_time - session_data["start_time"] > max_age_seconds:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self._active_sessions[session_id]
            if session_id in self._progress_callbacks:
                del self._progress_callbacks[session_id]
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired progress sessions")
        
        return len(expired_sessions)
