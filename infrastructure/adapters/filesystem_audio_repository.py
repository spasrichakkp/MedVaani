"""Filesystem audio repository for audio storage and retrieval."""

import asyncio
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import uuid

from application.ports.audio_repository_port import (
    AudioRepositoryPort, AudioStorageError, AudioNotFoundError, StorageFullError
)
from domain.value_objects.audio_data import AudioData
from infrastructure.logging.logger_factory import get_module_logger


class FileSystemAudioRepository(AudioRepositoryPort):
    """
    Filesystem-based audio repository implementation.
    
    This repository stores audio files and metadata on the local filesystem
    with organized directory structure and JSON metadata files.
    """
    
    def __init__(
        self,
        base_path: Path,
        max_storage_gb: float = 10.0,
        auto_cleanup_days: int = 30
    ):
        """
        Initialize filesystem audio repository.
        
        Args:
            base_path: Base directory for audio storage
            max_storage_gb: Maximum storage size in GB
            auto_cleanup_days: Days after which to auto-cleanup old files
        """
        self.base_path = Path(base_path)
        self.max_storage_bytes = int(max_storage_gb * 1024 * 1024 * 1024)
        self.auto_cleanup_days = auto_cleanup_days
        
        self.audio_dir = self.base_path / "audio"
        self.metadata_dir = self.base_path / "metadata"
        
        self.logger = get_module_logger(__name__)
        
        # Create directories
        self._ensure_directories()
        
        # File locks for thread safety
        self._file_locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
        
        # Create index file if it doesn't exist
        index_file = self.metadata_dir / "index.json"
        if not index_file.exists():
            with open(index_file, 'w') as f:
                json.dump({"files": {}, "created": datetime.now().isoformat()}, f)
    
    async def _get_file_lock(self, audio_id: str) -> asyncio.Lock:
        """Get or create a lock for a specific file."""
        async with self._global_lock:
            if audio_id not in self._file_locks:
                self._file_locks[audio_id] = asyncio.Lock()
            return self._file_locks[audio_id]
    
    async def save_audio(
        self, 
        audio: AudioData, 
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save audio data to filesystem.
        
        Args:
            audio: AudioData object to save
            filename: Optional filename, auto-generated if None
            metadata: Optional metadata to store with audio
            
        Returns:
            Unique identifier for the saved audio
        """
        try:
            # Check storage space
            await self._check_storage_space()
            
            # Generate unique ID and filename
            audio_id = str(uuid.uuid4())
            if filename is None:
                filename = f"{audio_id}.wav"
            
            # Ensure filename is unique
            audio_path = self.audio_dir / filename
            counter = 1
            while audio_path.exists():
                name_parts = filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    new_filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                else:
                    new_filename = f"{filename}_{counter}"
                audio_path = self.audio_dir / new_filename
                counter += 1
                filename = new_filename
            
            # Get file lock
            file_lock = await self._get_file_lock(audio_id)
            
            async with file_lock:
                # Save audio file
                await self._save_audio_file(audio, audio_path)
                
                # Prepare metadata
                file_metadata = {
                    "id": audio_id,
                    "filename": filename,
                    "path": str(audio_path),
                    "duration_seconds": audio.duration_seconds,
                    "sample_rate": audio.sample_rate,
                    "channels": audio.channels,
                    "format": audio.format,
                    "file_size_bytes": audio_path.stat().st_size,
                    "created_at": datetime.now().isoformat(),
                    "custom_metadata": metadata or {}
                }
                
                # Save metadata
                await self._save_metadata(audio_id, file_metadata)
                
                # Update index
                await self._update_index(audio_id, file_metadata)
                
                self.logger.info(f"Audio saved successfully: {audio_id}")
                return audio_id
                
        except Exception as e:
            self.logger.error(f"Failed to save audio: {e}")
            raise AudioStorageError(f"Audio save failed: {e}") from e
    
    async def _save_audio_file(self, audio: AudioData, file_path: Path) -> None:
        """Save audio data to file."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, audio.save_to_file, file_path)
    
    async def _save_metadata(self, audio_id: str, metadata: Dict[str, Any]) -> None:
        """Save metadata to JSON file."""
        metadata_path = self.metadata_dir / f"{audio_id}.json"
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._write_json_file(metadata_path, metadata)
        )
    
    def _write_json_file(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write JSON data to file (synchronous)."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def _update_index(self, audio_id: str, metadata: Dict[str, Any]) -> None:
        """Update the main index file."""
        index_path = self.metadata_dir / "index.json"
        
        # Read current index
        loop = asyncio.get_event_loop()
        index_data = await loop.run_in_executor(
            None,
            lambda: self._read_json_file(index_path)
        )
        
        # Update index
        index_data["files"][audio_id] = {
            "filename": metadata["filename"],
            "created_at": metadata["created_at"],
            "duration_seconds": metadata["duration_seconds"],
            "file_size_bytes": metadata["file_size_bytes"]
        }
        
        # Write updated index
        await loop.run_in_executor(
            None,
            lambda: self._write_json_file(index_path, index_data)
        )
    
    def _read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON data from file (synchronous)."""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    async def load_audio(self, audio_id: str) -> Optional[AudioData]:
        """
        Load audio data from filesystem.
        
        Args:
            audio_id: Unique identifier for the audio
            
        Returns:
            AudioData object or None if not found
        """
        try:
            # Get metadata
            metadata = await self.get_audio_metadata(audio_id)
            if not metadata:
                return None
            
            # Load audio file
            audio_path = Path(metadata["path"])
            if not audio_path.exists():
                self.logger.warning(f"Audio file not found: {audio_path}")
                return None
            
            # Get file lock
            file_lock = await self._get_file_lock(audio_id)
            
            async with file_lock:
                loop = asyncio.get_event_loop()
                audio_data = await loop.run_in_executor(
                    None,
                    AudioData.from_file,
                    audio_path
                )
                
                self.logger.debug(f"Audio loaded successfully: {audio_id}")
                return audio_data
                
        except Exception as e:
            self.logger.error(f"Failed to load audio {audio_id}: {e}")
            return None
    
    async def delete_audio(self, audio_id: str) -> bool:
        """
        Delete audio data from filesystem.
        
        Args:
            audio_id: Unique identifier for the audio
            
        Returns:
            True if deletion succeeded, False otherwise
        """
        try:
            # Get metadata
            metadata = await self.get_audio_metadata(audio_id)
            if not metadata:
                return False
            
            # Get file lock
            file_lock = await self._get_file_lock(audio_id)
            
            async with file_lock:
                # Delete audio file
                audio_path = Path(metadata["path"])
                if audio_path.exists():
                    audio_path.unlink()
                
                # Delete metadata file
                metadata_path = self.metadata_dir / f"{audio_id}.json"
                if metadata_path.exists():
                    metadata_path.unlink()
                
                # Update index
                await self._remove_from_index(audio_id)
                
                self.logger.info(f"Audio deleted successfully: {audio_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to delete audio {audio_id}: {e}")
            return False
    
    async def _remove_from_index(self, audio_id: str) -> None:
        """Remove entry from index file."""
        index_path = self.metadata_dir / "index.json"
        
        loop = asyncio.get_event_loop()
        index_data = await loop.run_in_executor(
            None,
            lambda: self._read_json_file(index_path)
        )
        
        # Remove from index
        if audio_id in index_data["files"]:
            del index_data["files"][audio_id]
        
        # Write updated index
        await loop.run_in_executor(
            None,
            lambda: self._write_json_file(index_path, index_data)
        )
    
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
        try:
            # Read index
            index_path = self.metadata_dir / "index.json"
            loop = asyncio.get_event_loop()
            index_data = await loop.run_in_executor(
                None,
                lambda: self._read_json_file(index_path)
            )
            
            # Get all file entries
            files = []
            for audio_id, file_info in index_data["files"].items():
                # Load full metadata if needed
                if filters:
                    metadata = await self.get_audio_metadata(audio_id)
                    if metadata and self._matches_filters(metadata, filters):
                        files.append(metadata)
                else:
                    files.append({
                        "id": audio_id,
                        **file_info
                    })
            
            # Sort by creation time (newest first)
            files.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            # Apply offset and limit
            if offset:
                files = files[offset:]
            if limit:
                files = files[:limit]
            
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to list audio files: {e}")
            return []
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches filters."""
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            if isinstance(value, str):
                if value.lower() not in str(metadata[key]).lower():
                    return False
            elif metadata[key] != value:
                return False
        
        return True
    
    async def get_audio_metadata(self, audio_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an audio file.
        
        Args:
            audio_id: Unique identifier for the audio
            
        Returns:
            Metadata dictionary or None if not found
        """
        try:
            metadata_path = self.metadata_dir / f"{audio_id}.json"
            if not metadata_path.exists():
                return None
            
            loop = asyncio.get_event_loop()
            metadata = await loop.run_in_executor(
                None,
                lambda: self._read_json_file(metadata_path)
            )
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to get metadata for {audio_id}: {e}")
            return None
    
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
        try:
            # Get current metadata
            current_metadata = await self.get_audio_metadata(audio_id)
            if not current_metadata:
                return False
            
            # Update metadata
            current_metadata.update(metadata)
            current_metadata["updated_at"] = datetime.now().isoformat()
            
            # Save updated metadata
            await self._save_metadata(audio_id, current_metadata)
            
            self.logger.debug(f"Metadata updated for {audio_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update metadata for {audio_id}: {e}")
            return False
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            # Calculate total size
            total_size = 0
            file_count = 0
            
            for audio_file in self.audio_dir.glob("*"):
                if audio_file.is_file():
                    total_size += audio_file.stat().st_size
                    file_count += 1
            
            # Get available space
            statvfs = shutil.disk_usage(self.base_path)
            available_space = statvfs.free
            
            return {
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "available_space_bytes": available_space,
                "available_space_mb": available_space / (1024 * 1024),
                "max_storage_bytes": self.max_storage_bytes,
                "usage_percentage": (total_size / self.max_storage_bytes) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_files(self, max_age_days: int) -> int:
        """
        Clean up old audio files.
        
        Args:
            max_age_days: Maximum age in days for files to keep
            
        Returns:
            Number of files deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            deleted_count = 0
            
            # Get all files
            files = await self.list_audio_files()
            
            for file_info in files:
                created_at = datetime.fromisoformat(file_info["created_at"])
                if created_at < cutoff_date:
                    if await self.delete_audio(file_info["id"]):
                        deleted_count += 1
            
            self.logger.info(f"Cleaned up {deleted_count} old audio files")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return 0
    
    async def _check_storage_space(self) -> None:
        """Check if there's enough storage space."""
        stats = await self.get_storage_stats()
        
        if stats.get("total_size_bytes", 0) >= self.max_storage_bytes:
            raise StorageFullError("Storage limit exceeded")
        
        # Auto-cleanup if usage is high
        usage_percentage = stats.get("usage_percentage", 0)
        if usage_percentage > 80:  # 80% threshold
            self.logger.warning(f"Storage usage high: {usage_percentage:.1f}%")
            await self.cleanup_old_files(self.auto_cleanup_days)
    
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
        try:
            # Load audio
            audio_data = await self.load_audio(audio_id)
            if not audio_data:
                return False
            
            # Ensure export directory exists
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to export path
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, audio_data.save_to_file, export_path)
            
            self.logger.info(f"Audio exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Export failed for {audio_id}: {e}")
            return False
    
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
        """
        try:
            # Load audio from file
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(None, AudioData.from_file, file_path)
            
            # Save to repository
            filename = file_path.name
            audio_id = await self.save_audio(audio_data, filename, metadata)
            
            self.logger.info(f"Audio imported from {file_path}: {audio_id}")
            return audio_id
            
        except Exception as e:
            self.logger.error(f"Import failed for {file_path}: {e}")
            raise AudioStorageError(f"Audio import failed: {e}") from e
    
    async def create_backup(self, backup_path: Path) -> bool:
        """
        Create a backup of all audio data.
        
        Args:
            backup_path: Path for the backup
            
        Returns:
            True if backup succeeded, False otherwise
        """
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copy entire repository
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                shutil.copytree,
                self.base_path,
                backup_path / "audio_repository",
                dirs_exist_ok=True
            )
            
            self.logger.info(f"Backup created at {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False
    
    async def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore audio data from a backup.
        
        Args:
            backup_path: Path to the backup
            
        Returns:
            True if restore succeeded, False otherwise
        """
        try:
            backup_repo_path = backup_path / "audio_repository"
            if not backup_repo_path.exists():
                return False
            
            # Copy backup to current location
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                shutil.copytree,
                backup_repo_path,
                self.base_path,
                dirs_exist_ok=True
            )
            
            self.logger.info(f"Backup restored from {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False
