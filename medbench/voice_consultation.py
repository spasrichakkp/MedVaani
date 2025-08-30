#!/usr/bin/env python3
"""
Voice-to-Voice Medical Consultation Workflow
Complete pipeline: Patient Voice → ASR → Medical LLM → TTS → Audio Playback
"""

import time
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

try:
    from .voice_interface import VoiceInterface, VoiceConfig
    from .models import load_pipeline
    from .scenarios import SCENARIOS
    from .config import load_model_config
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    print(f"Import error: {e}")

console = Console()

@dataclass
class ConsultationStep:
    """Represents a step in the consultation workflow"""
    name: str
    description: str
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0

class VoiceToVoiceConsultation:
    """Complete voice-to-voice medical consultation workflow"""
    
    def __init__(self, model_key: str = "flan_t5_small", scenario: str = "diagnosis"):
        if not IMPORTS_AVAILABLE:
            raise ImportError("Required modules not available")
        
        self.model_key = model_key
        self.scenario = scenario
        self.voice_interface = None
        self.medical_model = None
        self.models_config = None
        
        # Workflow steps
        self.steps = [
            ConsultationStep("audio_capture", "🎤 Capturing patient voice input"),
            ConsultationStep("speech_to_text", "👂 Converting speech to text"),
            ConsultationStep("medical_analysis", "🧠 Analyzing symptoms with medical AI"),
            ConsultationStep("text_to_speech", "🗣️ Converting response to speech"),
            ConsultationStep("audio_playback", "🔊 Playing AI doctor response")
        ]
        
        # Audio settings
        self.recording_duration = 10  # seconds
        self.audio_dir = Path("consultation_audio")
        self.audio_dir.mkdir(exist_ok=True)
        
        console.print("[blue]🏥 Voice-to-Voice Medical Consultation System Initialized[/blue]")
    
    def setup_system(self) -> bool:
        """Initialize all system components"""
        console.print("\n[yellow]⚙️ Setting up consultation system...[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            # Setup voice interface
            task1 = progress.add_task("Initializing voice interface...", total=100)
            try:
                voice_config = VoiceConfig(
                    tts_model="microsoft/speecht5_tts",
                    asr_model="openai/whisper-small",
                    sample_rate=16000,
                    audio_output_dir=str(self.audio_dir)
                )
                
                from .voice_interface import create_voice_interface
                self.voice_interface = create_voice_interface(voice_config)
                
                if not self.voice_interface:
                    raise Exception("Failed to create voice interface")
                
                progress.update(task1, advance=50)
                
                # Load TTS models
                tts_success = self.voice_interface.load_tts_models()
                if not tts_success:
                    raise Exception("Failed to load TTS models")
                
                progress.update(task1, advance=25)
                
                # Load ASR models
                asr_success = self.voice_interface.load_asr_models()
                if not asr_success:
                    raise Exception("Failed to load ASR models")
                
                progress.update(task1, advance=25)
                console.print("[green]✅ Voice interface ready[/green]")
                
            except Exception as e:
                console.print(f"[red]❌ Voice interface setup failed: {e}[/red]")
                return False
            
            # Setup medical model
            task2 = progress.add_task("Loading medical AI model...", total=100)
            try:
                # Load model configuration
                self.models_config = load_model_config("configs/models.yaml")
                progress.update(task2, advance=30)
                
                # Load medical model pipeline
                self.medical_model = load_pipeline(self.model_key, self.models_config)
                progress.update(task2, advance=70)
                
                console.print(f"[green]✅ Medical model {self.model_key} ready[/green]")
                
            except Exception as e:
                console.print(f"[red]❌ Medical model setup failed: {e}[/red]")
                # Fallback to simple response generation
                self.medical_model = None
                console.print("[yellow]⚠️ Using fallback medical responses[/yellow]")
        
        return True
    
    def capture_patient_voice(self) -> Tuple[bool, Optional[str]]:
        """Step 1: Capture patient's voice input"""
        step = self.steps[0]
        step.status = "running"
        start_time = time.time()
        
        console.print(f"\n[blue]{step.description}[/blue]")
        console.print(f"[yellow]🎤 Please speak your medical question or symptoms for {self.recording_duration} seconds...[/yellow]")
        console.print("[yellow]Recording will start in 3 seconds...[/yellow]")
        
        # Countdown
        for i in range(3, 0, -1):
            console.print(f"[yellow]{i}...[/yellow]")
            time.sleep(1)
        
        console.print("[green]🔴 RECORDING NOW - Speak clearly![/green]")
        
        try:
            # Record audio
            audio_file = self.voice_interface.record_audio(
                duration=self.recording_duration,
                output_file=str(self.audio_dir / "patient_input.wav")
            )
            
            if audio_file:
                step.status = "completed"
                step.result = audio_file
                step.duration = time.time() - start_time
                console.print(f"[green]✅ Audio captured: {audio_file}[/green]")
                return True, audio_file
            else:
                raise Exception("Failed to record audio")
                
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            step.duration = time.time() - start_time
            console.print(f"[red]❌ Audio capture failed: {e}[/red]")
            return False, None
    
    def transcribe_speech(self, audio_file: str) -> Tuple[bool, Optional[str]]:
        """Step 2: Convert speech to text using Whisper ASR"""
        step = self.steps[1]
        step.status = "running"
        start_time = time.time()
        
        console.print(f"\n[blue]{step.description}[/blue]")
        
        try:
            # Transcribe audio using Whisper
            transcription = self.voice_interface.speech_to_text(audio_file)
            
            if transcription and transcription.strip():
                step.status = "completed"
                step.result = transcription
                step.duration = time.time() - start_time
                
                console.print(Panel(
                    f"[green]Patient says:[/green]\n\n[cyan]'{transcription}'[/cyan]",
                    title="🗣️ Speech Transcription",
                    border_style="green"
                ))
                return True, transcription
            else:
                raise Exception("No speech detected or transcription failed")
                
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            step.duration = time.time() - start_time
            console.print(f"[red]❌ Speech transcription failed: {e}[/red]")
            return False, None
    
    def analyze_with_medical_ai(self, patient_input: str) -> Tuple[bool, Optional[str]]:
        """Step 3: Analyze patient input with medical LLM"""
        step = self.steps[2]
        step.status = "running"
        start_time = time.time()
        
        console.print(f"\n[blue]{step.description}[/blue]")
        console.print("[yellow]🧠 Medical AI is analyzing your symptoms...[/yellow]")
        
        try:
            if self.medical_model and self.scenario in SCENARIOS:
                # Use actual medical model
                scenario_handler = SCENARIOS[self.scenario]
                test_case = {"input": patient_input}
                
                result = scenario_handler.run_case(
                    self.medical_model,
                    test_case,
                    self.models_config.defaults.get('generation', {})
                )
                
                medical_response = result.get('output', 'I apologize, but I could not analyze your symptoms properly.')
                
            else:
                # Fallback medical response generation
                medical_response = self._generate_fallback_response(patient_input)
            
            step.status = "completed"
            step.result = medical_response
            step.duration = time.time() - start_time
            
            console.print(Panel(
                f"[blue]AI Doctor responds:[/blue]\n\n[yellow]{medical_response}[/yellow]",
                title="🩺 Medical Analysis",
                border_style="blue"
            ))
            
            return True, medical_response
            
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            step.duration = time.time() - start_time
            console.print(f"[red]❌ Medical analysis failed: {e}[/red]")
            return False, None
    
    def generate_voice_response(self, medical_response: str) -> Tuple[bool, Optional[str]]:
        """Step 4: Convert medical response to speech using SpeechT5"""
        step = self.steps[3]
        step.status = "running"
        start_time = time.time()
        
        console.print(f"\n[blue]{step.description}[/blue]")
        
        try:
            # Generate speech from medical response
            audio_file = self.voice_interface.text_to_speech(
                medical_response,
                str(self.audio_dir / "ai_doctor_response.wav")
            )
            
            if audio_file:
                step.status = "completed"
                step.result = audio_file
                step.duration = time.time() - start_time
                console.print(f"[green]✅ AI doctor voice generated: {audio_file}[/green]")
                return True, audio_file
            else:
                raise Exception("Failed to generate speech")
                
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            step.duration = time.time() - start_time
            console.print(f"[red]❌ Voice generation failed: {e}[/red]")
            return False, None
    
    def play_ai_response(self, audio_file: str) -> bool:
        """Step 5: Play the AI doctor's voice response"""
        step = self.steps[4]
        step.status = "running"
        start_time = time.time()
        
        console.print(f"\n[blue]{step.description}[/blue]")
        console.print("[green]🔊 Playing AI doctor's response...[/green]")
        
        try:
            # Play audio using system audio player
            self.voice_interface._play_audio(audio_file)
            
            step.status = "completed"
            step.result = "Audio played successfully"
            step.duration = time.time() - start_time
            console.print("[green]✅ AI doctor response played[/green]")
            return True
            
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            step.duration = time.time() - start_time
            console.print(f"[red]❌ Audio playback failed: {e}[/red]")
            console.print(f"[yellow]💡 You can manually play: {audio_file}[/yellow]")
            return False
    
    def _generate_fallback_response(self, patient_input: str) -> str:
        """Generate a fallback medical response when LLM is not available"""
        # Simple keyword-based responses for demonstration
        input_lower = patient_input.lower()
        
        if any(word in input_lower for word in ["chest pain", "heart", "cardiac"]):
            return ("Based on your symptoms of chest pain, I recommend seeking immediate medical attention. "
                   "Chest pain can be a sign of serious cardiac conditions that require prompt evaluation by a healthcare professional. "
                   "Please consider calling emergency services or visiting the nearest emergency room.")
        
        elif any(word in input_lower for word in ["headache", "head pain", "migraine"]):
            return ("For headache symptoms, ensure you're staying hydrated and getting adequate rest. "
                   "If headaches are severe, persistent, or accompanied by other symptoms like vision changes or fever, "
                   "please consult with a healthcare provider for proper evaluation.")
        
        elif any(word in input_lower for word in ["fever", "temperature", "hot"]):
            return ("Fever can indicate an infection or other medical condition. "
                   "Monitor your temperature, stay hydrated, and rest. "
                   "If fever persists above 101°F (38.3°C) or is accompanied by severe symptoms, "
                   "please contact a healthcare provider.")
        
        else:
            return ("Thank you for describing your symptoms. Based on what you've told me, "
                   "I recommend consulting with a qualified healthcare professional for proper evaluation and diagnosis. "
                   "They can provide personalized medical advice based on your complete medical history and physical examination.")
    
    def run_consultation(self) -> bool:
        """Execute the complete voice-to-voice consultation workflow"""
        console.print(Panel(
            "[bold green]🏥 Voice-to-Voice Medical Consultation[/bold green]\n\n"
            "[blue]Complete Workflow:[/blue]\n"
            "1. 🎤 Patient speaks symptoms\n"
            "2. 👂 AI transcribes speech\n"
            "3. 🧠 Medical AI analyzes symptoms\n"
            "4. 🗣️ AI generates voice response\n"
            "5. 🔊 Patient hears AI doctor's advice",
            title="Medical Consultation Workflow",
            border_style="green"
        ))
        
        # Setup system
        if not self.setup_system():
            console.print("[red]❌ System setup failed. Cannot proceed with consultation.[/red]")
            return False
        
        console.print("\n[green]🚀 Starting voice-to-voice medical consultation...[/green]")
        
        # Step 1: Capture patient voice
        success, audio_file = self.capture_patient_voice()
        if not success:
            return False
        
        # Step 2: Transcribe speech
        success, transcription = self.transcribe_speech(audio_file)
        if not success:
            return False
        
        # Step 3: Medical AI analysis
        success, medical_response = self.analyze_with_medical_ai(transcription)
        if not success:
            return False
        
        # Step 4: Generate voice response
        success, response_audio = self.generate_voice_response(medical_response)
        if not success:
            return False
        
        # Step 5: Play AI response
        success = self.play_ai_response(response_audio)
        
        # Show consultation summary
        self.show_consultation_summary()
        
        return True
    
    def show_consultation_summary(self):
        """Display a summary of the consultation workflow"""
        console.print("\n[bold blue]📊 Consultation Summary[/bold blue]")
        
        from rich.table import Table
        table = Table(title="Workflow Steps Performance")
        table.add_column("Step", style="cyan")
        table.add_column("Description", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Duration", justify="right", style="magenta")
        
        for step in self.steps:
            status_icon = {
                "completed": "✅",
                "failed": "❌",
                "running": "🔄",
                "pending": "⏳"
            }.get(step.status, "❓")
            
            duration_str = f"{step.duration:.2f}s" if step.duration > 0 else "-"
            
            table.add_row(
                step.name.replace("_", " ").title(),
                step.description,
                f"{status_icon} {step.status.title()}",
                duration_str
            )
        
        console.print(table)
        
        # Show total time
        total_time = sum(step.duration for step in self.steps)
        console.print(f"\n[blue]⏱️ Total consultation time: {total_time:.2f} seconds[/blue]")
        
        # Show generated files
        console.print(f"\n[yellow]📁 Generated files in {self.audio_dir}:[/yellow]")
        for audio_file in self.audio_dir.glob("*.wav"):
            console.print(f"  • {audio_file.name}")

def create_voice_consultation(model_key: str = "flan_t5_small", scenario: str = "diagnosis") -> Optional[VoiceToVoiceConsultation]:
    """Factory function to create voice consultation system"""
    try:
        return VoiceToVoiceConsultation(model_key, scenario)
    except Exception as e:
        console.print(f"[red]❌ Failed to create voice consultation system: {e}[/red]")
        return None
