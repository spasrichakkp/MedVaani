"""Structured logger implementation for medical research application."""

import json
import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union
from contextvars import ContextVar
from pathlib import Path

from .log_config import LogConfig, LogFormat


# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredLogger:
    """
    Structured logger that provides consistent logging with metadata.
    
    This logger adds structure to log messages including correlation IDs,
    timestamps, and contextual information for better observability.
    """
    
    def __init__(self, name: str, config: LogConfig):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (usually module name)
            config: Logging configuration
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(name)
        self.logger.setLevel(config.get_python_log_level())
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup logging handlers based on configuration."""
        # Console handler
        if self.config.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.config.get_python_log_level())
            console_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(console_handler)
        
        # File handler
        if self.config.enable_file and self.config.log_file:
            self.config.create_log_directory()
            
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                self.config.log_file,
                maxBytes=self.config.max_file_size_mb * 1024 * 1024,
                backupCount=self.config.backup_count
            )
            file_handler.setLevel(self.config.get_python_log_level())
            file_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(file_handler)
    
    def _get_formatter(self) -> logging.Formatter:
        """Get appropriate formatter based on configuration."""
        if self.config.format == LogFormat.JSON:
            return JsonFormatter(self.config)
        elif self.config.format == LogFormat.RICH:
            return RichFormatter(self.config)
        else:
            return TextFormatter(self.config)
    
    def _build_log_record(
        self, 
        level: str, 
        message: str, 
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """Build structured log record."""
        record = {
            "message": message,
            "level": level,
            "logger": self.name
        }
        
        # Add timestamp
        if self.config.include_timestamp:
            record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Add correlation ID
        correlation_id = correlation_id_var.get()
        if correlation_id:
            record["correlation_id"] = correlation_id
        
        # Add caller information
        if self.config.include_module or self.config.include_function or self.config.include_line_number:
            frame = traceback.extract_stack()[-4]  # Go up the stack to find caller
            
            if self.config.include_module:
                record["module"] = Path(frame.filename).stem
            
            if self.config.include_function:
                record["function"] = frame.name
            
            if self.config.include_line_number:
                record["line"] = frame.lineno
        
        # Add exception information
        if exc_info:
            record["exception"] = {
                "type": type(exc_info).__name__,
                "message": str(exc_info),
                "traceback": traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__)
            }
        
        # Add extra fields
        if extra:
            record.update(extra)
        
        return record
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        if self.logger.isEnabledFor(logging.DEBUG):
            record = self._build_log_record("DEBUG", message, extra)
            # Avoid clashing with reserved LogRecord keys
            safe_extra = {k: v for k, v in record.items() if k not in {"message", "level", "logger"}}
            # Also avoid Python logging reserved attributes broadly
            reserved = {"message", "levelname", "levelno", "pathname", "filename", "module", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process"}
            safe_extra = {k: v for k, v in safe_extra.items() if k not in reserved}
            self.logger.debug(json.dumps(record) if self.config.enable_structured else message, extra=safe_extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        if self.logger.isEnabledFor(logging.INFO):
            record = self._build_log_record("INFO", message, extra)
            # Avoid clashing with reserved LogRecord keys
            safe_extra = {k: v for k, v in record.items() if k not in {"message", "level", "logger"}}
            # Also avoid Python logging reserved attributes broadly
            reserved = {"message", "levelname", "levelno", "pathname", "filename", "module", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process"}
            safe_extra = {k: v for k, v in safe_extra.items() if k not in reserved}
            self.logger.info(json.dumps(record) if self.config.enable_structured else message, extra=safe_extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        if self.logger.isEnabledFor(logging.WARNING):
            record = self._build_log_record("WARNING", message, extra)
            # Avoid clashing with reserved LogRecord keys
            safe_extra = {k: v for k, v in record.items() if k not in {"message", "level", "logger"}}
            # Also avoid Python logging reserved attributes broadly
            reserved = {"message", "levelname", "levelno", "pathname", "filename", "module", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process"}
            safe_extra = {k: v for k, v in safe_extra.items() if k not in reserved}
            self.logger.warning(json.dumps(record) if self.config.enable_structured else message, extra=safe_extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Log error message."""
        if self.logger.isEnabledFor(logging.ERROR):
            record = self._build_log_record("ERROR", message, extra, exc_info)
            # Avoid clashing with reserved LogRecord keys
            safe_extra = {k: v for k, v in record.items() if k not in {"message", "level", "logger"}}
            # Also avoid Python logging reserved attributes broadly
            reserved = {"message", "levelname", "levelno", "pathname", "filename", "module", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process"}
            safe_extra = {k: v for k, v in safe_extra.items() if k not in reserved}
            self.logger.error(json.dumps(record) if self.config.enable_structured else message, extra=safe_extra)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None) -> None:
        """Log critical message."""
        if self.logger.isEnabledFor(logging.CRITICAL):
            record = self._build_log_record("CRITICAL", message, extra, exc_info)
            # Avoid clashing with reserved LogRecord keys
            safe_extra = {k: v for k, v in record.items() if k not in {"message", "level", "logger"}}
            # Also avoid Python logging reserved attributes broadly
            reserved = {"message", "levelname", "levelno", "pathname", "filename", "module", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process"}
            safe_extra = {k: v for k, v in safe_extra.items() if k not in reserved}
            self.logger.critical(json.dumps(record) if self.config.enable_structured else message, extra=safe_extra)
    
    def log_consultation_start(self, consultation_id: str, patient_id: str, consultation_type: str) -> None:
        """Log consultation start event."""
        self.info("Consultation started", {
            "event": "consultation_start",
            "consultation_id": consultation_id,
            "patient_id": patient_id,
            "consultation_type": consultation_type
        })
    
    def log_consultation_complete(self, consultation_id: str, duration_ms: int, success: bool) -> None:
        """Log consultation completion event."""
        self.info("Consultation completed", {
            "event": "consultation_complete",
            "consultation_id": consultation_id,
            "duration_ms": duration_ms,
            "success": success
        })
    
    def log_model_operation(self, operation: str, model_name: str, duration_ms: int, success: bool) -> None:
        """Log model operation event."""
        self.info(f"Model operation: {operation}", {
            "event": "model_operation",
            "operation": operation,
            "model_name": model_name,
            "duration_ms": duration_ms,
            "success": success
        })
    
    def log_audio_processing(self, operation: str, audio_duration_ms: int, success: bool) -> None:
        """Log audio processing event."""
        self.info(f"Audio processing: {operation}", {
            "event": "audio_processing",
            "operation": operation,
            "audio_duration_ms": audio_duration_ms,
            "success": success
        })


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, config: LogConfig):
        super().__init__()
        self.config = config
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        
        # Add extra fields from record
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'lineno', 'funcName', 'created', 
                              'msecs', 'relativeCreated', 'thread', 'threadName', 
                              'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                    log_data[key] = value
        
        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Text formatter for human-readable logging."""
    
    def __init__(self, config: LogConfig):
        format_parts = []
        
        if config.include_timestamp:
            format_parts.append("%(asctime)s")
        
        format_parts.append("%(levelname)s")
        
        if config.include_module:
            format_parts.append("%(name)s")
        
        if config.include_function:
            format_parts.append("%(funcName)s")
        
        if config.include_line_number:
            format_parts.append("%(lineno)d")
        
        format_parts.append("%(message)s")
        
        format_string = " - ".join(format_parts)
        super().__init__(format_string)


class RichFormatter(logging.Formatter):
    """Rich formatter for colorized console output."""
    
    def __init__(self, config: LogConfig):
        super().__init__()
        self.config = config
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with Rich styling."""
        # This is a simplified version - in a real implementation,
        # you would use Rich's logging handler for proper formatting
        level_colors = {
            "DEBUG": "dim",
            "INFO": "blue",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold red"
        }
        
        color = level_colors.get(record.levelname, "white")
        return f"[{color}]{record.levelname}[/{color}] {record.getMessage()}"


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID for current context."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """Clear correlation ID from current context."""
    correlation_id_var.set(None)
