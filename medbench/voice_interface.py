#!/usr/bin/env python3
"""
Voice Interface for Medical AI
Comprehensive TTS and ASR integration for interactive medical consultations
"""

import torch
import numpy as np
import soundfile as sf
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel

try:
    from transformers import (
        SpeechT5Processor,
        SpeechT5ForTextToSpeech,
        SpeechT5HifiGan,
        WhisperProcessor,
        WhisperForConditionalGeneration,
        AutoTokenizer,
        AutoModelForCausalLM
    )
    import torchaudio
    VOICE_AVAILABLE = True
except ImportError as e:
    VOICE_AVAILABLE = False
    print(f"Voice dependencies not available: {e}")

console = Console()

@dataclass
class VoiceConfig:
    """Configuration for voice interface"""
    tts_model: str = "microsoft/speecht5_tts"
    tts_vocoder: str = "microsoft/speecht5_hifigan"
    asr_model: str = "openai/whisper-small"
    sample_rate: int = 16000
    device: str = "auto"
    voice_speed: float = 1.0
    voice_pitch: float = 1.0
    enable_audio_save: bool = True
    audio_output_dir: str = "audio_outputs"

class VoiceInterface:
    """Comprehensive voice interface for medical AI"""
    
    def __init__(self, config: VoiceConfig = None):
        if not VOICE_AVAILABLE:
            raise ImportError("Voice dependencies not available. Install required packages.")
        
        self.config = config or VoiceConfig()
        self.device = self._get_device()
        
        # Initialize models
        self.tts_processor = None
        self.tts_model = None
        self.tts_vocoder = None
        self.asr_processor = None
        self.asr_model = None
        
        # Audio output directory
        self.audio_dir = Path(self.config.audio_output_dir)
        self.audio_dir.mkdir(exist_ok=True)
        
        console.print(f"[blue]🎤 Voice Interface initialized on {self.device}[/blue]")
    
    def _get_device(self) -> str:
        """Determine the best available device"""
        if self.config.device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return self.config.device
    
    def load_tts_models(self) -> bool:
        """Load text-to-speech models"""
        try:
            console.print("[yellow]Loading TTS models...[/yellow]")
            
            # Load SpeechT5 processor and model
            self.tts_processor = SpeechT5Processor.from_pretrained(self.config.tts_model)
            self.tts_model = SpeechT5ForTextToSpeech.from_pretrained(self.config.tts_model)
            
            # Try to load HiFiGAN vocoder
            try:
                self.tts_vocoder = SpeechT5HifiGan.from_pretrained(self.config.tts_vocoder)
                console.print("[green]✅ TTS models loaded with HiFiGAN vocoder[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ HiFiGAN vocoder not available: {e}[/yellow]")
                console.print("[yellow]Using built-in vocoder[/yellow]")
            
            # Move models to device
            self.tts_model = self.tts_model.to(self.device)
            if self.tts_vocoder:
                self.tts_vocoder = self.tts_vocoder.to(self.device)
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to load TTS models: {e}[/red]")
            return False
    
    def load_asr_models(self) -> bool:
        """Load automatic speech recognition models"""
        try:
            console.print("[yellow]Loading ASR models...[/yellow]")
            
            # Load Whisper processor and model
            self.asr_processor = WhisperProcessor.from_pretrained(self.config.asr_model)
            self.asr_model = WhisperForConditionalGeneration.from_pretrained(self.config.asr_model)
            
            # Move model to device
            self.asr_model = self.asr_model.to(self.device)
            
            console.print("[green]✅ ASR models loaded[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to load ASR models: {e}[/red]")
            return False
    
    def text_to_speech(self, text: str, output_file: Optional[str] = None) -> Optional[str]:
        """Convert text to speech"""
        if not self.tts_model or not self.tts_processor:
            console.print("[red]❌ TTS models not loaded[/red]")
            return None
        
        try:
            console.print(f"[blue]🗣️ Converting text to speech: '{text[:50]}...'[/blue]")
            
            # Tokenize input text
            inputs = self.tts_processor(text=text, return_tensors="pt")
            
            # Generate speaker embeddings (using default)
            # In a real implementation, you'd load speaker embeddings from a dataset
            speaker_embeddings = torch.randn(1, 512).to(self.device)
            
            # Generate speech
            with torch.no_grad():
                speech = self.tts_model.generate_speech(
                    inputs["input_ids"].to(self.device), 
                    speaker_embeddings
                )
            
            # Convert to audio using vocoder if available
            if self.tts_vocoder:
                with torch.no_grad():
                    audio = self.tts_vocoder(speech.unsqueeze(0))
                    audio = audio.squeeze().cpu().numpy()
            else:
                # Use the speech output directly (mel-spectrogram to audio conversion needed)
                audio = speech.cpu().numpy()
            
            # Save audio file
            if output_file is None:
                output_file = self.audio_dir / f"tts_output_{len(text)}.wav"
            
            sf.write(output_file, audio, self.config.sample_rate)
            
            console.print(f"[green]✅ Audio saved to {output_file}[/green]")
            
            # Play audio if possible
            self._play_audio(output_file)
            
            return str(output_file)
            
        except Exception as e:
            console.print(f"[red]❌ TTS failed: {e}[/red]")
            return None
    
    def speech_to_text(self, audio_file: str) -> Optional[str]:
        """Convert speech to text"""
        if not self.asr_model or not self.asr_processor:
            console.print("[red]❌ ASR models not loaded[/red]")
            return None
        
        try:
            console.print(f"[blue]👂 Converting speech to text from {audio_file}[/blue]")
            
            # Load audio file
            audio, sample_rate = torchaudio.load(audio_file)
            
            # Resample if necessary
            if sample_rate != self.config.sample_rate:
                resampler = torchaudio.transforms.Resample(sample_rate, self.config.sample_rate)
                audio = resampler(audio)
            
            # Convert to mono if stereo
            if audio.shape[0] > 1:
                audio = audio.mean(dim=0, keepdim=True)
            
            # Prepare input for Whisper
            audio_array = audio.squeeze().numpy()
            inputs = self.asr_processor(audio_array, sampling_rate=self.config.sample_rate, return_tensors="pt")
            
            # Generate transcription
            with torch.no_grad():
                predicted_ids = self.asr_model.generate(inputs["input_features"].to(self.device))
                transcription = self.asr_processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            
            console.print(f"[green]✅ Transcription: '{transcription}'[/green]")
            return transcription
            
        except Exception as e:
            console.print(f"[red]❌ ASR failed: {e}[/red]")
            return None
    
    def _play_audio(self, audio_file: str):
        """Play audio file using system audio player"""
        try:
            # Try different audio players based on OS
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                subprocess.run(["afplay", audio_file], check=True)
            elif system == "Linux":
                subprocess.run(["aplay", audio_file], check=True)
            elif system == "Windows":
                subprocess.run(["start", audio_file], shell=True, check=True)
            else:
                console.print(f"[yellow]⚠️ Cannot play audio on {system}[/yellow]")
                
        except subprocess.CalledProcessError:
            console.print("[yellow]⚠️ Could not play audio automatically[/yellow]")
        except FileNotFoundError:
            console.print("[yellow]⚠️ Audio player not found[/yellow]")
    
    def record_audio(self, duration: int = 5, output_file: Optional[str] = None) -> Optional[str]:
        """Record audio from microphone"""
        if output_file is None:
            output_file = self.audio_dir / f"recorded_audio_{duration}s.wav"
        
        try:
            console.print(f"[blue]🎤 Recording audio for {duration} seconds...[/blue]")
            
            # Use system recording (this is a simplified version)
            # In a real implementation, you'd use pyaudio or similar
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                cmd = [
                    "sox", "-d", "-r", str(self.config.sample_rate), 
                    "-c", "1", "-b", "16", str(output_file), 
                    "trim", "0", str(duration)
                ]
                subprocess.run(cmd, check=True)
            else:
                console.print(f"[yellow]⚠️ Audio recording not implemented for {system}[/yellow]")
                return None
            
            console.print(f"[green]✅ Audio recorded to {output_file}[/green]")
            return str(output_file)
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ Recording failed: {e}[/red]")
            return None
        except FileNotFoundError:
            console.print("[red]❌ Recording software (sox) not found[/red]")
            return None
    
    def interactive_conversation(self, medical_model, max_turns: int = 5):
        """Interactive voice conversation with medical AI"""
        console.print(Panel(
            "[bold green]🏥 Interactive Medical Voice Consultation[/bold green]\n"
            "Speak your symptoms and the AI doctor will respond with voice.\n"
            "Press Ctrl+C to exit.",
            title="Voice Medical Consultation"
        ))
        
        for turn in range(max_turns):
            try:
                console.print(f"\n[blue]Turn {turn + 1}/{max_turns}[/blue]")
                
                # Record patient input
                console.print("[yellow]🎤 Please describe your symptoms (5 seconds)...[/yellow]")
                audio_file = self.record_audio(duration=5)
                
                if not audio_file:
                    console.print("[red]❌ Could not record audio[/red]")
                    continue
                
                # Convert speech to text
                patient_text = self.speech_to_text(audio_file)
                if not patient_text:
                    console.print("[red]❌ Could not understand speech[/red]")
                    continue
                
                console.print(f"[cyan]Patient: {patient_text}[/cyan]")
                
                # Generate medical response (this would use your medical model)
                # For now, using a simple response
                medical_response = f"Based on your symptoms '{patient_text}', I recommend consulting with a healthcare professional for proper evaluation."
                
                console.print(f"[green]AI Doctor: {medical_response}[/green]")
                
                # Convert response to speech
                audio_response = self.text_to_speech(medical_response)
                
                if not audio_response:
                    console.print("[red]❌ Could not generate speech response[/red]")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Consultation ended by user[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]❌ Error in conversation: {e}[/red]")
                break

def create_voice_interface(config: VoiceConfig = None) -> Optional[VoiceInterface]:
    """Factory function to create voice interface"""
    try:
        interface = VoiceInterface(config)
        return interface
    except ImportError:
        console.print("[red]❌ Voice interface not available. Install required dependencies.[/red]")
        return None
