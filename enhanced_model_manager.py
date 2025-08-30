#!/usr/bin/env python3
"""
Enhanced Multi-Modal Medical AI Model Manager
Comprehensive model registry with intelligent space management and multi-modal capabilities
"""

import time
import shutil
import torch
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Union, Tuple
from enum import Enum
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, FileSizeColumn, TotalFileSizeColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
    CLIPModel,
    CLIPProcessor,
    SpeechT5Processor,
    SpeechT5ForTextToSpeech,
    SpeechT5HifiGan,
    WhisperProcessor,
    WhisperForConditionalGeneration
)

console = Console()

class ModelCategory(Enum):
    """Model categories for organization and resource management"""
    MEDICAL_REASONING = "medical_reasoning"
    TEXT_TO_SPEECH = "text_to_speech"
    SPEECH_TO_TEXT = "speech_to_text"
    MEDICAL_VISION = "medical_vision"
    MEDICAL_NLP = "medical_nlp"
    GENERAL_VISION = "general_vision"
    MULTILINGUAL = "multilingual"

class ModelTier(Enum):
    """Model tiers based on resource requirements"""
    ESSENTIAL = "essential"    # Core models, minimal space
    STANDARD = "standard"      # Enhanced capabilities
    PREMIUM = "premium"        # Full feature set
    EXPERIMENTAL = "experimental"  # Research/testing

@dataclass
class ModelSpec:
    """Comprehensive model specification"""
    name: str
    model_id: str
    category: ModelCategory
    tier: ModelTier
    estimated_size_gb: float
    capabilities: List[str]
    dependencies: List[str] = None
    requires_gpu: bool = False
    supports_streaming: bool = False
    languages: List[str] = None
    description: str = ""
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.languages is None:
            self.languages = ["en"]

