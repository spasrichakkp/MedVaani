"""Port interface for configuration management."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pathlib import Path


class ConfigurationPort(ABC):
    """
    Port interface for configuration management.
    
    This interface defines the contract for configuration operations
    including loading, saving, and managing application settings.
    """
    
    @abstractmethod
    async def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'voice.tts_model')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        pass
    
    @abstractmethod
    async def set_config(self, key: str, value: Any) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
            
        Returns:
            True if setting succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_all_config(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dictionary containing all configuration
        """
        pass
    
    @abstractmethod
    async def load_config_file(self, file_path: Path) -> bool:
        """
        Load configuration from a file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            True if loading succeeded, False otherwise
            
        Raises:
            ConfigurationError: If loading fails
        """
        pass
    
    @abstractmethod
    async def save_config_file(self, file_path: Path) -> bool:
        """
        Save configuration to a file.
        
        Args:
            file_path: Path to save configuration
            
        Returns:
            True if saving succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    async def reload_config(self) -> bool:
        """
        Reload configuration from source.
        
        Returns:
            True if reload succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    async def validate_config(self) -> List[str]:
        """
        Validate current configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        pass
    
    @abstractmethod
    async def get_config_schema(self) -> Dict[str, Any]:
        """
        Get configuration schema definition.
        
        Returns:
            Dictionary containing configuration schema
        """
        pass
    
    @abstractmethod
    async def reset_to_defaults(self) -> bool:
        """
        Reset configuration to default values.
        
        Returns:
            True if reset succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    async def backup_config(self, backup_path: Path) -> bool:
        """
        Create a backup of current configuration.
        
        Args:
            backup_path: Path for the backup
            
        Returns:
            True if backup succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    async def restore_config(self, backup_path: Path) -> bool:
        """
        Restore configuration from backup.
        
        Args:
            backup_path: Path to the backup
            
        Returns:
            True if restore succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    async def watch_config_changes(self, callback) -> bool:
        """
        Watch for configuration changes and call callback.
        
        Args:
            callback: Function to call when config changes
            
        Returns:
            True if watching started, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_environment_config(self) -> Dict[str, str]:
        """
        Get configuration from environment variables.
        
        Returns:
            Dictionary of environment-based configuration
        """
        pass
    
    @abstractmethod
    async def merge_config(self, config_dict: Dict[str, Any]) -> bool:
        """
        Merge configuration dictionary with current config.
        
        Args:
            config_dict: Configuration to merge
            
        Returns:
            True if merge succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_config_history(self) -> List[Dict[str, Any]]:
        """
        Get configuration change history.
        
        Returns:
            List of configuration changes
        """
        pass


class ConfigurationError(Exception):
    """Base exception for configuration errors."""
    pass


class ConfigurationNotFoundError(ConfigurationError):
    """Raised when configuration file is not found."""
    pass


class ConfigurationValidationError(ConfigurationError):
    """Raised when configuration validation fails."""
    pass


class ConfigurationParseError(ConfigurationError):
    """Raised when configuration file cannot be parsed."""
    pass


class ConfigurationPermissionError(ConfigurationError):
    """Raised when configuration file permissions are insufficient."""
    pass
