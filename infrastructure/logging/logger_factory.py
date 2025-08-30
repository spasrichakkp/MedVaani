"""Logger factory for creating structured loggers."""

import os
from typing import Dict, Optional
from pathlib import Path

from .structured_logger import StructuredLogger
from .log_config import LogConfig, LogLevel, LogFormat


class LoggerFactory:
    """
    Factory for creating and managing structured loggers.
    
    This factory ensures consistent logger configuration across
    the application and provides centralized logger management.
    """
    
    _instance: Optional["LoggerFactory"] = None
    _loggers: Dict[str, StructuredLogger] = {}
    _config: Optional[LogConfig] = None
    
    def __new__(cls) -> "LoggerFactory":
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, config: Optional[LogConfig] = None) -> "LoggerFactory":
        """
        Initialize the logger factory with configuration.
        
        Args:
            config: Logging configuration, auto-detected if None
            
        Returns:
            LoggerFactory instance
        """
        factory = cls()
        
        if config is None:
            config = cls._detect_config()
        
        factory._config = config
        
        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid logging configuration: {errors}")
        
        return factory
    
    @classmethod
    def _detect_config(cls) -> LogConfig:
        """Auto-detect logging configuration based on environment."""
        env = os.getenv("ENVIRONMENT", "development").lower()
        
        if env == "production":
            return LogConfig.production()
        elif env == "testing":
            return LogConfig.testing()
        else:
            return LogConfig.development()
    
    def get_logger(self, name: str) -> StructuredLogger:
        """
        Get or create a logger with the given name.
        
        Args:
            name: Logger name (usually module name)
            
        Returns:
            StructuredLogger instance
        """
        if self._config is None:
            raise RuntimeError("LoggerFactory not initialized. Call initialize() first.")
        
        if name not in self._loggers:
            self._loggers[name] = StructuredLogger(name, self._config)
        
        return self._loggers[name]
    
    def get_logger_for_module(self, module_name: str) -> StructuredLogger:
        """
        Get logger for a specific module.
        
        Args:
            module_name: Module name (e.g., __name__)
            
        Returns:
            StructuredLogger instance
        """
        # Extract just the module name without package path
        logger_name = module_name.split('.')[-1] if '.' in module_name else module_name
        return self.get_logger(logger_name)
    
    def update_config(self, config: LogConfig) -> None:
        """
        Update logging configuration for all loggers.
        
        Args:
            config: New logging configuration
        """
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid logging configuration: {errors}")
        
        self._config = config
        
        # Clear existing loggers to force recreation with new config
        self._loggers.clear()
    
    def set_log_level(self, level: LogLevel) -> None:
        """
        Set log level for all loggers.
        
        Args:
            level: New log level
        """
        if self._config:
            self._config.level = level
            
            # Update existing loggers
            for logger in self._loggers.values():
                logger.logger.setLevel(level.value)
    
    def enable_file_logging(self, log_file: Path) -> None:
        """
        Enable file logging for all loggers.
        
        Args:
            log_file: Path to log file
        """
        if self._config:
            self._config.enable_file = True
            self._config.log_file = log_file
            self._config.create_log_directory()
            
            # Clear loggers to force recreation with file handler
            self._loggers.clear()
    
    def disable_file_logging(self) -> None:
        """Disable file logging for all loggers."""
        if self._config:
            self._config.enable_file = False
            
            # Clear loggers to force recreation without file handler
            self._loggers.clear()
    
    def get_config(self) -> Optional[LogConfig]:
        """Get current logging configuration."""
        return self._config
    
    def list_loggers(self) -> list[str]:
        """Get list of active logger names."""
        return list(self._loggers.keys())
    
    def shutdown(self) -> None:
        """Shutdown all loggers and handlers."""
        import logging
        
        # Shutdown all handlers
        for logger in self._loggers.values():
            for handler in logger.logger.handlers[:]:
                handler.close()
                logger.logger.removeHandler(handler)
        
        # Clear logger cache
        self._loggers.clear()
        
        # Shutdown logging system
        logging.shutdown()


# Convenience functions for easy logger access
def get_logger(name: str) -> StructuredLogger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        StructuredLogger instance
    """
    factory = LoggerFactory()
    return factory.get_logger(name)


def get_module_logger(module_name: str) -> StructuredLogger:
    """
    Get a logger for a module.
    
    Args:
        module_name: Module name (usually __name__)
        
    Returns:
        StructuredLogger instance
    """
    factory = LoggerFactory()
    return factory.get_logger_for_module(module_name)


def initialize_logging(config: Optional[LogConfig] = None) -> LoggerFactory:
    """
    Initialize logging system.
    
    Args:
        config: Logging configuration
        
    Returns:
        LoggerFactory instance
    """
    return LoggerFactory.initialize(config)
