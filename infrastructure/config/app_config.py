"""Application configuration management."""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class VoiceConfig:
    """Configuration for voice processing."""
    tts_model: str = "microsoft/speecht5_tts"
    tts_vocoder: str = "microsoft/speecht5_hifigan"
    asr_model: str = "openai/whisper-small"
    sample_rate: int = 16000
    device: str = "auto"
    voice_speed: float = 1.0
    voice_pitch: float = 1.0
    enable_audio_save: bool = True
    audio_output_dir: str = "audio_outputs"
    max_recording_duration: int = 30
    audio_quality_threshold: float = 0.02


@dataclass
class MedicalConfig:
    """Configuration for medical AI models."""
    reasoning_model: str = "google/flan-t5-small"
    reasoning_model_large: str = "dmis-lab/llama-3-meerkat-8b-v1.0"
    ner_model: str = "samrawal/bert-base-uncased_clinical-ner"
    vision_model: str = "openai/clip-vit-base-patch32"
    max_new_tokens: int = 128
    do_sample: bool = False
    temperature: float = 0.7
    top_p: float = 0.9
    device_map: str = "auto"
    torch_dtype: str = "float16"
    low_cpu_mem_usage: bool = True


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    url: str = "sqlite:///medical_research.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class CacheConfig:
    """Configuration for caching."""
    enabled: bool = True
    backend: str = "memory"  # memory, redis, memcached
    default_timeout: int = 300
    max_entries: int = 1000
    redis_url: Optional[str] = None


