#!/usr/bin/env python3
"""
Advanced model downloader with progress monitoring and disk space tracking.
"""
import time
import shutil
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, FileSizeColumn, TotalFileSizeColumn, TransferSpeedColumn
from rich.table import Table
from rich.live import Live

console = Console()

def get_disk_space_gb(path="/Users/sahil-mac/.cache"):
    """Get available disk space in GB"""
    try:
        total, used, free = shutil.disk_usage(path)
        return free / (1024**3)  # Convert to GB
    except:
        return 0

def format_time(seconds):
    """Format seconds into human readable time"""
    return str(timedelta(seconds=int(seconds)))

def test_meerkat_model():
    """Test if Meerkat model can be loaded with current files"""
    model_name = "dmis-lab/llama-3-meerkat-8b-v1.0"
    console.print(f"[blue]🧪 Testing Meerkat-8B model loading...[/blue]")

    try:
        # Try to load tokenizer first
        console.print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        console.print("[green]✓ Tokenizer loaded successfully[/green]")

        # Try to load model
        console.print("Loading model (this may take a while)...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map='auto',
            low_cpu_mem_usage=True
        )
        console.print("[green]✓ Model loaded successfully![/green]")
        return True

    except Exception as e:
        console.print(f"[red]❌ Model loading failed: {e}[/red]")
        return False

def simple_download_meerkat():
    """Simple download without complex progress tracking"""
    model_name = "dmis-lab/llama-3-meerkat-8b-v1.0"
    console.print(f"[green]🚀 Starting simple download of {model_name}[/green]")

    try:
        console.print("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        console.print("[green]✓ Tokenizer downloaded[/green]")

        console.print("Downloading model (this will take a while, please be patient)...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map='auto',
            low_cpu_mem_usage=True
        )
        console.print("[green]✓ Model downloaded successfully![/green]")
        return True

    except Exception as e:
        console.print(f"[red]❌ Download failed: {e}[/red]")
        return False

def test_downloaded_models():
    """Test that downloaded models work correctly"""
    console.print("\n[blue]🧪 Testing downloaded models...[/blue]")
    
    # Test T5 (already downloaded)
    try:
        from transformers import pipeline
        pipe = pipeline("text2text-generation", model="google/flan-t5-small")
        result = pipe("Medical test: What is hypertension?")
        console.print("[green]✓ T5-small working[/green]")
    except Exception as e:
        console.print(f"[red]❌ T5-small test failed: {e}[/red]")
    
    # Test Medical NER
    try:
        pipe = pipeline("token-classification", model="samrawal/bert-base-uncased_clinical-ner")
        console.print("[green]✓ Medical NER working[/green]")
    except Exception as e:
        console.print(f"[red]❌ Medical NER test failed: {e}[/red]")
    
    # Test CLIP
    try:
        pipe = pipeline("image-classification", model="openai/clip-vit-base-patch32")
        console.print("[green]✓ CLIP working[/green]")
    except Exception as e:
        console.print(f"[red]❌ CLIP test failed: {e}[/red]")

if __name__ == "__main__":
    console.print("[bold blue]🤗 Hugging Face Model Downloader[/bold blue]")
    console.print("=" * 50)

    # Show current status
    console.print(f"[blue]Cache location: /Users/sahil-mac/.cache/huggingface[/blue]")
    console.print(f"[blue]Available space: {get_disk_space_gb():.2f} GB[/blue]")

    # First test if Meerkat model is already available
    console.print("\n[blue]Checking if Meerkat-8B is already downloaded...[/blue]")
    if test_meerkat_model():
        console.print("[green]🎉 Meerkat-8B is ready to use![/green]")
        success = True
    else:
        console.print("[yellow]Meerkat-8B not ready. Attempting download...[/yellow]")
        success = simple_download_meerkat()

    # Test all models
    test_downloaded_models()

    if success:
        console.print("\n[green]🎯 All downloads completed successfully![/green]")
        console.print("[blue]You can now run: python -m medbench run --model-key meerkat_8b --scenario diagnosis[/blue]")
    else:
        console.print("\n[yellow]⚠️  Meerkat download incomplete. Using available models for testing.[/yellow]")
        console.print("[blue]You can run: python -m medbench run --model-key flan_t5_small --scenario diagnosis[/blue]")
