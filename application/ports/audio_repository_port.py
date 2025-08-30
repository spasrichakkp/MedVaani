"""Port interface for audio storage and retrieval operations."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path
from domain.value_objects.audio_data import AudioData


class AudioRepositoryPort(ABC):
    """
    Port interface for audio storage and retrieval operations.
    
    This interface defines the contract for audio persistence,
    including saving, loading, and managing audio files.
    """
    
    @abstractmethod
    async def save_audio(
        self, 
        audio: AudioData, 
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save audio data to storage.
        
        Args:
            audio: AudioData object to save
            filename: Optional filename, auto-generated if None
            metadata: Optional metadata to store with audio
            
        Returns:
            Unique identifier or path for the saved audio
            
        Raises:
            AudioStorageError: If saving fails
        """
        pass
    
    @abstractmethod
    async def load_audio(self, audio_id: str) -> Optional[AudioData]:
        """
        Load audio data from storage.
        
        Args:
            audio_id: Unique identifier for the audio
            
        Returns:
            AudioData object or None if not found
            
        Raises:
            AudioStorageError: If loading fails
        """
        pass
    
    @abstractmethod
    async def delete_audio(self, audio_id: str) -> bool:
        """
        Delete audio data from storage.
        
        Args:
            audio_id: Unique identifier for the audio
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_audio_files(
        self, 
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List audio files in storage.
        
        Args:
            limit: Maximum number of files to return
            offset: Number of files to skip
            filters: Optional filters to apply
            
        Returns:
            List of audio file metadata
        """
        pass
    
    @abstractmethod
    async def get_audio_metadata(self, audio_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an audio file.
        
        Args:
            audio_id: Unique identifier for the audio
            
        Returns:
            Metadata dictionary or None if not found
        """
        pass
    
    @abstractmethod
    async def update_audio_metadata(
        self, 
        audio_id: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update metadata for an audio file.
        
        Args:
            audio_id: Unique identifier for the audio
            metadata: New metadata to store
            
        Returns:
            True if update succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary containing storage statistics
        """
        pass
    
    @abstractmethod
    async def cleanup_old_files(self, max_age_days: int) -> int:
        """
        Clean up old audio files.
        
        Args:
            max_age_days: Maximum age in days for files to keep
            
        Returns:
            Number of files deleted
        """
        pass
    
    @abstractmethod
    async def export_audio(
        self, 
        audio_id: str, 
        export_path: Path,
        format: str = "wav"
    ) -> bool:
        """
        Export audio to a specific path and format.
        
        Args:
            audio_id: Unique identifier for the audio
            export_path: Path to export the audio
            format: Audio format for export
            
        Returns:
            True if export succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    async def import_audio(
        self, 
        file_path: Path,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Import audio from a file path.
        
        Args:
            file_path: Path to the audio file
            metadata: Optional metadata to store
            
        Returns:
            Unique identifier for the imported audio
            
        Raises:
            AudioStorageError: If import fails
        """
        pass
    
    @abstractmethod
    async def create_backup(self, backup_path: Path) -> bool:
        """
        Create a backup of all audio data.
        
        Args:
            backup_path: Path for the backup
            
        Returns:
            True if backup succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    async def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore audio data from a backup.
        
        Args:
            backup_path: Path to the backup
            
        Returns:
            True if restore succeeded, False otherwise
        """
        pass


class AudioStorageError(Exception):
    """Base exception for audio storage errors."""
    pass


class AudioNotFoundError(AudioStorageError):
    """Raised when requested audio is not found."""
    pass


class AudioCorruptedError(AudioStorageError):
    """Raised when audio data is corrupted."""
    pass


class StorageFullError(AudioStorageError):
    """Raised when storage is full."""
    pass


class InvalidFormatError(AudioStorageError):
    """Raised when audio format is invalid."""
    pass