@dataclass
class SecurityConfig:
    """Configuration for security settings."""
    enable_cors: bool = True
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    enable_rate_limiting: bool = True
    rate_limit_per_minute: int = 60
    enable_authentication: bool = False
    jwt_secret_key: Optional[str] = None
    jwt_expiration_hours: int = 24


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and observability."""
    enable_metrics: bool = True
    enable_tracing: bool = False
    metrics_port: int = 8080
    health_check_interval: int = 30
    performance_monitoring: bool = True
    error_tracking: bool = True


@dataclass
class AppConfig:
    """Main application configuration."""
    
    # Environment
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    # Application settings
    app_name: str = "Medical Research AI"
    app_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # Component configurations
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    medical: MedicalConfig = field(default_factory=MedicalConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Paths
    data_dir: Path = field(default_factory=lambda: Path("data"))
    logs_dir: Path = field(default_factory=lambda: Path("logs"))
    models_dir: Path = field(default_factory=lambda: Path.home() / ".cache" / "huggingface")
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables."""
        config = cls()
        
        # Override with environment variables
        config.environment = os.getenv("ENVIRONMENT", config.environment)
        config.debug = os.getenv("DEBUG", str(config.debug)).lower() == "true"
        config.host = os.getenv("HOST", config.host)
        config.port = int(os.getenv("PORT", str(config.port)))
        config.workers = int(os.getenv("WORKERS", str(config.workers)))
        
        # Voice configuration from environment
        config.voice.tts_model = os.getenv("TTS_MODEL", config.voice.tts_model)
        config.voice.asr_model = os.getenv("ASR_MODEL", config.voice.asr_model)
        config.voice.sample_rate = int(os.getenv("SAMPLE_RATE", str(config.voice.sample_rate)))
        config.voice.device = os.getenv("VOICE_DEVICE", config.voice.device)
        
        # Medical configuration from environment
        config.medical.reasoning_model = os.getenv("MEDICAL_MODEL", config.medical.reasoning_model)
        config.medical.max_new_tokens = int(os.getenv("MAX_NEW_TOKENS", str(config.medical.max_new_tokens)))
        config.medical.temperature = float(os.getenv("TEMPERATURE", str(config.medical.temperature)))
        
        # Database configuration from environment
        config.database.url = os.getenv("DATABASE_URL", config.database.url)
        config.database.echo = os.getenv("DATABASE_ECHO", str(config.database.echo)).lower() == "true"
        
        # Cache configuration from environment
        config.cache.enabled = os.getenv("CACHE_ENABLED", str(config.cache.enabled)).lower() == "true"
        config.cache.backend = os.getenv("CACHE_BACKEND", config.cache.backend)
        config.cache.redis_url = os.getenv("REDIS_URL", config.cache.redis_url)
        
        # Security configuration from environment
        config.security.jwt_secret_key = os.getenv("JWT_SECRET_KEY", config.security.jwt_secret_key)
        config.security.enable_authentication = os.getenv("ENABLE_AUTH", str(config.security.enable_authentication)).lower() == "true"
        
        return config
    
    @classmethod
    def from_file(cls, config_path: Path) -> "AppConfig":
        """Load configuration from YAML file."""
        import yaml
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls.from_dict(config_data)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "AppConfig":
        """Create configuration from dictionary."""
        config = cls()
        
        # Update basic settings
        for key, value in config_dict.items():
            if hasattr(config, key) and not isinstance(getattr(config, key), (VoiceConfig, MedicalConfig, DatabaseConfig, CacheConfig, SecurityConfig, MonitoringConfig)):
                setattr(config, key, value)
        
        # Update component configurations
        if "voice" in config_dict:
            for key, value in config_dict["voice"].items():
                if hasattr(config.voice, key):
                    setattr(config.voice, key, value)
        
        if "medical" in config_dict:
            for key, value in config_dict["medical"].items():
                if hasattr(config.medical, key):
                    setattr(config.medical, key, value)
        
        if "database" in config_dict:
            for key, value in config_dict["database"].items():
                if hasattr(config.database, key):
                    setattr(config.database, key, value)
        
        if "cache" in config_dict:
            for key, value in config_dict["cache"].items():
                if hasattr(config.cache, key):
                    setattr(config.cache, key, value)
        
        if "security" in config_dict:
            for key, value in config_dict["security"].items():
                if hasattr(config.security, key):
                    setattr(config.security, key, value)
        
        if "monitoring" in config_dict:
            for key, value in config_dict["monitoring"].items():
                if hasattr(config.monitoring, key):
                    setattr(config.monitoring, key, value)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "host": self.host,
            "port": self.port,
            "workers": self.workers,
            "voice": {
                "tts_model": self.voice.tts_model,
                "asr_model": self.voice.asr_model,
                "sample_rate": self.voice.sample_rate,
                "device": self.voice.device,
                "voice_speed": self.voice.voice_speed,
                "voice_pitch": self.voice.voice_pitch,
                "enable_audio_save": self.voice.enable_audio_save,
                "audio_output_dir": self.voice.audio_output_dir,
                "max_recording_duration": self.voice.max_recording_duration,
                "audio_quality_threshold": self.voice.audio_quality_threshold
            },
            "medical": {
                "reasoning_model": self.medical.reasoning_model,
                "reasoning_model_large": self.medical.reasoning_model_large,
                "ner_model": self.medical.ner_model,
                "vision_model": self.medical.vision_model,
                "max_new_tokens": self.medical.max_new_tokens,
                "do_sample": self.medical.do_sample,
                "temperature": self.medical.temperature,
                "top_p": self.medical.top_p,
                "device_map": self.medical.device_map,
                "torch_dtype": self.medical.torch_dtype,
                "low_cpu_mem_usage": self.medical.low_cpu_mem_usage
            },
            "database": {
                "url": self.database.url,
                "echo": self.database.echo,
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow,
                "pool_timeout": self.database.pool_timeout,
                "pool_recycle": self.database.pool_recycle
            },
            "cache": {
                "enabled": self.cache.enabled,
                "backend": self.cache.backend,
                "default_timeout": self.cache.default_timeout,
                "max_entries": self.cache.max_entries,
                "redis_url": self.cache.redis_url
            },
            "security": {
                "enable_cors": self.security.enable_cors,
                "cors_origins": self.security.cors_origins,
                "enable_rate_limiting": self.security.enable_rate_limiting,
                "rate_limit_per_minute": self.security.rate_limit_per_minute,
                "enable_authentication": self.security.enable_authentication,
                "jwt_secret_key": self.security.jwt_secret_key,
                "jwt_expiration_hours": self.security.jwt_expiration_hours
            },
            "monitoring": {
                "enable_metrics": self.monitoring.enable_metrics,
                "enable_tracing": self.monitoring.enable_tracing,
                "metrics_port": self.monitoring.metrics_port,
                "health_check_interval": self.monitoring.health_check_interval,
                "performance_monitoring": self.monitoring.performance_monitoring,
                "error_tracking": self.monitoring.error_tracking
            }
        }
    
    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        import yaml
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if self.port < 1 or self.port > 65535:
            errors.append("Port must be between 1 and 65535")
        
        if self.workers < 1:
            errors.append("Workers must be at least 1")
        
        if self.voice.sample_rate <= 0:
            errors.append("Voice sample rate must be positive")
        
        if self.medical.max_new_tokens <= 0:
            errors.append("Max new tokens must be positive")
        
        if self.medical.temperature < 0 or self.medical.temperature > 2:
            errors.append("Temperature must be between 0 and 2")
        
        if self.cache.default_timeout <= 0:
            errors.append("Cache timeout must be positive")
        
        return errors
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment.lower() == "testing"
