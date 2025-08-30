#!/usr/bin/env python3
"""
Enhanced MedBench CLI with Voice Integration
Multi-modal medical AI interface supporting text, voice, and image inputs
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import existing MedBench components
from .config import load_model_config, load_scenarios_config
from .models import load_pipeline
from .scenarios import SCENARIOS

# Import voice interface
try:
    from .voice_interface import VoiceInterface, VoiceConfig, create_voice_interface
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

console = Console()

class EnhancedMedBenchCLI:
    """Enhanced CLI with multi-modal capabilities"""
    
    def __init__(self):
        self.voice_interface = None
        self.models_config = None
        self.scenarios_config = None
        self.loaded_models = {}
        
    def setup_voice_interface(self, voice_config: VoiceConfig = None) -> bool:
        """Setup voice interface if available"""
        if not VOICE_AVAILABLE:
            console.print("[yellow]⚠️ Voice interface not available[/yellow]")
            return False
        
        self.voice_interface = create_voice_interface(voice_config)
        if self.voice_interface:
            # Load TTS and ASR models
            tts_loaded = self.voice_interface.load_tts_models()
            asr_loaded = self.voice_interface.load_asr_models()
            return tts_loaded or asr_loaded
        return False
    
    def load_configs(self, models_config_path: str, scenarios_config_path: str):
        """Load configuration files"""
        try:
            self.models_config = load_model_config(models_config_path)
            self.scenarios_config = load_scenarios_config(scenarios_config_path)
            console.print("[green]✅ Configurations loaded[/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to load configs: {e}[/red]")
            sys.exit(1)
    
    def run_text_scenario(self, model_key: str, scenario: str, input_text: str, 
                         voice_output: bool = False) -> Dict[str, Any]:
        """Run a medical scenario with text input"""
        try:
            # Load model if not already loaded
            if model_key not in self.loaded_models:
                console.print(f"[yellow]Loading model {model_key}...[/yellow]")
                self.loaded_models[model_key] = load_pipeline(model_key, self.models_config)
            
            model_pipeline = self.loaded_models[model_key]
            
            # Get scenario handler
            if scenario not in SCENARIOS:
                console.print(f"[red]❌ Unknown scenario: {scenario}[/red]")
                return {"error": f"Unknown scenario: {scenario}"}
            
            scenario_handler = SCENARIOS[scenario]
            
            # Create test case from input
            test_case = {"input": input_text}
            
            # Run scenario
            console.print(f"[blue]🔬 Running {scenario} scenario...[/blue]")
            result = scenario_handler.run_case(
                model_pipeline, 
                test_case, 
                self.models_config.defaults.get('generation', {})
            )
            
            # Display result
            console.print(Panel(
                f"[green]Input:[/green] {input_text}\n\n"
                f"[blue]Output:[/blue] {result['output']}\n\n"
                f"[magenta]Score:[/magenta] {result.get('score', 'N/A')}",
                title=f"{scenario.title()} Result"
            ))
            
            # Convert to speech if requested
            if voice_output and self.voice_interface:
                console.print("[yellow]🗣️ Converting response to speech...[/yellow]")
                self.voice_interface.text_to_speech(result['output'])
            
            return result
            
        except Exception as e:
            console.print(f"[red]❌ Error running scenario: {e}[/red]")
            return {"error": str(e)}
    
    def run_voice_scenario(self, model_key: str, scenario: str, 
                          audio_file: Optional[str] = None, 
                          record_duration: int = 5) -> Dict[str, Any]:
        """Run a medical scenario with voice input"""
        if not self.voice_interface:
            console.print("[red]❌ Voice interface not available[/red]")
            return {"error": "Voice interface not available"}
        
        try:
            # Get audio input
            if audio_file:
                console.print(f"[blue]👂 Processing audio file: {audio_file}[/blue]")
                input_audio = audio_file
            else:
                console.print(f"[blue]🎤 Recording audio for {record_duration} seconds...[/blue]")
                input_audio = self.voice_interface.record_audio(duration=record_duration)
                
                if not input_audio:
                    return {"error": "Failed to record audio"}
            
            # Convert speech to text
            input_text = self.voice_interface.speech_to_text(input_audio)
            if not input_text:
                return {"error": "Failed to transcribe audio"}
            
            console.print(f"[cyan]Transcribed: {input_text}[/cyan]")
            
            # Run text scenario with voice output
            return self.run_text_scenario(model_key, scenario, input_text, voice_output=True)
            
        except Exception as e:
            console.print(f"[red]❌ Error in voice scenario: {e}[/red]")
            return {"error": str(e)}
    
    def interactive_consultation(self, model_key: str, max_turns: int = 5):
        """Interactive voice consultation"""
        if not self.voice_interface:
            console.print("[red]❌ Voice interface not available[/red]")
            return

        console.print(Panel(
            "[bold green]🏥 Interactive Medical Voice Consultation[/bold green]\n"
            f"Model: {model_key}\n"
            f"Max turns: {max_turns}\n\n"
            "Speak your symptoms and the AI will respond with voice.\n"
            "Press Ctrl+C to exit.",
            title="Voice Medical Consultation"
        ))

        for turn in range(max_turns):
            try:
                console.print(f"\n[blue]═══ Turn {turn + 1}/{max_turns} ═══[/blue]")

                # Record patient input
                console.print("[yellow]🎤 Please describe your symptoms (5 seconds)...[/yellow]")
                audio_file = self.voice_interface.record_audio(duration=5)

                if not audio_file:
                    console.print("[red]❌ Could not record audio[/red]")
                    continue

                # Convert speech to text
                patient_text = self.voice_interface.speech_to_text(audio_file)
                if not patient_text:
                    console.print("[red]❌ Could not understand speech[/red]")
                    continue

                console.print(f"[cyan]👤 Patient: {patient_text}[/cyan]")

                # Run diagnosis scenario
                result = self.run_text_scenario(model_key, "diagnosis", patient_text, voice_output=True)

                if "error" in result:
                    console.print(f"[red]❌ Error: {result['error']}[/red]")
                    continue

            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Consultation ended by user[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]❌ Error in consultation: {e}[/red]")
                break

    def voice_to_voice_consultation(self, model_key: str, scenario: str = "diagnosis"):
        """Complete voice-to-voice medical consultation workflow"""
        console.print(Panel(
            "[bold green]🎤 Voice-to-Voice Medical Consultation[/bold green]\n\n"
            "[blue]Complete Workflow:[/blue]\n"
            "1. 🎤 Patient speaks symptoms\n"
            "2. 👂 AI transcribes speech\n"
            "3. 🧠 Medical AI analyzes symptoms\n"
            "4. 🗣️ AI generates voice response\n"
            "5. 🔊 Patient hears AI doctor's advice\n\n"
            f"[yellow]Model:[/yellow] {model_key}\n"
            f"[yellow]Scenario:[/yellow] {scenario}",
            title="Voice-to-Voice Consultation",
            border_style="green"
        ))

        try:
            # Import voice consultation module
            from .voice_consultation import create_voice_consultation

            # Create consultation system
            consultation = create_voice_consultation(model_key, scenario)
            if not consultation:
                console.print("[red]❌ Failed to create voice consultation system[/red]")
                return

            # Run the complete workflow
            success = consultation.run_consultation()

            if success:
                console.print("\n[bold green]🎉 Voice-to-voice consultation completed successfully![/bold green]")
            else:
                console.print("\n[red]❌ Voice-to-voice consultation failed[/red]")

        except ImportError:
            console.print("[red]❌ Voice consultation module not available[/red]")
        except Exception as e:
            console.print(f"[red]❌ Voice consultation error: {e}[/red]")
    
    def list_available_models(self):
        """List available models"""
        if not self.models_config:
            console.print("[red]❌ Models config not loaded[/red]")
            return
        
        table = Table(title="Available Medical AI Models")
        table.add_column("Model Key", style="cyan")
        table.add_column("Model ID", style="yellow")
        table.add_column("Capabilities", style="green")
        
        for key, config in self.models_config.models.items():
            capabilities = ", ".join(config.get("capabilities", ["general"]))
            table.add_row(key, config["model_id"], capabilities)
        
        console.print(table)
    
    def list_available_scenarios(self):
        """List available scenarios"""
        table = Table(title="Available Medical Scenarios")
        table.add_column("Scenario", style="cyan")
        table.add_column("Description", style="yellow")
        table.add_column("Input Type", style="green")
        
        scenario_descriptions = {
            "diagnosis": "Multi-symptom medical diagnosis",
            "drug_interactions": "Drug interaction analysis",
            "summarization": "Clinical note summarization",
            "cds": "Clinical decision support",
            "imaging": "Medical image analysis"
        }
        
        for scenario in SCENARIOS.keys():
            description = scenario_descriptions.get(scenario, "Medical analysis")
            input_type = "Text, Voice, or Image"
            table.add_row(scenario, description, input_type)
        
        console.print(table)

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Enhanced MedBench CLI with Voice Integration")
    
    # Basic arguments
    parser.add_argument("--models-config", default="configs/models.yaml", help="Models configuration file")
    parser.add_argument("--scenarios-config", default="configs/scenarios.yaml", help="Scenarios configuration file")
    parser.add_argument("--model-key", required=True, help="Model to use")
    parser.add_argument("--scenario", required=True, help="Scenario to run")
    
    # Input options
    parser.add_argument("--text", help="Text input for the scenario")
    parser.add_argument("--audio-file", help="Audio file for voice input")
    parser.add_argument("--record-duration", type=int, default=5, help="Recording duration in seconds")
    
    # Voice options
    parser.add_argument("--voice", action="store_true", help="Enable voice output")
    parser.add_argument("--voice-input", action="store_true", help="Use voice input (record from microphone)")
    parser.add_argument("--interactive", action="store_true", help="Interactive voice consultation")
    parser.add_argument("--voice-to-voice", action="store_true", help="Complete voice-to-voice consultation workflow")

    # Utility options
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--list-scenarios", action="store_true", help="List available scenarios")
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = EnhancedMedBenchCLI()
    
    # Load configurations
    cli.load_configs(args.models_config, args.scenarios_config)
    
    # Setup voice interface if needed
    if args.voice or args.voice_input or args.interactive or args.voice_to_voice:
        if not cli.setup_voice_interface():
            console.print("[red]❌ Could not setup voice interface[/red]")
            sys.exit(1)
    
    # Handle utility commands
    if args.list_models:
        cli.list_available_models()
        return
    
    if args.list_scenarios:
        cli.list_available_scenarios()
        return
    
    # Handle interactive consultation
    if args.interactive:
        cli.interactive_consultation(args.model_key)
        return

    # Handle voice-to-voice consultation
    if args.voice_to_voice:
        cli.voice_to_voice_consultation(args.model_key, args.scenario)
        return
    
    # Handle voice input
    if args.voice_input:
        result = cli.run_voice_scenario(
            args.model_key, 
            args.scenario, 
            args.audio_file, 
            args.record_duration
        )
        print(json.dumps(result, indent=2))
        return
    
    # Handle text input
    if args.text:
        result = cli.run_text_scenario(
            args.model_key, 
            args.scenario, 
            args.text, 
            args.voice
        )
        print(json.dumps(result, indent=2))
        return
    
    # No input provided
    console.print("[red]❌ No input provided. Use --text, --voice-input, or --interactive[/red]")
    parser.print_help()

if __name__ == "__main__":
    main()