class ModelRegistry:
    """Centralized registry for all medical AI models"""
    
    def __init__(self):
        self.models = self._initialize_model_registry()
        self.cache_path = Path.home() / ".cache" / "huggingface"
        
    def _initialize_model_registry(self) -> Dict[str, ModelSpec]:
        """Initialize the comprehensive model registry"""
        models = {}
        
        # Medical Reasoning Models
        models["meerkat_8b"] = ModelSpec(
            name="Meerkat-8B",
            model_id="dmis-lab/llama-3-meerkat-8b-v1.0",
            category=ModelCategory.MEDICAL_REASONING,
            tier=ModelTier.PREMIUM,
            estimated_size_gb=15.0,
            capabilities=["medical_diagnosis", "clinical_reasoning", "medical_qa"],
            requires_gpu=True,
            description="Specialized medical reasoning model based on Llama-3"
        )
        
        models["flan_t5_small"] = ModelSpec(
            name="FLAN-T5 Small",
            model_id="google/flan-t5-small",
            category=ModelCategory.MEDICAL_REASONING,
            tier=ModelTier.ESSENTIAL,
            estimated_size_gb=0.3,
            capabilities=["text_generation", "medical_qa"],
            description="Lightweight general-purpose model for basic medical tasks"
        )
        
        # Text-to-Speech Models
        models["speecht5_tts"] = ModelSpec(
            name="SpeechT5 TTS",
            model_id="microsoft/speecht5_tts",
            category=ModelCategory.TEXT_TO_SPEECH,
            tier=ModelTier.STANDARD,
            estimated_size_gb=1.2,
            capabilities=["text_to_speech", "voice_synthesis"],
            supports_streaming=True,
            description="High-quality text-to-speech synthesis"
        )
        
        models["speecht5_hifigan"] = ModelSpec(
            name="SpeechT5 HiFiGAN",
            model_id="microsoft/speecht5_hifigan",
            category=ModelCategory.TEXT_TO_SPEECH,
            tier=ModelTier.STANDARD,
            estimated_size_gb=0.1,
            capabilities=["vocoder", "audio_generation"],
            dependencies=["speecht5_tts"],
            description="Vocoder for SpeechT5 TTS"
        )
        
        models["bark_small"] = ModelSpec(
            name="Bark Small",
            model_id="suno/bark-small",
            category=ModelCategory.TEXT_TO_SPEECH,
            tier=ModelTier.PREMIUM,
            estimated_size_gb=2.0,
            capabilities=["text_to_speech", "voice_cloning", "multilingual_tts"],
            languages=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "hu", "ko"],
            description="Advanced TTS with voice cloning and multilingual support"
        )
        
        # Speech-to-Text Models
        models["whisper_small"] = ModelSpec(
            name="Whisper Small",
            model_id="openai/whisper-small",
            category=ModelCategory.SPEECH_TO_TEXT,
            tier=ModelTier.ESSENTIAL,
            estimated_size_gb=0.5,
            capabilities=["speech_to_text", "multilingual_asr"],
            supports_streaming=True,
            languages=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "hu", "ko"],
            description="Fast multilingual speech recognition"
        )
        
        models["whisper_medium"] = ModelSpec(
            name="Whisper Medium",
            model_id="openai/whisper-medium",
            category=ModelCategory.SPEECH_TO_TEXT,
            tier=ModelTier.STANDARD,
            estimated_size_gb=1.5,
            capabilities=["speech_to_text", "multilingual_asr", "high_accuracy"],
            supports_streaming=True,
            languages=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "hu", "ko"],
            description="High-accuracy multilingual speech recognition"
        )
        
        # Medical Vision Models
        models["chexnet"] = ModelSpec(
            name="CheXNet",
            model_id="stanfordmlgroup/chexnet",
            category=ModelCategory.MEDICAL_VISION,
            tier=ModelTier.STANDARD,
            estimated_size_gb=0.5,
            capabilities=["chest_xray_analysis", "pathology_detection"],
            description="Chest X-ray pathology detection"
        )
        
        models["clip_vit_b32"] = ModelSpec(
            name="CLIP ViT-B/32",
            model_id="openai/clip-vit-base-patch32",
            category=ModelCategory.GENERAL_VISION,
            tier=ModelTier.ESSENTIAL,
            estimated_size_gb=0.6,
            capabilities=["image_text_matching", "medical_image_analysis"],
            description="General vision-language model for medical imaging"
        )
        
        # Medical NLP Models
        models["medical_ner"] = ModelSpec(
            name="Medical NER",
            model_id="d4data/biomedical-ner-all",
            category=ModelCategory.MEDICAL_NLP,
            tier=ModelTier.ESSENTIAL,
            estimated_size_gb=0.4,
            capabilities=["named_entity_recognition", "medical_text_analysis"],
            description="Medical named entity recognition"
        )
        
        models["biobert"] = ModelSpec(
            name="BioBERT",
            model_id="dmis-lab/biobert-v1.1",
            category=ModelCategory.MEDICAL_NLP,
            tier=ModelTier.STANDARD,
            estimated_size_gb=1.3,
            capabilities=["medical_text_understanding", "biomedical_qa"],
            description="BERT pre-trained on biomedical literature"
        )
        
        models["clinical_bert"] = ModelSpec(
            name="ClinicalBERT",
            model_id="emilyalsentzer/Bio_ClinicalBERT",
            category=ModelCategory.MEDICAL_NLP,
            tier=ModelTier.STANDARD,
            estimated_size_gb=1.3,
            capabilities=["clinical_text_understanding", "medical_classification"],
            description="BERT pre-trained on clinical notes"
        )
        
        return models
    
    def get_models_by_tier(self, tier: ModelTier) -> List[ModelSpec]:
        """Get all models in a specific tier"""
        return [model for model in self.models.values() if model.tier == tier]
    
    def get_models_by_category(self, category: ModelCategory) -> List[ModelSpec]:
        """Get all models in a specific category"""
        return [model for model in self.models.values() if model.category == category]
    
    def calculate_tier_size(self, tier: ModelTier) -> float:
        """Calculate total size for a tier"""
        models = self.get_models_by_tier(tier)
        return sum(model.estimated_size_gb for model in models)
    
    def get_available_space_gb(self) -> float:
        """Get available disk space in GB"""
        try:
            total, used, free = shutil.disk_usage(self.cache_path)
            return free / (1024**3)
        except:
            return 0
    
    def check_space_requirements(self, model_keys: List[str]) -> Tuple[bool, float, float]:
        """Check if there's enough space for specified models"""
        required_space = sum(self.models[key].estimated_size_gb for key in model_keys if key in self.models)
        available_space = self.get_available_space_gb()
        return available_space >= required_space, required_space, available_space

