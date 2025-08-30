"""Medical-specific logger for enhanced medical diagnosis system."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from infrastructure.logging.logger_factory import get_module_logger


class MedicalLogger:
    """
    Medical-specific logger with enhanced logging for medical operations.
    
    Provides structured logging for medical diagnosis, drug recommendations,
    and patient interactions with appropriate privacy considerations.
    """
    
    def __init__(self, name: str):
        """
        Initialize medical logger.
        
        Args:
            name: Logger name (usually module name)
        """
        self.logger = get_module_logger(name)
        self._session_context: Dict[str, Any] = {}
    
    def set_session_context(self, session_id: str, **context) -> None:
        """Set context for current medical session."""
        self._session_context = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            **context
        }
    
    def clear_session_context(self) -> None:
        """Clear current session context."""
        self._session_context = {}
    
    def _format_medical_message(self, message: str, **kwargs) -> str:
        """Format message with medical context."""
        context_parts = []
        
        if self._session_context:
            session_id = self._session_context.get("session_id", "unknown")
            context_parts.append(f"[Session:{session_id}]")
        
        if kwargs:
            # Filter out sensitive information
            safe_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['patient_data', 'personal_info', 'medical_history']}
            if safe_kwargs:
                context_parts.append(f"[{safe_kwargs}]")
        
        if context_parts:
            return f"{' '.join(context_parts)} {message}"
        return message
    
    def info(self, message: str, **kwargs) -> None:
        """Log info level message."""
        formatted_message = self._format_medical_message(message, **kwargs)
        self.logger.info(formatted_message)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug level message."""
        formatted_message = self._format_medical_message(message, **kwargs)
        self.logger.debug(formatted_message)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning level message."""
        formatted_message = self._format_medical_message(message, **kwargs)
        self.logger.warning(formatted_message)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error level message."""
        formatted_message = self._format_medical_message(message, **kwargs)
        self.logger.error(formatted_message)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical level message."""
        formatted_message = self._format_medical_message(message, **kwargs)
        self.logger.critical(formatted_message)
    
    # Medical-specific logging methods
    
    def log_diagnosis_start(self, symptoms: str, patient_age: Optional[int] = None) -> None:
        """Log start of medical diagnosis."""
        self.info(
            "Starting medical diagnosis",
            symptom_count=len(symptoms.split()) if symptoms else 0,
            patient_age_provided=patient_age is not None
        )
    
    def log_diagnosis_complete(self, confidence: float, urgency: str, processing_time_ms: int) -> None:
        """Log completion of medical diagnosis."""
        self.info(
            "Medical diagnosis completed",
            confidence=confidence,
            urgency=urgency,
            processing_time_ms=processing_time_ms
        )
    
    def log_drug_recommendation(self, drug_name: str, reason: str) -> None:
        """Log drug recommendation."""
        self.info(
            "Drug recommendation generated",
            drug_name=drug_name,
            reason=reason
        )
    
    def log_interactive_question(self, question_type: str, question_text: str) -> None:
        """Log interactive diagnosis question."""
        self.info(
            "Interactive question generated",
            question_type=question_type,
            question_length=len(question_text)
        )
    
    def log_progress_update(self, stage: str, progress_percentage: float) -> None:
        """Log progress update."""
        self.debug(
            "Progress update",
            stage=stage,
            progress_percentage=progress_percentage
        )
    
    def log_api_request(self, endpoint: str, method: str, response_time_ms: int) -> None:
        """Log API request."""
        self.info(
            "API request processed",
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time_ms
        )
    
    def log_model_performance(self, model_name: str, load_time_ms: int, memory_usage_mb: float) -> None:
        """Log model performance metrics."""
        self.info(
            "Model performance metrics",
            model_name=model_name,
            load_time_ms=load_time_ms,
            memory_usage_mb=memory_usage_mb
        )
    
    def log_safety_warning(self, warning_type: str, details: str) -> None:
        """Log medical safety warning."""
        self.warning(
            f"Medical safety warning: {warning_type}",
            warning_type=warning_type,
            details=details
        )
    
    def log_emergency_detection(self, symptoms: str, confidence: float) -> None:
        """Log emergency symptom detection."""
        self.critical(
            "Emergency symptoms detected",
            confidence=confidence,
            symptom_indicators=len(symptoms.split()) if symptoms else 0
        )
    
    def log_fallback_usage(self, primary_service: str, fallback_service: str, reason: str) -> None:
        """Log fallback service usage."""
        self.warning(
            "Fallback service activated",
            primary_service=primary_service,
            fallback_service=fallback_service,
            reason=reason
        )
    
    def log_session_metrics(self, session_duration_ms: int, questions_asked: int, final_confidence: float) -> None:
        """Log session completion metrics."""
        self.info(
            "Medical session completed",
            session_duration_ms=session_duration_ms,
            questions_asked=questions_asked,
            final_confidence=final_confidence
        )
    
    def log_drug_interaction_check(self, drug_count: int, interactions_found: int) -> None:
        """Log drug interaction checking."""
        self.info(
            "Drug interaction check completed",
            drug_count=drug_count,
            interactions_found=interactions_found
        )
    
    def log_privacy_compliance(self, action: str, data_type: str) -> None:
        """Log privacy compliance actions."""
        self.info(
            "Privacy compliance action",
            action=action,
            data_type=data_type
        )
    
    def log_error_with_context(self, error: Exception, context: str) -> None:
        """Log error with medical context."""
        self.error(
            f"Medical operation failed: {context}",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context
        )
    
    def log_model_fallback(self, primary_model: str, fallback_model: str, reason: str) -> None:
        """Log model fallback usage."""
        self.warning(
            "Model fallback activated",
            primary_model=primary_model,
            fallback_model=fallback_model,
            reason=reason
        )
