"""Logging configuration for the medical research application."""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class LogLevel(Enum):
    """Log levels for the application."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(Enum):
    """Log output formats."""
    JSON = "json"
    TEXT = "text"
    RICH = "rich"


@dataclass
class LogConfig:
    """Configuration for logging system."""
    
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.TEXT
    log_file: Optional[Path] = None
    max_file_size_mb: int = 100
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = False
    enable_structured: bool = False
    include_timestamp: bool = True
    include_module: bool = True
    include_function: bool = True
    include_line_number: bool = True
    correlation_id_header: str = "X-Correlation-ID"
    
    @classmethod
    def development(cls) -> "LogConfig":
        """Create development logging configuration."""
        return cls(
            level=LogLevel.DEBUG,
            format=LogFormat.RICH,
            enable_console=True,
            enable_file=False,
            include_function=True,
            include_line_number=True
        )
    
    @classmethod
    def production(cls) -> "LogConfig":
        """Create production logging configuration."""
        return cls(
            level=LogLevel.INFO,
            format=LogFormat.JSON,
            enable_console=True,
            enable_file=True,
            enable_structured=True,
            log_file=Path("logs/medical_research.log"),
            include_function=False,
            include_line_number=False
        )
    
    @classmethod
    def testing(cls) -> "LogConfig":
        """Create testing logging configuration."""
        return cls(
            level=LogLevel.WARNING,
            format=LogFormat.TEXT,
            enable_console=False,
            enable_file=False
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "level": self.level.value,
            "format": self.format.value,
            "log_file": str(self.log_file) if self.log_file else None,
            "max_file_size_mb": self.max_file_size_mb,
            "backup_count": self.backup_count,
            "enable_console": self.enable_console,
            "enable_file": self.enable_file,
            "enable_structured": self.enable_structured,
            "include_timestamp": self.include_timestamp,
            "include_module": self.include_module,
            "include_function": self.include_function,
            "include_line_number": self.include_line_number,
            "correlation_id_header": self.correlation_id_header
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "LogConfig":
        """Create configuration from dictionary."""
        return cls(
            level=LogLevel(config_dict.get("level", "INFO")),
            format=LogFormat(config_dict.get("format", "text")),
            log_file=Path(config_dict["log_file"]) if config_dict.get("log_file") else None,
            max_file_size_mb=config_dict.get("max_file_size_mb", 100),
            backup_count=config_dict.get("backup_count", 5),
            enable_console=config_dict.get("enable_console", True),
            enable_file=config_dict.get("enable_file", False),
            enable_structured=config_dict.get("enable_structured", False),
            include_timestamp=config_dict.get("include_timestamp", True),
            include_module=config_dict.get("include_module", True),
            include_function=config_dict.get("include_function", True),
            include_line_number=config_dict.get("include_line_number", True),
            correlation_id_header=config_dict.get("correlation_id_header", "X-Correlation-ID")
        )
    
    def get_python_log_level(self) -> int:
        """Get Python logging level integer."""
        level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        return level_map[self.level]
    
    def create_log_directory(self) -> None:
        """Create log directory if it doesn't exist."""
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if self.max_file_size_mb <= 0:
            errors.append("max_file_size_mb must be positive")
        
        if self.backup_count < 0:
            errors.append("backup_count must be non-negative")
        
        if self.enable_file and not self.log_file:
            errors.append("log_file must be specified when enable_file is True")
        
        if self.log_file and not self.log_file.parent.exists():
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create log directory: {e}")
        
        return errors