def get_disk_space_gb(path="/Users/sahil-mac/.cache"):
    """Get available disk space in GB - compatibility function"""
    try:
        total, used, free = shutil.disk_usage(path)
        return free / (1024**3)
    except:
        return 0

class EnhancedModelDownloader:
    """Enhanced model downloader with intelligent space management"""

    def __init__(self):
        self.registry = ModelRegistry()
        self.downloaded_models = set()
        self._scan_existing_models()

    def _scan_existing_models(self):
        """Scan for already downloaded models"""
        cache_path = self.registry.cache_path
        if cache_path.exists():
            for model_dir in cache_path.glob("models--*"):
                # Extract model name from cache directory
                model_name = model_dir.name.replace("models--", "").replace("--", "/")
                for key, spec in self.registry.models.items():
                    if spec.model_id.replace("/", "--") in model_dir.name:
                        self.downloaded_models.add(key)
                        break

    def show_model_registry(self):
        """Display the complete model registry"""
        console.print("\n[bold blue]🤖 Enhanced Medical AI Model Registry[/bold blue]")

        for tier in ModelTier:
            models = self.registry.get_models_by_tier(tier)
            if not models:
                continue

            total_size = sum(m.estimated_size_gb for m in models)

            table = Table(title=f"{tier.value.title()} Tier Models ({total_size:.1f}GB total)")
            table.add_column("Model", style="cyan")
            table.add_column("Category", style="yellow")
            table.add_column("Size", justify="right", style="green")
            table.add_column("Capabilities", style="magenta")
            table.add_column("Status", justify="center")

            for model in models:
                status = "✅ Downloaded" if any(key for key, spec in self.registry.models.items()
                                             if spec == model and key in self.downloaded_models) else "⬇️ Available"

                capabilities_str = ", ".join(model.capabilities[:3])
                if len(model.capabilities) > 3:
                    capabilities_str += f" (+{len(model.capabilities)-3} more)"

                table.add_row(
                    model.name,
                    model.category.value.replace("_", " ").title(),
                    f"{model.estimated_size_gb:.1f}GB",
                    capabilities_str,
                    status
                )

            console.print(table)
            console.print()

    def check_space_and_prompt(self, required_space_gb: float) -> bool:
        """Check available space and prompt user if insufficient"""
        available_space = self.registry.get_available_space_gb()

        console.print(f"\n[blue]💾 Disk Space Analysis[/blue]")
        console.print(f"Available: {available_space:.1f}GB")
        console.print(f"Required: {required_space_gb:.1f}GB")

        if available_space < required_space_gb:
            console.print(f"\n[red]⚠️ Insufficient disk space![/red]")
            console.print(f"[red]Need {required_space_gb - available_space:.1f}GB more space[/red]")
            console.print(f"\n[yellow]Please free up disk space and try again.[/yellow]")
            console.print(f"[yellow]Consider:[/yellow]")
            console.print(f"  • Clearing cache: rm -rf ~/.cache/huggingface/hub/models--*")
            console.print(f"  • Using smaller model tiers")
            console.print(f"  • Removing unused applications")
            return False

        return True

    def download_model_tier(self, tier: ModelTier, force: bool = False):
        """Download all models in a specific tier"""
        models = self.registry.get_models_by_tier(tier)
        total_size = sum(m.estimated_size_gb for m in models)

        console.print(f"\n[green]🚀 Downloading {tier.value.title()} Tier Models[/green]")
        console.print(f"Total size: {total_size:.1f}GB")

        if not force and not self.check_space_and_prompt(total_size):
            return False

        success_count = 0
        for model in models:
            model_key = next((key for key, spec in self.registry.models.items() if spec == model), None)
            if model_key and self.download_single_model(model_key):
                success_count += 1

        console.print(f"\n[green]✅ Downloaded {success_count}/{len(models)} models successfully[/green]")
        return success_count == len(models)

    def download_single_model(self, model_key: str) -> bool:
        """Download a single model with progress tracking"""
        if model_key not in self.registry.models:
            console.print(f"[red]❌ Unknown model: {model_key}[/red]")
            return False

        model_spec = self.registry.models[model_key]

        if model_key in self.downloaded_models:
            console.print(f"[yellow]⚠️ {model_spec.name} already downloaded[/yellow]")
            return True

        console.print(f"\n[blue]📥 Downloading {model_spec.name}[/blue]")
        console.print(f"Model ID: {model_spec.model_id}")
        console.print(f"Size: ~{model_spec.estimated_size_gb:.1f}GB")

        try:
            # Download based on model category
            if model_spec.category == ModelCategory.TEXT_TO_SPEECH:
                return self._download_tts_model(model_spec)
            elif model_spec.category == ModelCategory.SPEECH_TO_TEXT:
                return self._download_asr_model(model_spec)
            elif model_spec.category == ModelCategory.MEDICAL_VISION:
                return self._download_vision_model(model_spec)
            else:
                return self._download_standard_model(model_spec)

        except Exception as e:
            console.print(f"[red]❌ Download failed: {e}[/red]")
            return False

    def _download_standard_model(self, model_spec: ModelSpec) -> bool:
        """Download standard transformer models"""
        try:
            console.print(f"[yellow]Loading tokenizer...[/yellow]")
            tokenizer = AutoTokenizer.from_pretrained(model_spec.model_id)

            console.print(f"[yellow]Loading model...[/yellow]")
            if model_spec.category == ModelCategory.MEDICAL_REASONING:
                model = AutoModelForCausalLM.from_pretrained(
                    model_spec.model_id,
                    torch_dtype=torch.float16 if model_spec.requires_gpu else torch.float32,
                    device_map='auto' if model_spec.requires_gpu else None,
                    low_cpu_mem_usage=True
                )
            else:
                model = AutoModelForSequenceClassification.from_pretrained(model_spec.model_id)

            console.print(f"[green]✅ {model_spec.name} downloaded successfully[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to download {model_spec.name}: {e}[/red]")
            return False

    def _download_tts_model(self, model_spec: ModelSpec) -> bool:
        """Download text-to-speech models"""
        try:
            if "speecht5" in model_spec.model_id.lower():
                console.print(f"[yellow]Loading SpeechT5 processor...[/yellow]")
                processor = SpeechT5Processor.from_pretrained(model_spec.model_id)

                if "hifigan" in model_spec.model_id.lower():
                    console.print(f"[yellow]Loading HiFiGAN vocoder...[/yellow]")
                    vocoder = SpeechT5HifiGan.from_pretrained(model_spec.model_id)
                else:
                    console.print(f"[yellow]Loading SpeechT5 TTS model...[/yellow]")
                    model = SpeechT5ForTextToSpeech.from_pretrained(model_spec.model_id)
            else:
                # For other TTS models like Bark
                console.print(f"[yellow]Loading TTS model...[/yellow]")
                tokenizer = AutoTokenizer.from_pretrained(model_spec.model_id)
                model = AutoModelForCausalLM.from_pretrained(model_spec.model_id)

            console.print(f"[green]✅ {model_spec.name} downloaded successfully[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to download {model_spec.name}: {e}[/red]")
            return False

    def _download_asr_model(self, model_spec: ModelSpec) -> bool:
        """Download automatic speech recognition models"""
        try:
            console.print(f"[yellow]Loading Whisper processor...[/yellow]")
            processor = WhisperProcessor.from_pretrained(model_spec.model_id)

            console.print(f"[yellow]Loading Whisper model...[/yellow]")
            model = WhisperForConditionalGeneration.from_pretrained(model_spec.model_id)

            console.print(f"[green]✅ {model_spec.name} downloaded successfully[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to download {model_spec.name}: {e}[/red]")
            return False

    def _download_vision_model(self, model_spec: ModelSpec) -> bool:
        """Download vision models"""
        try:
            if "clip" in model_spec.model_id.lower():
                console.print(f"[yellow]Loading CLIP processor...[/yellow]")
                processor = CLIPProcessor.from_pretrained(model_spec.model_id)

                console.print(f"[yellow]Loading CLIP model...[/yellow]")
                model = CLIPModel.from_pretrained(model_spec.model_id)
            else:
                # For other vision models
                console.print(f"[yellow]Loading vision model...[/yellow]")
                model = AutoModelForSequenceClassification.from_pretrained(model_spec.model_id)

            console.print(f"[green]✅ {model_spec.name} downloaded successfully[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to download {model_spec.name}: {e}[/red]")
            return False

def main():
    """Main function for enhanced model management"""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Medical AI Model Manager")
    parser.add_argument("--show-registry", action="store_true", help="Show complete model registry")
    parser.add_argument("--download-tier", choices=["essential", "standard", "premium", "experimental"],
                       help="Download all models in specified tier")
    parser.add_argument("--download-model", type=str, help="Download specific model by key")
    parser.add_argument("--download-category", choices=["medical_reasoning", "text_to_speech", "speech_to_text",
                                                       "medical_vision", "medical_nlp", "general_vision", "multilingual"],
                       help="Download all models in specified category")
    parser.add_argument("--check-space", action="store_true", help="Check available disk space")
    parser.add_argument("--force", action="store_true", help="Force download without space check")

    args = parser.parse_args()

    downloader = EnhancedModelDownloader()

    console.print("[bold green]🏥 Enhanced Medical AI Model Manager[/bold green]")
    console.print("=" * 60)

    if args.show_registry:
        downloader.show_model_registry()
        return

    if args.check_space:
        available = downloader.registry.get_available_space_gb()
        console.print(f"\n[blue]💾 Available disk space: {available:.1f}GB[/blue]")

        for tier in ModelTier:
            tier_size = downloader.registry.calculate_tier_size(tier)
            status = "✅" if available >= tier_size else "❌"
            console.print(f"{status} {tier.value.title()} tier: {tier_size:.1f}GB")
        return

    if args.download_tier:
        tier = ModelTier(args.download_tier)
        downloader.download_model_tier(tier, force=args.force)
        return

    if args.download_model:
        downloader.download_single_model(args.download_model)
        return

    if args.download_category:
        category = ModelCategory(args.download_category)
        models = downloader.registry.get_models_by_category(category)
        total_size = sum(m.estimated_size_gb for m in models)

        console.print(f"\n[green]🚀 Downloading {category.value.replace('_', ' ').title()} Models[/green]")
        console.print(f"Total size: {total_size:.1f}GB")

        if not args.force and not downloader.check_space_and_prompt(total_size):
            return

        success_count = 0
        for model in models:
            model_key = next((key for key, spec in downloader.registry.models.items() if spec == model), None)
            if model_key and downloader.download_single_model(model_key):
                success_count += 1

        console.print(f"\n[green]✅ Downloaded {success_count}/{len(models)} models successfully[/green]")
        return

    # Default: show help and registry
    parser.print_help()
    console.print("\n")
    downloader.show_model_registry()

if __name__ == "__main__":
    main()
